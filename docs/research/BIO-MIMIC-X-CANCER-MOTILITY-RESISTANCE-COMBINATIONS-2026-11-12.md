# BIO-MIMIC X Ω — Audit scientifique : migration, échappement métabolique, combinaisons
Date d'arrêt : 2026-11-12. Domaine : recherche préclinique en oncologie. État global : **PARTIAL** (bibliographie primaire vérifiée ; aucune réplication indépendante de BIO-MIMIC X réalisée).

## Questions et portée
Q1. Quelles voies alimentent la migration/invasion tumorale, *indépendamment de la prolifération* ?
Q2. Quels échappements mécaniques ou métaboliques subsistent après blocage d'une voie ?
Q3. Quelles associations disposent d'une démonstration de complémentarité, de synergie, ou d'un signal clinique, et lesquelles restent hypothétiques ?

**Exclusion** : ne pas convertir des résultats sur lignée ou souris en promesse de traitement humain ; ne pas confondre migration, extravasation, métastase, survie sans progression et survie globale.

## Axe 1 — Migration tumorale

| Référence primaire | Matrice / modèle | Résultat rapporté | Contrôle défavorable ou réserve | Statut |
|---|---|---|---|---|
| Tagay et al. 2023, *Advanced Science*, DOI 10.1002/advs.202302229, PMID 37726225 | Cellules de cancer du sein, fibres biomimétiques 2D et hydrogels granulaires confinants 3D | Force produite par la dynéine et microtubules ; en 2D dynéine et actomyosine peuvent se compenser, en 3D confinée les deux moteurs sont nécessaires dans le modèle | Ne prouve pas une inhibition des métastases humaines ; données quantitatives à demander à l'auteur | **PASS** pour attribution bibliographique ; **UNVERIFIED** pour réplication indépendante |
| Kiweler et al. 2022, *Nature Communications*, DOI 10.1038/s41467-022-30363-y, PMID 35577770 | MDA-MB-468, 4T1, souris BALB/c (n=9/groupes de métastases macroscopiques fig. 7) | MTX : inhibition de prolifération sans inhibition corrélative de motilité ; dépendance à PHGDH/sérine et au catabolisme mitochondrial 1C ; Mthfd1l KD : diminution des métastases pulmonaires sans changement de masse de tumeur primaire | Contre-exemple essentiel : MTX seul ne bloque pas cette migration ; ALDH1L2 peut compenser partiellement une perturbation MTHFD1L ; contexte expérimental limité | **PASS** pour publication et disponibilité de données sources ; re-analyse **UNVERIFIED** |
| Liu et al. 2026, *Cell Research*, DOI 10.1038/s41422-026-01254-4, PMID 42151565 | Cancer colorectal, criblage CRISPR de 1685 enzymes métaboliques, modèles précliniques et corrélations humaines | Compression → hnRNPA0/stabilité ARNm DLD → métabolisme TCA/malate → liaison TUBA1B/microtubules → migration confinée ; perturbations DLD ou interaction malate-TUBA1B réduisent dissémination dans les modèles | Corrélation clinique ne prouve pas efficacité thérapeutique humaine ; toxicité des cibles et diversité tumorale non résolues | **PASS** pour publication ; transfert de mécanisme **UNVERIFIED** |

### Hypothèses falsifiables
- H1a : inhiber dynéine seule laisse migrer des cellules en 2D via l'actomyosine ; le contexte 3D modifie la dépendance aux moteurs. Mesures : déplacements single-cell, vitesse, persistance, invasion 3D, morphologie et viabilité.
- H1b : inhibition de SHMT2/MTHFD2/MTHFD1L/PHGDH modifie la migration après contrôle de prolifération, avec évaluation d'un échappement par ALDH1L2. Mesures : migration, 13C-sérine/formate, ATP, ROS, viabilité et prolifération séparées.
- H1c : DLD et malate–TUBA1B contribuent spécifiquement à la migration en confinement ; reproduire effet en géométries 2D/3D et dans un autre type tumoral sans extrapoler.

## Axe 2 — Résistance et plasticité

