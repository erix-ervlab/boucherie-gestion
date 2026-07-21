"""Marge par famille (Étape 4) — croise le CA HT des ventes et le coût HT
des achats, sur une période, par famille.

Approche « par période » : marge = CA HT vendu − coût HT acheté, par
famille. Fiable sur une longue période (mois/trimestre) ; bruitée à la
semaine à cause du décalage stock (achats ≠ ventes de la même période).
La précision par produit (rendement de découpe + CUMP) est l'étape 6.

⚠️ Fiabilité : une famille sans achat sur la période affiche un CA sans
coût → marge « 100 % » trompeuse. On la marque `fiable=false` pour ne
pas reproduire le biais de l'ancien Excel.
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Achat, AchatLigne, Famille, Produit, VenteLigne

router = APIRouter(prefix="/marge", tags=["marge"])


def _row(fam_id, nom, cible, ca_ht: float, cout_ht: float, gr) -> dict:
    marge = ca_ht - cout_ht
    taux = (marge / ca_ht * 100) if ca_ht > 0 else None
    return {
        "famille_id": fam_id,
        "famille": nom or "Prix libre / autre",
        "ca_ht": round(ca_ht, 2),
        "cout_ht": round(cout_ht, 2),
        "marge_eur": round(marge, 2),
        "taux_marge": round(taux, 1) if taux is not None else None,
        "marge_cible": float(cible) if cible is not None else None,
        "kg": round((gr or 0) / 1000, 3) if gr is not None else None,
        # Marge non fiable si aucun achat n'a été saisi pour cette famille.
        "fiable": cout_ht > 0,
    }


@router.get("/par-famille")
def par_famille(
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
):
    # --- CA HT des ventes par famille (montant TTC -> HT via le taux de TVA) ---
    ca_ht_expr = func.sum(
        VenteLigne.montant / (1 + func.coalesce(VenteLigne.taux_tva, 5.5) / 100)
    )
    ca_q = (
        db.query(
            Famille.id,
            Famille.nom,
            Famille.marge_cible,
            func.coalesce(ca_ht_expr, 0),
            func.coalesce(func.sum(VenteLigne.poids_gramme), 0),
        )
        .select_from(VenteLigne)
        .outerjoin(Produit, Produit.code_plu == VenteLigne.n_plu)
        .outerjoin(Famille, Famille.id == Produit.famille_id)
        .filter(VenteLigne.annule.is_(False))
    )
    if date_debut:
        ca_q = ca_q.filter(VenteLigne.date_vente >= date_debut)
    if date_fin:
        ca_q = ca_q.filter(VenteLigne.date_vente <= date_fin)
    ca_rows = ca_q.group_by(Famille.id, Famille.nom, Famille.marge_cible).all()

    # --- Coût HT des achats par famille (lignes produit uniquement) ---
    cout_q = (
        db.query(AchatLigne.famille_id, func.coalesce(func.sum(AchatLigne.montant_ht), 0))
        .join(Achat, Achat.id == AchatLigne.achat_id)
        .filter(AchatLigne.est_produit.is_(True), AchatLigne.famille_id.isnot(None))
    )
    if date_debut:
        cout_q = cout_q.filter(Achat.date_facture >= date_debut)
    if date_fin:
        cout_q = cout_q.filter(Achat.date_facture <= date_fin)
    couts = {fam_id: float(c) for fam_id, c in cout_q.group_by(AchatLigne.famille_id).all()}

    # --- Fusion ---
    lignes: list[dict] = []
    vues = set()
    for fam_id, nom, cible, ca_ht, gr in ca_rows:
        vues.add(fam_id)
        lignes.append(_row(fam_id, nom, cible, float(ca_ht), couts.get(fam_id, 0.0), gr))

    # Familles avec des achats mais aucune vente sur la période.
    infos = {f.id: (f.nom, f.marge_cible) for f in db.query(Famille).all()}
    for fam_id, cout in couts.items():
        if fam_id in vues:
            continue
        nom, cible = infos.get(fam_id, (None, None))
        lignes.append(_row(fam_id, nom, cible, 0.0, cout, 0))

    lignes.sort(key=lambda r: r["ca_ht"], reverse=True)

    tot_ca = sum(r["ca_ht"] for r in lignes)
    tot_cout = sum(r["cout_ht"] for r in lignes)

    # Combien de factures couvrent la période (pour prévenir si c'est maigre).
    aq = db.query(func.count(Achat.id))
    if date_debut:
        aq = aq.filter(Achat.date_facture >= date_debut)
    if date_fin:
        aq = aq.filter(Achat.date_facture <= date_fin)
    nb_achats = aq.scalar() or 0

    return {
        "lignes": lignes,
        "total": _row(None, "TOTAL", None, tot_ca, tot_cout, None),
        "nb_achats_periode": nb_achats,
    }
