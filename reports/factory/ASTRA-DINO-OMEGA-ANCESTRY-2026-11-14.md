# ASTRA DINO Ω — Évaluation exploratoire reproductible
Date de collecte et de calcul : 14 novembre 2026.
Branche isolée BIO-MIMIC X : `astra/dino-omega-ancestry-benchmark-20261114`.

## Objectif
Évaluer les caractères anatomiques fossiles masqués et la conservation de séquences mitochondriales d'oiseaux **vivants**. Ne pas présenter ces travaux comme la résurrection d'une espèce éteinte, la récupération d'ADN mésozoïque, ni comme un modèle génome→anatomie validé.

## Preuve A — Données morphologiques publiées
- Source scientifique : T. R. Holtz Jr., Université du Maryland, `https://www.geol.umd.edu/~tholtz/Gaia2000` (NEXUS, accessible le 14/11/2026).
- Taille de la matrice récupérée : **50 taxons × 386 caractères**. Exclusion explicite de `allzero` et des taxons composites : **34 taxons individuels** conservés.
- `?`, `-`, les états polymorphes `(01)` / `{01}` sont non évaluables ; les 0 ne sont jamais confondus avec une valeur manquante.
- Validation par exclusion **complète d'un taxon de l'entraînement** pour chaque prédiction ; les autres caractères de ce même taxon restent disponibles à l'inférence. Pour la colonne cible, seuls les autres caractères entrent dans la recherche des voisins. k=3 voisins, recouvrement minimal=20 caractères connus, mêmes cellules évaluables pour la référence majoritaire.

| Mesure | Résultat mesuré |
|---|---:|
| Cellules fossiles évaluables | 6 571 |
| Modèle de voisinage morphologique | 5 527 / 6 571 = **84,112 %** |
| Référence : état majoritaire de l'entraînement | 5 034 / 6 571 = **76,609 %** |
| Gain observé | **+7,503 points** |
| Taxons améliorés / dégradés / égaux | 27 / 5 / 2 |
| Contrôle négatif : 30 échantillonnages aléatoires d'étiquettes d'entraînement, k=3 | **73,384 %** de moyenne, étendue **72,089–74,205 %** |
| Rééchantillonnage par taxon, 2 000 réplications (écart en points) | **[+5,43 ; +9,47]** ; indicatif et non une garantie de généralisation |

Vérifications individuelles : **Archaeopteryx** 274/351 (référence 219/351), **Confuciusorn** 211/292 (référence 159/292), **Caudipteryx** 202/242 (référence 173/242), **Carnotaurus** 253/304 (référence 213/304), **Rahonavis** 106/143 (référence 85/143).

**Interprétation limitée :** les tests prédisent des scores déjà connus mais temporairement cachés, en exploitant d'autres scores anatomiques du même taxon. Il n'existe pas ici d'essai prospectif, d'arbre phylogénétique externe, de datation fossile incorporée, ni de simulation d'animal vivant. La distribution des caractères et la parenté des taxons peuvent surestimer la généralisation.

## Preuve B — Séquences réelles d'oiseaux
Récupération via NCBI E-utilities FASTA, accessions **versionnées**, contrôle du nom d'accession, de la composition A/C/G/T/N et de la longueur :
- Gallus gallus : `NC_001323.1` — 16 775 nucléotides, GC 45,96 %.
- Meleagris gallopavo : `NC_010195.2` — 16 719 nucléotides, GC 43,51 %.
- Anas platyrhynchos : `NC_009684.1` — 16 604 nucléotides, GC 48,59 %.
- Struthio camelus : `NC_002785.1` — 16 595 nucléotides, GC 44,61 %.

Total : **66 693 nucléotides mitochondriaux** (et non 66 693 caractères indépendants).

Comparaison exploratoire d'ensembles de 11-mères exacts distincts (indice de Jaccard, **pas** une identité de séquence alignée) :
- poule / dinde : 3 910 11-mères communs, J=0,1338 ;
- poule / canard : 2 451, J=0,0802 ;
- poule / autruche : 2 248, J=0,0731 ;
- dinde / canard : 2 144, J=0,0695 ;
- dinde / autruche : 2 044, J=0,0660 ;
- canard / autruche : 2 156, J=0,0702.

Ces mitochondries ne permettent pas à elles seules de caractériser les gènes nucléaires de morphogenèse, et aucun génome de dinosaure non avien n'a été obtenu. **Les deux analyses ne sont pas encore couplées par un apprentissage multi-omique.**

## Code et audit
- `validation/astra_dino_ancestry.mjs` : accès direct aux sources, parseur strict NEXUS, prédiction leave-one-taxon-out, contrôles négatifs, bootstrap par taxon, comparateur des mitochondries NCBI.
- `tests/test_astra_dino_ancestry.mjs` : tests hors ligne, échecs explicites en cas de données incorrectes.
- Commande de validation : `node --test tests/test_astra_dino_ancestry.mjs`.
- Commande d'analyse réelle (connexion à sources requise) : `node validation/astra_dino_ancestry.mjs --online`.
- Local Node.js 22.16 : **8/8 tests du prototype de même logique PASS**. Une exécution du fichier publié, des jeux de données complets depuis le runtime du dépôt ou une CI GitHub restent **UNVERIFIED** ; les calculateurs sur les données réelles ont été exécutés séparément au moyen de connecteurs de lecture.
- **Absence de checksum canonique figé pour le fichier source Holtz** : intégrité en amont seulement partiellement vérifiée, malgré les dimensions et états stricts.
- Aucun coût supplémentaire, aucune fusion, aucun workflow GitHub Actions ajouté, aucune modification d'organisme vivant.

## Prochaine épreuve scientifique
Chercher une matrice morphologique archosaurienne indépendante **avec oiseaux actuels + fossiles** et caractères homologues sourcés, puis effectuer une validation externe préenregistrée sans relabeling à partir des mêmes taxons. Ne passer à une véritable prédiction **génome→caractère fossile** que si les lignes génomiques et anatomiques sont appariées au même taxon ou par une méthode évolutive explicitement modélisée.

**Statuts :** récupération des sources et calcul exploratoire : PASS ; intégration expérimentale au dépôt : PARTIAL ; tests logiciels locaux : PASS (8/8 prototype) ; re-test du commit GitHub : UNVERIFIED ; validation biologique et « résurrection » : UNVERIFIED.
