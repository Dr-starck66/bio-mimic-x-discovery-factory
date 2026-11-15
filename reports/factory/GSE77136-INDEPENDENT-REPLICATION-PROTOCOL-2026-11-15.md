# BIO-MIMIC X Ω — Pré-enregistrement de réplication indépendante GSE77136
**Date :** 15 novembre 2026 — **Coût :** 0 € — **Statut :** PARTIAL (appariement des métadonnées, pas de modèle sur matrices numériques).

## Cohorte retenue et provenance

- [GSE77136](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE77136), Ivanov et al., *PLOS Genetics* (2016), DOI: [10.1371/journal.pgen.1005819](https://doi.org/10.1371/journal.pgen.1005819), source publique, publication CC BY avec attribution.
- [GSE77131](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE77131) : transcriptome RNA-seq, 22 GSM listés, fichier public `GSE77131_geneCounts.csv.gz` (~627 kB). Le rapport des auteurs précise qu'un `2533.Dura` n'a pas passé le contrôle qualité et est absent des données traitées.
- [GSE77135](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE77135) : methylation Illumina 450k, 21 GSM, `GSE77135_signal_intensities.csv.gz` (~52,5 MB) et tables de fractions methylées normalisées au niveau GSM. Le nom « signal intensities » **ne prouve pas** que ses colonnes sont directement des valeurs bêta.
- Rapport d'appariement : [GSE77136-INDEPENDENT-MULTIOMICS-CROSSWALK-2026-11-15.json](GSE77136-INDEPENDENT-MULTIOMICS-CROSSWALK-2026-11-15.json).

## Sous-cohorte effectivement utilisable

Les titres GEO permettent 21 couples ARN/DNAm appariés par **même donneur + même tissu** (scalp/dura), provenant de 11 donneurs distincts : 10 donneurs ont leurs deux tissus représentés dans les deux modalités ; le donneur 2533 ne dispose que de `Scalp`. Son échantillon `2533.Dura` est exclu avant tout calcul. **Ne pas remplacer cette exclusion par imputation** ni considérer des échantillons de même donneur comme « même aliquot physique ».

Le gate métadonnées s'est exécuté en JS sur les deux listes d'accessions GEO publiées : **15/15 PASS**, y compris trois contrôles négatifs (donneur/tissu altéré, doublon GSM, faux appariement par position dans les listes). La matrice réelle de valeurs RNA et les bêta DNAm ne sont **pas** téléchargées dans ce tour, donc aucune statistique de vieillissement n'est annoncée.

## Hypothèse verrouillée pour l'analyse numérique future

**Hypothèse principale :** sur ce jeu indépendant, une association ADN-méthylation / âge résiste-t-elle à l'ajustement pour le tissu d'origine et un score de lignée fibroblastique mesuré par RNA-seq ?

**Méthode à appliquer aux véritables matrices après vérification SHA-256 et formats** :

1. Vérifier noms et cardinalité de colonnes par clé `<donor>.<tissue>`. Reporter en premier le nombre réel de colonnes conservées, le nombre de CpG et de gènes, les exclusions, et le taux de valeurs manquantes. Aucune jointure par l'ordre des colonnes.
2. Lire les données ARN réellement exprimées ; mapper les identifiants connus `UCSC knownGene/hg19` vers les symboles modernes à partir d'une annotation de provenance vérifiée. **Ne pas forcer** une interprétation des ID du fichier `geneCounts.csv.gz` comme des symboles de gènes.
3. Lire des **bêta DNAm 0–1 réellement normalisés** (ou dériver selon le pipeline minfi traçable à partir d'intensités M/U), rejeter les colonnes d'intensité en tant que bêta tant que leur signification n'est pas vérifiée.
4. Prédéfinir les marqueurs RNA fibroblastiques `COL1A1, COL1A2, DCN, LUM, FN1, THY1`, sans sélection optimiste après observation de l'âge. Si un marqueur est absent ou ambigu, le signaler.
5. Ajuster descriptivement `DNA methylation endpoint ~ age_years + tissue + RNA marker score`, comparé au modèle sans score RNA. Analyser aussi les **10 différences scalp–dura intra-donneur** : l'âge ne change pas au sein d'un donneur et **ne peut pas être identifié dans un modèle avec effets fixes de donneur**. Séparer strictement ces estimands.
6. Contrôles négatifs préspécifiés : permutations des âges **par donneur entier**, permutations des étiquettes tissus **à l'intérieur de chaque paire**, effet des principaux marqueurs ARN non discriminants et exclusion d'un donneur entier (leave-one-donor-out). Aucun entraînement/test avec les deux tissus d'un même donneur répartis entre deux plis.
7. Publier les résultats favorables **et défavorables** : coefficients signés, taille d'effet, nombre de donneurs, marges d'incertitude descriptives si calculables, résultats LODO, empreintes de toutes les entrées et paramètres. Avec **11 donneurs**, ne pas promettre une inférence causale ou une généralisation clinique.

## Preuves et limites en date de ce rapport

- **PASS :** référencement GEO/publication; appariement identifiant par donneur/tissu; 15 contrôles structurels dont mutations négatives; trace GitHub versionnée.
- **PARTIAL :** préparation d'une réplication multi-omique indépendante GSE179849 → GSE77136.
- **UNVERIFIED :** récupération des octets numériques officiels, SHA-256 des matrices, coefficients comparés entre ARN et DNAm, robustesse statistique, causalité ou rajeunissement.
- **Obstacle concret :** téléchargement binaire GEO indisponible depuis les outils réseau disponibles dans cette exécution. Aucune donnée fictive n'est substituée; aucune commande Windows demandée au titulaire.
- **Prochaine action technique prioritaire :** récupérer directement depuis une infrastructure cloud gratuite déjà autorisée les **deux matrices GEO vérifiables**, puis appliquer le protocole bloqué ci-dessus et attacher les journaux et SHA au même rapport.

La présence d'une donnée publique ne constitue pas en soi une autorisation de traiter de données de santé identifiantes. Ici seules des données d'études publiques pseudonymisées et des agrégats scientifiques sont visés; aucune donnée dbGaP contrôlée n'est sollicitée ou contournée.
