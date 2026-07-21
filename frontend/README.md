# Frontend — Refine (à venir, étape 2)

Le front n'est pas encore initialisé. Il sera un projet **Refine**
(React) branché sur l'API FastAPI via le data-provider `simple-rest`
(le backend expose déjà les conventions attendues : pagination
`_start`/`_end`, tri `_sort`/`_order`, en-tête `X-Total-Count`).

## Initialisation prévue

```bash
npm create refine-app@latest frontend
# Choix : Vite · REST (simple-rest) · Ant Design (ou Material UI)
```

Puis pointer le data-provider sur `http://localhost:8000` et déclarer
les ressources : `familles`, `sous-familles`, `fournisseurs`,
`produits`, `imports`.
