"""Copilote IA — agent Claude avec un outil SQL en LECTURE SEULE.

Claude reçoit une question en langage naturel, écrit une requête SQL
contre la base de la boucherie, l'exécute via un rôle Postgres
`grafana_ro` (SELECT uniquement), lit les résultats et répond avec
analyse + conseils. Trois garde-fous sur l'outil SQL :
  1. rôle Postgres en lecture seule (grafana_ro) ;
  2. connexion `default_transaction_read_only=on` + `statement_timeout` ;
  3. validation : la requête doit commencer par SELECT/WITH, une seule
     instruction (pas de `;`).
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal

import anthropic
from sqlalchemy import create_engine, text

from .config import settings
from .modeles import kwargs_reflexion, resoudre

_engine = create_engine(
    settings.copilot_database_url,
    pool_pre_ping=True,
    connect_args={
        "options": "-c statement_timeout=5000 -c default_transaction_read_only=on"
    },
)

_client = anthropic.Anthropic()  # lit ANTHROPIC_API_KEY dans l'environnement

MAX_ROWS = 500
MAX_RESULT_CHARS = 20000
MAX_STEPS = 10

SYSTEM = """Tu es le copilote data de « La Boucherie de l'Abbatiale » (Guîtres, 33).
Tu aides la bouchère (non technicienne) à comprendre son activité et à décider.

Tu as accès en LECTURE SEULE à la base PostgreSQL via l'outil `requete_sql`.
Fonde TOUJOURS tes chiffres sur de vraies requêtes — ne devine jamais. Tu as
accès aux VENTES, aux ACHATS et au RENDEMENT de découpe (voir schéma). N'affirme
jamais qu'une donnée « n'est pas en base » sans avoir vérifié par une requête.

=== VENTES (caisse) ===
- famille(id, code, nom, marge_cible)  -- Bœuf, Porc… ; marge_cible en %
- sous_famille(id, famille_id, code, nom)
- produit(id, code_plu, nom, famille_id, sous_famille_id, tva, prix_vente, unite, actif)
    -- catalogue PLU ; prix_vente = prix de vente TTC (€/kg ou €/pièce)
- vente_ligne(id, numero_rapport_z, numero_ticket, n_plu, nom_plu, poids_gramme,
    montant, type_vente, numero_vendeur, prix_unitaire, taux_tva, date_vente,
    horodatage, annule)  -- montant en € (TTC), poids_gramme en grammes
- import_journal(...)  -- historique des imports caisse

=== ACHATS (factures fournisseurs) ===
- fournisseur(id, nom, actif)
- achat(id, fournisseur_id, numero_facture, date_facture, montant_ht, montant_tva,
    montant_ttc, statut, created_at)  -- une facture ; montants en €
- achat_ligne(id, achat_id, reference_fournisseur, designation, quantite, poids_kg,
    unite, prix_unitaire, montant_ht, taux_tva, numero_lot, origine, est_produit,
    famille_id, sous_famille_id)
    -- lignes de facture ; poids_kg en kg ; taux_tva FIABLE ici (contrairement aux ventes) ;
    -- est_produit=false = frais (port, cotisations Interbev/CVO, taxes) À EXCLURE du coût matière.
- correspondance_fournisseur(id, fournisseur_id, reference_fournisseur, designation,
    famille_id, sous_famille_id, gamme_id)
    -- mémoire réf fournisseur -> famille, et -> gamme si l'article est transformé.
- journal_operation(id, horodatage, action, entite, entite_id, libelle, details) -- audit.

=== RENDEMENT de découpe (gammes) — utilise de PRÉFÉRENCE ces vues ===
- gamme_decoupe(id, nom, note, actif) + gamme_sortie(id, gamme_id, produit_id, rendement_pct)
    -- recettes : un morceau acheté -> plusieurs PLU selon des % de rendement (reste = perte).
- v_rendement_theorique(date_facture, fournisseur, morceau, reference_fournisseur,
    produit, code_plu, famille, theo_kg, cout_alloc, prix_vente, ca_potentiel)
    -- 1 ligne par (achat transformé × PLU produit). cout_alloc = coût d'achat réparti
    -- à la VALEUR MARCHANDE. Coût de revient/kg = SUM(cout_alloc)/SUM(theo_kg).
    -- Marge € = SUM(ca_potentiel) - SUM(cout_alloc). CA potentiel = theo_kg × prix_vente.
- v_rendement_morceau(date_facture, fournisseur, morceau, input_kg, cout_ht,
    rendement_total_pct, vendable_kg, perte_kg)  -- bilan matière/perte par morceau.
- v_ventes_plu(date_vente, produit, code_plu, famille, vendu_kg, vendu_ca) -- ventes réelles/PLU.

