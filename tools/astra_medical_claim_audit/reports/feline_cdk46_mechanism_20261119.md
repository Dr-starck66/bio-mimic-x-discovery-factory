# ASTRA MEDICAL Ω — Audit mécanistique CDK4/6–RB–E2F sur FELINE

Date du calcul : 19 novembre 2026. **Résultat négatif maintenu**.

## Question ciblée

L'expression prétraitement de **RB1, CCNE1, ESR1**, un score **CCNE1−RB1**, ou un programme de prolifération **E2F1/MCM2/PCNA/TOP2A/MKI67**, permet-elle d'identifier un bénéfice *spécifique* de l'ajout du ribociclib au létrozole ?

**Réponse expérimentale actuelle : non démontré.** Aucun des dix intervalles bootstrap exploratoires des cinq marqueurs d'intérêt n'exclut zéro. Le contrôle négatif technique ACTB/GAPDH ne fournit pas de confirmation non plus.

Les cohortes FELINE GEO GSE158724 (23 patientes, 47 947 cellules prétraitement) et GSE211434 (26 patientes, 57 011 cellules) ont été traitées séparément. Bras ribociclib + létrozole vs létrozole seul : respectivement 14/9 puis 15/11 patientes. Analyse par patiente, exclusivement J0, critère de qualité ≥100 cellules tumorales.

## Résultats agrégés

| Marqueur | AUC Ribo découverte | AUC Ribo validation | p exact découverte | p exact validation | IC interaction découverte | IC interaction validation |
| --- | --- | --- | --- | --- | --- | --- |
| RB1_presence | 0.531 | 0.591 | 0.902 | 0.661 | [-0.9; 0.85556] | [-0.69524; 0.75714] |
| CCNE1_escape | 0.510 | 0.364 | 1.000 | 0.489 | [-1.03571; 0.58571] | [-0.79048; 0.69524] |
| ESR1_dependence | 0.510 | 0.273 | 1.000 | 0.226 | [-1.13333; 0.475] | [-0.65873; 0.71429] |
| CCNE1_minus_RB1 | 0.449 | 0.386 | 0.805 | 0.571 | [-0.95833; 0.66667] | [-0.65119; 0.76667] |
| E2F_proliferation | 0.510 | 0.500 | 1.000 | 1.000 | [-1.07143; 0.58571] | [-0.6631; 0.76667] |
| HOUSEKEEPING_negative_control | 0.776 | 0.636 | 0.097 | 0.489 | [-0.06667; 1.55556] | [-0.00238; 1.3] |

AUC = classification des répondantes **dans un bras** ; ce n'est **pas** un test causal de réponse différentielle au ribociclib. *p exact* = permutation exhaustive des étiquettes de réponse au sein du bras traité. Interactions rapportées = différence de différences des probabilités de réponse pour groupes high/low constitués à la médiane du biomarqueur dans chaque cohorte, avec bootstrap patient 1 500 rééchantillonnages. Ce ne sont pas des tests confirmatoires validés. La correction de Holm sur les six variables dans chaque cohorte ne laisse aucun signal d'AUC significatif.

Le **contrôle négatif** ACTB/GAPDH donne des AUC élevées mais non significatives dans les deux bras ribociclib (0,776 et 0,636), rappelant la vulnérabilité des petites cohortes sélectionnées à des biais d'expression ou de composition.

## Preuves techniques

- Code : `tools/astra_medical_claim_audit/feline_cdk46_mechanism_20261119.py`, commit GitHub `053d97d5a787f162aba21b489f6bf82066956705`.
- Exécution dans la sandbox Vercel Hobby `sbx_5UPslIRLwSbCwxdhBYJZ3Zgk5GmC` : **exit 0**, durée 47,965 s, **8/8 tests internes PASS**.
- Toutes les 10 cibles ARN ont été retrouvées dans chacune des deux matrices publiques, puis 6 caractéristiques calculées (5 d'intérêt, 1 contrôle négatif).
- Source JSON d'exécution de **19 926 octets**, SHA256 `d3c66107c2a6fe14e4e1e491c4b036198080c4b006fef7cfd0efaf9be29639a7`. Ce fichier original est dans une sandbox temporaire, **non archivé** dans GitHub. Le présent rapport et le JSON compact adjoint reprennent les statistiques vérifiées dans les journaux.
- Aucune matrice contenant des données individuelles, ni identifiant de patiente, n'a été publié sur GitHub.

## Décision scientifique

**PASS :** lecture et analyse de données authentiques, tests du programme, vérification des groupes et contrôles négatifs, archivage de résultats agrégés.

**FAIL :** identification d'un marqueur cliniquement confirmé de réponse spécifique au ribociclib à partir de ces données.

**UNVERIFIED :** transportabilité à NATALEE, capacité à recommander individuellement le traitement, sécurité clinique et validation indépendante.

Le statut FAIL porte sur le **critère scientifique**, non sur l'exécution. Aucune performance clinique ou causalité individuelle inventée.

## Conditions d'une validation autorisée

Une équipe NATALEE disposant légitimement des données randomisées devra tester sur un échantillon suffisamment large une interaction traitement×biomarqueur préenregistrée, avec modèle comparatif du risque sans biomarqueur, calibration des **effets absolus**, IC et analyses de multiplicité, puis réplication externe. Le critère de NATALEE est la survie/récidive adjuvante, alors que FELINE mesure une réponse néoadjuvante.

Sources : [FELINE découverte](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE158724), [FELINE validation](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE211434), [article biomarqueurs NATALEE ASCO 2026](https://doi.org/10.1200/JCO.2026.44.16_suppl.501), [étude résistance](https://pmc.ncbi.nlm.nih.gov/articles/pmid/40738893/).
