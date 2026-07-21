"""Achats — factures fournisseurs : lecture IA, validation, consultation."""

from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Achat, AchatLigne, CorrespondanceFournisseur, Fournisseur

router = APIRouter(prefix="/achats", tags=["achats"])


# --- Schémas d'entrée (validation humaine du brouillon) ---
class LigneIn(BaseModel):
    reference_fournisseur: str | None = None
    designation: str
    quantite: float | None = None
    poids_kg: float | None = None
    unite: str | None = None
    prix_unitaire: float | None = None
    montant_ht: float
    taux_tva: float | None = None
    numero_lot: str | None = None
    origine: str | None = None
    est_produit: bool = True
    famille_id: int | None = None
    sous_famille_id: int | None = None


class AchatIn(BaseModel):
    fournisseur_id: int | None = None
    fournisseur_nom: str | None = None
    numero_facture: str
    date_facture: date | None = None
    montant_ht: float | None = None
    montant_tva: float | None = None
    montant_ttc: float | None = None
    fichier_nom: str | None = None
    lignes: list[LigneIn]


def _apprendre(db: Session, fournisseur_id: int, lignes: list[LigneIn]) -> int:
    """Mémorise réf -> famille pour les lignes produits affectées. Retourne le
    nombre de nouvelles correspondances créées (les autres sont mises à jour)."""
    nouveaux = 0
    for l in lignes:
        if l.est_produit and l.reference_fournisseur and l.famille_id:
            corr = (
                db.query(CorrespondanceFournisseur)
                .filter_by(
                    fournisseur_id=fournisseur_id,
                    reference_fournisseur=l.reference_fournisseur,
                )
                .first()
            )
            if corr is None:
                corr = CorrespondanceFournisseur(
                    fournisseur_id=fournisseur_id,
                    reference_fournisseur=l.reference_fournisseur,
                )
                db.add(corr)
                nouveaux += 1
            corr.famille_id = l.famille_id
            corr.sous_famille_id = l.sous_famille_id
            corr.designation = l.designation
    return nouveaux


def _resoudre_fournisseur(db: Session, payload: AchatIn) -> Fournisseur | None:
    if payload.fournisseur_id:
        f = db.get(Fournisseur, payload.fournisseur_id)
        if f:
            return f
    if payload.fournisseur_nom:
        nom = payload.fournisseur_nom.strip()
        f = db.query(Fournisseur).filter(Fournisseur.nom.ilike(nom)).first()
        if f is None:
            f = Fournisseur(nom=nom)
            db.add(f)
            db.flush()
        return f
    return None


@router.post("/extraire")
async def extraire(
    file: UploadFile = File(...),
    modele: str | None = Form(None),
    db: Session = Depends(get_db),
):
    """Lecture IA d'une facture PDF. Renvoie un brouillon (non enregistré)."""
    if not settings.anthropic_api_key:
        raise HTTPException(503, "Lecture IA indisponible : ANTHROPIC_API_KEY absente.")
    content = await file.read()
    from ..importers import facture as facture_mod  # import différé (SDK anthropic)

    try:
        return facture_mod.extraire(db, content, file.filename or "facture.pdf", modele)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(500, f"Échec de la lecture IA : {e}")


@router.post("")
def creer(payload: AchatIn, db: Session = Depends(get_db)):
    """Enregistre une facture validée + mémorise les correspondances (apprentissage)."""
    fournisseur = _resoudre_fournisseur(db, payload)
    if fournisseur is None:
        raise HTTPException(422, "Fournisseur manquant (id ou nom requis).")

    # Idempotence : une facture (fournisseur + numéro) ne s'enregistre pas 2 fois.
    existant = (
        db.query(Achat)
        .filter_by(fournisseur_id=fournisseur.id, numero_facture=payload.numero_facture)
        .first()
    )
    if existant:
        raise HTTPException(
            409, f"Facture {payload.numero_facture} déjà enregistrée (achat n°{existant.id})."
        )

    achat = Achat(
        fournisseur_id=fournisseur.id,
        numero_facture=payload.numero_facture,
        date_facture=payload.date_facture,
        montant_ht=payload.montant_ht,
        montant_tva=payload.montant_tva,
        montant_ttc=payload.montant_ttc,
        fichier_nom=payload.fichier_nom,
        statut="valide",
    )
    for l in payload.lignes:
        achat.lignes.append(AchatLigne(**l.model_dump()))
    db.add(achat)
    db.flush()

    appris = _apprendre(db, fournisseur.id, payload.lignes)

    db.commit()
    db.refresh(achat)
    return {
        "id": achat.id,
        "fournisseur": fournisseur.nom,
        "nb_lignes": len(achat.lignes),
        "correspondances_apprises": appris,
    }


