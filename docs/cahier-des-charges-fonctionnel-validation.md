# Cahier des charges fonctionnel — Nouvel outil de gestion de la boucherie

*Ce document explique ce qu'on cherche à construire, ce que ça change dans le travail quotidien, et les points qui doivent être validés avant de démarrer le développement. Il ne demande aucune connaissance informatique.*

---

## 1. Pourquoi ce projet

Aujourd'hui, le suivi de la marge se fait dans un fichier Excel qui est devenu difficile à tenir à jour : chaque ligne de facture fournisseur doit être recopiée à la main, chaque vente de la caisse doit être recopiée aussi, et ça prend un temps considérable — au point que les achats ne sont presque plus saisis, ce qui rend le calcul de marge faux.

**L'objectif** : un outil qui fait le travail répétitif automatiquement (récupérer les ventes de la caisse, lire les factures fournisseurs), pour que le temps humain serve uniquement à vérifier et corriger, pas à tout retaper.

---

## 2. Ce que l'outil va permettre de voir

- Le chiffre d'affaires, les kg vendus, les produits qui se vendent bien ou mal — jour par jour, semaine par semaine
- La marge réelle, par catégorie de produit (et, si les conditions du §5 sont réunies, produit par produit)
- Les achats qui semblent anormalement chers par rapport aux fois précédentes
- Une vision de ce qui devrait rester en stock par rapport à ce qui a été acheté et vendu — utile pour repérer une perte anormale, un problème de découpe, ou un produit qui stagne

---

## 3. Impact sur le travail administratif (saisie des achats)

Aujourd'hui : chaque ligne de facture est recopiée à la main dans Excel, avec la famille de produit à associer manuellement.

**Avec le nouvel outil, le geste quotidien devient :**

1. La facture arrive (papier ou par mail) → elle est **scannée** si elle est en papier (ou le PDF est simplement récupéré si elle arrive par mail)
2. Le fichier est **glissé-déposé** dans l'outil (aucune saisie de champ à la main à ce stade)
3. L'outil **lit automatiquement** la facture (fournisseur, produits, poids, prix) grâce à une lecture assistée par IA, et propose une affectation par famille/catégorie
4. **Une vérification humaine est obligatoire avant validation** : chaque ligne lue automatiquement s'affiche à l'écran, avec la possibilité de corriger un montant, un poids, ou une catégorie mal reconnue, avant de valider
5. Une fois qu'une référence fournisseur a été validée une première fois (ex. "Arrière de veau VVF" chez ce fournisseur), l'outil **s'en souvient** — la fois suivante, la proposition sera déjà correcte, la vérification devient plus rapide avec le temps

**Ce qui ne change pas** : c'est toujours une personne qui a le dernier mot sur chaque facture. L'IA propose, elle ne décide jamais seule.

**Ce qu'il faut valider** : est-ce que ce geste (scanner/déposer + vérifier) vous semble réaliste à intégrer dans le travail administratif existant, et à quelle fréquence (au fil de l'eau, ou un moment dédié par semaine) ?

---

## 4. Impact sur le travail en boutique (récupération des données de caisse)

**Aucun changement dans le geste de vente au quotidien** — la caisse continue de fonctionner normalement.

En revanche, contrairement à ce qui était écrit dans une version précédente de ce document, la récupération des données de caisse **n'est pas automatique**. Le geste attendu, de façon similaire aux factures fournisseurs :

1. Faire une **demande d'export** sur libraVISOR pour une période donnée (par exemple, chaque semaine)
2. **Mettre le fichier obtenu à disposition** de l'outil (dépôt dans l'application)

**Un point important, géré automatiquement par l'outil pour vous simplifier la vie** : comme les périodes demandées se chevaucheront forcément un peu d'une fois sur l'autre (par sécurité, pour être sûr de ne rien manquer), l'outil est conçu pour **ne jamais compter une vente deux fois**, même si le même ticket apparaît dans deux exports différents. À l'inverse, si une période semble manquer entre deux exports (un oubli, une semaine sautée), l'outil le **détecte et prévient** plutôt que de laisser un trou silencieux dans les données. L'objectif est de finir avec une base de ventes complète et fiable dans la durée, sans que la personne qui dépose les fichiers ait à s'inquiéter des chevauchements ou des oublis.

