# ASTRA DINO Ω — Stress test sur fossiles incomplets (14/11/2026)

## Provenance indépendante
Wang M., Lloyd G., Zhang C., Zhou Z. (2021), *The patterns and modes of the evolution of disparity in Mesozoic birds*, Proceedings of the Royal Society B, DOI **10.1098/rspb.2020.3105**. Matrice sur `graemetlloyd/ProjectAncientBeak`, fichier `data/matrix.nex` au commit `67e7d4375374395e1c17a98a85b8314a71feb685`, Git blob SHA-1 **a083926bc99c7f1c37aecab6ffdc4ad1489a6f1f**. Empreinte vérifiée directement par le connecteur GitHub. 80 taxons × 280 caractères, dont 77 oiseaux fossiles, 2 oiseaux actuels et le groupe composite Dromaeosauridae, exclu de la prédiction.

## Nouvelle épreuve d'ablation : caractères incomplets
Pour chacun des 79 taxons individuels : exclusion totale de ce taxon du jeu de référence; révélation aléatoire d'une fraction des *autres* états morphologiques observés, puis prédiction des états connus mais cachés. Ne jamais se servir des états cibles comme variables d'entrée. États polymorphes, absents ou inapplicables exclus du dénominateur. Baseline : état majoritaire dans les autres taxons pour chaque colonne sur les **mêmes** prédictions couvertes. Voisinage morphologique k=3 avec au moins 20 caractères d'entrée communs. Cinq répétitions déterministes par fraction, graine 20261114.

| Fraction des caractères connus fournis | Score kNN | Majorité comparable | Gain (points) | Couverture des cibles éligibles |
|---|---:|---:|---:|---:|
| 20 % | 79,53 % | 71,21 % | +8,32 | 83,47 % |
| 40 % | 82,55 % | 70,99 % | +11,55 | 98,36 % |
| 60 % | 82,80 % | 70,74 % | +12,05 | 99,80 % |
| 80 % | 83,19 % | 70,67 % | +12,52 | 100,00 % |

À 20 % de caractères révélés : environ 8 706 cellules éligibles **par répétition**, dont 7 267 prédictions couvertes en moyenne. Ces taux sont agrégés sur les cinq répétitions, ils ne constituent pas des intervalles de confiance.

## Contrôles, garde-fous, limites
- Source d'origine et SHA vérifiés : **PASS**.
- Calcul effectif sur la matrice source (via connecteur de lecture et analyse JS) : **PASS exploratoire**.
- Prototype logiciel local : **5/5 tests PASS**, couvrant déterminisme, exclusion des cibles inconnues, abstention et paramètres invalides.
- Nouvelle exécution du futur commit GitHub et CI : **UNVERIFIED** tant qu'aucun test du code distant n'est confirmé.
- Manque non aléatoire dans un fossile réel : **NON modélisé**. L'expérience supprime au hasard des caractères connus; ce mécanisme est plus simple que la fossilisation réelle.
- Deux matrices Holtz et Wang : caractères non harmonisés; le modèle de voisinage est reconstitué dans chaque matrice, **ce n'est pas** un modèle figé appris sur Holtz puis testé sans adaptation sur Wang.
- Aucun apprentissage génome→anatomie, aucun génome de dinosaure éteint et aucune preuve de résurrection.

**Décision :** retenir ce protocole comme test de robustesse morphologique, puis vérifier sur une matrice externe aux caractères homologues harmonisés, et avec des schémas de données manquantes non aléatoires avant toute affirmation de prédiction d'un caractère véritablement inconnu.
