"""Endpoints d'import de l'export caisse + consultation du journal."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db import get_db
from ..importers import catalogue, gdpdu
from ..models import ImportJournal
from ..schemas import ImportJournalRead

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/ventes")
async def importer_ventes(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Dépôt manuel d'un export GDPdU. Import idempotent + détection de trous."""
    content = await file.read()
    try:
        result = gdpdu.import_ventes(db, content, file.filename or "export.csv")
    except NotImplementedError as e:
        # Mapping de colonnes pas encore calibré sur un export réel.
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "fichier": result.fichier_nom,
        "lignes_ajoutees": result.nb_lignes_ajoutees,
        "lignes_deja_connues": result.nb_lignes_deja_connues,
        "lignes_ignorees": result.nb_lignes_ignorees,
        "annulations": result.nb_annulations,
        "z_min": result.z_min,
        "z_max": result.z_max,
        "trous_z": result.trous_z,
    }


@router.post("/catalogue")
async def importer_catalogue(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Chargement initial du catalogue PLU depuis l'Excel de marge (.xlsx)."""
    content = await file.read()
    try:
        result = catalogue.import_catalogue(db, content, file.filename or "catalogue.xlsx")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {
        "fichier": file.filename,
        "familles": result.familles,
        "produits_ajoutes": result.produits_ajoutes,
        "produits_maj": result.produits_maj,
    }


@router.get("", response_model=list[ImportJournalRead])
def liste_imports(db: Session = Depends(get_db)):
    return (
        db.query(ImportJournal)
        .order_by(ImportJournal.date_depot.desc())
        .limit(100)
        .all()
    )
