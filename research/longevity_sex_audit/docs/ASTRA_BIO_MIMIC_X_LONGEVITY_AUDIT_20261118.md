# ASTRA Ω / BIO-MIMIC X — Audit exploratoire de longévité réelle (2026-11-18)

## Verdict scientifique : PARTIAL — résultat empirique, pas de rajeunissement démontré

Cette fois la variable observée est la **variation rapportée de durée de vie**, et non la classification du cancer. Dataset réel : DrugAge de Human Ageing Genomic Resources (HAGR), **Build 5 figé** récupéré dans le dépôt tiers `zwbao/longevity-skills` (Git blob `de17d28db4dc1337e627b7404e6fb01da796f113`). La publication du Build 6 (3 441 entrées, 15/11/2026) a été confirmée sur HAGR mais **n'est pas intégrée ici** : il faut éviter toute confusion de version.

### Résultat d'un calcul effectif sur l'intégralité des 3 423 lignes du CSV

- 333 conditions mâle/femelle comparées à **molécule, espèce, souche, dose, âge de début, durée de traitement et PMID identiques** ; 101 identifiants PubMed représentés.
- Différence `Female lifespan-change % - Male lifespan-change %` : **−0,898 point** en moyenne par PMID, toutes espèces ; test de permutation de signe par étude : **p≈0,2714** ; bootstrap par PMID, intervalle descriptif 95 % **[−2,480 ; +0,691]** points. **Contrôle négatif : absence de signal général.**
- Souris : 121 conditions appariées, 35 PMIDs ; différence moyenne par publication **−2,186 points** ; permutation exploratoire **p≈0,0490**, intervalle bootstrap **[−4,285 ; −0,159]**, mais **q=0,196** après correction de Benjamini–Hochberg sur les 4 espèces ayant au moins 5 PMIDs. **Non significatif après ce contrôle de multiplicité.**
- Drosophile : 115 conditions, 43 PMIDs ; **+0,679 point**, p≈0,4246, q≈0,7174.
- Réplications descriptives souris en faveur des mâles : acarbose **−10,889 points** (3 PMIDs : 24245565, 27312235, 30688027), canagliflozine **−14 points** (2 PMIDs : 32990681, 38753230), 17α-estradiol **−15 points** (2 PMIDs : 24245565, 27312235). Ces effets **sont déjà décrits dans les articles scientifiques** : **pas une découverte de mécanisme ou d'intervention inédite**.
- Rapamycine : **6 PMIDs**, directions contradictoires selon le protocole. Le signal n'autorise pas à affirmer une supériorité universelle d'un sexe.

Les valeurs p/intervalle ci-dessus proviennent de l'exécution **JavaScript sur la source GitHub authentifiée**, 20 000 permutations bilatérales et 10 000 bootstrap de PMIDs, graine 20261118. Le script Python fourni utilise la même logique, mais le générateur pseudoaléatoire est différent ; les p-values aléatoires seront proches, **pas bit-à-bit identiques**. L'inférence par PMID est exploratoire et ne remplace pas une méta-analyse à partir des données individuelles avec tailles d'échantillon et variances.

### Hypothèse de recherche utile

Une intervention de longévité peut avoir une **efficacité dépendant du sexe, de la dose et de l'âge d'introduction**, sans généralisation à toutes les espèces. Pour évaluer cette hypothèse de façon neuve et falsifiable : (1) comparer les survies individuelles, (2) mesurer l'exposition pharmacocinétique, (3) valider prospectivement sur des cohortes indépendantes ; (4) disposer de témoins négatifs; (5) appliquer les corrections de multiplicité.

**Aucune expérience animale, thérapie humaine, action clinique ou démonstration de rajeunissement n'a été réalisée.** Pas de preuve quantique, pas de lien causal avec HAND1/HAND2 ou la physique des supersolides.

### Reproduction sans service payant

Dans le dossier `research/longevity_sex_audit/` contenant le CSV figé :

```bash
python -m unittest discover -s tests -p 'test_drugage_sex_study_audit.py' -v
python analysis/drugage_sex_study_audit.py data/drugage_build5_snapshot.csv --output reports/recalculated.json
```

**Test local :** 12/12 tests unitaires sur jeux synthétiques conçus pour contrôler appariement, pertes, faux appariements, pseudoréplication, nullité et correction FDR. **Audit complet en Python : UNVERIFIED en conteneur** parce que la source authentique était accessible par le connecteur GitHub mais pas téléchargeable dans le runtime Python. **Calcul complet en JavaScript : PASS** et résultats archivés dans `reports/DRUGAGE_SEX_AUDIT_20261118.json` (authentification + identifiant de blob). Les résultats JavaScript et Python doivent être rapprochés une fois l'exécution Python sur la source originale réalisée.

### Licence, sources, limites

Données DrugAge : **CC BY 3.0**, attribution HAGR (Barardo D. *et al.*, *Aging Cell* 2017 ; de Magalhães JP *et al.*, *Nucleic Acids Research* 2024). Copie de travail tierce : https://github.com/zwbao/longevity-skills/blob/main/skills/longevitybench/data/drugage.csv . Site primaire : https://hagr.ageing-map.org/drugs/ . Article historique sur les différences mâle/femelle : https://pubmed.ncbi.nlm.nih.gov/24245565/ . Article canagliflozine : https://pubmed.ncbi.nlm.nih.gov/38753230/ . Revue récente sur les limitations : https://pmc.ncbi.nlm.nih.gov/articles/PMC12301548/ .

Le corpus est **sélectionné** par les interventions étudiées et publiées, les lignes ne sont pas toutes indépendantes, les contrôles peuvent varier et les mêmes PMIDs peuvent rassembler plusieurs cohortes. Les comparaisons de pourcentages ne prouvent pas un avantage biologique causal et ne transposent rien chez l'humain.