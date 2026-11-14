# ASTRA OBESITY Ω — dossier de recherche mondial (pilote v0.1)

**Statut : PARTIAL — logiciel expérimental ; aucune efficacité thérapeutique ni diagnostic clinique démontré.**  
**Coût supplémentaire : 0 €.** Aucune nouvelle automatisation, aucun contact patient, aucun traitement recommandé ni modification de production.

## Objectif

Étudier les mécanismes biologiques, sociaux et environnementaux de l'obésité chronique, ses formes cliniques, la durabilité des interventions et l'accès équitable aux soins. L'objectif à terme est une contribution scientifique vérifiable à la prévention et au traitement durable, et non une affirmation de « guérison universelle ».

## Réutilisation du patrimoine ASTRA des trois derniers mois

Source de routage : `Dr-starck66/indexation/ASTRA_REGISTRY.md` (279 entrées documentaires relevées au 14/11/2026, NON 279 logiciels opérationnels). Source de code : `factory/brick_registry.json` et `factory/` dans BIO-MIMIC X.

| Brique existante | Statut du raccordement à cette mission | Rôle |
|---|---|---|
| ASTRA-086 BRICK REGISTRY + ASTRA-087 AUTO-ROUTER | consultation du registre : PASS ; activation automatique mondiale : UNVERIFIED | Sélection des briques pertinentes, anti-doublon |
| BIO-MIMIC X hypothesis-engine | **exécuté dans le pilote local** | Trois hypothèses falsifiables par question |
| BIO-MIMIC X debate-engine / DUALITY-X | **exécuté dans le pilote local** | Critique des causes non démontrées, objections et contrôles |
| BIO-MIMIC X experiment-planner / Ω-EXPERIMENT | **exécuté dans le pilote local** | Projets d'expériences explicitement non exécutées |
| Evidence Network / Claim Ledger | métadonnées de provenance inscrites dans la mission ; intégration au control-plane : UNVERIFIED | Ne pas transformer sources en essais |
| ASTRA-097 EVIDENCE LEDGER / ASTRA-039 AUTOMATION EVIDENCE | contrat de preuve appliqué dans le dossier ; orchestration globale : UNVERIFIED | Statuts et SHA reproductibles |
| Morpheus + Ω-CAUSAL + Negative Knowledge Graph | partiellement représentés par les objections et falsificateurs ; moteur complet : UNVERIFIED | Écarter les conclusions prématurées |
| AION-NEXUS / Data Fusion / AgentShield | modules documentés, **non exécutés** par ce pilote | Futurs adaptateurs multi-sources et confiance |
| Human Bridge | module existant, **non exécuté** pour l'obésité | Vérifier transposition animale → humaine, sans extrapolation |
| BENCHMARK-X10 + Model Immune Gate | modules existants, **non exécutés** ici | Comparer à une baseline et refuser les dégradations |
| ASTRA-205 REAL DATA CONNECTORS | sources ouvertes repérées ; **aucune extraction brute exécutée** | NHANES, Open Targets, GWAS Catalog |
| ASTRA MEDICAL CLAIM AUDIT Ω | PR #48 existante **ouverte/non fusionnée**, non raccordée | Vérifier les affirmations médicales avant usage public |
| ASTRA-070 CONTINUOUS EXECUTION | instructions consultées ; processus autonome et persistant **non prouvé pour cette mission** | Exécution dans un environnement raccordé |

Les briques SEO, prospection, trading, blockchain et diffusion ne sont pas nécessaires au pilote scientifique. Elles ne sont ni activées ni présentées comme des moyens de découverte biomédicale.

## Premier lot vérifiable

- **Q1 — classification clinique** : plan de benchmark prédictif indépendant du moteur d'hypothèses causales, pour comparer adiposité + atteintes fonctionnelles à IMC seul. Aucun diagnostic individuel ni expérience de perturbation n'est généré pour cette piste.
- **Q2 — durabilité** : chercher les facteurs du maintien des bénéfices et de la reprise pondérale, avec contrôles pour arrêt du traitement, effets indésirables et équité d'accès.
- **Q3 — dysfonction du tissu adipeux** : tester des hypothèses inflammatoires avec contrôles négatifs indépendants et contrôle de la transposition à l'humain ; aucune efficacité thérapeutique déduite.
- **Sources primaires publiées** : OMS 07/10/2026, Commission Lancet 2025, Nature 11/11/2026 (844 108 adultes), OMS 01/12/2025.
- **Source de réplication candidate** : NHANES août 2021–août 2023. Aucun enregistrement individuel n'a été téléchargé ou analysé dans ce pilote.

### Exécuter

Depuis la racine du dépôt :

```bash
python -m unittest tests.test_astra_obesity_omega -v
python research/astra_obesity_omega/mission.py > obesity_dossier.json
```

Le dossier JSON déclare toujours les hypothèses comme `HYPOTHESIS`, les plans comme `PROPOSED_NOT_EXECUTED`, les essais humains et la résolution mondiale comme `False`. Son `sha256` est déterministe et permet une vérification ultérieure. Les chiffres de la publication Nature sont cités comme données de littérature, **pas recalculés à partir des cohortes originales**.

