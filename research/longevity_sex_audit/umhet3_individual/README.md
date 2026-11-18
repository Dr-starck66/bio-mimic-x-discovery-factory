# BIO-MIMIC X | UM-HET3 Site × Sexe × Poids à 6 mois (18/11/2026)

Dossier de réanalyse scientifique **exploratoire**, sans revendication d'effet causal ou clinique.

**Données primaires :** dépôt auteur https://github.com/DannyArends/UM-HET3 ; blob `4b23a79950182df8564af63803b481179f6e8d17`. Le sous-ensemble dérivé de 6 438 souris (fichier individuel CSV) est enregistré sur la PR BIO-MIMIC X #65, branche `astra/longevity-sex-audit-20261118`, chemin `research/longevity_sex_audit/umhet3_individual/data/UMHET3_6438_PHENOTYPES.csv`. Il n'est pas joint à cette archive locale, faute de transfert disponible du connecteur vers le conteneur.

**Pour reproduire l'ensemble :** récupérer le CSV depuis le dépôt GitHub accessible au propriétaire, le placer dans `data/`, puis lancer :

```bash
python -m pip install numpy
python -m unittest discover -s tests -p 'test_umhet3_site_audit.py' -v
python analysis/umhet3_site_audit.py data/UMHET3_6438_PHENOTYPES.csv --bootstrap 1100 --permutations 600 --out reports/python_replay.json
```

Le `report JSON` fourni contient les résultats réellement calculés en JavaScript via récupération authentifiée du blob GitHub. Les tests Python (12/12 PASS) ont été réellement exécutés sur des fixtures synthétiques. Reproduction Python complète 6 438 lignes : **UNVERIFIED**.

Deux erreurs à ne pas commettre : déduire un effet causal de l'ajustement sur le poids à six mois, et oublier que l'hétérogénéité inter-sites et la liaison poids-longévité sont déjà documentées par la littérature (2019 et 2026).