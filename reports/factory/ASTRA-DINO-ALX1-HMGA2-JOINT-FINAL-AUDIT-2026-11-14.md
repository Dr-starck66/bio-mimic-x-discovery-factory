# ASTRA DINO Ω — ALX1/HMGA2 : audit réel et conclusion négative contrôlée
**Date :** 14 novembre 2026. **Branche isolée :** `astra/dino-omega-ancestry-benchmark-20261114`, PR #52. **Statut général : PARTIAL (exécution PASS, causalité/pouvoir prédictif UNVERIFIED).**

## 1. Sources authentifiées et conservation
- Dryad Lifjeld et al. 2025 (DOI https://doi.org/10.5061/dryad.3ffbg79w8), version 402749. Trois originaux transférés légalement via l'Université d'Oslo, dont le VCF 59 719 262 octets. Intégrité **3/3 PASS** par SHA-256 recalculés : `Morphometrics.txt`, `pPCAeigen.txt`, `Prun64_3miss2mafNoZ_1.vcf.gz`. Sommes complètes dans le JSON joint.
- Les **50** échantillons récents suivent la règle `SampleID → AccNo` confirmée par courriel par Jan Terje Lifjeld ; les **14** anciennes séquences SRA ne sont pas appariées à des mesures par convention inventée.
- **Sauvegardes durables vérifiées le 14 novembre 2026 après l'analyse initiale :** les trois fichiers originaux ont été retrouvés intacts dans la Bibliothèque ChatGPT, puis copiés vers un dossier privé dédié `ASTRA/BIO-MIMIC-X/ASTRA-DINO/OSLO-2025-ORIGINALS` et vers Google Drive connecté (`ASTRA Ω — Sources Project ChatGPT/BIO-MIMIC-X/ASTRA-DINO/OSLO-2025-ORIGINALS`). La lecture de retour depuis **chacun des deux stockages** a recalculé les trois empreintes SHA-256 officielles, **3/3 PASS par fournisseur** ; VCF 59 719 262 octets, en-tête de 64 échantillons confirmé. Un manifeste SHA-256 et une notice sont présents dans chaque sauvegarde. Les originaux et leurs copies de sauvegarde **ne sont pas publiés sur GitHub** ; le lien de transfert institutionnel reste confidentiel, expiration annoncée au **4 décembre 2026**. Cette vérification prouve la conservation et la relecture sur deux fournisseurs au moment du contrôle, pas une garantie absolue de pérennité.

**Mise à jour des échanges (14/11/2026, 16:45 UTC).** Jan Terje Lifjeld a confirmé par retour d'email que la publication de référence et son matériel supplémentaire sont ceux de Rubin et al., *Science Advances*, DOI `10.1126/sciadv.abm5982`. Cette réponse est cohérente avec l'assemblage déjà retenu ; elle ne fournit pas de nouveaux génotypes ni de nouvelle validation indépendante. Les fichiers originaux ont été récupérés et vérifiés lors d'une session antérieure du même jour (3/3 SHA PASS) : **ne plus qualifier cette étape de bloquée par Dryad**. Les octets n'ont pas été archivés durablement ; ne pas publier le lien privé FileSender.

## 2. Localisation ALX1 et HMGA2 — coordonnées exactes
**Assemblage unique :** Ensembl release 116 `Camarhynchus_parvulus_V1.1` / **`GCA_902806625.1`**, chromosome **1A**, coordonnées **1-based inclusives**.

| Gène examiné | Ensembl ID | Chromosome | Début | Fin | Nature de la preuve |
|---|---|---|---:|---:|---|
| ALX1 (orthologue de référence) | `ENSCPVG00000017961` | 1A | 40877644 | 40920855 | Gène sans symbole Ensembl, protéine `ENSCPVP00000027391.1` identique à **326/328 aa** avec ALX1 `Geospiza fortis` `XP_005421635.1` ; 37 peptides de 14 aa alignés au locus |
| HMGA2 | `ENSCPVG00000006117` | 1A | 33408202 | 33520236 | Nom et coordonnées présents dans le GTF Ensembl release 116 |

**L'annotation ALX1 est étayée par l'orthologie de séquence**, pas par un nom de gène explicite dans le GTF. Ce sont les **corps des gènes**, non les limites des haplotypes historiques de 240 kb / 525 kb.

## 3. Contrôle indépendant de l'ADN de référence
- L'assembly report NCBI associe le chromosome 1A à l'accession GenBank **`LR761574.1`** (taille attendue **72 438 334 bases**).
- Les séquences complètes de 1A téléchargées indépendamment depuis **ENA** et **Ensembl** sont identiques **base par base**, **0 discordance**, SHA-256 normalisé : `8f718d54d008f90f3d5075919a35a55354757d0b761d3a6313ae7b2772ed5803`.
- Un contrôle supplémentaire des **21 809** allèles REF du chromosome 1A dans le VCF donne **21 809/21 809** correspondances avec ce FASTA ; le contrôle décalé d'une base n'en donne que 4 666/21 809.
- La comparaison complète des **1 756 contigs** et l'identité octet par octet avec le fichier de travail local `C_parvulus_sm.fa` de l'équipe restent **UNVERIFIED** ; ne pas élargir la validation du chromosome cible à tout le génome.
- Le vérificateur de référence rejette une séquence mutée et un en-tête d'accession incorrect (**2 contrôles négatifs PASS**).

## 4. Scan VCF réel — mêmes individus, mêmes coordonnées
- **261 754** SNPs VCF ; **64** génotypes ; **50** échantillons avec mesures du bec via la règle auteur.
- Corps ALX1 : **9 SNPs** bialléliques, **6** avec fréquence mineure ≥ 5 % et ≥ 80 % de génotypes appelés dans le groupe de 50.
- Corps HMGA2 : **36 SNPs** bialléliques, **23** retenus sur les mêmes filtres.
- Mutation artificielle d'une base REF dans le chromosome : le moteur réel répond **`VCF_REF_FASTA_MISMATCH:1`** (**PASS rejet mutation**).

## 5. Modèle conjoint et contrôles défavorables
Méthode : un score PC1 génotypique **sans accès aux phénotypes** par locus, régression conjointe à deux scores après retrait des moyennes des 11 populations, **10 000 permutations de phénotypes appariés**, graines fixées. Critères exploratoires : `log(hauteur/longueur)` et `log(moyenne géométrique longueur × hauteur × largeur)`. Mesures biologiques et génotypes réellement observés ; les scores et endpoints sont des résumés statistiques, **pas des haplotypes fonctionnels prouvés**.

### Modèle primaire seulement
| Endpoint | R² résiduel | p corrigée sur 2 endpoints |
|---|---:|---:|
| Forme du bec | 0.1451 | 0.0851 |
| Taille du bec | 0.1845 | 0.0347 |

### Correction élargie après exploration des fenêtres voisines
| Modèle, endpoint taille | R² résiduel | p corrigée 2 endpoints du modèle | p corrigée globale **8 tests** |
|---|---:|---:|---:|
| Gènes ALX1 + HMGA2 | 0.1845 | 0.0347 | 0.0847 |
| Fenêtres gauches (même largeur) | 0.1765 | 0.0572 | 0.1005 |
| Fenêtres droites (même largeur) | 0.2877 | 0.0015 | 0.0084 |
| Gauche ALX1 + droite HMGA2 | 0.2871 | 0.0014 | 0.0086 |

**Conclusion négative :** après correction des **4 modèles × 2 endpoints**, le modèle initial ALX1+HMGA2 **ne franchit plus 5 %** pour la taille du bec (p = **0.0847**) ni pour la forme (p = **0.1847**). Les fenêtres droites conservent un signal plus fort (taille p globale = **0.0084**), mais ces fenêtres ne sont **pas indépendantes**, et le déséquilibre de liaison peut expliquer cette proximité ; aucune causalité génique précise démontrée.

**Contrôle de stabilité :** retrait successif de chaque population, 11/11 coefficients descriptifs HMGA2 de même signe, R² de taille compris entre **0.0952** et **0.2740**. Il ne s'agit **pas** d'une validation prospective externe.

## 6. Exécution, tests et limites
- **PASS** : téléchargements autorisés 3/3 SHA ; correspondance du chromosome entier ENA/Ensembl ; 21 809 allèles REF ; scan 9 + 36 SNP ; exécution Python code 0 ; **12/12 tests synthétiques**, mutation REF réelle rejetée ; contrôle source ENA mutée rejeté.
- **PARTIAL** : signaux statistiques exploratoires sur 50 oiseaux et 11 populations ; absence d'estimation robuste de haplotype causal, et pas de génome supplémentaire.
- **UNVERIFIED** : fonction biologique des SNPs, causalité ALX1/HMGA2, faisabilité de prédiction indépendante, validation sur autre cohorte, identité de tout le génome, validation CI GitHub/serveur.
- **Aucune** fusion sur main, aucun déploiement, aucune automatisation, aucune dépense ni email envoyé.

## 7. Reproduction et preuves conservées
- Auditeur primaire : `validation/astra_dino_alx1_hmga2_joint_real.py`
- Auditeur sensibilité : `validation/astra_dino_joint_flank_sensitivity.py`
- Contrôle double référence : `validation/astra_dino_reference_1a_crosscheck.py`
- Tests : `tests/test_astra_dino_alx1_hmga2_joint_real.py` (12 tests)
- Preuve primaire : `reports/factory/astra_dino_alx1_hmga2_joint_real_evidence_20261114.json`
- Preuve sensibilité incluant p globale 8 tests : `reports/factory/astra_dino_joint_flank_sensitivity_20261114.json`
- Preuve indépendante ENA/Ensembl : `reports/factory/astra_dino_reference_1a_ena_ensembl_20261114.json`

Les fichiers originaux sont volontairement exclus du contrôle de version **mais ont maintenant deux copies privées persistantes, avec vérification de relecture SHA-256 réussie**, dans ChatGPT Library et dans Google Drive. Les preuves JSON et scripts restent persistés sur la branche isolée. Le chemin de sauvegarde et le manifeste privés constituent la voie de reprise prioritaire ; ne pas redemander inutilement le transfert Oslo.

**Action scientifique prioritaire :** obtenir une **cohorte indépendante avec morphométrie et génotypes appariés**, puis définir a priori et valider les haplotypes complets sur GCA_902806625.1 avant tout nouvel essai prédictif. Aucun succès causal ou commercial n'est revendiqué.
