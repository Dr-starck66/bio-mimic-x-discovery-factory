# ASTRA DINO Ω — blocs génétiques entiers : ALX1, HMGA2 et 26 comparateurs

**14 novembre 2026 · Audit réel : PASS (logiciel et fichiers) · Validité causale / prédictive externe : UNVERIFIED · Coût : 0 €**

## Résumé exécutif

Les 3 originaux Oslo vérifiés par SHA-256 et les 28 intervalles issus du dépôt des auteurs Rubin (Git blob épinglé) ont été réanalysés sur l’assemblage `GCA_902806625.1`. Parmi 64 échantillons VCF, 50 disposent de dimensions du bec appariées. Le VCF contient 261 754 positions, dont 6 928 dans les 28 régions et 3 570 SNP bialléliques passant MAF ≥5 % et call rate ≥80 %.

**Aucune association ne reste significative après correction max-R² familiale sur les 58 tests (28 blocs × 2 traits + modèle conjoint × 2 traits).** Le programme a effectué 20 000 permutations intra-population et un retest à seconde graine. Les R² reflètent des ajustements in-sample et ne sont ni une preuve d’effet causal, ni une capacité de prédiction externe.

## Résultats des deux régions scientifiques ciblées

| Profil génétique non phasé | SNPs | R² forme | p forme brute | p forme corrigée 58 | R² taille | p taille brute | p taille corrigée 58 |
|---|---:|---:|---:|---:|---:|---:|---:|
| LOCUS_03_HMGA2 | 394 | 0.1081 | 0.0513 | 0.9994 | 0.2234 | 0.0333 | 0.5214 |
| LOCUS_07_ALX1 | 238 | 0.0348 | 0.4052 | 1.0000 | 0.1427 | 0.1090 | 0.9726 |
| JOINT_03_07 | 632 | 0.1244 | 0.1450 | 0.9940 | 0.2668 | 0.0788 | 0.2656 |

Les régions authentiques sont HMGA2 = locus auteur n°3 sur 1A **32 232 902–34 354 642**, ALX1 = locus auteur n°7 sur 1A **40 692 203–42 199 937** (bornes imprimées par les auteurs). Les composantes génétiques sont construites à partir des génotypes dosage 0/1/2, **sans phasage** des allèles. L’incertitude de convention aux limites ne touche pas ces deux régions dans le comptage du dernier audit.

## Panel comparateur et corrections multiples

- Meilleur candidat parmi les 29 modèles pour la **forme** : `LOCUS_01`, R²=0.2579, p brute=0.0008, **p max-R² corrigée=0.3074** (non significative).
- Meilleur candidat parmi les 29 modèles pour la **taille** : `LOCUS_24`, R²=0.3274, p brute=0.0049, **p max-R² corrigée=0.0875** (non significative).
- Les 26 autres blocs préalablement sélectionnés par Rubin sont des **comparateurs génomiques**, pas des témoins biologiques négatifs garantis. Les permutations intra-population constituent le contrôle de distribution nulle. Les hypothèses sont de taille différente (2 PCs pour les blocs seuls, 4 PCs conjoints) ; les maxima des statistiques R² sont recalculés sous permutation pour contrôler ce biais.
- 95e percentile du maximum nul sur 58 tests : **0.3549** ; la plus forte association en taille observée reste à R²=0.3274.

## Sensibilité et contrôle de sélection du modèle

Deux composantes PCA par bloc et le panel de 58 tests définissent **l’analyse primaire**. Des analyses secondaires ont examiné la famille limitée à six tests focaux et un modèle alternatif à une seule composante génétique par bloc. Ces comparaisons sont exploratoires et ne valident aucune découverte.

| Modèle | 2 PC : p taille corrigée 6 | 1 PC : p taille corrigée 6 | 1 PC : p corrigée 12 (choix du nombre de PC) |
|---|---:|---:|---:|
| LOCUS_03_HMGA2 | 0.1489 | 0.0724 | 0.1666 |
| LOCUS_07_ALX1 | 0.4213 | 0.2246 | 0.4382 |
| JOINT_03_07 | 0.0801 | 0.0383 | 0.0914 |

**Avertissement essentiel :** le modèle conjoint à une seule composante par bloc affiche p=0,0383 dans la famille de six tests, mais **p=0,0914** lorsque le choix entre une ou deux composantes est lui aussi corrigé (12 tests) ; avec la famille primaire de 58 tests, aucune preuve positive n’est obtenue. Il serait incorrect d’annoncer cette comparaison secondaire comme une découverte significative.

