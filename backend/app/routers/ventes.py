"""Analytique des ventes — socle du tableau de bord (étape 2).

Toutes les agrégations excluent les lignes annulées et acceptent les
mêmes filtres optionnels : `date_debut`, `date_fin` (ISO AAAA-MM-JJ) et
`famille_id`. La dimension « famille » est obtenue par **jointure à la
volée** entre `vente_ligne.n_plu` et `produit.code_plu` (pas de linkage
persistant) ; les lignes sans correspondance (prix libre / hors
catalogue) tombent dans « Prix libre / autre ».
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Famille, Produit, VenteLigne

router = APIRouter(prefix="/ventes", tags=["ventes"])


def _prep(
    db: Session,
    cols,
    date_debut: date | None,
    date_fin: date | None,
    famille_id: int | None,
    *,
    join_famille: bool = False,
):
    """Construit une requête agrégée filtrée (annulations exclues)."""
    q = db.query(*cols).select_from(VenteLigne).filter(VenteLigne.annule.is_(False))
    if famille_id is not None or join_famille:
        q = q.outerjoin(Produit, Produit.code_plu == VenteLigne.n_plu)
    if join_famille:
        q = q.outerjoin(Famille, Famille.id == Produit.famille_id)
    if famille_id is not None:
        q = q.filter(Produit.famille_id == famille_id)
    if date_debut:
        q = q.filter(VenteLigne.date_vente >= date_debut)
    if date_fin:
        q = q.filter(VenteLigne.date_vente <= date_fin)
    return q


def _euro(v) -> float:
    return round(float(v or 0), 2)


@router.get("/plage")
def plage(db: Session = Depends(get_db)):
    """Bornes de dates disponibles (pour initialiser le sélecteur)."""
    lo, hi = (
        db.query(func.min(VenteLigne.date_vente), func.max(VenteLigne.date_vente))
        .filter(VenteLigne.annule.is_(False))
        .one()
    )
    return {
        "min": lo.isoformat() if lo else None,
        "max": hi.isoformat() if hi else None,
    }


@router.get("/stats")
def stats(
    date_debut: date | None = None,
    date_fin: date | None = None,
    famille_id: int | None = None,
    db: Session = Depends(get_db),
):
    ticket_key = func.concat(VenteLigne.numero_rapport_z, "-", VenteLigne.numero_ticket)
    row = _prep(
        db,
        [
            func.coalesce(func.sum(VenteLigne.montant), 0),
            func.coalesce(func.sum(VenteLigne.poids_gramme), 0),
            func.count(),
            func.count(func.distinct(ticket_key)),
            func.count(func.distinct(VenteLigne.n_plu)),
        ],
        date_debut,
        date_fin,
        famille_id,
    ).one()
    ca, gr, lignes, tickets, plu = row
    ca = _euro(ca)
    return {
        "ca_eur": ca,
        "kg": round((gr or 0) / 1000, 3),
        "lignes": lignes,
        "tickets": tickets,
        "plu_distincts": plu,
        "panier_moyen": round(ca / tickets, 2) if tickets else 0.0,
    }


@router.get("/par-jour")
def par_jour(
    date_debut: date | None = None,
    date_fin: date | None = None,
    famille_id: int | None = None,
    db: Session = Depends(get_db),
):
    rows = (
        _prep(
            db,
            [
                VenteLigne.date_vente,
                func.coalesce(func.sum(VenteLigne.montant), 0),
                func.coalesce(func.sum(VenteLigne.poids_gramme), 0),
            ],
            date_debut,
            date_fin,
            famille_id,
        )
        .group_by(VenteLigne.date_vente)
        .order_by(VenteLigne.date_vente)
        .all()
    )
    return [
        {
            "jour": d.isoformat() if d else None,
            "ca_eur": _euro(ca),
            "kg": round((gr or 0) / 1000, 3),
        }
        for d, ca, gr in rows
    ]


@router.get("/par-heure")
def par_heure(
    date_debut: date | None = None,
    date_fin: date | None = None,
    famille_id: int | None = None,
    db: Session = Depends(get_db),
):
    h = func.extract("hour", VenteLigne.horodatage)
    rows = (
        _prep(
            db,
            [h.label("h"), func.coalesce(func.sum(VenteLigne.montant), 0)],
            date_debut,
            date_fin,
            famille_id,
        )
        .filter(VenteLigne.horodatage.isnot(None))
        .group_by("h")
        .all()
    )
    par_h = {int(hh): _euro(ca) for hh, ca in rows}
    return [{"heure": f"{hh}h", "ca_eur": par_h.get(hh, 0.0)} for hh in range(7, 21)]


@router.get("/par-famille")
def par_famille(
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
):
    nom = func.coalesce(Famille.nom, "Prix libre / autre")
    rows = (
        _prep(
            db,
            [nom, func.coalesce(func.sum(VenteLigne.montant), 0), func.coalesce(func.sum(VenteLigne.poids_gramme), 0)],
            date_debut,
            date_fin,
            None,
            join_famille=True,
        )
        .group_by(nom)
        .order_by(func.sum(VenteLigne.montant).desc())
        .all()
    )
    return [
        {"famille": n, "ca_eur": _euro(ca), "kg": round((gr or 0) / 1000, 3)}
        for n, ca, gr in rows
    ]


@router.get("/par-vendeur")
def par_vendeur(
    date_debut: date | None = None,
    date_fin: date | None = None,
    famille_id: int | None = None,
    db: Session = Depends(get_db),
):
    rows = (
        _prep(
            db,
            [VenteLigne.numero_vendeur, func.coalesce(func.sum(VenteLigne.montant), 0), func.count()],
            date_debut,
            date_fin,
            famille_id,
        )
        .group_by(VenteLigne.numero_vendeur)
        .order_by(func.sum(VenteLigne.montant).desc())
        .all()
    )
    return [
        {"vendeur": v or "?", "ca_eur": _euro(ca), "lignes": n} for v, ca, n in rows
    ]


@router.get("/top-produits")
def top_produits(
    date_debut: date | None = None,
    date_fin: date | None = None,
    famille_id: int | None = None,
    limit: int = 12,
    db: Session = Depends(get_db),
):
    nom = func.max(func.coalesce(Produit.nom, VenteLigne.nom_plu, VenteLigne.n_plu))
    rows = (
        _prep(
            db,
            [VenteLigne.n_plu, nom, func.coalesce(func.sum(VenteLigne.montant), 0), func.coalesce(func.sum(VenteLigne.poids_gramme), 0)],
            date_debut,
            date_fin,
            famille_id,
        )
        .group_by(VenteLigne.n_plu)
        .order_by(func.sum(VenteLigne.montant).desc())
        .limit(limit)
        .all()
    )
    return [
        {"code_plu": p, "nom": n, "ca_eur": _euro(ca), "kg": round((gr or 0) / 1000, 3)}
        for p, n, ca, gr in rows
    ]
