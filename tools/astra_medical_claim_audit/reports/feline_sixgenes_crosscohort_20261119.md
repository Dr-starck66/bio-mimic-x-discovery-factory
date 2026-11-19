# ASTRA MEDICAL Ω — six biomarqueurs, deux cohortes FELINE (19 novembre 2026)

**PASS** : exécution de code réel sur fichiers GEO GSE158724 et GSE211434, 8/8 tests intégrés, exit 0, 49 283 ms, Vercel Hobby éphémère (session `sbx_zKsN5t9k8JPMRhinFDG5twGhtp22`, commande `cmd_44c206d67fff4e9daa94e6d42ca8`).

**FAIL** : la réplication indépendante de la discrimination MAPT et tout signal robuste des six biomarqueurs comme sélection de traitement. **UNVERIFIED** : prédiction clinique individualisée du bénéfice du ribociclib; pas de données individuelles NATALEE.

Data: 23 patientes/47 947 cellules prétraitement (discovery; ribociclib+letrozole n=14, contrôle n=9), 26 patientes/57 011 cellules (validation; ribociclib n=15, contrôle n=11). Unité statistique patiente, non cellule; biopsies avant traitement uniquement, seuil préfixé >=100 cellules tumorales. Réponses à 6 mois FELINE, non mortalité NATALEE.

Les gènes CEACAM6, NOD2, GPX3, GATA3, SLC39A6 et MAPT ont tous été trouvés dans les matrices de comptage RNA. Analyse d'expression moyenne par cellule tumorale avec sensibilités ratios ACTB/GAPDH; permutation exacte pour l'AUC par bras, interaction exploratoire par différence de différences avec bootstrap (1 500 tirages) par cohortes.

| Gène | AUC Ribo découverte | p exact découverte | AUC Ribo validation | p exact validation | IC95 % interaction découverte | IC95 % interaction validation |
|---|---:|---:|---:|---:|---:|---:|
| CEACAM6 | 0.510 | 1.0000 | 0.295 | 0.2799 | [-0.35; 1.28571] | [-1.05833; 0.39286] |
| NOD2 | 0.408 | 0.6200 | 0.659 | 0.4117 | [-1.01667; 0.59167] | [-0.94167; 0.56667] |
| GPX3 | 0.520 | 0.9336 | 0.614 | 0.5714 | [-0.90159; 1.0127] | [-0.39762; 0.99405] |
| GATA3 | 0.408 | 0.6200 | 0.568 | 0.7531 | [-1.08571; 0.57857] | [-0.99405; 0.16667] |
| SLC39A6 | 0.673 | 0.3176 | 0.568 | 0.7531 | [-0.84444; 1.01587] | [-1.11111; 0.1746] |
| MAPT | 0.449 | 0.8048 | 0.864 | 0.0396 | [-0.61429; 1] | [-0.34921; 0.90873] |

**Toutes les 12 bornes d'interactions de risque incluent 0 ; aucune interaction confirmée.** Holm sur six comparaisons d'AUC au sein du bras ribociclib: découverte tous p ajustés 1 ; validation MAPT p ajusté **0,2374**, autres p ajustés 1. Les p d'AUC ne sont **pas** des tests d'interaction traitement×gène; les interactions médianes sont descriptives, sans validation statistique formelle sur jeu IPD NATALEE.

Le signal MAPT ne se reproduit pas: AUC 0,449 en découverte vs 0,864 en validation; dans le bras témoin, AUC 0,55 et 0,821 respectivement. Découverte examinée après que validation avait déjà été explorée, pas d'épreuve prospective aveugle. Substudy séquencé de petite taille, bras FELINE B/C groupés malgré différents schémas posologiques, métriques d'expression sensibles à profondeur de séquençage, seuils médianes calculés par cohorte. Aucune utilisation clinique.

Provenance exécution: JSON agrégé original 54 590 octets, SHA256 `23576751ddd4996147aca3d2c54f51390a2720ff84b494d0b19a2714bb527299`. **Le JSON original n'a pas pu être transféré hors de la sandbox avant expiration (410 sandbox_stopped).** Archive de conversation `ASTRA_MEDICAL_FELINE_SIX_GENES_AUDIT_20261119.zip` : **résumé reconstruit depuis sorties effectivement observées**, pas copie du fichier original, SHA256 ZIP `3ab86ee90a427452bfd171810888a8348a13ba7e8e6a745975a4f088f041a144`, 8/8 contrôles de cohérence du résumé PASS. Toutes les commandes de test source ont réussi ; limites d'archivage documentées.

Fichiers d'origine :
- `tools/astra_medical_claim_audit/feline_sixgenes_crosscohort_20261119.py` (code vérifiable et ré-exécutable, branche `astra/medical-sequential-20261118`).
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE158724
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE211434
- https://doi.org/10.1200/JCO.2026.44.16_suppl.501 (hypothèses de biomarqueurs; autre essai et autre critère)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11876604/ (étude FELINE unicellulaire)

**Décision de recherche :** six candidats non confirmés ; ne publier aucune règle de sélection thérapeutique ou bénéfice individuel sur cette base. Demander une évaluation à une équipe oncologie/biostatistique autorisée sur NATALEE et examiner les interactions officielles traitement×biomarqueurs.
