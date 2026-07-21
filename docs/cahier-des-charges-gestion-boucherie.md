# Cahier des charges — Outil de gestion pour La Boucherie de l'Abbatiale

*Document de cadrage issu d'une phase de discussion et d'analyse des données réelles de la caisse (CAS CT100 / libraVISOR), de l'Excel de marge existant, et d'une facture fournisseur (Soviago). À utiliser comme référence de travail pour le développement (Claude Code).*

---

## 1. Contexte et objectif

La Boucherie de l'Abbatiale (Guîtres, 33) suit actuellement sa marge via un fichier Excel devenu ingérable ("usine à gaz") : saisie manuelle des achats fournisseurs, rapprochement manuel avec les familles de produits, copier-coller du CSV de caisse. Résultat : les achats ne sont quasiment pas saisis (77 € HT sur 4282 € HT de CA sur 11 jours observés), ce qui rend la marge affichée (~98%) inexploitable.

**Objectif** : remplacer cet Excel par une application web sur mesure, hébergée sur un serveur Proxmox personnel, qui automatise l'import des ventes et des achats, et donne une vraie visibilité sur la marge — sans alourdir le travail quotidien en boutique/atelier.

**Utilisatrice principale au quotidien** : la fille du porteur de projet (non technicienne — l'outil doit être simple d'usage, aucune formule à comprendre).

**Développement et hébergement** : délégués à Claude Code (développement, maintenance des repositories, déploiements) sur un serveur Proxmox déjà en place (actuellement vierge). **Rien n'existe encore côté données** : ni base de données, ni solution de sauvegarde — tout est à construire depuis zéro, y compris la stratégie de sauvegarde (qui ne doit pas être un point traité après-coup, vu qu'elle portera à terme les données de compta de la boucherie).

---

## 2. Stack technique retenue

| Composant | Choix | Justification |
|---|---|---|
| Frontend | React avec **Refine** (framework CRUD/admin) | Refine est justement pensé pour ce type d'appli (beaucoup d'écrans CRUD, tableaux de bord) — évite de réécrire la plomberie standard (listes, formulaires, auth, providers de données) à la main |
| Backend | Python (FastAPI) | Traitement de données, lecture de factures par IA, statistiques (écosystème pandas) |
| Base de données | PostgreSQL | Robustesse, standard, bien supporté |
| Visualisation avancée | Différée — tableau de bord interne d'abord, Grafana envisageable en V2 si le besoin dépasse les capacités internes | Éviter un service supplémentaire à sécuriser dès le départ |
| Hébergement | VM dédiée sur Proxmox existant | Serveur déjà disponible |

---

## 3. Sources de données

### 3.1 Export de caisse (CAS CT100 / libraVISOR) — format GDPdU
- Fichier CSV (encodage cp1252, séparateur `;`), structure décrite par `index.xml` / DTD GDPdU.
- **Une ligne par mouvement**, pas par ticket. Colonne clé : `Type_enregistrement` :
  - `1` = ligne de vente (article) — **seule donnée utile pour le CA/kg vendus**
  - `2` = total du ticket
  - `3` = grand total cumulé
  - `4` = ligne de paiement