### Retrait d’une population à la fois (description, pas validation externe)

- `LOCUS_03_HMGA2` : R² taille entre 0.1195 et 0.3722 selon la population supprimée. Les composantes PCA restent initialement estimées sur l’échantillon entier ; il ne s’agit **pas d’un test aveugle**.
- `LOCUS_07_ALX1` : R² taille entre 0.0396 et 0.3910 selon la population supprimée. Les composantes PCA restent initialement estimées sur l’échantillon entier ; il ne s’agit **pas d’un test aveugle**.
- `JOINT_03_07` : R² taille entre 0.2095 et 0.5276 selon la population supprimée. Les composantes PCA restent initialement estimées sur l’échantillon entier ; il ne s’agit **pas d’un test aveugle**.

### Contrôles négatifs conservés

- Mutations synthétiques, allèles fixes, génotypes non bialléliques, >20 % d’appels manquants, correspondance d’individus incorrecte, tableau d’intervalles falsifié : tests de rejet PASS dans la suite locale. La graine de permutation est publiée. Les permutations conservent la relation taille/forme à l’intérieur d’un individu par permutation conjointe des deux traits.
- Un jeu de phénotypes réattribués au hasard à l’intérieur des populations a servi de contrôle témoin descriptif, **sans prétendre qu’une seule permutation prouve l’absence de biais**.
- Les familles de six et de douze tests ont été rapportées en complément, même lorsqu’elles présentent des chiffres numériquement favorables : elles n’annulent pas la correction primaire.

## Retest indépendant des permutations

La première série utilise 20 000 permutations, graine 20261114 ; la seconde utilise 20 000 permutations, graine 20261115. Les R² et comptes SNP sont identiques au dernier chiffre enregistré. La plus grande variation absolue de p corrigée sur 58 tests est **0.006050**. Les deux séries concluent à **0/58 significatifs**.

## Protocole reproductible (sans publier le VCF privé)

```bash
python -m pip install "numpy>=1.24,<3"
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s tests -p "test_astra_dino_rubin_block_profiles.py" -v
OPENBLAS_NUM_THREADS=1 python validation/astra_dino_rubin_block_profiles.py \
  --oslo-dir /DOSSIER_PRIVE/OSLO-2025-ORIGINALS \
  --loci-tsv data/Rubin2022_28Loci_start_stop_author_original.txt \
  --nperm 20000 \
  --output reports/astra_dino_rubin_block_profiles_20000_20261114.json
```

Les trois originaux restent stockés dans la bibliothèque ASTRA et **ne sont pas inclus** dans l’archive publique ni dans la branche GitHub. Ils sont vérifiés en début d’exécution contre leurs SHA-256 fixes. Le fichier des 28 coordonnées est épinglé par son Git blob SHA-1 `dc6ec1da23aa6426fcc16dc5b5d1124d55699616`; le CSV complémentaire des auteurs a été confronté dans la phase précédente mais n’est pas indispensable à la reproduction du présent calcul.

## Limitations scientifiques et résultat défavorable

- 50 individus appartenant à 11 groupes (dont 4 de seulement 2 oiseaux) : puissance et échangeabilité des permutations limitées ; parenté, environnement et lot technique non contrôlés. Les tests supposent l’échangeabilité des individus à l’intérieur de chaque groupe.
- Les profils PCA génétiques ne sont **pas** des haplotypes phasés, et l’introduction de nombreux SNP en déséquilibre de liaison ne démontre pas un variant fonctionnel.
- Le panel Rubin a été identifié dans une étude distincte, mais il ne constitue pas un génome témoin aléatoire, ni une validation externe génotype–bec chez les mêmes espèces.
- Aucune prédiction sur un échantillon tenu à l’écart, aucun score de prédiction fossile, aucun résultat causal ALX1/HMGA2 et aucun test expérimental d’expression ne sont fournis.

**Prochaine action scientifique unique :** obtenir une cohorte réellement indépendante et appariée génotype↔dimensions du bec, avant de promettre un bénéfice prédictif ; verrouiller a priori l’assemblage, le nombre de PCs et les critères de succès.

**Sources publiques** :
- Rubin et al. (2022), DOI https://doi.org/10.1126/sciadv.abm5982 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/
- Intervalles authentiques auteurs : https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/XX_twisst_topology_weighting/28Loci_start_stop.txt
- Table de statistiques : https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/supplementary_data_for_github/Supplementary_data_2_all_peaks_median_diversity_stat.csv
- Oslo : https://doi.org/10.5061/dryad.3ffbg79w8 (original privé en possession de l’utilisateur)