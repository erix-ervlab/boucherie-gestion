"""Gammes de découpe (rendement théorique) — CRUD avec sorties imbriquées.

Compatible Refine (en-tête X-Total-Count sur la liste). Chaque gamme
renvoie ses sorties enrichies (nom PLU + prix de vente) et le total de
rendement / la perte implicite (100 − Σ rendements)."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import GammeDecoupe, GammeSortie, Produit
from ..schemas import GammeIn, GammeRead, GammeSortieRead

router = APIRouter(prefix="/gammes", tags=["gammes"])


def _to_read(g: GammeDecoupe, prod: dict[int, Produit]) -> GammeRead:
    sorties: list[GammeSortieRead] = []
    total = Decimal(0)
    for s in g.sorties:
        p = prod.get(s.produit_id)
        sorties.append(
            GammeSortieRead(
                id=s.id,
                produit_id=s.produit_id,
                rendement_pct=s.rendement_pct,
                produit_nom=p.nom if p else None,
                prix_vente=p.prix_vente if p else None,
            )
        )
        total += s.rendement_pct or Decimal(0)
    return GammeRead(
        id=g.id,
        nom=g.nom,
        note=g.note,
        actif=g.actif,
        sorties=sorties,
        rendement_total=total,
        perte_pct=Decimal(100) - total,
    )


def _valider_sorties(payload: GammeIn) -> None:
    total = sum((s.rendement_pct or Decimal(0)) for s in payload.sorties)
    if total > Decimal(100):
        raise HTTPException(
            422,
            f"La somme des rendements ({total}%) dépasse 100%. "
            "Le reste doit rester disponible pour la perte (os, gras, chutes).",
        )
    vus = set()
    for s in payload.sorties:
        if s.produit_id in vus:
            raise HTTPException(422, "Un même PLU apparaît deux fois dans la gamme.")
        vus.add(s.produit_id)


@router.get("", response_model=list[GammeRead])
def liste(response: Response, db: Session = Depends(get_db)):
    prod = {p.id: p for p in db.query(Produit).all()}
    gammes = db.query(GammeDecoupe).order_by(GammeDecoupe.nom).all()
    response.headers["X-Total-Count"] = str(len(gammes))
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    return [_to_read(g, prod) for g in gammes]


@router.get("/{gamme_id}", response_model=GammeRead)
def detail(gamme_id: int, db: Session = Depends(get_db)):
    g = db.get(GammeDecoupe, gamme_id)
    if g is None:
        raise HTTPException(404, f"Gamme {gamme_id} introuvable")
    prod = {p.id: p for p in db.query(Produit).all()}
    return _to_read(g, prod)


@router.post("", response_model=GammeRead, status_code=201)
def creer(payload: GammeIn, db: Session = Depends(get_db)):
    _valider_sorties(payload)
    g = GammeDecoupe(nom=payload.nom, note=payload.note, actif=payload.actif)
    for s in payload.sorties:
        g.sorties.append(
            GammeSortie(produit_id=s.produit_id, rendement_pct=s.rendement_pct)
        )
    db.add(g)
    db.commit()
    db.refresh(g)
    prod = {p.id: p for p in db.query(Produit).all()}
    return _to_read(g, prod)


def _maj(gamme_id: int, payload: GammeIn, db: Session) -> GammeRead:
    g = db.get(GammeDecoupe, gamme_id)
    if g is None:
        raise HTTPException(404, f"Gamme {gamme_id} introuvable")
    _valider_sorties(payload)
    g.nom = payload.nom
    g.note = payload.note
    g.actif = payload.actif
    # Remplace intégralement les sorties (cascade delete-orphan).
    g.sorties.clear()
    for s in payload.sorties:
        g.sorties.append(
            GammeSortie(produit_id=s.produit_id, rendement_pct=s.rendement_pct)
        )
    db.commit()
    db.refresh(g)
    prod = {p.id: p for p in db.query(Produit).all()}
    return _to_read(g, prod)


@router.put("/{gamme_id}", response_model=GammeRead)
def remplacer(gamme_id: int, payload: GammeIn, db: Session = Depends(get_db)):
    return _maj(gamme_id, payload, db)


@router.patch("/{gamme_id}", response_model=GammeRead)
def modifier(gamme_id: int, payload: GammeIn, db: Session = Depends(get_db)):
    return _maj(gamme_id, payload, db)


@router.delete("/{gamme_id}")
def supprimer(gamme_id: int, db: Session = Depends(get_db)):
    g = db.get(GammeDecoupe, gamme_id)
    if g is None:
        raise HTTPException(404, f"Gamme {gamme_id} introuvable")
    db.delete(g)
    db.commit()
    return {"ok": True, "id": gamme_id}