1. **Compensation biomécanique** : dynein/actomyosine selon géométrie (Tagay 2023). Contrôle négatif : chacune des perturbations séparées ; combinaison et restauration génétique (« rescue ») requises.
2. **Autarcie mitochondriale** : sous méthotrexate, le compartiment cytosolique 1C peut être bloqué tandis que le compartiment mitochondrial continue d'alimenter la motilité (Kiweler 2022). Contrôle négatif : MTX seul pour la migration, et séparation des effets létaux/cytostatiques.
3. **Reprogrammation glycolytique/lactate** : Matvere et al. 2026, *Molecular Cancer*, DOI 10.1186/s12943-026-02757-9, PMID 42983524 : écrans CRISPR identifient MCT1 comme échappement à l'inhibition SMAD3 ; blocage conjoint MCT1/SMAD3, synergie rapportée sur viabilité du mélanome BRAF muté ; mécanisme différent de la migration par dynéine. **Ne pas prétendre que MCT1 sauve une inhibition de dynéine**.
4. **EMT et résistance** : Roth et al. 2026, *Nature*, DOI 10.1038/s41586-026-10436-4, PMID 42020751 : inhibition nétrine-1/NP137 avec mFOLFIRINOX dans cancer pancréatique localement avancé ; signal transcriptomique EMT et clinique, mais essai de phase 1b sans randomisation permettant d'attribuer l'efficacité au seul NP137.
5. **Contrôle défavorable** : étude 2025 sur doxorubicine à exposition subcytotoxique : la migration/invasion augmente via ROS mitochondriaux dans certains modèles, *sans augmentation de métastases observée chez des souris immunocompétentes* ; ne jamais transformer un effet de migration in vitro en effet métastatique in vivo (PMID 40703453).

### Signaux de résistance à mesurer, sans prédire leur présence
- Glycolyse/lactate (SLC16A1/MCT1), OXPHOS, sérine/formate, redox (ROS, NRF2), phénotype EMT, expression DYNC1H1/MYH9 et changement de mode de migration.
- Viabilité et prolifération obligatoirement mesurées en parallèle, notamment pour exclure un artefact de perte de cellules.
- Contrôles : véhicules ; cibles génétiques indépendantes ; « rescue » ; lignées non tumorales ; 2D versus 3D ; matrice et contraintes mécaniques documentées ; absence de traitement ; fenêtre temporelle fixée avant analyse.

## Axe 3 — Associations thérapeutiques : classement strict

| Proposition | Fondement disponible | Ce qui n'est PAS prouvé | Qualification |
|---|---|---|---|
| Blocage dynéine + actomyosine | Complémentarité biomécanique en modèles 2D/3D (Tagay 2023) | Synergie pharmacologique sécurisée, spécificité tumorale, efficacité in vivo ou clinique | **HYPOTHÈSE — UNVERIFIED** |
| Blocage métabolisme mitochondrial 1C + traitement antiprolifératif | Motilité persistante sous MTX ; effet métastatique de Mthfd1l KD chez la souris (Kiweler 2022) | Bénéfice et tolérance de la combinaison chez l'humain ; généralisation au-delà des modèles | **HYPOTHÈSE — PARTIAL** (mécanismes précliniques) |
| MCT1 + SMAD3 | Synergie préclinique rapportée sur viabilité et cellules tolérantes (Matvere 2026) | Réduction clinique des métastases, transfert à un modèle dynéine/1C | **PARTIAL** (modèle spécifique) |
| Anti-nétrine-1 NP137 + mFOLFIRINOX | Étude phase 1b sur 43 patients, mécanisme EMT et signaux d'activité (Roth 2026) | Attribution causale d'efficacité à NP137 sans essai comparatif randomisé | **PARTIAL** (signal clinique exploratoire) |
| DLD/malate-TUBA1B + chimiothérapie ou anti-migration | Axe mécanistique nouveau (Liu 2026) | Combinaison testée et bénéfice clinique | **UNVERIFIED** |

