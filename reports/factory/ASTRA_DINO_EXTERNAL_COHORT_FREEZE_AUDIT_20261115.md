# ASTRA DINO Ω — audit de disponibilité d'une cohorte externe et modèle prédictif figé

**Date du gel :** 2026-11-15. **Coût supplémentaire : 0 €.**

**STATUT : PARTIAL** — le modèle est entraîné et son protocole est figé avant l'utilisation de toute donnée de validation externe ; **aucune cohorte externe appariée n'a encore été vérifiée**, aucune performance externe n'est démontrée. Les tests sur données synthétiques ne sont pas une validation scientifique.

## Origine du modèle verrouillé

- Cohorte entraînement : Oslo 2025 Dryad DOI `10.5061/dryad.3ffbg79w8`, originaux privés (VCF compressé + 2 tables), empreintes vérifiées par les validateurs déjà audités.
- `GCA_902806625.1` ; 50 spécimens possédant chacun des génotypes et des mesures individuelles, sur 11 populations.
- Intervalles Rubin 2022 identiques au fichier public original (`data/astra_dino_rubin2022_28loci_author_original.txt`, `Git blob dc6ec1da23aa6426fcc16dc5b5d1124d55699616`).
- Locus 3 HMGA2 : 394 SNP ; locus 7 ALX1 : 238 SNP ; total 632 SNP distincts.
- Standardisation/ imputation par la moyenne **Oslo uniquement** ; deux composantes PCA génétiques par bloc ; orientation déterministe des vecteurs propres ; modèle ridge `lambda=10` fixé sans voir la validation externe. Le modèle conjoint dispose de quatre composantes d'entrée.
- Les variables sont explicitement réordonnées `taille = (ln L + ln H + ln W)/3` en premier puis `forme = ln(H/L)` ; correction d'un risque réel d'inversion détectée à l'audit du script Oslo.
- Référence de prédiction : moyenne des phénotypes de la seule cohorte Oslo, figée. Les prédictions sont comparées par **gain relatif de MSE sur cette référence**.
- Critère principal préspécifié avant consultation de toute cohorte indépendante : gain MSE strictement positif pour la **taille** sous le modèle conjoint, et *p* unilatérale ≤ 0,05 lors de 20 000 permutations de libellés à l'intérieur de clusters de validation. Les trois modèles × deux phénotypes constituent six comparaisons secondaires corrigées par Holm (contrôle FWER).
- Critères d'entrée : ≥30 spécimens strictement indépendants d'Oslo, ≥5 clusters de validation, correspondance exacte échantillon VCF → spécimen → mesures, assemblage et allèles REF/ALT concordants, ≥80 % des 394 SNP HMGA2 et ≥80 % des 238 SNP ALX1, taux d'appels par variant apparié ≥80 %. Aucun alignement approximatif ou inversions d'allèle tacites.

**Modèle privé SHA-256 :** `4e2d80b60dde9906442856af26f218b16cfd0804370764e2ec17e207b6dcf18c` ; `106658 octets` ; le modèle privé comprend les paramètres appris et des empreintes d'identifiants, **ne pas le publier sur GitHub**.

**Source auditeur SHA-256 :** `491a40322512a43beae31654495dda69c4cdc8307b7a23f7331ef2379e4f226d`.

## Candidats indépendants examinés

### 1. Enbody et al. (2023) — PRIORITÉ D'ACQUISITION, accès non démontré

- *Science*, 2023, DOI `10.1126/science.adf6218`, 3 955 pinsons de Daphne Major, génomes + étude morphologique.
- Code d'analyse des auteurs : <https://github.com/erikenbody/finch_4k_lowpass_code>, notamment `Analysis_Code/01_GEMMA/plot_locus_pheno_correlations.R`, qui ouvre `output/combined_genotypes/Darwins_finches_combined_genotype_calls.csv` et étudie des mesures individuelles de bec.
- **Ce fichier de données n'est pas présent dans l'arborescence publique du dépôt du code inspectée.** Il ne faut pas considérer la présence d'un chemin dans le script comme la possession des octets ou d'un croisement vérifié d'identifiants.
- Deux demandes de données déjà envoyées à Erik Enbody le 14 novembre 2026 ; la recherche des réponses sur les comptes Gmail connectés n'a trouvé aucune réponse de cet auteur pour le moment. **Ne pas relancer en doublon.**
- Espèces `Geospiza` contre `Camarhynchus` dans Oslo : transfert inter-genre à haut risque de distribution ; l'alignement des variants homologues doit être démontré, pas supposé.

### 2. Sebastianelli Arbelaez et al. (2026) — FAIL pour validation individuelle à ce stade

