"""Lecture IA d'une facture fournisseur PDF (Claude + sortie structurée).

Claude lit le PDF et renvoie les lignes au format JSON (schéma imposé via
`output_config.format`). Pour chaque ligne produit, deux niveaux de
pré-affectation de la famille :
  1. la **correspondance apprise** (réf fournisseur -> famille) si elle
     existe -> marquée `connu` (fiable) ;
  2. sinon, une **suggestion de l'IA** d'après la désignation, piochée
     dans la liste des familles existantes -> marquée `suggere`.
Le résultat reste un BROUILLON à vérifier/corriger par un humain.
"""

from __future__ import annotations

import base64
import json

import anthropic
from sqlalchemy.orm import Session

from ..modeles import resoudre
from ..models import CorrespondanceFournisseur, Famille, Fournisseur

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
  - `famille_suggeree` : la famille la plus probable de l'article, PARMI la
    liste de familles fournie ci-dessous, d'après la désignation (ex.
    « AIGUILLETTE DE POULET » -> Volaille, « CÔTE DE BŒUF » -> Bœuf,
    « JAMBON » -> Charcuterie ou Porc selon le cas). Mets « Aucune » si tu
    hésites vraiment ou pour une ligne non-produit (frais).
- N'invente aucune valeur : mets null si une information est absente.
"""


def _construire_schema(noms_familles: list[str]) -> dict:
    ligne = {
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
            "famille_suggeree": {"type": "string", "enum": noms_familles + ["Aucune"]},
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
            "famille_suggeree",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "fournisseur": {"type": "string"},
            "numero_facture": {"type": "string"},
            "date_facture": {"type": "string"},
            "montant_ht": {"type": ["number", "null"]},
            "montant_tva": {"type": ["number", "null"]},
            "montant_ttc": {"type": ["number", "null"]},
            "lignes": {"type": "array", "items": ligne},
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


def extraire(
    db: Session, file_bytes: bytes, fichier_nom: str, modele: str | None = None
) -> dict:
    familles = db.query(Famille).order_by(Famille.nom).all()
    noms = [f.nom for f in familles]
    nom_to_id = {f.nom.strip().lower(): f.id for f in familles}

    schema = _construire_schema(noms)
    system = (
        EXTRACT_SYSTEM
        + "\n\nFamilles disponibles pour `famille_suggeree` : "
        + ", ".join(noms)
        + "."
    )

    b64 = base64.standard_b64encode(file_bytes).decode("ascii")
    # 16000 : les modèles récents (Sonnet 5, Opus) raisonnent par défaut
    # (thinking adaptatif) avant d'émettre le JSON ; 8000 était épuisé par
    # la seule réflexion sur les grosses factures -> réponse vide.
    resp = _client.messages.create(
        model=resoudre(modele, usage="facture"),
        max_tokens=16000,
        system=system,
        output_config={"format": {"type": "json_schema", "schema": schema}},
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
    if not texte.strip():
        # Réponse sans texte : quasi toujours max_tokens épuisé par la
        # réflexion. Message explicite plutôt qu'une erreur JSON obscure.
        raise ValueError(
            "Le modèle n'a pas renvoyé de résultat "
            f"(arrêt : {resp.stop_reason}). Réessaie, éventuellement avec un "
            "autre modèle."
        )
    data = json.loads(texte)

    # Rapprochement fournisseur.
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
        if c:  # affectation déjà apprise pour ce fournisseur -> fiable
            ligne["famille_id"] = c.famille_id
            ligne["sous_famille_id"] = c.sous_famille_id
            ligne["gamme_id"] = c.gamme_id
            ligne["connu"] = True
            ligne["suggere"] = False
        else:  # sinon, suggestion de l'IA d'après la désignation
            sug = (ligne.get("famille_suggeree") or "").strip()
            fid = nom_to_id.get(sug.lower()) if sug and sug.lower() != "aucune" else None
            ligne["famille_id"] = fid
            ligne["sous_famille_id"] = None
            ligne["gamme_id"] = None
            ligne["connu"] = False
            ligne["suggere"] = bool(fid)

    data["fichier_nom"] = fichier_nom
    return data
