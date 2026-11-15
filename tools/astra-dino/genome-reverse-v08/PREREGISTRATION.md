# ASTRA DINO Ω v0.8 — protocole figé avant lecture de la troisième matrice
Date : 2026-11-15. Branche isolée. Aucun coût ni changement de production.

## Sources
- Développement **Hendrickx et al. (2022)** et **Baron–Brown corrigée (2017)** ; aucun nouvel ajustement de paramètres autorisé.
- **Troisième jeu de test TENU À L'ÉCART** : Xi et al. 2024, *New evidence for the earliest ornithischian dinosaurs from Asia* ; Dryad DOI 10.5061/dryad.08kprr5d0, fichier **Dataset_S1.tnt** (73 taxons, 383 caractères déclarés par l'auteur). Aucune des données de Xi n'est utilisable pour choisir un paramètre.
- Arbres externes candidats : Černý & Simonoff (2023), DOI 10.5281/zenodo.7979718, phylogénies de réanalyse sur données Baron : externes par auteurs, **pas indépendantes par caractères** ; et Open Paleo version 2026.11 : **hiérarchie de clades, pas arbre de taxons résolu**. NE PAS confondre ces sources avec une phylogénie externe validée à chaque espèce.

## Méthode gelée : doit conserver les options v0.7
- Modèle Mk symétrique, taux fixe **0.25** ; références vote majoritaire et Mk.
- Ancrages anatomiques indices 0,5,10,... (`j%5==0`) toujours fournis pour le taxon cible ; toutes les autres réponses tenues cachées.
- Complément de cooccurrence sur les taxons d'entraînement seulement ; `lambda=0.35`, maximum **12** voisins, minimum **3** ancrages communs.
- Modèle témoin ancrages du taxon cible mélangés selon graine **20261114** ; le taxon cible doit rester exclu pour toutes les valeurs du caractère prédit.
- États sous protocole `0,1,2,3,4` comme v0.7 : toutes autres valeurs isolées, sans modifier les paramètres. `?` et `-` jamais convertis en 0 ; caractères non pris en charge exclus avec compte explicite.
- Pour une matrice TNT sans arbre indépendant, référence Mk à **topologie étoilée non résolue**, explicitement signalée (pas un arbre « vérifié »).
- Métriques fixées : exactitude sur toutes les observations y compris erreurs/abstentions, log-loss, score de Brier ; bootstrap **500** rééchantillonnages par taxon, graine **20261114**, intervalle bilatéral empirique 95 %.
- Aucune mise au point ou adaptation sur la troisième matrice. Tout ajustement futur est v0.9 et nécessite une QUATRIÈME matrice indépendante.

## Critères de PASS scientifique forts
- Fichier source récupéré exactement, SHA-256 mesuré, taille taxons/caractères et données manquantes auditées.
- Prévisions invariantes à une mutation de la réponse cachée.
- Le conjoint doit dépasser à la fois Mk et le vote majoritaire en score et calibration sur la troisième matrice, avec CI robuste ; les ancrages mélangés doivent échouer ; reproductibilité vérifiée sur code persisté.
- Une phylogénie **véritablement indépendante des états cachés** est nécessaire pour tout PASS phylogénétique. Un arbre construit sur la même matrice/les mêmes caractères = contexte ou analyse de sensibilité seulement, pas validation indépendante.
- Aucun PASS de « génome de dinosaure » à partir de seuls caractères anatomiques.

Ce protocole est déposé **avant la récupération et le scoring** du fichier `Dataset_S1.tnt`.