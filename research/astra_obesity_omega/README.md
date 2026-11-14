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

- **Q1 — classification clinique** : tester sur cohorte indépendante le gain de la combinaison adiposité et atteintes fonctionnelles vs IMC seul. Sur aucun sujet individuel on ne pose de diagnostic à partir de l'IMC seulement.
- **Q2 — durabilité** : chercher les facteurs du maintien des bénéfices et de la reprise pondérale, avec contrôles pour arrêt du traitement, effets indésirables et équité d'accès.
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
