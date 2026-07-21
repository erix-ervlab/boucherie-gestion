"""Import idempotent de l'export de caisse GDPdU (CAS CT100 / libraVISOR).

Règles (cf. docs/cahier-des-charges-gestion-boucherie.md §3.1) :
- CSV cp1252, séparateur `;`, une ligne par mouvement ;
- ne garder que `Type_enregistrement == 1` (lignes de vente) ;
- exclure les `Annulation == True` du CA/kg (mais on peut les archiver
  avec le drapeau `annule` pour la traçabilité fiscale) ;
- dédupliquer les copies de ticket ;
- upsert sur la clé métier -> réimporter un export chevauchant ne
  duplique rien ;
- détecter les trous dans la séquence des `Numéro_Rapport_Z`.

⚠️ CALIBRAGE REQUIS : le mapping exact des en-têtes de colonnes GDPdU
n'est PAS encore figé — il doit être établi sur un VRAI export (le
fichier `index.xml` / la DTD GDPdU donnent les noms officiels). Tant
que `COLUMN_MAP` n'est pas complété, `normalize()` lève une erreur
explicite. Le reste (upsert, détection de trous, journal) est réel et
opérationnel.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..models import ImportJournal, VenteLigne

# Clé métier -> colonnes de VenteLigne composant la contrainte d'unicité.
BUSINESS_KEY = (
    "id_sd_device",
    "numero_rapport_z",
    "numero_ticket",
    "type_enregistrement",
    "n_plu",
    "poids_gramme",
    "montant",
    "position_ticket",
)

# TODO(calibrage sur export réel) : associer chaque champ interne au nom
# exact de la colonne dans l'export GDPdU. Renseigner à partir d'un vrai
# fichier + son index.xml. Laisser vide déclenche une erreur claire.
COLUMN_MAP: dict[str, str] = {
    # "id_sd_device":        "ID_SD_Device",
    # "numero_rapport_z":    "Numéro_Rapport_Z",
    # "numero_ticket":       "Numéro_Ticket",
    # "type_enregistrement": "Type_enregistrement",
    # "n_plu":               "N_PLU",
    # "poids_gramme":        "Poids_Gramme",
    # "montant":             "Montant",
    # "annule":              "Annulation",
    # "copie_ticket":        "Copie ticket",
    # "horodatage":          "Date_Heure",
}


@dataclass
class ImportResult:
    fichier_nom: str
    nb_lignes_ajoutees: int = 0
    nb_lignes_deja_connues: int = 0
    nb_lignes_ignorees: int = 0
    z_min: int | None = None
    z_max: int | None = None
    trous_z: list[int] = field(default_factory=list)


def detect_z_gaps(known_z: set[int], incoming_z: set[int]) -> list[int]:
    """Numéros de rapport Z manquants dans l'intervalle [min, max] observé.

    Les Z sont séquentiels : tout numéro absent entre le plus petit et le
    plus grand connus signale un export potentiellement incomplet.
    """
    all_z = known_z | incoming_z
    if not all_z:
        return []
    lo, hi = min(all_z), max(all_z)
    return [z for z in range(lo, hi + 1) if z not in all_z]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Applique le nettoyage métier et renomme vers le schéma interne.

    Lève une erreur explicite tant que le mapping de colonnes n'est pas
    calibré sur un export réel.
    """
    if not COLUMN_MAP:
        raise NotImplementedError(
            "Mapping GDPdU non calibré : compléter COLUMN_MAP dans "
            "app/importers/gdpdu.py à partir d'un export réel (voir index.xml). "
            "Le reste de la chaîne d'import (upsert, détection de trous, "
            "journal) est prêt."
        )

    missing = [src for src in COLUMN_MAP.values() if src not in df.columns]
    if missing:
        raise ValueError(f"Colonnes attendues absentes de l'export : {missing}")

    renamed = df.rename(columns={v: k for k, v in COLUMN_MAP.items()})

    # Ne garder que les lignes de vente (Type_enregistrement == 1).
    renamed = renamed[renamed["type_enregistrement"].astype(int) == 1]

    # Dédoublonner les copies d'impression de ticket si la colonne existe.
    if "copie_ticket" in renamed.columns:
        renamed = renamed[~renamed["copie_ticket"].astype(str).str.lower().isin(
            {"true", "1", "vrai", "oui"}
        )]

    return renamed


def import_ventes(
    db: Session,
    file_bytes: bytes,
    fichier_nom: str,
) -> ImportResult:
    """Importe un export GDPdU : nettoie, upsert idempotent, journalise."""
    df = pd.read_csv(io.BytesIO(file_bytes), sep=";", encoding="cp1252", dtype=str)
    clean = normalize(df)

    incoming_z = {int(z) for z in clean["numero_rapport_z"].dropna().unique()}
    known_z = {
        z for (z,) in db.query(VenteLigne.numero_rapport_z).distinct().all()
    }
    trous = detect_z_gaps(known_z, incoming_z)

    rows = clean.to_dict("records")
    result = ImportResult(fichier_nom=fichier_nom)
    result.trous_z = trous
    result.z_min = min(incoming_z) if incoming_z else None
    result.z_max = max(incoming_z) if incoming_z else None

    if rows:
        stmt = (
            pg_insert(VenteLigne)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_vente_ligne_cle_metier")
        )
        res = db.execute(stmt)
        result.nb_lignes_ajoutees = res.rowcount or 0
        result.nb_lignes_deja_connues = len(rows) - result.nb_lignes_ajoutees

    journal = ImportJournal(
        fichier_nom=fichier_nom,
        nb_lignes_ajoutees=result.nb_lignes_ajoutees,
        nb_lignes_deja_connues=result.nb_lignes_deja_connues,
        nb_lignes_ignorees=len(df) - len(clean),
        nb_anomalies=len(trous),
        anomalies=json.dumps({"trous_z": trous}) if trous else None,
        z_min=result.z_min,
        z_max=result.z_max,
    )
    db.add(journal)
    db.commit()
    return result
