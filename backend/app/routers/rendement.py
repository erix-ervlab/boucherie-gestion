"""Rendement (étape 6) — comparaison indicative théorique vs réel.

Théorique : dérivé automatiquement des achats. Une référence marquée
« transformable » (correspondance_fournisseur.gamme_id) applique sa gamme
au poids acheté -> production théorique par PLU. Le coût d'achat du morceau
est réparti sur les PLU produits **à la valeur marchande** (rendement% ×
prix de vente), ce qui donne un coût de revient par PLU réaliste.

Réel : ventes effectives par PLU (limité par le « prix libre »). Un
indicateur global en kg, lui, est immunisé au prix libre (le poids est
saisi même sur les ventes en prix libre).
"""

from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    Achat,
    AchatLigne,
    CorrespondanceFournisseur,
    GammeDecoupe,
    Produit,
    VenteLigne,
)

router = APIRouter(prefix="/rendement", tags=["rendement"])


@router.get("/synthese")
def synthese(
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
):
    produits = {p.id: p for p in db.query(Produit).all()}
    gammes = {g.id: g for g in db.query(GammeDecoupe).all()}

    # gamme_id -> sorties [{produit_id, rendement, prix_vente, ...}]
    gamme_sorties: dict[int, list[dict]] = {}
    for g in gammes.values():
        rows = []
        for s in g.sorties:
            p = produits.get(s.produit_id)
            rows.append(
                {
                    "produit_id": s.produit_id,
                    "rendement": float(s.rendement_pct or 0),
                    "prix_vente": float(p.prix_vente) if p and p.prix_vente else 0.0,
                }
            )
        gamme_sorties[g.id] = rows

    # (fournisseur_id, reference) -> gamme_id, pour les réfs transformables
    corr: dict[tuple[int, str], int] = {}
    for c in db.query(CorrespondanceFournisseur).filter(
        CorrespondanceFournisseur.gamme_id.isnot(None)
    ):
        corr[(c.fournisseur_id, c.reference_fournisseur)] = c.gamme_id

    # Lignes d'achat de la période
    q = db.query(AchatLigne, Achat).join(Achat, Achat.id == AchatLigne.achat_id)
    if date_debut:
        q = q.filter(Achat.date_facture >= date_debut)
    if date_fin:
        q = q.filter(Achat.date_facture <= date_fin)

    theo: dict[int, dict] = defaultdict(
        lambda: {"theo_kg": 0.0, "cost": 0.0, "gammes": set()}
    )
    input_kg_total = 0.0
    perte_kg_total = 0.0
    cout_total = 0.0
    kg_achetes_vendables = 0.0  # indicateur magasin (immunisé prix libre)

    for al, a in q.all():
        if not al.est_produit:
            continue
        poids = float(al.poids_kg or 0)
        if poids <= 0:
            continue
        gid = corr.get((a.fournisseur_id, al.reference_fournisseur or ""))
        rows = gamme_sorties.get(gid) if gid else None
        if rows:
            cost = float(al.montant_ht or 0)
            sum_rend = sum(r["rendement"] for r in rows)
            weights = [r["rendement"] * r["prix_vente"] for r in rows]
            sw = sum(weights)
            for r, w in zip(rows, weights):
                if sw > 0:
                    share = w / sw
                elif sum_rend > 0:
                    share = r["rendement"] / sum_rend
                else:
                    share = 0.0
                theo[r["produit_id"]]["theo_kg"] += poids * r["rendement"] / 100.0
                theo[r["produit_id"]]["cost"] += cost * share
                theo[r["produit_id"]]["gammes"].add(gammes[gid].nom)
            input_kg_total += poids
            cout_total += cost
            perte_kg_total += poids * max(0.0, 1 - sum_rend / 100.0)
            kg_achetes_vendables += poids * min(1.0, sum_rend / 100.0)
        else:
            # produit affecté directement (non transformé) : supposé vendable à 100%
            kg_achetes_vendables += poids

    # Ventes réelles par PLU (rattaché au catalogue)
    vq = (
        db.query(
            Produit.id,
            func.coalesce(func.sum(VenteLigne.poids_gramme), 0),
            func.coalesce(func.sum(VenteLigne.montant), 0),
        )
        .join(VenteLigne, VenteLigne.n_plu == Produit.code_plu)
        .filter(VenteLigne.annule.is_(False))
    )
    if date_debut:
        vq = vq.filter(VenteLigne.date_vente >= date_debut)
    if date_fin:
        vq = vq.filter(VenteLigne.date_vente <= date_fin)
    vq = vq.group_by(Produit.id)
    sold = {pid: (float(g) / 1000.0, float(ca)) for pid, g, ca in vq.all()}

    # Total kg vendus (toutes lignes, prix libre inclus)
    tq = db.query(func.coalesce(func.sum(VenteLigne.poids_gramme), 0)).filter(
        VenteLigne.annule.is_(False)
    )
    if date_debut:
        tq = tq.filter(VenteLigne.date_vente >= date_debut)
    if date_fin:
        tq = tq.filter(VenteLigne.date_vente <= date_fin)
    kg_vendus_total = float(tq.scalar() or 0) / 1000.0

    lignes = []
    for pid, acc in theo.items():
        p = produits.get(pid)
        tkg = acc["theo_kg"]
        cout_kg = acc["cost"] / tkg if tkg > 0 else None
        pv = float(p.prix_vente) if p and p.prix_vente else None
        skg, sca = sold.get(pid, (0.0, 0.0))
        lignes.append(
            {
                "produit_id": pid,
                "produit": p.nom if p else None,
                "code_plu": p.code_plu if p else None,
                "gammes": sorted(acc["gammes"]),
                "theo_kg": round(tkg, 1),
                "cout_revient_kg": round(cout_kg, 2) if cout_kg is not None else None,
                "prix_vente": pv,
                "marge_kg": round(pv - cout_kg, 2)
                if (pv and cout_kg is not None)
                else None,
                "marge_pct": round((pv - cout_kg) / pv * 100, 1)
                if (pv and cout_kg is not None and pv > 0)
                else None,
                "ca_potentiel": round(tkg * pv, 0) if pv else None,
                "vendu_kg": round(skg, 1),
                "vendu_ca": round(sca, 0),
                "taux_ecoulement_pct": round(skg / tkg * 100, 0) if tkg > 0 else None,
            }
        )
    lignes.sort(key=lambda r: (r["ca_potentiel"] or 0), reverse=True)

    return {
        "periode": {"debut": date_debut, "fin": date_fin},
        "morceaux": {
            "entree_kg": round(input_kg_total, 1),
            "vendable_theo_kg": round(input_kg_total - perte_kg_total, 1),
            "perte_kg": round(perte_kg_total, 1),
            "taux_perte_pct": round(perte_kg_total / input_kg_total * 100, 1)
            if input_kg_total > 0
            else None,
            "cout_total_ht": round(cout_total, 0),
        },
        "global_magasin": {
            "kg_achetes_vendables": round(kg_achetes_vendables, 1),
            "kg_vendus": round(kg_vendus_total, 1),
            "ecart_kg": round(kg_vendus_total - kg_achetes_vendables, 1),
            "taux_ecoulement_pct": round(kg_vendus_total / kg_achetes_vendables * 100, 0)
            if kg_achetes_vendables > 0
            else None,
        },
        "lignes": lignes,
    }