- **Colonne `Annulation` (True/False)** : une ligne de vente annulée (ex. erreur de pesée corrigée) reste dans l'export pour traçabilité fiscale, mais ne doit **jamais** être comptée dans le CA/kg. Vérifié sur données réelles (ticket 3173) : le champ `Montant_Total` d'un ticket est **brut, il inclut les lignes annulées** — le montant réellement payé est `Montant_Total_Paiement` (sur la ligne de type 2) ou la ligne de paiement (type 4). Toujours utiliser ce dernier pour vérifier la cohérence d'un ticket nettoyé.
- Autre colonne à surveiller : `Copie ticket` (doublon d'impression, à dédupliquer si nécessaire).
- **Import prévu : hebdomadaire**, sur demande manuelle d'export à libraVISOR pour une période donnée (pas de flux automatique). Les périodes demandées se chevaucheront nécessairement dans le temps (par précaution, pour ne rien manquer), ce qui implique un import **idempotent** : réimporter un fichier contenant des lignes déjà connues ne doit ni les dupliquer, ni les modifier.
- **Cohérence des données dans la durée** — objectif : maintenir une base de ventes complète et fiable malgré des imports répétés et potentiellement redondants ou incomplets. Deux mécanismes à prévoir :
  - **Déduplication** : définir une clé métier stable par ligne (le fichier ne fournit qu'un numéro de ligne propre à chaque export, non réutilisable comme identifiant). Piste : combinaison `ID_SD_Device + Numéro_Rapport_Z + Numéro_Ticket + Type_enregistrement + N_PLU + Poids_Gramme + Montant` (+ position dans le ticket si nécessaire pour distinguer deux lignes identiques dans un même ticket, cf. l'exemple réel du ticket 3173 où le PLU "Chorizo ibérique" apparaît deux fois avec des poids différents). Import en `upsert` sur cette clé.
  - **Détection des trous** : `Numéro_Rapport_Z` (clôture de caisse) est séquentiel. À chaque nouvel import, vérifier la continuité des numéros de Z par rapport à ce qui est déjà en base ; en cas de saut, signaler un écart potentiel plutôt que de laisser un trou silencieux.
  - **Journal des imports** : conserver un historique (période demandée, date de dépôt, nombre de lignes ajoutées / déjà connues / anomalies détectées) consultable par l'utilisatrice.
- **Catalogue PLU** : le CSV de vente ne contient que les PLU **effectivement vendus** (166 sur la période observée), pas le catalogue complet. **Le catalogue complet n'est pas exportable depuis la caisse** — il existe aujourd'hui dans un fichier Excel maintenu à la main (291 PLU référencés). Ce fichier sera **importé directement** en base au démarrage du projet, puis géré ensuite via un **CRUD dédié** dans l'application (plus d'entretien manuel d'Excel une fois l'import initial fait).

