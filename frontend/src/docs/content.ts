// Contenu de la documentation intégrée. Un objet par section ; le corps est
// du Markdown (rendu par react-markdown + remark-gfm). Versionné avec le code
// pour rester synchrone avec l'application.

export type DocSection = { id: string; title: string; body: string };

export const DOCS: DocSection[] = [
  {
    id: "prise-en-main",
    title: "Prise en main",
    body: `# Bienvenue 👋

Cet outil aide à **piloter la boucherie** : suivre les ventes, enregistrer les
factures d'achat, estimer les marges et le rendement de découpe, et poser des
questions à un copilote.

## À quoi sert chaque partie du menu

- **Pilotage** — vos tableaux de bord, la marge, le rendement, le copilote et
  l'exploration libre (Grafana).
- **Achats & fournisseurs** — charger et vérifier les factures, gérer les
  fournisseurs, les correspondances apprises et les gammes de découpe.
- **Catalogue** — vos produits (PLU) et vos familles.
- **Données & journal** — l'import des ventes de la caisse et l'historique des
  opérations.
- **Aide** — cette documentation.

## Le rythme conseillé

| Quand | Quoi |
|---|---|
| **Chaque semaine** | Importer l'export de ventes de la caisse (menu *Import caisse*). |
| **À chaque livraison** | Charger la facture fournisseur (menu *Achats*), vérifier, valider. |
| **Une fois** (puis à l'occasion) | Régler le catalogue, les gammes de découpe et les correspondances. |
| **Quand vous voulez** | Consulter les tableaux de bord, interroger le copilote. |

> 💡 Plus vous codez vos ventes avec des **PLU** (au lieu du « prix libre ») et
> plus vous saisissez de **factures**, plus les analyses deviennent précises.
`,
  },
  {
    id: "ventes-import",
    title: "Importer les ventes (caisse)",
    body: `# Importer les ventes de la caisse

Menu **Données & journal › Import caisse**.

## Comment faire
1. Exportez le fichier de ventes depuis la caisse (format **GDPdU**, un fichier
   \`.csv\`).
2. Déposez-le dans la zone d'import.
3. L'outil lit le fichier, nettoie les lignes et vous affiche un récapitulatif :
   lignes ajoutées, déjà connues, ignorées, et d'éventuelles **anomalies**.

## Ce que fait l'outil automatiquement
- **Pas de doublon** : si vous réimportez un fichier qui chevauche un précédent,
  les lignes déjà connues ne sont **pas** ré-ajoutées (import « idempotent »).
- **Annulations** : conservées pour l'historique mais **jamais comptées** dans le
  chiffre d'affaires ni les kilos.
- **Trous de séquence** : l'outil signale un rapport Z manquant (export peut-être
  incomplet).

## Bon à savoir
- Vous pouvez importer aussi souvent que vous voulez, même des périodes qui se
  recouvrent : rien ne sera dupliqué.
- L'historique de tous les imports est visible dans **Historique**.
`,
  },
  {
    id: "tableaux-bord",
    title: "Tableaux de bord",
    body: `# Lire les tableaux de bord

## Dans l'application — *Pilotage › Tableau de bord*
Vue synthétique des ventes : chiffre d'affaires, tickets, panier moyen, et
graphiques par jour / famille. Utilisez le **sélecteur de dates** et le **filtre
par famille** en haut.

## Exploration libre — *Pilotage › Exploration (Grafana)*
Grafana est intégré dans l'application. Trois tableaux de bord y sont prêts :

- **Pilotage des ventes** — CA, tickets, panier, rythme par jour de semaine et
  par heure, familles et produits, vendeurs.
- **Suivi des fournisseurs** — dépenses par fournisseur, évolution des achats,
  familles achetées, **suivi des prix** par référence.
- **Rendement de découpe** — théorique vs réel, filtrable par **famille /
  morceau / fournisseur**.

### Astuces Grafana
- En haut de chaque tableau : un **sélecteur de période** (glissez pour zoomer).
- Sur le tableau Rendement : les listes **Famille / Morceau / Fournisseur**
  filtrent tous les panneaux ; « All » = tout.
- Les tableaux se rafraîchissent tout seuls quand vous changez la période.
`,
  },
  {
    id: "achats",
    title: "Achats & factures",
    body: `# Enregistrer une facture fournisseur

Menu **Achats & fournisseurs › Achats**.

## 1. Charger la facture
Glissez le **PDF** de la facture dans la zone d'import. L'**IA lit la facture**
(≈ 30 secondes) et propose un **brouillon** : lignes, poids, montants, TVA, lots,
origines.

> Vous pouvez choisir le **modèle d'IA** en haut à droite (Opus / Sonnet / Haiku).
> Opus est le plus fin, Haiku le plus rapide et économique.

## 2. Vérifier et corriger
Le brouillon est **modifiable ligne par ligne** :
- **Produit ?** — décochez pour les **frais** (port, cotisations Interbev/CVO,
  taxes) : ils ne comptent pas comme coût de marchandise.
- **Famille** — à affecter (pré-remplie si connue, voir *Correspondances*).
  Badge **appris** = déjà mémorisé, **suggéré** = proposé par l'IA (à vérifier).
- **Gamme (si transformé)** — si l'article est un morceau à découper, choisissez
  sa gamme (voir *Rendement*). Sinon laissez « vente directe ».

## 3. Valider
Cliquez **Valider et enregistrer**. L'outil mémorise au passage les
**correspondances** (réf → famille, réf → gamme) : la prochaine facture du même
article sera pré-remplie automatiquement.

## Corriger après coup
Dans la liste des factures : **Modifier** (rouvre le brouillon) ou **Supprimer**.
Toutes ces opérations sont tracées dans l'**Historique**.
`,
  },
  {
    id: "correspondances",
    title: "Correspondances (apprentissage)",
    body: `# Correspondances — la mémoire de l'outil

Menu **Achats & fournisseurs › Correspondances**.

Une correspondance relie une **référence fournisseur** à une **famille** et,
éventuellement, à une **gamme de découpe**. C'est ce qui permet le pré-remplissage
automatique des factures.

## Comment ça se remplit
- **Automatiquement** : chaque fois que vous validez une facture avec une famille
  (et/ou une gamme), la correspondance est créée ou mise à jour.
- **À la main** : vous pouvez créer/éditer une correspondance ici directement.

## À quoi ça sert
| Colonne | Rôle |
|---|---|
| **Famille** | classe l'article (Bœuf, Porc…) pour les analyses. |
| **Gamme (transformé)** | indique que l'article est un morceau à découper → active le rendement. « direct » = vendu tel quel. |

> 💡 Corriger une correspondance ici met à jour les **prochaines** lectures de
> facture ; les factures déjà enregistrées ne changent pas rétroactivement (sauf
> le rendement, qui, lui, se recalcule — voir *Rendement*).
`,
  },
  {
    id: "catalogue",
    title: "Catalogue (produits & familles)",
    body: `# Catalogue

## Produits (PLU) — *Catalogue › Produits*
Le catalogue des articles vendus en caisse : **code PLU**, nom, **famille**,
**TVA**, **prix de vente** (€/kg ou €/pièce). C'est ce catalogue qui relie les
ventes de la caisse à leurs familles.

- Recherche et filtres en haut de la liste.
- Un produit sans PLU codé en caisse tombe dans « Prix libre / autre » dans les
  analyses (voir *Notions clés & limites*).

## Familles — *Catalogue › Familles*
Les grandes catégories (Bœuf, Porc, Veau…). Chaque famille peut avoir une
**marge cible** (en %), utilisée comme repère dans l'écran *Marge*.

> Le catalogue a été chargé au démarrage depuis votre Excel, puis se gère ici.
`,
  },
  {
    id: "rendement",
    title: "Gammes & rendement de découpe",
    body: `# Rendement de découpe

Idée : un **morceau acheté** (carcasse, quartier…) donne **plusieurs PLU** vendus,
avec de la **perte** (os, gras, parures). On estime ça avec des **gammes**.

## 1. Créer une gamme — *Achats & fournisseurs › Gammes de découpe*
Une gamme décrit l'**éclatement d'un morceau** :
- un **nom** (ex. « Arrière de veau ») ;
- la liste des **PLU produits** avec leur **% de rendement** (part du poids qui
  devient ce PLU) ;
- le reste (100 − somme) = **perte**, calculé automatiquement.

## 2. Relier le morceau à sa gamme
Sur la ligne de facture (ou dans *Correspondances*), choisissez la gamme pour la
référence du morceau. Une seule fois : toutes les factures de cette référence en
profitent, **passées et futures**.

## 3. Lire le rendement — *Pilotage › Rendement*
Pour la période choisie :
- **Bilan matière** : entré / vendable / perte, coût d'achat.
- **Par PLU** : kg théorique produit, **coût de revient/kg**, marge, et
  **écoulement** (théorique vs réellement vendu).

## Points importants
- Le calcul est **fait à l'affichage**, jamais figé : si vous ajustez un %, tout
  se recalcule (y compris l'historique).
- Les **% sont vos estimations** (calées sur les standards du métier), **pas** une
  mesure de votre découpe réelle.
- Le coût d'achat est réparti sur les PLU **à la valeur marchande** (les morceaux
  nobles portent plus de coût).
`,
  },
  {
    id: "marge",
    title: "Marge",
    body: `# Marge

Menu **Pilotage › Marge**.

Compare, par **famille** et sur une période :
- le **chiffre d'affaires HT** des ventes,
- le **coût d'achat HT** de la marchandise,
- la **marge** qui en résulte, face à la **marge cible** de la famille.

## À lire avec prudence
La marge affichée est un **indicateur**, pas un chiffre comptable exact, car :
- une partie des ventes est en **prix libre** (non rattachée à une famille) ;
- il y a un **décalage** entre le moment où on achète et où on vend (stock) ;
- toutes les factures ne sont pas forcément saisies.

La colonne **« fiable »** signale les familles où l'on a assez d'achats pour que
le chiffre ait du sens. Voir aussi le *Rendement* pour une marge par morceau, et
*Notions clés & limites*.
`,
  },
  {
    id: "copilote",
    title: "Copilote IA",
    body: `# Copilote

Menu **Pilotage › Copilote**.

Posez une question en **langage courant** (« Quel est mon meilleur jour ? »,
« Compare le bœuf et le porc en juillet »…). Le copilote **interroge vraiment la
base** (ventes, achats, rendement) et répond avec analyse + conseils.

## Bon usage
- Soyez **précis** sur la période et ce que vous cherchez.
- Vous pouvez **choisir le modèle** (Opus / Sonnet / Haiku) selon le besoin de
  finesse ou d'économie.
- Les **requêtes SQL** utilisées peuvent être affichées (transparence).

## Ses limites (à garder en tête)
- Il lit la base en **lecture seule** : il ne modifie jamais rien.
- Il est soumis aux mêmes limites que les analyses (**prix libre**, **rendements
  estimés**, décalage stock) : ses marges sont des **tendances**, pas des chiffres
  au centime.
- Comme toute IA, il peut se tromper dans une **formulation** ou une
  interprétation. En cas de doute, recoupez avec un tableau de bord.
`,
  },
  {
    id: "historique",
    title: "Historique (journal)",
    body: `# Historique

Menu **Données & journal › Historique**.

Trace **persistante** de toutes les opérations importantes :
- imports de ventes et de catalogue,
- création / modification / suppression de factures d'achat.

Chaque entrée indique la **date**, l'**action**, l'**entité** concernée et un
**libellé**. Utilisez le filtre (Tout / Achats / Ventes / Catalogue) pour
retrouver rapidement une opération. C'est votre **filet de sécurité** en cas de
doute sur une saisie.
`,
  },
  {
    id: "notions-limites",
    title: "Notions clés & limites",
    body: `# Notions clés & limites

Pour bien **interpréter** les chiffres, gardez ces points en tête.

## Le « prix libre »
Quand une vente est saisie en caisse **sans code PLU**, elle apparaît en « prix
libre » : on connaît le montant et le poids, mais **pas le produit ni la famille**.
- Conséquence : les analyses **par famille / par produit** ne couvrent que les
  ventes **codées**.
- Cette part **varie dans le temps** — elle a fortement baissé depuis que le
  codage PLU a démarré. **Plus vous codez, plus vous pilotez.**
- Les totaux **en kilos et en euros**, eux, restent justes (poids toujours saisi).

## La TVA de la caisse
Sur les lignes de vente, le taux de TVA n'est **pas fiable** (souvent 0). Pour un
chiffre HT côté ventes, l'outil applique le taux **viande 5,5 %**. Côté **achats**,
la TVA lue sur la facture est, elle, fiable.

## Les rendements de découpe
Les pourcentages des gammes sont des **estimations** (standards du métier), pas une
mesure de votre découpe réelle. Ils servent à **donner une idée**, pas à auditer la
découpe au gramme près.

## La marge « à la valeur marchande »
Le coût d'un morceau est réparti sur ses PLU au prorata de leur **valeur de vente**.
C'est réaliste, mais ça donne une marge **« mélangée »** : la marge d'un même PLU
peut varier selon les morceaux dont il provient.

## Le stock et le décalage
On **achète** puis on **vend** plus tard. Sur une période donnée, achats et ventes
ne correspondent donc pas exactement. Raisonnez en **tendance** sur plusieurs
semaines, pas au jour le jour.

---

> **En résumé** : cet outil donne des **tendances fiables et actionnables**, à
> condition de les lire avec ces limites. Elles se réduisent au fur et à mesure
> que vous codez les ventes et saisissez les achats.
`,
  },
];
