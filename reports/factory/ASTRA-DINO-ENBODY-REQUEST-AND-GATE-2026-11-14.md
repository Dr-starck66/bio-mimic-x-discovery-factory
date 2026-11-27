# ASTRA DINO Ω — Demande d'origine Enbody 2023 et vérificateur d'admission (14 novembre 2026)

**Bilan : PARTIAL — AUCUNE nouvelle cohorte indépendante reçue.**

## 1. Action externe réelle

- Le 14 novembre 2026, email **envoyé** à Erik Enbody, destinataire `erik.enbody@gmail.com`, depuis la boîte Gmail principale. Confirmation du connecteur : ID `1a1da64d5fc50993`, labels `SENT`, puis deuxième vérification par recherche Gmail.
- Sujet : `Darwin's finches 2023 — request for the individual-level genotype/beak phenotype dataset`.
- Demande explicite du CSV `Darwins_finches_combined_genotype_calls.csv`, ou sous-ensemble autorisé incluant `specimen_id`, `genotype_sample_id`, `bill.length`, `bill.depth`, `bill.width`, origine génétique, assemblage et SNP ALX1/HMGA2 et fenêtres de même longueur.
- Demande expresse des correspondances nécessaires pour exclure toute réutilisation des 50 oiseaux de la cohorte Oslo 2025.
- **Aucune réponse ni pièce jointe Enbody reçue à l'heure de l'audit ; pas de suivi envoyé en doublon.**

## 2. Origines inspectées, résultats défavorables conservés

- Publication Enbody et al., *Science* 2023 (doi:10.1126/science.adf6218), cohorte publiée de 3 955 pinsons séquencés et 2 543 adultes avec mesures du bec. **Pas 2 543 couples indépendants authentifiés aujourd'hui**.
- Dépôt officiel de scripts `erikenbody/finch_4k_lowpass_code` : GitHub **PASS** en lecture, README et script R `Analysis_Code/06_phenotypic_data/plot_annual_pheno.R` inspectés. Ils désignent le fichier combiné `output/combined_genotypes/Darwins_finches_combined_genotype_calls.csv`.
- **FAIL HTTP 404** à la récupération via GitHub de ce chemin exact ; le fichier de synthèse phénotypique généré n'est pas non plus disponible à son chemin `output/...`.
- Zenodo DOI `10.5281/zenodo.8044096` mentionné par la publication ; **fichiers internes non accessibles/inspectés** dans les outils disponibles. Aucun contenu inventé.
- BioProject `PRJNA897926` : lectures brutes publiques, mais **pas** une table combinée de phénotypes et génotypes imputés prête à l'emploi.
- Environnement local : DNS Internet non disponible ; le navigateur complémentaire connecté a atteint son quota gratuit. Aucune dépense.

## 3. Porte d'admission conçue et testée localement

Une archive générée dans la conversation **ASTRA_DINO_ENBODY_VALIDATION_GATE_20261114.zip** contient :
`astra_dino_cohort_gate.py`, `test_cohort_gate.py`, `manifest_template.json`, `README.md`, `gate_negative.json`, `test_results.log`, `file_sha256.json`.

- Archive ZIP SHA-256 `485fd208d6f911e3ee37cbff32d6606d91d33d32cd7bd7e16f159e12b6d3fcfe`.
- Script Python SHA-256 `2be7ea95e34909e29f1ecebe75082a5fa541ff4e59c214fe20291e98b63be391`.
- **9/9 tests locaux synthétiques PASS** : source manifest/hashes, doublons, jointure 1:1, chevauchement avec les IDs Oslo, alias non attestés, assemblage incompatible, SNP HMGA2 non couvert, phénotype invalide, allèle REF muté.
- **Contrôle sur manifest non renseigné : FAIL_CLOSED**, retour `SOURCE_DOI_MISSING`.
- Code autonome standard library ; le compteur de variants couvre les intervalles nucléotidiques ALX1/HMGA2 et quatre fenêtres adjacentes sur `GCA_902806625.1`.
- **Limite :** les tests sont sur des fichiers **entièrement synthétiques** ; le code n'a PAS exécuté de validation scientifique sur une cohorte Enbody réelle. La vérité d'une attestation d'indépendance doit être vérifiée auprès de la source, elle ne peut être garantie automatiquement par un booléen de manifeste.

## 4. Verdict

| Critère | État | Preuve |
|---|---|---|
| Contact scientifique envoyé | **PASS** | Gmail SENT `1a1da64d5fc50993` |
| Fichier authentique Enbody obtenu | **FAIL / NOT_OBTAINED** | HTTP 404 GitHub + aucun autre fichier recevable |
| SHA-256 fichier Enbody | **UNVERIFIED** | aucun octet fourni |
| Appariement individuel | **UNVERIFIED** | fichier manquant |
| Non-chevauchement Oslo 2025 | **UNVERIFIED** | alias et ID non confrontés |
| Couverture ALX1/HMGA2 réelle dans Enbody | **UNVERIFIED** | VCF imputé indisponible |
| Contrôles logiciels synthétiques | **PASS LOCAL 9/9** | `test_results.log` dans l'archive de conversation |
| Nouvelle validation statistique indépendante | **NOT_EXECUTED** | zéro nouvel individu admis |

**Prochaine priorité unique :** réception de l'original ou d'un sous-ensemble Enbody autorisé puis audit rigoureux du manifeste, SHA, provenance, identifiants, absence de réutilisation et couverture de l'assemblage, *avant* tout modèle statistique. Aucune fusion, automatisation doublon, dépense ou secret révélé.
