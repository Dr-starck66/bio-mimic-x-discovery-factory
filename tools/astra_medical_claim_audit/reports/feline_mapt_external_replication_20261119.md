# ASTRA MEDICAL Ω — MAPT validation indépendante à l'intérieur de FELINE

Date : 19 novembre 2026. **Exécution réelle, aucun résultat clinique inventé.**

## Résultat principal : MAPT ne se reproduit PAS comme discriminateur de réponse sous ribociclib

Deux cohortes distinctes du même essai randomisé FELINE NCT02712723, pas NATALEE, ont été téléchargées directement de GEO dans une sandbox Vercel Hobby gratuite, uniquement cellules tumorales **avant traitement**, avec calcul **agrégé par patiente** et seuil fixé préalablement ≥100 cellules tumorales exploitables.

| Métrique | Découverte GSE158724 | Validation GSE211434 |
|---|---:|---:|
| Patientes originales incluses dans les séries publiées | 35 | 27 |
| Avec biopsie J0 et ≥100 cellules tumorales exploitables | 23 | 26 |
| Cellules retenues | 47 947 | 57 011 |
| Sous ribociclib + létrozole | 14 | 15 |
| Sous létrozole seul | 9 | 11 |
| Répondeuses sous ribociclib | 7 | 11 |
| MAPT expression moyenne, AUC sous ribociclib | **0,448980** | **0,863636** |
| Test exact de permutation (bilatéral), sous ribociclib | **0,804779** (3432 assignations) | **0,039560** (1365 assignations) |
| Bootstrap 3000x, IC95% AUC sous ribociclib | [0,142857 ; 0,775510] | [0,636364 ; 1,000] |
| MAPT AUC, létrozole seul | 0,550000 | 0,821429 |
| Interaction exploratoire (différence de différences des probabilités de réponse, découpage médian) | 0,20714 | 0,26587 |
| IC bootstrap 95 % interaction | [-0,61429 ; 1,00000] | [-0,34921 ; 0,90873] |

AUC calculée sur les expressions MAPT moyennes **par cellule tumorale** (moyenne UMI, non corrigée de la profondeur totale de séquençage sur GSE158724). Contrôles de sensibilité avec fraction de cellules exprimant MAPT et ratios MAPT/ACTB, MAPT/GAPDH.

**Résultat négatif important :** absence de réplication du signal fort dans la cohorte de découverte. Dans la cohorte dite de validation, MAPT distingue aussi la réponse au létrozole seul (AUC 0,821), ce qui ne constitue pas une preuve d'effet propre au ribociclib. Aucun intervalle d'interaction sur la métrique principale n'exclut 0. **Ce test ne valide ni biomarqueur prédictif ni outil de sélection des patientes.**

## Tests et intégrité

- Pipeline GitHub `tools/astra_medical_claim_audit/feline_mapt_external_20261119.py`, commit de checkpoint **959ea0637d254c01268ece9f0077146f45e729de**. Relecture GitHub du code identique.
- Vercel Hobby session `sbx_lSbARR37BpuuQbbQMk4UO0v22IBb`; première exécution complète **exit 0**, 42 612 ms. Tests intégrés **6/6 PASS** et les deux cohortes effectivement calculées ; bootstrap indépendant second passage **exit 0**.
- Rapport agrégé JSON SHA-256 **e7c2a24f6d68f897471dd5b27780c2c7699324b1ebf6fb3a58d3ff6fe8a6e040** enregistré initialement dans sandbox éphémère, pas sur GitHub ; seules les statistiques non identifiantes ci-dessus sont consignées.
- Contrôle négatif sur inversion des étiquettes : AUC 0,551020 en découverte et 0,136364 en validation, soit 1−AUC comme attendu.
- Système local de fonctions mathématiques : **9/9 unittest PASS** après correction explicite d'une attente erronée dans un premier essai (erreur visible, corrigée).
- Aucun enregistrement individuel, ID de patient, matrice ou gène par patiente sauvegardé dans GitHub, ChatGPT ou rapport partagé.
- Une session précédente avait expiré avant l'analyse de validation (exit 143) ; une nouvelle session a terminé les deux analyses, d'où **PASS pour la nouvelle exécution seulement**.

## Limites et décision scientifique

1. Pré-traitement seulement, mais le sous-groupe sélectionné de personnes ayant assez de cellules séquencées peut être biaisé. 49/62 patientes des cohortes publiées sont évaluables après exigences J0/QC.
2. Le comparateur et les schémas de doses FELINE sont différents de NATALEE. Réponse néoadjuvante ≠ survie à six ans.
3. La cohorte de découverte a été analysée après l'identification exploratoire de MAPT dans la cohorte nommée « validation » ; réplication rétrospective, non prospective ni aveugle au sens fort.
4. Normalisation : métrique principale MAPT moyenne brute par cellule, sensible aux profondeurs de séquençage; contrôles de ratios ACTB/GAPDH, mais non équivalents à une normalisation standard avec facteurs de bibliothèque intégrals.
5. Tests de permutation p non corrigés pour les multiples choix de gènes, métriques et cohortes. L'examen précédent de six candidats (notamment MAPT) ne validait aucun signal après correction.
6. AUC *à l'intérieur d'un bras* = pronostic de réponse, **non** interaction causale traitement×biomarqueur. Interaction risque (médiane) descriptive et IC instable sur petits effectifs, ne prouve pas le bénéfice individuel.
7. Absence de données individuelles NATALEE, aucune validation clinique indépendante, aucune recommandation de traitement.

**Sources publiques** : 
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE158724
- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE211434
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11876604/

**Verdict :** PASS pipeline de calcul réel et vérification des données accessibles. FAIL de la réplication du signal MAPT dans les données FELINE accessibles. UNVERIFIED outil de sélection clinique. Coût additionnel engagé : aucun achat ni nouvel abonnement ; usage d'une sandbox Hobby limitée dans le temps.