Règles métier IMPORTANTES :
- VENTES — CA/kg : TOUJOURS `WHERE annule = false`. kg = poids_gramme/1000.
- Ventilation ventes par famille : `vente_ligne.n_plu = produit.code_plu` puis
  `produit.famille_id = famille.id` ; sinon COALESCE(famille.nom, 'Prix libre / autre').
- ⚠️ PRIX LIBRE : ~89 % du CA est saisi en « prix libre » (n_plu '0'/'1001'), non rattaché
  à un PLU. L'analyse par PLU/famille des VENTES ne couvre donc qu'une fraction du CA ;
  dis-le. En revanche le POIDS (poids_gramme) est saisi même en prix libre -> les
  totaux en kg sont fiables. Le `taux_tva` des ventes n'est PAS fiable (0 sur ~86 %) :
  pour un HT ventes, utilise 5,5 % (viande) ou produit.tva, pas vente_ligne.taux_tva.
- ACHATS — coût matière = SUM(achat_ligne.montant_ht) WHERE est_produit = true.
  Filtre période sur achat.date_facture. Achats HT fiables.
- RENDEMENT — le théorique est INDICATIF (dérivé des poids achetés × rendement des
  gammes ; le coût est réparti à la valeur marchande, ce qui donne une marge % « mélangée »).
  Le « réel par PLU » (v_ventes_plu) reste aveugle au prix libre. Utilise les vues
  v_rendement_* plutôt que de refaire le calcul.
- MARGE : compare CA HT vs coût d'achat HT par famille, OU coût de revient (vues rendement)
  vs prix_vente. Reste PRUDENT : peu de factures d'achat, décalage stock/temps, prix libre
  -> présente des tendances, pas des marges nettes exactes.

Style : réponds en français, clair et concret, pour une bouchère. Formate les
montants en euros. Sois synthétique. Donne des analyses ET des conseils
actionnables. Explore plusieurs requêtes si besoin (ventes, achats, rendement)
avant de conclure. Si une question dépasse les données, dis-le honnêtement.
"""

SQL_TOOL = {
    "name": "requete_sql",
    "description": (
        "Exécute UNE requête SQL SELECT en lecture seule sur la base PostgreSQL "
        "de la boucherie et renvoie les lignes (JSON). À utiliser pour toute "
        "question chiffrée."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "Une seule requête SELECT (ou WITH … SELECT), syntaxe PostgreSQL.",
            }
        },
        "required": ["sql"],
    },
}


def _json_safe(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def run_sql(sql: str) -> str:
    """Valide et exécute une requête SELECT ; renvoie le résultat en JSON (texte)."""
    q = (sql or "").strip().rstrip(";").strip()
    if not re.match(r"(?is)^(select|with)\b", q):
        return "Erreur : seules les requêtes SELECT (ou WITH … SELECT) sont autorisées."
    if ";" in q:
        return "Erreur : une seule requête à la fois (pas de ';')."
    try:
        with _engine.connect() as conn:
            result = conn.execute(text(q))
            cols = list(result.keys())
            rows = result.fetchmany(MAX_ROWS)
    except Exception as e:  # noqa: BLE001 — on renvoie l'erreur à Claude pour qu'il corrige
        return f"Erreur SQL : {e}"

    lignes = [{c: _json_safe(v) for c, v in zip(cols, row)} for row in rows]
    payload = {"colonnes": cols, "nb_lignes": len(lignes), "lignes": lignes}
    txt = json.dumps(payload, ensure_ascii=False, default=str)
    if len(txt) > MAX_RESULT_CHARS:
        txt = txt[:MAX_RESULT_CHARS] + " …(résultat tronqué, affine ta requête)"
    return txt


def chat(messages: list[dict], modele: str | None = None) -> dict:
    """Boucle agent : messages = historique [{role, content(str)}]. Renvoie la
    réponse finale + la liste des requêtes SQL exécutées (transparence)."""
    model = resoudre(modele)
    convo: list[dict] = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    requetes: list[str] = []

    for _ in range(MAX_STEPS):
        resp = _client.messages.create(
            model=model,
            max_tokens=8000,
            system=SYSTEM,
            tools=[SQL_TOOL],
            messages=convo,
            **kwargs_reflexion(model),
        )

        if resp.stop_reason == "tool_use":
            convo.append({"role": "assistant", "content": resp.content})
            results = []
            for block in resp.content:
                if block.type == "tool_use" and block.name == "requete_sql":
                    sql = (block.input or {}).get("sql", "")
                    requetes.append(sql)
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": run_sql(sql),
                        }
                    )
            convo.append({"role": "user", "content": results})
            continue

        texte = "".join(b.text for b in resp.content if b.type == "text")
        return {"reponse": texte, "requetes_sql": requetes, "modele": model}

    return {
        "reponse": "Désolé, je n'ai pas réussi à conclure en un nombre raisonnable d'étapes.",
        "requetes_sql": requetes,
        "modele": model,
    }
