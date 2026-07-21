"""Consultation des ventes importées + statistiques agrégées.

Base du futur tableau de bord (étape 2). Toutes les agrégations
excluent les lignes annulées (`annule = False`).
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import VenteLigne

router = APIRouter(prefix="/ventes", tags=["ventes"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """CA, kg, nombre de lignes/tickets, PLU distincts — hors annulations."""
    base = db.query(VenteLigne).filter(VenteLigne.annule.is_(False))

    ca = base.with_entities(func.coalesce(func.sum(VenteLigne.montant), 0)).scalar()
    kg = base.with_entities(
        func.coalesce(func.sum(VenteLigne.poids_gramme), 0)
    ).scalar()
    lignes = base.count()
    tickets = base.with_entities(
        func.count(func.distinct(func.concat(VenteLigne.numero_rapport_z, "-", VenteLigne.numero_ticket)))
    ).scalar()
    plu = base.with_entities(func.count(func.distinct(VenteLigne.n_plu))).scalar()
    annulees = db.query(VenteLigne).filter(VenteLigne.annule.is_(True)).count()

    return {
        "ca_eur": float(ca),
        "kg": round((kg or 0) / 1000, 3),
        "lignes": lignes,
        "tickets": tickets,
        "plu_distincts": plu,
        "lignes_annulees": annulees,
    }


@router.get("/par-vendeur")
def par_vendeur(db: Session = Depends(get_db)):
    rows = (
        db.query(
            VenteLigne.numero_vendeur,
            func.coalesce(func.sum(VenteLigne.montant), 0),
            func.count(),
        )
        .filter(VenteLigne.annule.is_(False))
        .group_by(VenteLigne.numero_vendeur)
        .order_by(func.sum(VenteLigne.montant).desc())
        .all()
    )
    return [
        {"vendeur": v, "ca_eur": float(ca), "lignes": n} for v, ca, n in rows
    ]


@router.get("/par-jour")
def par_jour(db: Session = Depends(get_db)):
    rows = (
        db.query(
            VenteLigne.date_vente,
            func.coalesce(func.sum(VenteLigne.montant), 0),
            func.count(),
        )
        .filter(VenteLigne.annule.is_(False))
        .group_by(VenteLigne.date_vente)
        .order_by(VenteLigne.date_vente)
        .all()
    )
    return [
        {"jour": d.isoformat() if isinstance(d, date) else None, "ca_eur": float(ca), "lignes": n}
        for d, ca, n in rows
    ]
