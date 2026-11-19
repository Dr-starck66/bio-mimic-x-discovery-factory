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

## AUDIT ADDITIONNEL — SURVIE 6 ANS, SEPT PAIRES DE SOUS-GROUPES (2026-11-19)
Source primaire : publication NATALEE DOI https://doi.org/10.1016/j.annonc.2026.10.1288. Les HR et IC95 ont été extraits des résultats de survie globale par sous-groupe de l'étude à six ans ; audit sur chiffres **agrégés et arrondis**, sans IPD.

| Sous-groupes comparés | Ratio HR entre groupes | p Wald bilatéral APPROX | Holm approx |
|---|---:|---:|---:|
| N0 vs N1–3 | 0,967 | 0,9246 | 1,0 |
| Stade II vs III | 1,040 | 0,8730 | 1,0 |
| Chimiothérapie antérieure oui/non | 1,339 | 0,4633 | 1,0 |
| Hormonothérapie antérieure oui/non | 1,119 | 0,6001 | 1,0 |
| Préménopause vs postménopause | 0,798 | 0,3043 | 1,0 |
| Région Amérique du Nord/Europe de l'Ouest/Océanie vs autres | 1,107 | 0,6236 | 1,0 |
| Ki-67 ≤20 % vs >20 % | 1,018 | 0,9351 | 1,0 |

**0/7 interactions approximatives significatives**. Méthode : SE(log HR) extrait des IC95 publiés, Z de différence de log(HR) entre groupes disjoints, p bilatéral, correction Holm sur sept tests. C'est une exploration **non équivalente** au test officiel de Cox traitement×variable effectué sur les données individuelles. Ne pas conclure à la preuve d'une absence d'hétérogénéité ni à un algorithme de sélection de patientes.

Source moléculaire indépendante : abstract ASCO 2026, 3022 échantillons et interaction PAM50×traitement **p=0,34**, avec six gènes candidats exploratoires CEACAM6, NOD2, GPX3, GATA3, SLC39A6, MAPT : https://doi.org/10.1200/JCO.2026.44.16_suppl.501 . Aucun biomarqueur sélectionneur validé.

**Point critique de relecture** : Howard et al., *Clinical Cancer Research* 2026, méthode du Cox pondéré (10 covariables plus indicateur de traitement), DOI https://doi.org/10.1158/1078-0432.CCR-25-1946 : sans interaction explicite traitement×covariable, un modèle Cox impose un **HR relatif constant pour tous x**, tout en permettant un bénéfice absolu variable selon le risque initial. Une telle personnalisation du risque n'est pas une démonstration d'une sensibilité biologique individuelle au médicament. Les auteurs indiquent des exemples de code sur https://osf.io/rnsua/ ; contenu non téléchargé ni exécuté (outil Web 403, conteneur DNS inaccessible).

**Politique d'accès** : https://clinicalstudydatarequest.com/Study-Sponsors/Study-Sponsors-Novartis.aspx interdit normalement le partage des analyses intermédiaires des essais en cours et exclut certaines données génétiques / biomarqueurs exploratoires. Ceci restreint significativement la revalidation directe des six candidats. Aucune donnée individuelle NATALEE n'a été obtenue.

**Exécution réellement confirmée en conteneur isolé** : 13/13 tests Python PASS + 13/13 sous `python -O` PASS, calcul et export JSON, contrôle ZIP d'intégrité PASS ; archive de conversation `ASTRA_MEDICAL_NATALEE_7_SOUS_GROUPES_20261119.zip`, SHA256 `e4d088a75b9e6da0db331b2574a2e5d8828496c37abb94adc2841ea559e5e142`. Code de référence GitHub ajouté :
- `tools/astra_medical_claim_audit/natalee_6yr_os_subgroups_20261119.py`;
- `tools/astra_medical_claim_audit/test_natalee_6yr_os_subgroups_20261119.py`.

**Portée des preuves** : PASS calculs sur chiffres publiés, tests unitaires de la version locale, lecture GitHub après commit; UNVERIFIED exécutabilité de cette version GitHub dans un serveur externe et toute prédiction individualisée validée. Aucun déploiement clinique, aucune dépense ni nouveau cron.