### Portes scientifiques avant toute allégation

1. Obtenir des fichiers authentiques ou un accès légal pour une cohorte indépendante ; journaliser version, licence, empreinte et exclusions.
2. Préenregistrer variables/critères cliniques, groupes, mesures de calibration, tests négatifs et seuils d'arrêt.
3. Comparer le nouveau modèle à une baseline IMC seul, en validations géographiques réellement tenues hors apprentissage.
4. Contrôler durée, événements indésirables, biais démographiques, robustesse et coût d'accès dans des pays différents.
5. Ne jamais déclarer d'efficacité, de guérison ou de causalité humaine à partir de ce moteur de littérature.

**Limite connue :** les moteurs hérités reconnaissent les sources `PMID:` pour leur comptage, pas les URLs DOI/OMS. Les références URL du dossier sont visibles, mais le compteur de sources PMID reste délibérément à zéro jusqu'à normalisation vérifiée ; aucun score de plausibilité n'est une probabilité de guérison.

## Sources

- OMS : https://www.who.int/news-room/fact-sheets/detail/obesity-and-overweight
- Lancet Commission : https://pmc.ncbi.nlm.nih.gov/articles/PMC11870235/
- Nature (2026) : https://www.nature.com/articles/s41586-026-11237-5
- OMS GLP-1 : https://www.who.int/news/item/01-12-2025-who-issues-global-guideline-on-the-use-of-glp-1-medicines-in-treating-obesity
- NHANES : https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- Open Targets : https://platform.opentargets.org/
- GWAS Catalog : https://www.ebi.ac.uk/gwas/labs/downloads/summary-statistics

## NHANES Aug 2021–Aug 2023 : premier essai sur données authentiques (14 novembre 2026)

**Sources authentifiées :** \`DEMO_L.xpt\` (11 933 enregistrements, SHA-256 \`ca4374a158b493b8b0163e1388da21d57a18d1b9cecff2aa4e2fa2bec494fe23\`), \`BMX_L.xpt\` (8 860 enregistrements, SHA-256 \`44440c416d9ad709e8b1708a5975378ab4d5b18edc39eb5015c2ae7186500170\`), \`GHB_L.xpt\` (7 199 enregistrements, SHA-256 \`67aee0353160e2392dc0a33bece99b90764a630c76d82415ac4639105ad9dd03\`). La récupération via HTTPS officiel a effectivement fonctionné depuis un runner public GitHub.

**Analyse préspécifiée :** adultes ≥20 ans, exclusion des grossesses déclarées, jointure \`SEQN\`, variables complètes uniquement, \`WTPH2YR\` pour le biomarqueur sanguin, cinq validations en groupes de pseudo-PSU masqués \`SDMVSTRA+SDMVPSU\`. Critère biologique : **HbA1c ≥6,5 %**, marqueur transversal, **PAS une définition de l'obésité clinique**. Régression logistique, métrique ROC-AUC pondérée ; contrôle négatif avec tour de taille mélangé dans chaque fold. Unité PSA masquée ≠ site géographique indépendant.

**Échantillon :** 6 023 adultes non enceintes dans la jointure, 5 453 observations complètes, 665 HbA1c élevées. Les 570 cas exclus et les traitements hypoglycémiants peuvent influer sur les conclusions.

| Modèle | AUC pondérée | Brier pondéré |
|---|---:|---:|
| IMC seul | 0,679019 | 0,088668 |
| IMC + tour de taille/taille | 0,745322 | 0,084606 |
| IMC + âge + sexe | 0,761921 | 0,084412 |
| IMC + tour de taille/taille + âge + sexe | 0,781072 | 0,082551 |
| Contrôle négatif — tour de taille mélangé | 0,677623 | 0,088697 |

AUC delta principal = **+0,066303** ; avec âge/sexe constants = **+0,019151**. Ré-échantillonnage exploratoire par pseudo-PSU pour la première différence : [0,036402 ; 0,090261] ; **ce n'est pas un intervalle de confiance corrigé pour le plan d'enquête NHANES** et ne suffit pas pour une conclusion clinique.

**Preuves :** [Workflow et 12 contrôles logiciels PASS](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43640222018) ; [rapport persistant du résultat](evidence/nhanes_2021_2023_run_43640222018.json) ; artefact GitHub \`14132040620\`, digest ZIP \`sha256:e85bff84b3f2b3d44eb10be9fd92969dc683258ae0e78158546360617dd96c48\` ; SHA-256 du rapport recalculé et conforme : \`0f01c05860cbab1388712274d16667880985c206beba46e7254e09cca21c1bd9\`.

**Statut :** PASS téléchargement, contrôle d'intégrité, analyse statistique sur véritables observations, tests logiciels et persistance du rapport résumé. **PARTIAL** : preuve biomédicale. **UNVERIFIED** : causalité, validation sur un autre pays, progrès longitudinal, efficacité thérapeutique, diagnostic clinique, déploiement autonome. Aucune donnée individuelle n'est publiée ni conservée dans le dépôt ; données brutes seulement sur le runner éphémère pendant l'exécution. Zéro dépense et aucune nouvelle tâche programmée.