### 3.2 Factures fournisseurs (PDF)
- Reçues par mail ou scannées, une mise en page différente par fournisseur (Soviago, Métro, Promocash, Loste, Marceteau, Saveurs d'Antoine identifiés à ce stade).
- Testé avec succès sur une facture Soviago réelle (extraction ligne à ligne, recoupement des totaux exact).
- Chaque ligne comporte : référence fournisseur, désignation, poids/quantité, prix unitaire, montant HT — **aucun lien natif vers les familles/PLU internes**.
- Présence de lignes non-produits à filtrer (frais de port, participation, cotisations Interbev/CVO...) qui gonflent légèrement le coût réel de la matière première si elles sont ignorées.
- Présence de numéros de lot de traçabilité (ex. `VDC1941539`) — utile pour un futur lien achat ↔ production, non prioritaire au démarrage.
- **Avant de démarrer le développement du module de lecture de factures** : demander une facture type à chaque fournisseur utilisé (Soviago, Métro, Promocash, Loste, Marceteau, Saveurs d'Antoine, et tout autre identifié) afin d'établir le modèle de données à partir d'exemples réels, plutôt que de généraliser depuis un seul fournisseur (Soviago) déjà testé.

---

## 4. Modules fonctionnels

### 4.1 Référentiels (CRUD)
- **Familles** (et sous-familles, cf. §5)
- **PLU / Produits** : code, nom, famille, TVA, prix de vente — import initial depuis le fichier Excel existant (291 PLU), puis gestion exclusive via CRUD
- **Fournisseurs**
- **Table de correspondance fournisseur → famille/sous-famille** : mémorise l'affectation choisie pour chaque référence fournisseur, afin de ne jamais revalider deux fois la même ligne. Cœur du système d'apprentissage.

### 4.2 Achats
- CRUD achats (date, fournisseur, lignes, montants)
- Affectation de chaque ligne à une famille/sous-famille via la table de correspondance
- **Saisie assistée par IA** : lecture automatique des factures PDF (déposées manuellement au départ — pas de connexion boîte mail automatique dans un premier temps), proposition d'affectation, **vérification et correction humaine obligatoire** avant validation, via une interface CRUD dédiée.

### 4.3 Ventes
- Dépôt manuel du fichier d'export libraVISOR sur une période demandée (pas d'automatisation du côté caisse)
- Import **idempotent** (déduplication par clé métier) et **détection de trous** (continuité des numéros de rapport Z) — cf. §3.1
- Nettoyage automatique : exclusion des lignes non-ventes (types 2/3/4), des annulations, dédoublonnage des copies de ticket
- Rattachement automatique aux PLU/familles existants

### 4.4 Tableaux de bord
- CA, kg vendus, panier moyen, top produits/familles, par période
- Marge par famille et sous-famille (cf. §5)
- Détection des achats anormalement chers par rapport à l'historique fournisseur (signal simple, sans dépendre du module de rendement)
- Externalisation vers Grafana envisageable en V2

---

## 5. Granularité de la marge — décision de conception

Trois niveaux de précision possibles, retenus dans cet ordre de priorité :

1. **Par famille** (niveau déjà couvert par l'Excel actuel) — socle de base, toujours disponible.
2. **Par sous-famille** (ex. "Veau à griller" / "Veau à mijoter" / "Veau haché") — niveau intermédiaire, affecté directement à la ligne d'achat, sans effort de pesée supplémentaire.
3. **Par PLU précis via rendement de découpe** — niveau cible, mais avec une méthode adaptée pour ne pas alourdir le travail quotidien :

### 5.1 Rendement par calibrage périodique (et non pesée systématique)
Peser à chaque découpe a été écarté : la découpe/transformation ne se fait pas en une seule fois, et l'astreinte quotidienne de pesée reproduirait l'échec déjà constaté sur la saisie des achats.

**Méthode retenue** : établir, pour chaque type de pièce achetée, un **rendement moyen de découpe** par échantillonnage périodique (une pesée-type de temps en temps, recalibrée si besoin) — par exemple *"1 kg d'arrière de veau donne en moyenne 36% rôti / 27% steaks / 18% mijoter / 9% haché / 10% perte"*. Ce ratio est ensuite appliqué automatiquement par le logiciel à chaque achat de ce type de pièce, sans saisie quotidienne.

### 5.2 Méthode d'allocation du coût entre produits issus d'une même pièce
Deux méthodes envisagées, à choisir selon la question posée :
- **Au poids** : coût/kg identique pour toutes les sorties. Simple, mais produit des marges "en trompe-l'œil" (un sous-produit obligatoire comme le haché peut apparaître artificiellement déficitaire).
- **À la valeur de vente** (recommandé pour la fiabilité comptable) : le coût est réparti proportionnellement au prix de vente de chaque sortie — la marge % est alors identique sur tous les produits issus d'un même achat. Cette méthode répond bien à *"cet achat est-il rentable dans son ensemble ?"* mais, par construction, ne permet pas de dire qu'un produit est plus rentable qu'un autre au sein d'un même lot (coût joint : la production de rôti implique mécaniquement la production de haché).

**À trancher lors du développement du module rendement/production** : la méthode d'allocation finale (à la valeur par défaut, avec possibilité de comparer à la méthode au poids pour information).

### 5.3 Notion de stock / coût moyen pondéré
Découpe et vente ne sont pas simultanées (un rôti découpé aujourd'hui peut se vendre sur plusieurs jours). Le module de rendement nécessitera donc un **coût unitaire moyen pondéré (CUMP) par PLU**, recalculé à chaque nouveau lot produit, plutôt qu'un coût figé à l'achat.

---

## 6. Séquencement de développement proposé

| Étape | Contenu | Dépend de |
|---|---|---|
| 1 | Schéma de base (familles, PLU, fournisseurs) + import initial du catalogue PLU depuis l'Excel existant + import du CSV caisse sur dépôt manuel, **idempotent dès le départ** (déduplication + détection de trous, cf. §3.1), avec nettoyage (annulations, copies, types non-ventes) | — |
| 2 | Tableau de bord ventes simple (CA, kg, top produits/familles) | 1 |
| 3 | CRUD achats manuel + affectation famille/sous-famille + table de correspondance fournisseur | 1 |
| 4 | Première vraie marge par famille/sous-famille | 2, 3 |
| 5 | Lecture IA des factures PDF (dépôt manuel) alimentant le CRUD achats, avec vérification humaine | 3 |
| 6 | Module rendement de découpe par calibrage périodique + CUMP par PLU → marge par produit fini | 4 |
| 7 | Détection achats anormaux, prévisions de fabrication, Grafana si besoin | 6 |

---

## 7. Points de vigilance identifiés (non résolus, à surveiller)

- **Sauvegarde** : aucune solution en place aujourd'hui — ni la base de données ni la stratégie de sauvegarde n'existent. À concevoir dès l'étape 1 (pas en fin de projet) : fréquence, rétention, et surtout stockage **hors du Proxmox** pour survivre à une panne matérielle du serveur.
- **Lecture IA des factures** : fiabilité non garantie à 100%, en particulier sur factures scannées de mauvaise qualité — la vérification humaine reste obligatoire à chaque facture, au moins au démarrage.
- **Modèle de données factures** : à ne pas généraliser depuis la seule facture Soviago testée — attendre la collecte d'un exemple par fournisseur avant de figer la structure de lecture/import.
- **Adhésion opérationnelle** : le succès du module achats (et plus tard rendement) dépend de la discipline de saisie humaine — le logiciel seul ne résout pas ce risque, seulement la friction.
