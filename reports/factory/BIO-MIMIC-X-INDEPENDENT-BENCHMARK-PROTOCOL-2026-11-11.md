# BIO-MIMIC X — protocole de benchmark indépendant (11 novembre 2026)

Statut : **PARTIAL — protocole fixé, comparaison industrielle non exécutée**.

## Référence externe vérifiée
- Open Orthobench (Emms & Kelly), 70 orthogroupes curatés, 12 protéomes d'entrée, script officiel `benchmark.py` : https://github.com/davidemms/Open_Orthobench
- Archive : https://github.com/davidemms/Open_Orthobench/releases
- Référence scientifique : https://doi.org/10.1093/gbe/evaa211
- QfO Benchmark Service : https://orthology.benchmarkservice.org/proxy/ (protéomes 2022_02 ou 2020_04, prédictions d'orthologues à soumettre ; ne pas mélanger avec Orthobench).

## Comparaison recevable
1. Exécuter les moteurs ASTRA **sur les mêmes 12 protéomes** qu'Orthobench ; ne pas utiliser le seul HAND2 pour calculer une précision générale.
2. Baselines : OrthoFinder, best reciprocal hits (BRH) et, si disponible gratuitement, résultats publics d'OMA/OrthoDB, en conservant versions et paramètres. OrthoFinder et BRH doivent être effectivement exécutés sur les mêmes entrées ; résultats publiés historiques ne sont pas des temps de calcul comparables.
3. Geler les versions, empreintes SHA-256 des entrées, prédictions et sorties avant de regarder les étiquettes curatées.
4. Utiliser le `benchmark.py` officiel pour les 70 RefOGs, en complément d'une matrice de confusion au niveau paires lorsque les étiquettes négatives sont explicites. Ne jamais assimiler « paire non curatée » à « faux positif » sans protocole de vérité terrain.
5. Calculer précision, rappel, F1, taux de faux positifs (sur négatifs admissibles), couverture, abstentions, répétabilité de trois exécutions, temps mural, CPU, mémoire max, environnement et coût.
6. Contrôles négatifs : familles paralogues HAND1/HAND2, étiquettes permutées (test de fuite), entrée tronquée et FASTA corrompu (échec sûr). Les contrôles synthétiques ne comptent pas dans le score biologique indépendant.
7. Validation : aucun ajustement des seuils après lecture du benchmark ; afficher intervalles de confiance par orthogroupe (bootstrap stratifié), différences appariées, cas d'échec et résultats défavorables.

## Critères préenregistrés
- Critère de **preuve de différenciation** : F1 ASTRA supérieur à au moins une baseline effectivement exécutée, intervalle de confiance apparié de la différence excluant 0, **sans hausse** du taux de faux positifs ; sinon FAIL/PARTIAL selon données.
- Répétabilité : trois exécutions mêmes versions/entrées donnant prédictions identiques ; sinon FAIL.
- Temps : ratio médian des temps ASTRA/baseline mesuré sur même machine ; aucune promesse de vitesse sans mesures.
- Critère de sûreté : abstention explicite sur cas ambigus, jamais promotion d'un résultat HAND2 local en unicité génomique.

## Compatibilité ASTRA — limitation à lever
Les scripts existants `validation/hand2_direct_reciprocal.py`, `validation/hand2_reciprocal_synteny.py` et `validation/hand2_flank_synteny.py` travaillent sur **locus ciblé / fenêtres sélectionnées** ; ils ne produisent pas encore les orthogroupes complets requis par Orthobench. Le benchmark officiel ne peut donc **pas** être revendiqué comme exécuté avant adaptation/extension du moteur et génération de prédictions sur les 12 protéomes.

## Résultats
- Source externe et protocole : PASS documentaire.
- Exécution ASTRA vs OrthoFinder/BRH sur Orthobench : UNVERIFIED / non exécutée.
- Précision, faux positifs, reproductibilité inter-runs, temps : **non mesurés**.
- Valeur commerciale ou performance supérieure : **UNVERIFIED**.

Aucune dépense, aucun nouveau cron, aucune modification de production.
