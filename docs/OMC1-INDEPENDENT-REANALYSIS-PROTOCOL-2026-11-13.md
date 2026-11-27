# BIO-MIMIC X Ω — OMC1/REC8 : protocole de réanalyse indépendante v0.1

Date : 13 novembre 2026. Statut : PARTIAL — analyseur et tests locaux opérationnels ; pas de données individuelles réellement analysées.

## Étude et sources identifiées

Iisaka S. et al., *Oocyte-specific OMC1 is required for maintaining chromosome cohesion through reproductive life*, Nature Aging (29 octobre 2026), DOI : https://doi.org/10.1038/s43587-026-01245-5

Les auteurs déclarent :
- Données des figures : liens « Source data » de la publication (fichiers non encore récupérés).
- Images originales : https://doi.org/10.6084/m9.figshare.32586201 (fichiers non récupérés).
- PIC–RNA-seq ovarien : GSE333390, NCBI GEO.
- scRNA-seq spermatocytes : DRR703875, DDBJ.
- scRNA-seq ovocytes : DRA013182 (E14.5), DRA015395 (E15.5/E18.5).
- Séquence murine Omc1 : LC858587, GenBank.
- Lignée KO : CARD 3587, non obtenue.

**Ne jamais inventer des lignes individuelles à partir de statistiques de groupe ou de graphiques.** Les identifiants d'accession et le texte scientifique sont vérifiés, mais le téléchargement des fichiers expérimentaux n'est pas établi.

## Question primaire préenregistrée

Chez la souris de 8 semaines, l'absence d'Omc1 augmente-t-elle la proportion d'ovocytes à séparation prématurée des chromatides sœurs (PSSC) à la métaphase II ?

- Groupes : WT et KO Omc1. Endpoint binaire PSSC par ovocyte.
- Unité indépendante : souris donneuse, avec origine biologique de chaque ovocyte et identifiant d'expérience.
- Effet principal : moyenne des taux PSSC par animal KO moins WT.
- Test : permutation bilatérale exacte des étiquettes KO/WT **à l'intérieur de chaque expérience**, en conservant les effectifs par groupe.
- Intervalle descriptif : bootstrap par animal, graine fixe. Analyse exploratoire, non essai clinique.
- Refus du calcul en l'absence d'identifiant d'animal, si chaque expérience ne comprend pas les deux groupes, ou s'il y a moins de 2 animaux par groupe.
- Contrôle préalable : animaux distincts, métadonnées d'âge et de génotype fiables, documentation des protocoles d'imagerie, annotations vérifiées, exclusions préenregistrées.

Schéma d'entrée CSV : oocyte_id, animal_id, experiment_id, age_weeks, genotype, pssc.
Les colonnes manquantes et les données mal formées bloquent l'analyse. L'outil n'invente et n'impute aucune observation.

## Axes secondaires, à implémenter uniquement après accès aux données

1. REC8 chromosomique à la métaphase I (Figs 5 et 7) ; distinguer la fraction chromosomique et les niveaux totaux.
2. Distance entre kinétochores (Fig. 7) ; hiérarchie paires → ovocytes → animaux → expériences.
3. Rescue par ARNm Omc1 : dose, entrée en anaphase I, récupération partielle et absence de restauration complète.
4. Mutant stop-gain R151 de souris, correspondant à R162 humain (Fig. 8) ; aucune démonstration thérapeutique chez l'humain.
5. Expression de Ccdc201 selon le stade ovarien, contrôle de l'effet batch et de l'annotation sur GEO/DRA.

## Contrôles négatifs et résultats défavorables

- Progression Meta I / Ana I sans retard significatif dans le KO de 8 semaines : conserver ce résultat.
- Absence d'altération majeure de SYCP1/SYCP3 dans certaines conditions ; altération modeste de SYCE3.
- Artefacts possibles de segmentation des kinétochores et différence REC8 chromosomique vs REC8 total.
- L'excès d'OMC1 peut perturber la progression méiotique ; rescue incomplet.
- Conserver effets nuls, analyses de sensibilité, limites, données manquantes et p-values défavorables.

## Procédure reproductible

1. Acquérir légalement les fichiers « Source data » et la table ovocyte → animal → expérience.
2. Consigner URL, horodatage, licence, SHA-256 et correspondance des colonnes.
3. Rejeter tout tableau qui ne permet pas de retrouver l'animal ; aucun test au niveau ovocyte ne doit se substituer au niveau animal.
4. Exécuter omc1_pssc_analysis.py sur un CSV réel validé et produire un JSON avec SHA-256, effectifs, effet, p exact, IC et avertissements.
5. Vérifier les résultats par lecture indépendante et archiver aussi les résultats négatifs.

Les 9 tests logiciels v0.1 exécutés localement (PASS 9/9) vérifient les calculs et les blocages sur **des données synthétiques uniquement**. Ils ne prouvent pas une réplication biologique. Les fichiers Python et le journal des tests sont fournis comme livrable séparé ; leur dépôt dans cette branche sera audité distinctement.

## Cadre scientifique

Ré-analyse numérique indépendante ≠ reproduction expérimentale indépendante. L'étude porte sur des modèles animaux ; aucune efficacité clinique chez l'humain ni rajeunissement général ne peut en être inféré. Une demande de brevet japonais 2026-192022 a été déclarée. Requérir les autorisations adéquates avant réutilisation des réactifs/données restreintes.

Contacts : emails envoyés le 13 novembre 2026 à Kei-ichiro Ishiguro, Tomoya S. Kitajima et Marie-Hélène Verlhac. Vérification de la boîte principale le même jour : aucune réponse reçue. Les données disponibles via une réponse future devront être soumises aux mêmes contrôles de provenance.

**Blocage à lever :** obtenir les mesures et les métadonnées animal/expérience avant toute conclusion statistique sur les résultats publiés.
