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
MAX_STEPS = 6

SYSTEM = """Tu es le copilote data de « La Boucherie de l'Abbatiale » (Guîtres, 33).
Tu aides la bouchère (non technicienne) à comprendre ses ventes et à décider.

Tu as accès en LECTURE SEULE à la base PostgreSQL via l'outil `requete_sql`.
Fonde TOUJOURS tes chiffres sur de vraies requêtes — ne devine jamais.

Schéma :
- famille(id, code, nom, marge_cible)  -- familles (Bœuf, Porc…) ; marge_cible en %
- sous_famille(id, famille_id, code, nom)
- produit(id, code_plu, nom, famille_id, sous_famille_id, tva, prix_vente, unite, actif)
    -- catalogue PLU ; prix_vente = prix de vente TTC (€/kg ou €/pièce selon `unite`)
- fournisseur(id, nom, actif)
- vente_ligne(id, numero_rapport_z, numero_ticket, n_plu, nom_plu, poids_gramme,
    montant, type_vente, numero_vendeur, prix_unitaire, taux_tva, date_vente,
    horodatage, annule)
    -- lignes de vente de la caisse ; montant en €, poids_gramme en grammes
- import_journal(...)  -- historique des imports d'export caisse

Règles métier IMPORTANTES :
- CA / kg : TOUJOURS filtrer `WHERE annule = false` (les annulations ne comptent pas).
- kg = poids_gramme / 1000.
- Ventilation par famille : joindre `vente_ligne.n_plu = produit.code_plu` puis
  `produit.famille_id = famille.id`. Les lignes sans correspondance (souvent des
  ventes en « PRIX LIBRE », nom_plu = 'PRIX LIBRE', ou hors catalogue) →
  COALESCE(famille.nom, 'Prix libre / autre').
- Les ACHATS ne sont PAS encore en base (module à venir) : tu ne peux donc PAS
  calculer la marge réelle. Tu peux comparer prix de vente et marge cible, et
  analyser CA, volumes, tendances, vendeurs, horaires. Dis-le si on te demande la marge.

Style : réponds en français, clair et concret, pour une bouchère. Formate les
montants en euros. Sois synthétique. Donne des analyses ET des conseils
actionnables quand c'est pertinent. Si une question dépasse les données
disponibles, dis-le honnêtement plutôt que d'inventer.
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
