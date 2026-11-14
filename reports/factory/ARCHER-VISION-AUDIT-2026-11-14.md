# ASTRA ARCHER VISION Ω — audit expérimental v0.1

**Date :** 2026-11-14  
**Statut :** PARTIAL — tests logiciels locaux PASS, validité biologique et données réelles UNVERIFIED.

## Fondement scientifique

Newport et al. (2016), Scientific Reports, doi: https://doi.org/10.1038/srep27523. L'étude originale utilisait un choix forcé entre **deux images simultanément**, en présentant 44 nouveaux visages au fil des essais. Elle ne consistait **pas** à choisir une image parmi 45 portraits affichés simultanément. Le test ci-dessous comporte donc deux tâches à 2 choix (dont « éviter un visage appris », proche de l'épreuve originale) et un stress-test séparé à 45 choix. Aucun score n'est comparé directement aux performances des poissons.

## Protocole vérifié

- Générateur **100 % synthétique** de portraits 64×64 en niveaux de gris : aucune image biométrique réelle.
- **Trois graines** : 20261114, 20261115 et 20261116. Pour chaque graine, 46 identités ; deux identités familières (0 et 1), puis 44 autres identités jamais apprises (2–45).
- 6 vues par identité familière à l'entraînement. Épisodes de test 1000–1023, distincts des vues d'entraînement 0–5.
- 24 épisodes par graine et par condition, donc 72 épisodes/condition et 72 × 44 = 3168 paires/condition. Les 3168 paires **ne sont pas indépendantes**.
- Deux conditions : **matched** (bruit/décalage léger) et **shifted** (rotation, éclairage, décalage, bruit supplémentaires).
- Comparateurs : pixel lissé (256 dimensions), HOG classique (576), **Retina-Pool** (320 : contraste centre-périphérie, gradients orientés, pooling spatial).
- Score : similarité cosinus à un prototype. Le moteur ne prétend pas reproduire l'anatomie neuronale du poisson.

## Résultats locaux cumulés

| Modèle | Condition | Éviter visage appris (2AFC ; hasard 50 %) | Choisir visage appris (2AFC ; hasard 50 %) | Top-1 45 choix (hasard 2,22 %) |
|---|---|---:|---:|---:|
| Pixels | matched | 3066/3168 (96,8 %) | 3112/3168 (98,2 %) | 45/72 (62,5 %) |
| HOG | matched | 3124/3168 (98,6 %) | 3129/3168 (98,8 %) | 51/72 (70,8 %) |
| **Retina-Pool** | matched | **3162/3168 (99,8 %)** | **3146/3168 (99,3 %)** | **57/72 (79,2 %)** |
| Pixels | shifted | 1754/3168 (55,4 %) | 1982/3168 (62,6 %) | 8/72 (11,1 %) |
| HOG | shifted | 1911/3168 (60,3 %) | **2141/3168 (67,6 %)** | 12/72 (16,7 %) |
| **Retina-Pool** | shifted | **2194/3168 (69,3 %)** | 2036/3168 (64,3 %) | **14/72 (19,4 %)** |

**Contrôle négatif :** quand les 46 personnes synthétiques sont générées avec les mêmes traits morphologiques (graine 20261114, 24 épisodes), la précision en 45 choix retombe à 0 ou 1 sur 24 selon le modèle ; les résultats 2AFC sont proches de 50 % (environ 46,7 à 54,1 %).

**Résultat défavorable conservé :** avec changement de domaine, HOG dépasse Retina-Pool dans le test 2AFC « choisir le familier » (67,6 % contre 64,3 %). Les modèles se dégradent nettement sous décalage.

### Coût de calcul observé (même machine, sans GPU, trois exécutions)

Sur l'ensemble des trois graines et les deux conditions : pixels ~0,633 s ; HOG ~18,024 s ; Retina-Pool ~2,408 s pour les extractions de caractéristiques et scores (hors rendu des portraits). Ces durées reflètent **cette implémentation Python**, pas la consommation d'énergie ou la supériorité d'une architecture matérielle.

## Portée des preuves

- **PASS local :** 9 tests unitaires Python ; génération déterministe, sortie à dimensions contrôlées, 44 distracteurs distincts, vues d'entraînement et de test séparées, provenance explicite, identité effacée, empreintes SHA-256 par score.
- **PARTIAL scientifique :** uniquement un simulateur synthétique ; nombre d'identités faible ; mêmes identités réutilisées entre épisodes ; étude exploratoire sans intervalle statistique validé entre graines.
- **UNVERIFIED :** généralisation à des vrais visages consentis/licenciés ; robustesse en conditions terrain ; économie d'énergie ; fidélité au cerveau du poisson.

## Reproduction à coût nul

Depuis la racine du dépôt, disposer de Python et installer numpy, scipy, pillow dans un environnement isolé :

    python -m unittest tests.test_archer_vision_benchmark -v
    python validation/archer_vision_benchmark.py --seed 20261114 --episodes 24 --shots 6 --out reports/factory/ARCHER-VISION-SEED-20261114.json
    python validation/archer_vision_benchmark.py --seed 20261114 --episodes 24 --shots 6 --identity-ablation --out reports/factory/ARCHER-VISION-IDENTITY-ABLATION.json

Les fichiers JSON de l'expérience (3 graines, contrôle d'identité et synthèse) sont archivés dans le paquet livré à l'utilisateur. Aucun déploiement, fusion, API payante ou traitement d'image personnelle.