- *Nature Communications*, publication du 11 octobre 2026, DOI `10.1038/s41467-026-78507-8` ; code <https://github.com/MatteoSebastianelli/Tree_finches> ; archive déclarée Figshare DOI `10.6084/m9.figshare.30284983`.
- **77 individus Camarhynchus génomiques** parmi 415 pinsons séquencés, mais mesures morphologiques de **348 spécimens de musée** traitées dans un autre échantillon. La publication ne fournit pas, sur les éléments vérifiés, un lien individuel certifié entre ces mesures de musée et les génotypes. Les 415 génomes réutilisent largement d'anciens séquençages, seuls deux C. psittacula ayant été ajoutés à cette étude : toute tentative de validation doit exclure les recouvrements avec Oslo et d'autres panels de formation.
- Figshare : enregistrement cité par les auteurs, mais fichiers binaires non vérifiés dans cette session. Statut `NO_VERIFIED_1_TO_1_JOIN` ; pas de création de correspondances espèces/individus fictives.

### 3. Santa Cruz et autres morphométries — CONTRÔLE NÉGATIF

- La présence de milliers de mesures individuelles n'est pas suffisante : elles doivent appartenir **aux mêmes oiseaux** que les lignes d'un VCF indépendant. Aucun appariement individuel vérifié actuellement.

## Tests réellement effectués

1. **PASS — entraînement local** sur les 3 originaux Oslo, avec assertions des 394 / 238 variants.
2. **PASS — modèle gelé reproductible :** deux exécutions consécutives produisent exactement le même SHA-256 `4e2d80...18c`.
3. **PASS — 17/17 tests unitaires** : DOI/assemblage invalide, doublons, fuite Oslo, spécimen réutilisé, effectif insuffisant, tests statistiques négatifs et positifs purement synthétiques, PCA non supervisée, dimensions morphologiques invalides, et cluster insuffisant.
4. **PASS — test complet purement SYNTHÉTIQUE**, 30 faux oiseaux, 5 faux clusters, 632 fausses lignes SNP construites selon le fichier de marqueurs, et 20 000 permutations : `PASS_EXTERNAL_EXECUTION__PRIMARY_HYPOTHESIS_NOT_CONFIRMED`, sans gain de prédiction. **Ce test ne constitue absolument pas une cohorte indépendante réelle.**
5. **UNVERIFIED — cohorte externe réelle** : aucun VCF indépendant + table de morphométrie avec preuve d'appariement + provenance n'a été obtenu. **Aucun score externe réel, aucune confirmation biologique.**

## Protocole d'exécution lorsqu'une cohorte réelle est accessible

Le code et les empreintes du script sont épinglés dans `frozen_external_model_manifest.json` et dans la branche scientifique GitHub, avant consultation de la validation externe. Le modèle entraîné est conservé séparément dans le dossier privé ASTRA.

```bash
OPENBLAS_NUM_THREADS=1 python validation/astra_dino_external_locked.py --mode validate \
  --model /DOSSIER_PRIVE/frozen_oslo_transfer_v1.json \
  --preregistration reports/frozen_external_model_manifest.json \
  --external-vcf /SOURCE_EXTERNE/independent.vcf.gz \
  --phenotypes /SOURCE_EXTERNE/individual_beaks.tsv \
  --provenance /SOURCE_EXTERNE/evidence.json
```

L'exécuteur **refuse** le modèle modifié, l'inversion d'une variable, un assemblage discordant, les pièces d'appariement manquantes, les échantillons d'Oslo et les variants insuffisamment concordants. Les identifiants externes bruts, la matrice de génotypes et les phénotypes ne sont pas imprimés ni transférés vers GitHub ; seules des mesures agrégées et empreintes de fichiers le sont.

## Interprétation et décision

Les tests Oslo antérieurs portaient sur des R² de formation, correction maxT sur 58 comparaisons, et ont échoué à établir une association corrigée de 5 %. Le protocole de transfert est **nouveau et préspécifié seulement maintenant**, après des analyses exploratoires antérieures sur Oslo ; il ne doit pas être présenté comme une préinscription antérieure à toute recherche.

La validation future doit aussi évaluer l'effet des liens de parenté entre oiseaux et le décalage de distribution entre espèces/cohortes. Un éventuel gain prédictif ne démontre ni causalité génétique ni reconstruction de l'ADN d'espèces fossiles.

**Action scientifique suivante unique :** obtenir le véritable tableau apparié individuel (génotypes + bec + provenance/année/identifiant) d'Enbody/Daphne Major, vérifier SHA-256 et exclusion de tout recouvrement avec Oslo ; ensuite seulement déclencher le script gelé. **Statut scientifique actuel : PARTIAL.**
