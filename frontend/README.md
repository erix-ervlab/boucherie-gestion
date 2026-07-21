# Frontend — Refine + Ant Design

Interface d'administration de la boucherie (React + [Refine](https://refine.dev)
+ Ant Design), branchée sur l'API FastAPI via le data-provider
`simple-rest`.

## Écrans

- **Tableau de bord** (`/`) : CA, kg, tickets, PLU vendus, CA par jour et
  par vendeur (endpoints `/ventes/stats`, `/par-jour`, `/par-vendeur`).
- **Import caisse** (`/imports`) : dépôt du CSV GDPdU et de l'Excel
  catalogue (glisser-déposer) + journal des imports.
- **CRUD** : Produits (PLU), Familles, Fournisseurs.

## Architecture de déploiement

Servi par **nginx** (image docker-compose `frontend`, port 80) qui :
- sert le build statique de Vite,
- proxifie `/api/*` vers le service `backend` → **même origine, pas de CORS**.

Le data-provider pointe donc sur `/api` (chemin relatif).

## Développement local

```bash
npm install
npm run dev   # Vite sur :5173, proxy /api -> http://localhost:8000
```

> ⚠️ L'exécution/déploiement se fait sur la VM Proxmox (`boucherie-01`),
> pas en local — le build a lieu dans l'image Docker (`Dockerfile`).
