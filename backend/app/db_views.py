"""Vues SQL du rendement, source unique pour Grafana.

Le calcul du rendement vit en Python (endpoint /rendement) pour l'app ;
ces vues **reproduisent la même formule en SQL** pour que Grafana puisse
filtrer/trier/agréger par famille, morceau, fournisseur, PLU… sans passer
par l'API. Recréées (CREATE OR REPLACE) à chaque démarrage -> toujours à
jour, non matérialisées -> rétroactives.

Grains :
- v_rendement_theorique : 1 ligne par (ligne d'achat × PLU produit). Coût
  d'achat réparti à la valeur marchande (rendement% × prix_vente). Porte
  tous les axes (famille du PLU, morceau, fournisseur).
- v_rendement_morceau   : 1 ligne par morceau acheté -> bilan matière/perte.
- v_ventes_plu          : ventes réelles par PLU (pour théorique vs réel).
"""

from sqlalchemy import text

VIEWS_SQL = """
CREATE OR REPLACE VIEW v_rendement_morceau AS
SELECT
  al.id AS achat_ligne_id,
  a.date_facture,
  a.fournisseur_id,
  f.nom AS fournisseur,
  c.gamme_id,
  g.nom AS morceau,
  al.reference_fournisseur,
  al.designation,
  al.poids_kg::numeric AS input_kg,
  al.montant_ht::numeric AS cout_ht,
  gt.rend_tot AS rendement_total_pct,
  al.poids_kg::numeric * gt.rend_tot / 100.0 AS vendable_kg,
  al.poids_kg::numeric * (1 - gt.rend_tot / 100.0) AS perte_kg
FROM achat_ligne al
JOIN achat a ON a.id = al.achat_id
JOIN correspondance_fournisseur c
  ON c.fournisseur_id = a.fournisseur_id
 AND c.reference_fournisseur = al.reference_fournisseur
 AND c.gamme_id IS NOT NULL
JOIN gamme_decoupe g ON g.id = c.gamme_id
LEFT JOIN fournisseur f ON f.id = a.fournisseur_id
JOIN (SELECT gamme_id, SUM(rendement_pct)::numeric AS rend_tot
      FROM gamme_sortie GROUP BY gamme_id) gt ON gt.gamme_id = c.gamme_id
WHERE al.est_produit = true AND al.poids_kg > 0
""".strip()

VIEW_THEORIQUE = """
CREATE OR REPLACE VIEW v_rendement_theorique AS
WITH base AS (
  SELECT al.id AS achat_ligne_id, a.date_facture, a.fournisseur_id, c.gamme_id,
         al.reference_fournisseur, al.poids_kg::numeric AS input_kg,
         al.montant_ht::numeric AS input_cost, gs.produit_id,
         gs.rendement_pct::numeric AS rendement_pct,
         COALESCE(p.prix_vente, 0)::numeric AS prix_vente
  FROM achat_ligne al
  JOIN achat a ON a.id = al.achat_id
  JOIN correspondance_fournisseur c
    ON c.fournisseur_id = a.fournisseur_id
   AND c.reference_fournisseur = al.reference_fournisseur
   AND c.gamme_id IS NOT NULL
  JOIN gamme_sortie gs ON gs.gamme_id = c.gamme_id
  LEFT JOIN produit p ON p.id = gs.produit_id
  WHERE al.est_produit = true AND al.poids_kg > 0
),
w AS (
  SELECT base.*, rendement_pct * prix_vente AS valeur,
         SUM(rendement_pct * prix_vente) OVER (PARTITION BY achat_ligne_id) AS valeur_tot,
         SUM(rendement_pct) OVER (PARTITION BY achat_ligne_id) AS rend_tot
  FROM base
)
SELECT w.date_facture, w.fournisseur_id, f.nom AS fournisseur, w.gamme_id,
       g.nom AS morceau, w.reference_fournisseur, w.produit_id, p.code_plu,
       p.nom AS produit, p.famille_id, fam.nom AS famille, w.input_kg,
       w.rendement_pct, w.prix_vente,
       (w.input_kg * w.rendement_pct / 100.0) AS theo_kg,
       CASE WHEN w.valeur_tot > 0 THEN w.input_cost * w.valeur / w.valeur_tot
            WHEN w.rend_tot > 0 THEN w.input_cost * w.rendement_pct / w.rend_tot
            ELSE 0 END AS cout_alloc,
       (w.input_kg * w.rendement_pct / 100.0) * w.prix_vente AS ca_potentiel
FROM w
JOIN gamme_decoupe g ON g.id = w.gamme_id
LEFT JOIN fournisseur f ON f.id = w.fournisseur_id
LEFT JOIN produit p ON p.id = w.produit_id
LEFT JOIN famille fam ON fam.id = p.famille_id
""".strip()

VIEW_VENTES = """
CREATE OR REPLACE VIEW v_ventes_plu AS
SELECT vl.date_vente, p.id AS produit_id, p.code_plu, p.nom AS produit,
       p.famille_id, fam.nom AS famille,
       vl.poids_gramme / 1000.0 AS vendu_kg, vl.montant::numeric AS vendu_ca
FROM vente_ligne vl
JOIN produit p ON p.code_plu = vl.n_plu
LEFT JOIN famille fam ON fam.id = p.famille_id
WHERE vl.annule = false
""".strip()

GRANT = (
    "GRANT SELECT ON v_rendement_theorique, v_rendement_morceau, "
    "v_ventes_plu TO grafana_ro"
)

_STATEMENTS = [VIEWS_SQL, VIEW_THEORIQUE, VIEW_VENTES, GRANT]


def ensure_views(engine) -> None:
    """(Re)crée les vues du rendement. Le GRANT peut échouer si le rôle
    grafana_ro n'existe pas encore : on l'isole pour ne pas bloquer le reste."""
    with engine.begin() as conn:
        for stmt in _STATEMENTS[:-1]:
            conn.execute(text(stmt))
    try:
        with engine.begin() as conn:
            conn.execute(text(GRANT))
    except Exception as e:  # noqa: BLE001
        print(f"[db_views] GRANT grafana_ro ignoré : {e}")
