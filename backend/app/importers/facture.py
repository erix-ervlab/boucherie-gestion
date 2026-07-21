"""Lecture IA d'une facture fournisseur PDF (Claude + sortie structurée).

Claude lit le PDF et renvoie les lignes au format JSON (schéma imposé via
`output_config.format`). On rapproche ensuite le fournisseur et on
pré-affecte les familles connues via la table de correspondance
apprenante. Le résultat est un BROUILLON à vérifier/corriger par un
humain avant enregistrement (cf. cahier §4.2 — vérification obligatoire).
"""

from __future__ import annotations

import base64
import json

import anthropic
from sqlalchemy.orm import Session

from ..config import settings
from ..models import CorrespondanceFournisseur, Fournisseur

_client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY dans l'environnement

EXTRACT_SYSTEM = """Tu extrais les données d'une facture fournisseur d'une boucherie.
Renvoie STRICTEMENT le JSON demandé (schéma imposé), rien d'autre.

Consignes :
- En-tête : nom du fournisseur, numéro de facture, date (format AAAA-MM-JJ),
  et les totaux Total HT / Total TVA / Total TTC.
- Une entrée par ligne d'article. Pour chaque ligne :
  - `reference` : la référence fournisseur (colonne Réf, ex « 233001-00 »).
  - `designation` : le libellé de l'article.
  - `poids_kg` : le poids facturé en kg si l'article est au poids, sinon null.
  - `quantite` : le nombre de pièces si vendu à la pièce, sinon null.
  - `unite` : « Kg » ou « Pce ».
  - `prix_unitaire` : le prix unitaire net (€/kg ou €/pièce).
  - `montant_ht` : le montant HT de la ligne.
  - `taux_tva` : 5.5 pour la viande / l'alimentaire, 20 pour les services
    (frais de port, contributions). Déduis-le de la colonne de TVA si présente.
  - `numero_lot` : le numéro de lot (« Lot N. … ») s'il y en a un, sinon null.
  - `origine` : l'info espèce/pays (« espece : VEAU pays abattage : FRANCE… »)
    résumée, sinon null.
  - `est_produit` : true pour la marchandise (viande, charcuterie, traiteur…) ;
    **false** pour tout ce qui n'est pas de la marchandise : participation/frais
    de port, cotisations Interbev, CVO, surcoût gasoil, redevance sanitaire,
    contributions diverses, taxes.
- N'invente aucune valeur : mets null si une information est absente.
"""

_LIGNE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "reference": {"type": "string"},
        "designation": {"type": "string"},
        "quantite": {"type": ["number", "null"]},
        "poids_kg": {"type": ["number", "null"]},
        "unite": {"type": ["string", "null"]},
        "prix_unitaire": {"type": ["number", "null"]},
        "montant_ht": {"type": "number"},
        "taux_tva": {"type": ["number", "null"]},
        "numero_lot": {"type": ["string", "null"]},
        "origine": {"type": ["string", "null"]},
        "est_produit": {"type": "boolean"},
    },
    "required": [
        "reference",
        "designation",
        "quantite",
        "poids_kg",
        "unite",
        "prix_unitaire",
        "montant_ht",
        "taux_tva",
        "numero_lot",
        "origine",
        "est_produit",
    ],
}

FACTURE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "fournisseur": {"type": "string"},
        "numero_facture": {"type": "string"},
        "date_facture": {"type": "string"},
        "montant_ht": {"type": ["number", "null"]},
        "montant_tva": {"type": ["number", "null"]},
        "montant_ttc": {"type": ["number", "null"]},
        "lignes": {"type": "array", "items": _LIGNE_SCHEMA},
    },
    "required": [
        "fournisseur",
        "numero_facture",
        "date_facture",
        "montant_ht",
        "montant_tva",
        "montant_ttc",
        "lignes",
    ],
}


def _match_fournisseur(db: Session, nom: str) -> Fournisseur | None:
    nom_l = (nom or "").strip().lower()
    if not nom_l:
        return None
    for f in db.query(Fournisseur).all():
        fl = (f.nom or "").lower()
        if fl and (fl in nom_l or nom_l in fl):
            return f
    return None


def extraire(db: Session, file_bytes: bytes, fichier_nom: str) -> dict:
    b64 = base64.standard_b64encode(file_bytes).decode("ascii")
    resp = _client.messages.create(
        model=settings.copilot_model,
        max_tokens=8000,
        system=EXTRACT_SYSTEM,
        output_config={"format": {"type": "json_schema", "schema": FACTURE_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": "Extrais cette facture fournisseur."},
                ],
            }
        ],
    )
    texte = "".join(b.text for b in resp.content if b.type == "text")
    data = json.loads(texte)

    # Rapprochement fournisseur + pré-affectation des familles connues.
    fournisseur = _match_fournisseur(db, data.get("fournisseur", ""))
    data["fournisseur_id"] = fournisseur.id if fournisseur else None

    corr: dict[str, CorrespondanceFournisseur] = {}
    if fournisseur:
        for c in db.query(CorrespondanceFournisseur).filter_by(
            fournisseur_id=fournisseur.id
        ):
            corr[c.reference_fournisseur] = c

    for ligne in data.get("lignes", []):
        c = corr.get(ligne.get("reference"))
        ligne["famille_id"] = c.famille_id if c else None
        ligne["sous_famille_id"] = c.sous_famille_id if c else None
        ligne["connu"] = bool(c)  # affectation déjà mémorisée ?

    data["fichier_nom"] = fichier_nom
    return data