### Plan de qualification expérimental (non réalisé par BIO-MIMIC X)
1. Sélectionner un seul contexte : modèle de cancer du sein avec référence 2022/2023, puis validation indépendante dans un second modèle. Les données des cohortes NMIBC de la PR #45 portent sur une autre question : **ne pas les réutiliser comme démonstration de migration**.
2. Pré-enregistrer l'endpoint primaire : migration/invasion normalisée par le nombre de cellules vivantes, sous deux géométries 2D/3D ; résultats de métastases in vivo distincts et explicitement non disponibles ici.
3. Plan factoriel à quatre bras (contrôle, cible A, cible B, combinaison) ; doses et temps définis avec spécialiste ; toutes mesures de cytotoxicité et prolifération synchrones.
4. Ne conclure à « synergie » qu'après calcul explicite sur les mesures réelles, modèle additif préspécifié (p. ex. Bliss pour lecture appropriée), incertitude et correction de comparaisons multiples ; un ralentissement de migration par perte de viabilité n'est **pas** une preuve d'anti-migration spécifique.
5. Deux guides CRISPR indépendants par cible ou perturbations orthogonales ; rescue quand possible ; lignées non tumorales ; contrôle de lot, géométrie et image-analysis aveugle ; réplication biologique indépendante.
6. Échecs publiables : compensation, résistance, aucune efficacité, diminution de migration sans effet de métastase, toxicité élevée, absence de données.

### Acquisition de données et reproductibilité
- Kiweler 2022 : fichier **Source Data** joint à PMC9110368, données de protéomique PRIDE **PXD027175**, métabolomique partiellement dans les suppléments. L'article indique les effectifs de Fig.7 : n=9 par groupe pour comptage des métastases, pas d'accès à la matrice brute contrôlé dans cette exécution.
- Tagay 2023 : supplément vidéo et PDF publics (PMC10625109), mais la déclaration de disponibilité précise « from corresponding author upon reasonable request » pour les données sous-jacentes. Pas d'invention de trajectoires.
- Liu 2026, Matvere 2026, Roth 2026 : métadonnées/résumés consultés ; matrices originales non téléchargées ni recalculées.
- Aucun calcul de p-value, taille d'effet, score de synergie, SHA-256 d'un jeu scientifique ou réplication indépendante n'est revendiqué.
- Aucune nouvelle analyse de tissus, culture cellulaire, traitement de patients, expérimentation animale ou validation clinique.

### Registre de discordances
- **D-01** : croissance tumorale ≠ motilité ; MTX peut arrêter la prolifération sans arrêter la migration.
- **D-02** : migration en 2D ≠ invasion confinée 3D ≠ métastase animal ≠ survie patient.
- **D-03** : compensation dynéine/actomyosine dépend du contexte ; généralisation inter-tumorale non établie.
- **D-04** : association NP137 + mFOLFIRINOX sans bras randomisé ne démontre pas le gain attribuable à NP137.
- **D-05** : exposition subcytotoxique à la doxorubicine augmente certains marqueurs migratoires sans augmenter les métastases chez souris immunocompétentes dans le modèle rapporté.
- **D-06** : lien journalistique share.google fourni initialement non résolu en URL source directe ; identité exacte de cet article **UNVERIFIED**. Aucune étude n'est présentée comme sa source certaine.

### Sources primaires vérifiables
- Tagay et al. 2023 : https://doi.org/10.1002/advs.202302229 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC10625109/
- Kiweler et al. 2022 : https://doi.org/10.1038/s41467-022-30363-y ; https://pmc.ncbi.nlm.nih.gov/articles/PMC9110368/
- Liu et al. 2026 : https://doi.org/10.1038/s41422-026-01254-4 ; https://pubmed.ncbi.nlm.nih.gov/42151565/
- Matvere et al. 2026 : https://doi.org/10.1186/s12943-026-02757-9 ; https://pubmed.ncbi.nlm.nih.gov/42983524/
- Roth et al. 2026 : https://doi.org/10.1038/s41586-026-10436-4 ; https://pubmed.ncbi.nlm.nih.gov/42020751/
- Mitochondrial ROS inhibition prevents doxorubicin-induced breast cancer cell migration and invasion (2025), PMID 40703453 : https://pubmed.ncbi.nlm.nih.gov/40703453/

**Statuts MYTHOS** : recherche bibliographique **PASS** (sources identifiées et consultées) ; synthèse mécanistique **PARTIAL** ; accès à matrices/trajectoires **PARTIAL** ; reproduction quantitative **UNVERIFIED** ; validation BIO-MIMIC X **UNVERIFIED** ; application thérapeutique humaine **UNVERIFIED**.
