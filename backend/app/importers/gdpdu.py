"""Import idempotent de l'export de caisse GDPdU (CAS CT100 / libraVISOR).

CALIBRÉ sur un export réel (samples/ventes/, device 441FB12F789B9B93).
Le CSV réel est en **cp1252**, séparateur `;`, **décimale = virgule**,
en-tête français sur la 1re ligne, 43 colonnes. Les noms de colonnes
diffèrent des noms « officiels » de l'index.xml (spec GDPdU) — on mappe
sur les en-têtes réellement présents.

Règles (cf. docs/cahier-des-charges-gestion-boucherie.md §3.1) :
- ne garder que `Type_enregistrement == 1` (lignes de vente) ; les
  totaux (2), grands totaux (3) et paiements (4) ne sont pas stockés ;
- exclure les `Copie ticket == True` (doublons d'impression) ;
- garder les `Annulation == True` mais avec le drapeau `annule` — elles
  ne doivent JAMAIS être comptées dans le CA/kg (validé : le total-ticket
  brut les inclut, d'où l'écart avec la somme des lignes comptées) ;
- upsert sur la clé métier -> réimporter un export chevauchant ne
  duplique rien ;
- détecter les trous dans la séquence des `Numéro_Rapport_Z`.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..models import ImportJournal, VenteLigne

# Champ interne -> en-tête réel de l'export libraVISOR CT100.
COL = {
    "id_sd_device": "ID_SD_Device",
    "copie_ticket": "Copie ticket",
    "annulation": "Annulation",
    "type_enregistrement": "Type_enregistrement",
    "type_vente": "Type_vente",
    "numero_rapport_z": "Numéro_Rapport_Z",
    "numero_ticket": "Numéro_Ticket",
    "date": "Ticket_Date",
    "heure": "Ticket_Heure",
    "numero_vendeur": "Numéro_vendeur",
    "n_plu": "N_PLU",
    "nom_plu": "Nom_PLU",
    "poids_gramme": "Poids_Gramme",
    "prix_plu": "Prix_PLU",
    "taux_tva": "Taux_TVA",
    "montant": "Montant",
}


@dataclass
class ImportResult:
    fichier_nom: str
    nb_lignes_ajoutees: int = 0
    nb_lignes_deja_connues: int = 0
    nb_lignes_ignorees: int = 0  # types != 1, copies
    nb_annulations: int = 0
    z_min: int | None = None
    z_max: int | None = None
    trous_z: list[int] = field(default_factory=list)


def _is_true(v: str | None) -> bool:
    return (v or "").strip().lower() == "true"


def _dec(s: str | None) -> Decimal:
    """Parse un nombre en format européen (séparateur milliers '.', décimale ',')."""
    s = (s or "").strip().replace(".", "").replace(",", ".")
    if s in ("", "-"):
        return Decimal("0")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _int(s: str | None) -> int:
    s = (s or "").strip()
    try:
        return int(s)
    except ValueError:
        return 0


def _date(s: str | None) -> date | None:
    s = (s or "").strip().strip('"')
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


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


def _normalize(all_rows: list[dict]) -> tuple[list[dict], int]:
    """Nettoie et convertit les lignes de vente. Retourne (lignes, nb_ignorées)."""
    position: dict[tuple[int, int], int] = {}
    out: list[dict] = []
    ignored = 0

    for r in all_rows:
        if (r.get(COL["type_enregistrement"]) or "").strip() != "1":
            ignored += 1
            continue
        if _is_true(r.get(COL["copie_ticket"])):
            ignored += 1
            continue

        z = _int(r.get(COL["numero_rapport_z"]))
        ticket = _int(r.get(COL["numero_ticket"]))
        pos = position.get((z, ticket), 0)
        position[(z, ticket)] = pos + 1

        d = _date(r.get(COL["date"]))
        heure = (r.get(COL["heure"]) or "").strip().strip('"')
        horod: datetime | None = None
        if d and heure:
            try:
                horod = datetime.combine(d, datetime.strptime(heure, "%H:%M").time())
            except ValueError:
                horod = None

        out.append(
            {
                "id_sd_device": (r.get(COL["id_sd_device"]) or "").strip().strip('"'),
                "numero_rapport_z": z,
                "numero_ticket": ticket,
                "type_enregistrement": 1,
                "type_vente": (r.get(COL["type_vente"]) or "").strip() or None,
                "n_plu": (r.get(COL["n_plu"]) or "").strip(),
                "nom_plu": (r.get(COL["nom_plu"]) or "").strip().strip('"') or None,
                "poids_gramme": _int(r.get(COL["poids_gramme"])),
                "prix_unitaire": _dec(r.get(COL["prix_plu"])),
                "taux_tva": _dec(r.get(COL["taux_tva"])),
                "montant": _dec(r.get(COL["montant"])),
                "position_ticket": pos,
                "numero_vendeur": (r.get(COL["numero_vendeur"]) or "").strip() or None,
                "date_vente": d,
                "horodatage": horod,
                "annule": _is_true(r.get(COL["annulation"])),
            }
        )

    return out, ignored


def import_ventes(db: Session, file_bytes: bytes, fichier_nom: str) -> ImportResult:
    """Importe un export GDPdU : nettoie, upsert idempotent, journalise."""
    text = file_bytes.decode("cp1252")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")

    missing = [src for src in COL.values() if src not in (reader.fieldnames or [])]
    if missing:
        raise ValueError(
            "Colonnes attendues absentes de l'export (format inattendu) : "
            + ", ".join(missing)
        )

    rows, ignored = _normalize(list(reader))

    incoming_z = {r["numero_rapport_z"] for r in rows}
    known_z = {z for (z,) in db.query(VenteLigne.numero_rapport_z).distinct().all()}
    trous = detect_z_gaps(known_z, incoming_z)

    result = ImportResult(fichier_nom=fichier_nom)
    result.nb_lignes_ignorees = ignored
    result.nb_annulations = sum(1 for r in rows if r["annule"])
    result.trous_z = trous
    result.z_min = min(incoming_z) if incoming_z else None
    result.z_max = max(incoming_z) if incoming_z else None

    if rows:
        # rowcount du ON CONFLICT DO NOTHING n'est pas fiable (psycopg3
        # renvoie -1) : on compte réellement avant/après.
        before = db.query(func.count()).select_from(VenteLigne).scalar() or 0
        stmt = (
            pg_insert(VenteLigne)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_vente_ligne_cle_metier")
        )
        db.execute(stmt)
        db.flush()
        after = db.query(func.count()).select_from(VenteLigne).scalar() or 0
        result.nb_lignes_ajoutees = after - before
        result.nb_lignes_deja_connues = len(rows) - result.nb_lignes_ajoutees

    dates = [r["date_vente"] for r in rows if r["date_vente"]]
    journal = ImportJournal(
        fichier_nom=fichier_nom,
        periode_debut=min(dates) if dates else None,
        periode_fin=max(dates) if dates else None,
        nb_lignes_ajoutees=result.nb_lignes_ajoutees,
        nb_lignes_deja_connues=result.nb_lignes_deja_connues,
        nb_lignes_ignorees=ignored,
        nb_anomalies=len(trous),
        anomalies=json.dumps({"trous_z": trous}) if trous else None,
        z_min=result.z_min,
        z_max=result.z_max,
    )
    db.add(journal)

    from ..journal import enregistrer

    enregistrer(
        db,
        "import",
        "ventes",
        f"Import ventes « {fichier_nom} » : {result.nb_lignes_ajoutees} lignes ajoutées, "
        f"{result.nb_lignes_deja_connues} déjà connues"
        + (f", {len(trous)} trou(s) de Z" if trous else ""),
        details={"z_min": result.z_min, "z_max": result.z_max},
    )

    db.commit()
    return result
