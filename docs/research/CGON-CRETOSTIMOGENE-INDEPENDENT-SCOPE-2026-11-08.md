# BIO-MIMIC X × CG Oncology — dossier scientifique exploratoire indépendant

**Date : 8 novembre 2026 · Statut : PARTIAL · Coût : 0 € · Aucune affiliation ni collaboration avec CG Oncology.**

## Question scientifique utile

Peut-on identifier et valider sur des cohortes publiques des caractéristiques tumorales et immunitaires liées à la réponse au BCG dans le cancer de la vessie non infiltrant le muscle (NMIBC), puis formuler des hypothèses falsifiables **à proposer** pour une validation distincte chez des patients traités par cretostimogene ?

**Non** : ces données BCG ne constituent pas une cohorte cretostimogene ; elles ne peuvent démontrer ni la réponse individuelle ni l'efficacité d'une intervention avec l'adénovirus.

## Vérifications documentaires (8 novembre)

- **BOND-003, cohorte C** — essai de phase 3 **à bras unique** NCT04452591 ; article dans *The Lancet Oncology* (2026), DOI `10.1016/S1470-2045(26)00194-4`, PMID 42508433. Réponse complète à un moment quelconque du suivi : 83/110 participants évaluables (environ 75,5 %). Un essai non randomisé ne fournit pas à lui seul une comparaison directe d'efficacité avec les alternatives. Source : https://pubmed.ncbi.nlm.nih.gov/42508433/
- **PIVOT-006** — NCT06111235 ; essai randomisé, ouvert, après TURBT, cretostimogene vs surveillance ; annonce de données principales prévue **en novembre 2026** selon le communiqué du 6 novembre ; résultats non encore vérifiés dans cette mission. Sources : https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCT06111235 et https://cgoncology.com/news-media/cg-oncology-reports-third-quarter-2026-financial-results-and-provides-business-updates
- **Mécanisme connu** — thérapie oncolytique intravésicale expérimentale, ciblant la biologie RB/E2F et induisant une réponse immunitaire. Ne pas confondre expression d'un récepteur d'entrée, capacité de réplication ou bénéfice clinique. Source : https://bladder.uroonco.uroweb.org/publication/intravesical-cretostimogene-grenadenorepvec-oncolytic-immunotherapy-in-high-risk-bcg-unresponsive-non-muscle-invasive-bladder-cancer-with-carcinoma-in-situ-bond-003-cohort-c-a-single-arm-phase-3/

## Données ouvertes identifiées (indirectes, sans étiquette de réponse au cretostimogene)

| GEO | Modalité / population | Apport possible | Limite |
|---|---|---|---|
| [GSE176178](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE176178) | HG T1 NMIBC, transcriptome, réponse durable au BCG | Première association exploratoire | Pas de patients traités par cretostimogene |
| [GSE244895](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE244895) | RNA-seq longitudinal avant/après BCG | Contrôle intra-patient | Petit effectif, confusions temporelles |
| [GSE322495](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE322495) | scRNA-seq immunitaire, BCG répondants/non-répondants | Phénotypes macrophages/T | Prélèvement et modalité différents |
| [GSE269877](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE269877) | scRNA-seq NMIBC naïfs/récidivants après BCG | CD6/ALCAM, état immunitaire | Résistance au BCG ≠ résistance au cretostimogene |

**Accès réel** : fiches GEO identifiées via index public, accès direct aux pages parfois bloqué par protection anti-bot dans cette session. Les données brutes, métadonnées patient et matrices d'expression **n'ont pas été téléchargées ni analysées** ici.

## Hypothèses pré-enregistrables — aucune validée

- **H1, biologie d'entrée et prolifération** : évaluer la co-variation de CXADR et des signatures RB/E2F dans le NMIBC, en séparant prolifération générique et expression du récepteur. Aucun lien avec la sensibilité effective au cretostimogene n'est présumé.
- **H2, réponse antivirale et T** : tester si signatures d'interféron et états T correspondent à des différences de réponse au BCG dans des cohortes indépendantes. Leur transposition à un virus oncolytique resterait une hypothèse.
- **H3, immunité et macrophages** : tester la robustesse des états macrophages, CD8 épuisés et T régulateurs dans les cohortes disponibles, en contrôlant composition cellulaire et effets de lot.

## Pipeline à réutiliser, non recréer

Dépôt existant `Dr-starck66/bio-mimic-x-discovery-factory` : exploiter **Evidence Network / Claim Ledger**, **Negative Knowledge Graph**, **DUALITY-X / Arbiter**, **Morpheus adversarial audit**, **Ω-EXPERIMENT replay SHA-256**, et le **Data Fusion Engine** listés dans son README. La présence des briques est documentée ; leur exécution sur cette mission n'a pas encore été prouvée.

**Protocole minimal avant toute affirmation scientifique :** (1) récupérer matrices et annotations avec empreintes SHA-256 ; (2) vérifier consentements, granularité patient et partitions ; (3) harmoniser les définitions de réponse BCG sans mélanger les populations ; (4) analyses exploratoires sous contrôle qualité ; (5) validation externe par cohorte entière, contrôles négatifs (permutation, gènes de contrôle, composition cellulaire, effet de lot) ; (6) conserver les résultats défavorables ; (7) rédiger un dossier non confidentiel pour discussion scientifique.

**Critères d'arrêt** : méta-données incohérentes, échantillons non comparables, fuite d'information, absence de signal répliqué ou données d'effet clinique manquantes -> FAIL/PARTIAL, jamais « découverte » ni « outil prédictif cretostimogene ».

## Actions et états

- **PASS — veille documentaire :** sources primaires/registre et jeux GEO publics identifiés avec URLs et limites ; essais cliniques distingués.
- **PARTIAL — mission structurée :** manifeste machine-lisible connexe dans `research/cretostimogene/public_evidence_manifest_2026-11-08.json`.
- **UNVERIFIED — analyse biologique :** aucune matrice brute reanalysée, aucun résultat de biomarqueur, aucune performance validée.
- **UNVERIFIED — partenariat :** aucun contact CG Oncology initié et aucun accord, accès privé ou validation de l'entreprise.
- **Suivante seule étape scientifique prioritaire :** récupérer la matrice et métadonnées d'au moins une cohorte GEO et lancer un test reproductible des hypothèses avec les moteurs BIO-MIMIC X existants, sans toucher aux expérimentations virales ni aux données confidentielles.

*Document de veille et proposition de recherche indépendante. Pas un avis médical, une expérimentation virologique ou une preuve clinique.*
