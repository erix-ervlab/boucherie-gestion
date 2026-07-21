"""Journal d'audit des opérations (consultation)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import JournalOperation

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("")
def lister(entite: str | None = None, db: Session = Depends(get_db)):
    q = db.query(JournalOperation)
    if entite:
        q = q.filter(JournalOperation.entite == entite)
    rows = (
        q.order_by(JournalOperation.horodatage.desc(), JournalOperation.id.desc())
        .limit(300)
        .all()
    )
    return [
        {
            "id": r.id,
            "horodatage": r.horodatage.isoformat() if r.horodatage else None,
            "action": r.action,
            "entite": r.entite,
            "entite_id": r.entite_id,
            "libelle": r.libelle,
        }
        for r in rows
    ]