---

## 5. Impact sur le travail en atelier (découpe) — le point le plus important à valider

C'est le point qui demande un vrai changement d'habitude, donc celui qui doit être discuté et validé en priorité.

**Le besoin** : pour connaître la marge réelle d'un produit précis (par exemple : "est-ce que le rôti de veau est plus rentable que le veau haché ?"), il faut savoir combien de kilos de chaque produit sort d'une pièce achetée. Cette information n'existe nulle part aujourd'hui.

**Ce qui est demandé concrètement** : peser, de temps en temps (pas à chaque découpe), ce qui sort d'une pièce type — par exemple, une fois qu'un arrière de veau est découpé, noter combien de kilos sont partis en rôti, en steaks, en morceaux à mijoter, en haché, et ce qui a été perdu (os, gras). Cette pesée n'a **pas besoin d'être faite à chaque fois** : une pesée de temps en temps par type de pièce suffit à établir une moyenne fiable ("un arrière de veau donne en général X% de rôti, Y% de steaks..."), que l'outil réutilise ensuite automatiquement pour toutes les découpes suivantes du même type.

**Ce que ça implique en pratique** :
- Une pesée occasionnelle, pas un geste quotidien systématique
- Un recalibrage de temps en temps si les proportions semblent avoir changé (nouvelle pièce, nouveau fournisseur...)
- Sans cette information, l'outil peut quand même donner une marge — mais seulement par **catégorie de produit** (ex. "le Veau" dans son ensemble), pas produit par produit. Ce n'est pas bloquant pour démarrer, juste moins précis.

**Ce qu'il faut valider** :
- Est-ce que cette pesée occasionnelle est réaliste à intégrer dans le travail de découpe ?
- À quelle fréquence semble raisonnable pour un recalibrage (par saison ? au changement de fournisseur ? à la demande ?) ?

---

## 6. Un point de vocabulaire à valider ensemble : qu'est-ce qu'une "famille" de produits ?

Une proposition de départ, à discuter et corriger si elle ne correspond pas à la réalité du métier :

- **Famille** = grande catégorie, correspondant à ce qu'on achète (Bœuf, Porc, Veau, Agneau, Volaille, Charcuterie/Traiteur...)
- **Sous-famille** (optionnelle, plus fine) = façon dont le produit est utilisé/vendu au sein d'une famille (par exemple pour le Bœuf : "à griller", "à mijoter", "haché")
- **Produit (PLU)** = l'article précis vendu en caisse, avec son propre code et son propre prix

**Question ouverte** : est-ce que ce découpage correspond à la façon dont vous pensez naturellement les produits, ou une autre logique serait plus parlante (par exemple, un découpage par rayon, ou par mode de vente) ?

---

## 7. Un contrôle automatique en plus, pas une contrainte de travail

Une fois que les rendements de découpe (§5) sont établis, l'outil pourra comparer, sur une période donnée, ce que les achats auraient dû produire (achats × rendement) à ce qui a réellement été vendu. Un écart important entre les deux est un signal utile (perte anormale, casse, rendement mal calibré, produit qui ne se vend pas) — c'est un contrôle qui tourne tout seul, sans demander de travail supplémentaire à personne.

---

## 8. Résumé des questions à valider avant de démarrer le développement

1. Le geste "scanner/déposer une facture + vérifier la lecture automatique" (§3) est-il réaliste dans le travail administratif actuel ?
2. La pesée occasionnelle pour établir les rendements de découpe (§5) est-elle acceptable dans le travail d'atelier ? À quelle fréquence de recalibrage ?
3. La définition de famille / sous-famille proposée (§6) correspond-elle à la réalité du métier, ou faut-il l'ajuster ?