@router.put("/{achat_id}")
def modifier(achat_id: int, payload: AchatIn, db: Session = Depends(get_db)):
    """Modifie une facture existante (en-tête + lignes remplacées) et réapprend."""
    achat = db.get(Achat, achat_id)
    if achat is None:
        raise HTTPException(404, "Achat introuvable")

    fournisseur = _resoudre_fournisseur(db, payload) or db.get(
        Fournisseur, achat.fournisseur_id
    )
    if fournisseur is None:
        raise HTTPException(422, "Fournisseur manquant.")

    # Pas de doublon (fournisseur + numéro) sur une AUTRE facture.
    dup = (
        db.query(Achat)
        .filter(
            Achat.fournisseur_id == fournisseur.id,
            Achat.numero_facture == payload.numero_facture,
            Achat.id != achat_id,
        )
        .first()
    )
    if dup:
        raise HTTPException(
            409, f"Une autre facture {payload.numero_facture} existe déjà (n°{dup.id})."
        )

    achat.fournisseur_id = fournisseur.id
    achat.numero_facture = payload.numero_facture
    achat.date_facture = payload.date_facture
    achat.montant_ht = payload.montant_ht
    achat.montant_tva = payload.montant_tva
    achat.montant_ttc = payload.montant_ttc
    if payload.fichier_nom:
        achat.fichier_nom = payload.fichier_nom

    # Remplacement complet des lignes (cascade delete-orphan).
    achat.lignes.clear()
    db.flush()
    for l in payload.lignes:
        achat.lignes.append(AchatLigne(**l.model_dump()))
    db.flush()

    appris = _apprendre(db, fournisseur.id, payload.lignes)

    db.commit()
    db.refresh(achat)
    return {
        "id": achat.id,
        "fournisseur": fournisseur.nom,
        "nb_lignes": len(achat.lignes),
        "correspondances_apprises": appris,
    }


@router.get("")
def lister(db: Session = Depends(get_db)):
    achats = (
        db.query(Achat)
        .order_by(Achat.date_facture.desc().nullslast(), Achat.id.desc())
        .limit(200)
        .all()
    )
    noms = {f.id: f.nom for f in db.query(Fournisseur).all()}
    return [
        {
            "id": a.id,
            "fournisseur": noms.get(a.fournisseur_id),
            "numero_facture": a.numero_facture,
            "date_facture": a.date_facture.isoformat() if a.date_facture else None,
            "montant_ht": float(a.montant_ht) if a.montant_ht is not None else None,
            "montant_ttc": float(a.montant_ttc) if a.montant_ttc is not None else None,
            "nb_lignes": len(a.lignes),
        }
        for a in achats
    ]


@router.get("/{achat_id}")
def detail(achat_id: int, db: Session = Depends(get_db)):
    a = db.get(Achat, achat_id)
    if a is None:
        raise HTTPException(404, "Achat introuvable")
    f = db.get(Fournisseur, a.fournisseur_id)
    return {
        "id": a.id,
        "fournisseur": f.nom if f else None,
        "fournisseur_id": a.fournisseur_id,
        "numero_facture": a.numero_facture,
        "date_facture": a.date_facture.isoformat() if a.date_facture else None,
        "montant_ht": float(a.montant_ht) if a.montant_ht is not None else None,
        "montant_tva": float(a.montant_tva) if a.montant_tva is not None else None,
        "montant_ttc": float(a.montant_ttc) if a.montant_ttc is not None else None,
        "lignes": [
            {
                "reference_fournisseur": l.reference_fournisseur,
                "designation": l.designation,
                "poids_kg": float(l.poids_kg) if l.poids_kg is not None else None,
                "quantite": float(l.quantite) if l.quantite is not None else None,
                "unite": l.unite,
                "prix_unitaire": float(l.prix_unitaire) if l.prix_unitaire is not None else None,
                "montant_ht": float(l.montant_ht),
                "taux_tva": float(l.taux_tva) if l.taux_tva is not None else None,
                "est_produit": l.est_produit,
                "famille_id": l.famille_id,
                "sous_famille_id": l.sous_famille_id,
                "numero_lot": l.numero_lot,
                "origine": l.origine,
            }
            for l in a.lignes
        ],
    }


@router.delete("/{achat_id}")
def supprimer(achat_id: int, db: Session = Depends(get_db)):
    a = db.get(Achat, achat_id)
    if a is None:
        raise HTTPException(404, "Achat introuvable")
    db.delete(a)
    db.commit()
    return {"supprime": achat_id}
