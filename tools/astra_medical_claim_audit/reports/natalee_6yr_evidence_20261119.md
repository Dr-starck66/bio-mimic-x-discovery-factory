# ASTRA MEDICAL Ω — NATALEE 6 ans (19 novembre 2026)
**Statut : PASS pour l'audit arithmétique agrégé ; UNVERIFIED pour la prédiction individuelle et la validation clinique.**
Ce document isolé ne modifie pas le système diagnostique SDBench et n'entraîne aucune décision thérapeutique.

## Sources primaires et provenance
- NATALEE, survie globale 6 ans, Annals of Oncology (23/10/2026) : https://pubmed.ncbi.nlm.nih.gov/42918423/
- Tableau de résultats 2026 : https://www.novartis.com/us-en/news/media-releases/kisqali-shows-clinically-meaningful-overall-survival-broadest-hrher2-early-breast-cancer-population-high-risk-recurrence
- Tolérance : étude avec cutoff au **29/04/2024** : https://pmc.ncbi.nlm.nih.gov/articles/PMC13726065/
- Modèle ML préalable de pronostic / traitement utilisant NATALEE et Flatiron (2026), éviter fausse nouveauté : https://pmc.ncbi.nlm.nih.gov/articles/PMC12809111/
- Voie d'accès aux données individuelles Novartis (accès **non obtenu**) : https://www.clinicalstudydatarequest.com/Study-Sponsors/Study-Sponsors-Novartis.aspx

## Audit reproductible effectué hors GitHub (Python stdlib, 2026-11-19)
- n randomisés = 2 549 + 2 552 = **5 101**.
- Survie globale Kaplan-Meier à 6 ans : 91,86 % vs 89,73 %, écart **2,13 points**, soit NNT descriptif ≈ **47** à cet horizon (aucune inférence individuelle).
- iDFS à 6 ans : 83,23 % vs 77,92 % ; écart **5,31 points**, critère composite.
- HR de décès = **0,809** (IC95 % 0,661–0,989) : baisse relative du *hazard* de **19,1 %**, **pas** baisse absolue de mortalité.
- P unilatéral nominal publié = 0,019 ; approximation Wald par CI arrondi = **0,0196**, non un nouvel essai.
- Décès bruts = 178/2 549 contre 205/2 552, soit 6,98 % vs 8,03 % (**1,05 point**, **pas** le Kaplan-Meier à six ans ; censure non ajustée).
- Effets indésirables grade ≥3 dans l'analyse de tolérance antérieure = 64,2 % vs 19,7 % (**44,5 points**); ne pas les soustraire au résultat OS (endpoints/cutoffs différents).

## Preuves de fonctionnement et contrôles négatifs
- Script indépendant : `audit_natalee.py`; jeu de faits : `aggregate_source.json`; protocole : `PROTOCOLE_ACCES_DONNEES.md`; rapport : `RAPPORT_NATALEE.md`, livrés comme archive de conversation.
- **10/10 tests unitaires PASS** en Python normal **et 10/10 PASS** sous `python -O`.
- Tests négatifs : différence OS falsifiée (8,0 points), bras inversés, dénominateur nul, HR hors IC, réduction du hazard falsifiée — tous rejetés.
- ZIP local SHA256 : `16d3ce070e2752e99ffa3531137c8675643d7a7744637addc700dbdf42db6d55`. Empreinte du fichier produit en session, non preuve d'hébergement GitHub.
- **Limites :** valeurs publiques agrégées seulement, pas de bras individuels ni survies censurées ; impossible de mesurer l'hétérogénéité causale du traitement, l'AUC clinique, la calibration, l'amélioration du modèle de 2026 ou la décision thérapeutique.

**Précaution :** branche de recherche seulement, aucune publication de données patient, aucun service payant, aucune nouvelle automatisation.