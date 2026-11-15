# ASTRA DINO Ω — GENOME REVERSE v0.8

**15 novembre 2026 · Branche isolée · Coût additionnel 0 € · SCIENTIFIC GATE: PARTIAL.**

## Origine du test
Le document `PREREGISTRATION.md` a figé le modèle avant lecture de la troisième matrice. Le TNT Xi 2024 a répondu **HTTP 401/403** et le complément de Yang 2025 n'a pas pu être obtenu. Les amendements `AMENDMENT_THIRD_DATASET.md` et `AMENDMENT_02_PUBLIC_NEXUS_HOLDOUT.md` ont été commis *avant* toute lecture du repli Sues (2011).

**Troisième source réellement lue** : Sues, Nesbitt, Berman & Henrici, 2011, *A late-surviving basal theropod dinosaur from the latest Triassic of North America*, DOI [10.1098/rspb.2011.0410](https://doi.org/10.1098/rspb.2011.0410). Matrice [SuesEA11_Theropoda.nex](https://github.com/rossmounce/cladistic-data/blob/ea2a30384cf1654271970d5c8b661c08dcd3158d/nexus_files/SuesEA11_Theropoda.nex), Git blob SHA `2c89cac975cdb8e2b13ebe109fd66a0a29a26907`.

42 taxons × 319 caractères, 13 398 cellules ; 5 189 `?`/`-`, 6 états ambigus, 8 203 états simples.

## Réelle validation hors développement

**6 526 caractères cachés** chez 42 taxons ; les ancrages `j % 5 == 0` de chaque taxon cible sont **visibles**, donc prédiction anatomique conditionnelle et NON reconstruction du génome ni masquage morphologique total.

Modèle figé v0.7 : Mk symétrique taux 0.25, arbre étoile faute d'arbre externe validé, coefficient conjoint 0.35, max. 12 voisins, ≥3 ancrages, 500 bootstraps regroupés par taxon, seed 20261114.

| Méthode | Correct/6526 | Exactitude | Log-loss | Brier |
|---|---:|---:|---:|---:|
| Majorité d'entraînement | 4780 | 73.2455% | **0.64837** | **0.378060** |
| Mk étoile | 4779 | 73.2302% | 0.93903 | 0.443403 |
| ASTRA conjoint | **4814** | **73.7665%** | 0.76079 | 0.379580 |
| Ancrages substitués | 4777 | 73.1995% | 0.88186 | 0.429692 |

Gain conjoint − Mk : **+0.536 point**, bootstrap 95% **[+0.266,+0.765]**. Gain conjoint − majorité : **+0.521 point**, bootstrap 95% **[+0.244,+0.765]**. Le recalcul **indépendant** de majorité a retrouvé 4 780 prédictions correctes.

**Verdict** : avantage en **exactitude** sur une troisième matrice, mais **échec de supériorité probabiliste** contre la majorité simple (meilleure log-loss et Brier). Aucune capacité nouvelle de reconstruction génomique ancestrale n'est démontrée.

Voir `evidence_sues2011_real_holdout_v08.json`, `audit_majority_independent_v08.json`.

## Arbre externe : rejet explicite des substituts circulaires

- **Černý & Simonoff (2023)** : `baron_unconstrained.treefile` réellement présent dans leur ZIP Zenodo ; il provient des *caractères de Baron* : PAS indépendant du jeu de test Baron.
- **Open Paleo** : hiérarchie générale de clades, PAS un arbre résolu de tous les taxons.
- **Yang et al. 2025, Fig. 17** : arbre à 74 taxons ; **seulement 7 correspondances exactes sur les 42 taxons Sues**, 9 au niveau du genre. Insuffisant pour projection sans hypothèses supplémentaires.

Voir `external_phylogeny_gate_v08.json`. La condition **« phylogénie externe indépendante applicable » est UNVERIFIED**.

## Communications scientifiques
- **Baron : FAIL de délivrance**, avis Gmail 550 5.4.1 Recipient address rejected: Access denied.
- **Hendrickx : envoi effectué, aucune réponse observée**.
- **Brownstein / Griffin : envoi effectué, aucune réponse observée**.

Aucune réponse scientifique inventée.

## Code autonome et tests
Un paquet ZIP de conversation **ASTRA_DINO_GENOME_REVERSE_OMEGA_V08_20261115.zip** contient une implémentation Node 22+ sans npm, ses 9 tests logiciels, rapports, SHA-256 et fixture explicite. Tests locaux **9/9 PASS**, mais sur **cas synthétiques**. Exécution du vrai jeu de 6 526 observations et validation indépendante de la majorité faites séparément depuis les données authentifiées via GitHub ; la réexécution du **même script Node sur le NEXUS réel** est **UNVERIFIED** faute de réseau DNS dans l'environnement local.

Aucune fusion vers `main`, aucune modification de production.

**Action prioritaire** : une phylogénie externe taxon par taxon réellement indépendante des caractères cachés, provenance vérifiable, suivie d'une nouvelle calibration Mk et d'une épreuve entièrement vierge.