# ASTRA RETINA REGEN Ω — Note de recherche comparative (18 octobre 2026)

**Périmètre :** BIO-MIMIC X · vision/rétine · biomimétisme régénératif. Il s'agit de biologie rétinienne (ophtalmologie), et non d'une méthode validée de correction optométrique.

## Problème scientifique

Pourquoi la rétine adulte du poisson-zèbre reconstitue-t-elle plusieurs populations neuronales après lésion via les cellules gliales de Müller, alors que la capacité de régénération des mammifères reste très limitée ?

**Hypothèse ASTRA R1 (proposée, NON DÉMONTRÉE) :** la restauration d'une diversité neuronale fonctionnelle dépend moins de l'activation isolée d'un « facteur de jeunesse » que de la persistance temporelle d'un état glial compétent, combinant maintien de SOX2, induction contrôlée d'un programme de neurogenèse (notamment ASCL1/STAT3), accessibilité chromatinienne et signaux adaptés au type de lésion. La connectivité restaurée doit être mesurée séparément de l'expression des marqueurs neuronaux.

Cette hypothèse est **une synthèse testable de mécanismes déjà étudiés**, pas une découverte, une thérapie ni une revendication de nouveauté.

## Registre de preuves et contrôles négatifs

| Espèce / système | Observation documentée | Type de preuve | Rôle expérimental |
|---|---|---|---|
| **Danio rerio (poisson-zèbre)** | Glies de Müller capables de produire plusieurs types de neurones rétiniens après lésion. Reconstruction de sous-types et projections rétinotectales rapportée en 2026. | Article de synthèse 2024 + prépublication bioRxiv v2 du 28/07/2026 (non évaluée par les pairs) | **Témoin positif** pour régénération multi-classe |
| **Oryzias latipes (médaka)** | Réponse plus limitée, essentiellement photorécepteurs dans le paradigme étudié ; maintien expérimental de Sox2 élargit la réponse. | Article expérimental eLife 2018 | **Contrôle négatif majeur** : autre poisson téléostéen mais régénération restreinte |
| **Mus musculus (souris)** | Régénération spontanée nettement inférieure ; des manipulations peuvent stimuler certains programmes gliaux. | Revue comparative 2024 | **Contrôle de transfert** mammifère, ne pas confondre neurogenèse partielle et récupération de vision |
| **Homo sapiens (humain)** | Aucune restauration spontanée comparable de la rétine adulte n'est établie. | État des connaissances (revues 2024–2026) | **Cible translationnelle** seulement ; aucune revendication clinique |

### Sources vérifiables
- Jui & Goldman, *Annual Review of Genetics* (2024), revue poisson-zèbre/souris : https://doi.org/10.1146/annurev-genet-111523-102000
- Lust et al., *eLife* (2018), poisson-zèbre/médaka et rôle de Sox2 : https://elifesciences.org/articles/32319
- Nagashima et al., *bioRxiv* v2 (28 juillet 2026), régénération de diversité/circuits chez le poisson-zèbre : https://www.biorxiv.org/content/10.64898/2026.03.15.711785v2 — **prépublication non évaluée**
- *Annual Review of Vision Science*, mécanismes SOX2/ASCL1/STAT3, Notch et signalisation inflammatoire : https://doi.org/10.1146/annurev-vision-121219-081808
- Revue générale (2026), mécanismes et obstacles translationnels : https://pubmed.ncbi.nlm.nih.gov/42608764/

## Protocole computationnel préenregistré (non exécuté sur données biologiques à ce stade)

1. **Obtenir des données authentiques** et attribuer un identifiant immuable par étude, espèce, cellule, temps post-lésion et type de lésion. Exclure les données sans annotation de ce qui a effectivement régénéré.
2. Quantifier séparément : (a) maintien temporel de SOX2 ; (b) activation ASCL1/STAT3 ; (c) accessibilité/état chromatinien quand mesuré ; (d) diversité neuronale reconstituée ; (e) preuves de connectivité et/ou fonction visuelle.
3. Comparer deux modèles sur études tenues hors apprentissage : **M0** programme neurogénique seul (ASCL1/STAT3) ; **M1** M0 + maintien SOX2 + signaux contextuels + dynamique temporelle. Vérifier si M1 prédit mieux **des résultats fonctionnels mesurés** et pas simplement l'expression de marqueurs.
4. **Contrôles défavorables conservés** : médaka sans sauvetage Sox2 ; données souris sans restauration démontrée ; étiquettes d'espèce mélangées ; perturbation temporelle des profils ; analyses séparées par type de lésion.
5. **Critère d'échec** : pas de données comparables interespèces, aucune amélioration hors-échantillon, ou amélioration limitée à des marqueurs cellulaires sans diversité/connectivité. Dans ces cas, statut FAIL/UNVERIFIED et abandon de l'allégation.
6. Aucun calcul sur données patients ni intervention biomédicale ne sont autorisés par cette note.

## Audit ASTRA Ω
- **PASS** — dossier de recherche créé et références scientifiques identifiées.
- **UNVERIFIED** — récupération et harmonisation des jeux de données moléculaires annotés par lésion/temps/espèce.
- **UNVERIFIED** — hypothèse R1, prédiction supérieure au modèle nul, régénération fonctionnelle chez mammifère/humain.
- **Aucune propriété industrielle, traitement, médicament ou résultat clinique revendiqué.**

**Prochaine étape de recherche scientifique définie :** identification et acquisition de données single-cell cross-species avec données de régénération mesurées ; ne pas remplacer ce verrou par une simulation présentée comme découverte.
