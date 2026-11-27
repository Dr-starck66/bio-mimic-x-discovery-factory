# ASTRA DINO Ω — Validation sur la matrice indépendante Wang et al. (2021)

**Date :** 2026-11-14. **Statut : PARTIAL SCIENTIFIC / PASS exploratory computation.**
**Dépôt :** `Dr-starck66/bio-mimic-x-discovery-factory`, branche `astra/dino-omega-ancestry-benchmark-20261114`. Aucun déploiement, fusion, nouvelle automatisation ou coût ajouté.

## Provenance figée

- Publication : Wang M., Lloyd G. T., Zhang C., Zhou Z. (2021), *The patterns and modes of the evolution of disparity in Mesozoic birds*, *Proceedings of the Royal Society B*, DOI: [10.1098/rspb.2020.3105](https://doi.org/10.1098/rspb.2020.3105).
- Dépôt scientifique : [ProjectAncientBeak](https://github.com/graemetlloyd/ProjectAncientBeak).
- [Matrice NEXUS originale figée](https://github.com/graemetlloyd/ProjectAncientBeak/blob/67e7d4375374395e1c17a98a85b8314a71feb685/data/matrix.nex), commit `67e7d4375374395e1c17a98a85b8314a71feb685`, **Git blob SHA-1** `a083926bc99c7f1c37aecab6ffdc4ad1489a6f1f`, 26 639 octets.
- Dimensions lues directement : **80 lignes, 280 caractères**. Deux taxons actuels **`Anas`** et **`Gallus`**, 77 taxons d'oiseaux fossiles et l'outgroup composite `Dromaeosauridae`. Ce dernier a été exclu de l'entraînement et de l'évaluation : **79 taxons**.
- Les caractères polymorphes, inconnus et inapplicables sont traités comme manquants.

## Protocole préservé de BIO-MIMIC X / ASTRA DINO Ω

- **Même méthode et hyperparamètres** que le premier essai Holtz : k=3 voisins, minimum 20 caractères comparables, scoring leave-one-taxon-out, colonne cible totalement exclue du calcul de similarité, autres scores du taxon testé disponibles.
- Comparaison obligatoire à la majorité des états de la colonne, calculée **sans** le taxon testé sur les **mêmes cellules évaluables**.
- Contrôle négatif de sélection aléatoire de 3 états parmi les taxons d'entraînement : 30 répétitions avec graine 20261114 ; contrôle qui conserve approximativement les fréquences de classes.
- **Ce n'est pas un transfert direct des poids d'un modèle Holtz préentraîné :** les 386 caractères Holtz et les 280 de Wang n'ont pas été appariés par homologie. La méthode seule est transférée.

## Résultats vérifiés par une exécution du calcul sur les 26 639 caractères source via le connecteur de lecture GitHub

| Sous-ensemble | Cellules évaluables | ASTRA | Majorité |
|---|---:|---:|---:|
| 77 taxons d'oiseaux fossiles | 10 356 | 8 666 (83,681 %) | 7 393 (71,389 %) |
| 2 espèces d'oiseaux vivants | 534 | 423 (79,213 %) | 310 (58,052 %) |
| **Ensemble 79 taxons** | **10 890** | **9 089 (83,462 %)** | **7 703 (70,735 %)** |
| **Gain ensemble** |  | **+12,727 points** | — |

Détail des taxons vivants : `Anas`, **213/267**, majorité **157/267** ; `Gallus`, **210/267**, majorité **153/267**.

Contrôle négatif 30 répétitions : **65,890 %** de moyenne, minimum **65,115 %**, maximum **66,648 %**. En comparant 79 taxons individuellement : **76** améliorés, **3** dégradés, **0** ex æquo. Pas de test prospectif sur un nouveau fossile ni de modèle génome→trait.

## Démonstration, garde-fous, état

- **PASS** : le connecteur GitHub a délivré le contenu de la matrice citée, dimensions vérifiées, calcul de prédiction réellement exécuté, groupes vivants/fossiles vérifiés, témoins négatifs exécutés.
- **PASS** : 14/14 tests logiciels **locaux** Node.js réussis, incluant les 8 tests antérieurs et 6 nouveaux : intégrité Git blob, dimensions 80×280, présence des deux oiseaux vivants, exclusion de `Dromaeosauridae`, contrôle des dénominateurs et tests hors ligne sur matrice synthétique.
- **PARTIAL** : moteur et tests ajoutés sur la branche GitHub ; la **réexécution Node exacte du commit de la branche contre la matrice réelle n'est pas attestée** (l'accès HTTP sortant de l'environnement de test local est indisponible).
- **UNVERIFIED** : généralisation à une matrice vraiment inconnue lors du développement ; reconnaissance de traits jamais décrits ; reconstitution des séquences nucléaires perdues ; embryon ou organisme ressuscité.

## Conclusions non trompeuses

Cette évaluation **réplique une méthode d'imputation morphologique** sur un second jeu indépendant contenant les deux oiseaux actuels. Elle ne démontre pas la résurrection de dinosaures non aviens ; le groupe fossilifère étudié est principalement **avien**, et l'outgroup non avien `Dromaeosauridae` est un composite exclu de la métrique. Les 2 études utilisent des caractères non harmonisés : un modèle réellement transféré nécessiterait un dictionnaire d'homologies audité et un jeu de données externe disjoint.

**Action scientifique unique :** établir le tableau d'homologies indépendamment contrôlé entre les deux jeux de caractères, avant de tester un modèle réellement figé sur une troisième source sans réentraînement.
