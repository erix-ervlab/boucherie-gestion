# Boucherie de l'Abbatiale — Outil de gestion

Application web sur mesure pour **remplacer l'Excel de marge** de la
Boucherie de l'Abbatiale (Guîtres, 33) : import automatisé des ventes
(export caisse GDPdU) et des achats (lecture IA des factures PDF), pour
un suivi de marge réel et une saisie réduite au strict contrôle humain.

> Cadrage complet dans [`docs/`](docs/) — cahier des charges technique
> et fonctionnel (non-tech).

## Stack

| Composant | Choix |
|---|---|
| Frontend | React + **Refine** (à venir, étape 2) |
| Backend | **FastAPI** (Python 3.13, SQLAlchemy 2, pandas) |
| Base de données | **PostgreSQL 17** |
| Déploiement | **docker-compose** sur une VM Proxmox dédiée |

## Démarrage (dev)

```bash
cp .env.example .env        # adapter le mot de passe
docker compose up --build
```

- API : http://localhost:8000 — doc interactive : http://localhost:8000/docs
- Santé : http://localhost:8000/health

## Ce qui est en place (Étape 1 — en cours)

- Schéma DB : `famille`, `sous_famille`, `produit` (PLU), `fournisseur`,
  `vente_ligne`, `import_journal`.
- CRUD référentiels compatibles Refine (pagination/tri/`X-Total-Count`).
- Chaîne d'import de l'export caisse **GDPdU** : upsert idempotent (clé
  métier), détection des trous de `Numéro_Rapport_Z`, journal d'imports.
- Script de **sauvegarde** `pg_dump` (`scripts/backup.sh`) — copie
  hors-site à activer (exigence cahier §7).

## À faire avant d'aller plus loin

- [ ] **Calibrer le parser GDPdU** : compléter `COLUMN_MAP` dans
  `backend/app/importers/gdpdu.py` à partir d'un **vrai export** (+ son
  `index.xml`). Tant que non fait, `POST /imports/ventes` répond 422 avec
  un message explicite.
- [ ] **Importer le catalogue PLU** (291) depuis l'Excel existant.
- [ ] Basculer `dev_create_all` → **Alembic** avant toute vraie donnée.
- [ ] Choisir et brancher la **cible de sauvegarde hors-Proxmox**.

## Feuille de route (cahier §6)

1. Schéma + imports idempotents *(en cours)* → 2. Dashboard ventes →
3. CRUD achats + correspondance fournisseur → 4. Marge famille/sous-famille →
5. Lecture IA factures PDF → 6. Rendement de découpe + CUMP → 7. Anomalies.
