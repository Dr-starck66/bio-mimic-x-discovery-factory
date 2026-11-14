# ASTRA DINO Ω — Rubin 2022 Data S2 × VCF Oslo 2025

**Date : 14 novembre 2026. Coût supplémentaire : 0 €.** Résultat d’intersection **PASS (réel)** ; prédiction/causalité **UNVERIFIED**. Aucun individu ni génotype individuel publié.

## 1. PDF officiel : téléchargement et SHA-256 vérifiés

- Source ouverte hébergée par PMC Open Access : https://pmc-oa-opendata.s3.amazonaws.com/PMC9269886.1/sciadv.abm5982_sm.pdf
- Fichier : `sciadv.abm5982_sm.pdf`, **7 409 153 octets**, signature `%PDF-`, **30 pages** lues et identifiées ; statut HTTP 200 depuis un Sandbox Vercel gratuit déjà actif.
- **SHA-256 mesuré sur les octets** : `5fabf42bbd0ab7df31e067ec36a1c4db60937c81ed0524b0cd64c638767aa8dc`.
- PDF temporairement enregistré dans le sandbox ; la vérification de ce SHA par relecture d’une copie persistante dans ChatGPT Library **n’a pas été réalisée**. Le SHA atteste l’identité binaire du fichier téléchargé sur ce sandbox, pas à lui seul la certification éditoriale.
- Le PDF, page 4, indique explicitement que « Data S2 » liste les 28 régions et renvoie vers `https://doi.org/10.5061/dryad.p2ngf1vsk`. Ce DOI répond **404** à ce contrôle et l’API Dryad renvoie zéro version publique pour l’identifiant 86266.

## 2. Contournement autorisé : archives publiques des auteurs elles-mêmes

- Répertoire public des auteurs : https://github.com/erikenbody/Darwins_finch_comparative_genomics
- Original de coordonnées : https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/XX_twisst_topology_weighting/28Loci_start_stop.txt
- Git blob original `dc6ec1da23aa6426fcc16dc5b5d1124d55699616`; SHA-256 du fichier texte local `9702730b625dc8a93eafe01025dda2ebacb0d2c34d34e418c5940df44ff28770`. Le vérificateur recrée le Git blob SHA sur les octets exacts avant de lire les 28 lignes.
- Tableau original de **Data S2** : https://github.com/erikenbody/Darwins_finch_comparative_genomics/blob/master/supplementary_data_for_github/Supplementary_data_2_all_peaks_median_diversity_stat.csv
- Git blob original du CSV `383cebcfa21ec5bc898ddd5e3c2c2ab0560f2b21`. Via l’accès GitHub connecté, **84 lignes (3 contrastes × 28 régions) ont été retrouvées et leurs 28 quadruplets (locus, chromosome, début, fin) correspondent exactement à ceux du fichier de coordonnées**. Cette contre-vérification croisée est une preuve documentaire, pas le recalcul de chaque statistique de diversité du CSV.
- Attention à la numérotation : la table du dépôt auteur emploie les **locus 3 et 7**, tandis que la figure de l’article utilise un autre classement. Les correspondances ont été déterminées par les **coordonnées géniques et le contenu du tableau auteur**, jamais par supposition à partir du numéro de figure.

## 3. Intersection réelle avec 64 génotypes, dont 50 oiseaux avec morphologie appariée

- Les trois originaux Oslo (VCF, morphométrie, PCA) ont été contrôlés **3/3 SHA-256**, avant exécution. VCF total : **261 754 variantes**, chromosome 1A : **21 809 variantes**.
- Assemblage `Camarhynchus_parvulus_V1.1` / **GCA_902806625.1**. Origine: Dryad 2025 `10.5061/dryad.3ffbg79w8`, version privée déjà archivée et appariée par règle auteur.
- Échantillons 50/50 appariés, 14 autres exclus des statistiques individuelles ; aucun appariement inventé.
- Filtres pour les SNP : **bialléliques**, **MAF ≥ 5 %**, **taux de génotypes appelés ≥ 80 %** parmi les 50. Aucune valeur de phénotype n’est utilisée pour choisir les variants.

| Source des auteurs | Intervalles exacts (bornes originales) | Variants VCF | SNP retenus |
|---|---|---:|---:|
| **Bloc HMGA2 — région auteur 3** | `chr1A:32 232 902–34 354 642` | **706** | **394** |
| **Bloc ALX1 — région auteur 7** | `chr1A:40 692 203–42 199 937` | **410** | **238** |
| **Toutes les 28 régions** | Chromosomes `1`, `1A`, `2`, `3`, `5`, `7`, `9`, `25` | **6928** | **3570** |

Les deux régions géniques sont entièrement incluses dans leur bloc source respectif ; les anciens compteurs **36 variants HMGA2** et **9 variants ALX1** dans les seuls corps des gènes sont reproduits. **Les variants de toute la région ne sont pas tous des haplotypes reconstruits ou des variants causaux.**

## 4. Contrôles négatifs, conventions et reproductibilité

- Tests unitaires : **19/19 PASS** (11 sur le scanner préexistant + 8 pour l’intégration source auteur). Mutation d’un seul octet du fichier des coordonnées → rejet `AUTHOR_INTERVAL_SOURCE_GIT_BLOB_MISMATCH`.
- Second scanner **indépendant** : tri des positions réelles et recherche `bisect_left/bisect_right` → **28/28 correspondances de comptage**.
- La colonne `size` du CSV auteur correspond à **fin − début**, d’où une ambiguïté potentielle entre les conventions **1-based inclusive** et **0-based half-open** : chaque région a été contrôlée pour les variants précisément sur la borne de début. **3 variants de bord dans l’ensemble**, sur les régions auteur 9 et 18 ; aucun sur les deux régions d’intérêt HMGA2 et ALX1. Les comptages de ces deux blocs sont donc invariants sous ces deux interprétations.
- Contrôle défavorable antérieur, non modifié : le modèle initial à deux gènes reste à **p globale corrigée = 0,0847** pour la taille (huit tests), et les fenêtres adjacentes montraient de plus forts signaux exploratoires. **Aucune nouvelle p-value ni validation indépendante** n’a été fabriquée à partir de ces comptages.
- Le scanner d’intersection actuel ne constitue **pas** une reconstruction d’haplotypes phasés ; l’authenticité des bornes et leur présence dans les VCF ne prouvent pas une fonction génétique causalement déterminée.

## 5. Reproduction

```bash
python -m unittest discover -s tests -p 'test_astra_dino*.py' -v
python validation/astra_dino_data_s2_author_intersect.py \
  --oslo-dir /CHEMIN/PRIVÉ/OSLO-2025-ORIGINALS \
  --loci-tsv data/Rubin2022_28Loci_start_stop_author_original.txt \
  --output reports/astra_dino_author_data_s2_oslo_vcf_20261114.json
```

La reprise du **VCF original privé** exige seulement son accès autorisé déjà disponible. Le dossier public ne contient **aucun** génome, identifiant individuel ou liaison privée ; il contient le code, les contrôles agrégés et les attestations d’origine.

## 6. Prochaine investigation scientifique

Comparer **les profils de génotypes sur l’ensemble des blocs officiels** avec la morphologie des 50 oiseaux (permutations intra-populations, contrôles négatifs et validation sur cohorte non chevauchante), en **préenregistrant** les fenêtres et les métriques avant tout test prédictif. L’association ou la causalité d’une variante particulière reste **UNVERIFIED**.