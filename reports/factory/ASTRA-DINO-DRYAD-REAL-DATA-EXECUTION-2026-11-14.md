# ASTRA DINO Ω — Exécution sur les originaux Dryad 2025 (14 novembre 2026)

**Projet :** BIO-MIMIC X / ASTRA DINO Ω, PR #52.  
**Statut global : PARTIAL** (intégrité des fichiers PASS ; exécution de l'auditeur PASS ; preuve d'association génétique UNVERIFIED).  
**Aucune fusion, aucun paiement, aucune automatisation, aucun partage de lien d'accès temporaire.**

## Provenance et intégrité — 3/3 PASS

Fichiers obtenus par le lien FileSender explicitement envoyé par l'Université d'Oslo, confirmé dans Gmail le 14/11/2026. Référence officielle Dryad DOI `10.5061/dryad.3ffbg79w8`, version 402749. Les octets ont été téléchargés dans une **session de calcul distante temporaire**, puis les SHA-256 ont été **recalculés** et comparés au manifeste du dépôt.

| Fichier | Taille locale vérifiée (octets) | SHA-256 recalculé | Résultat |
|---|---:|---|---|
| Morphometrics.txt | 5295 | 4722f565feeda8290d3985b4a65d9e0c4e91690270264cfc931d26f24cc51555 | PASS |
| pPCAeigen.txt | 6421 | d615bd8dd3fd22091b971b20f18a49832d1f2afaf390a30ea3465f6a276b5bff | PASS |
| Prun64_3miss2mafNoZ_1.vcf.gz | 59719262 | 471db73a5eb65a8bb6af8f25872a5a2d0bc0115556203250f69eb61988163d34 | PASS |

**Attention :** les trois gros/petits originaux n'ont pas été versés dans le dépôt GitHub ni dans un stockage persistant. Leur présence après fermeture de la session distante n'est pas garantie. Le lien autorisé d'origine expire le 04/12/2026 et doit rester dans Gmail.

## Exécution réelle de l'auditeur existant

Script Python téléchargé de la branche `astra/dino-omega-ancestry-benchmark-20261114` :
`validation/astra_dino_dryad2025_audit.py`.

Commande exécutée en Python 3 dans la session distante :

```bash
python3 /tmp/astra_dino_dryad2025_audit.py \
  --morph /tmp/Morphometrics.txt \
  --pca /tmp/pPCAeigen.txt \
  --vcf /tmp/Prun64_3miss2mafNoZ_1.vcf.gz \
  --output /tmp/astra_dino_real_data_evidence.json
```

- Code de sortie : **0** ; stderr vide ; temps constaté : **1,26 s**.
- SHA-256 du rapport JSON d'exécution : `e8476f9be46489f9fff64d2b926922f9175ad1b0905d8de71b8e3343a3e0f08e`.
- `morphology.raw_rows=106`, `valid_six_digit_unique=106`, `rejected_rows=0`.
- `pca_entries=64` ; `vcf_samples=64` ; `observed_vcf_records=261754`.
- `candidate_pairs=50` ; `independently_verified_pairs=0` selon le garde-fou du script ; 14 échantillons SRA sans correspondance individuelle automatique ; 0 VCF sample absent de PCA.
- La correspondance des 50 nouveaux génomes par `SampleID` a été confirmée dans un courriel par le Pr Jan Terje Lifjeld ; le logiciel ne la qualifie toujours pas d'appariement indépendant définitif.
- VCF `##reference=file://C_parvulus_sm.fa`, et non accession formellement versionnée ; l'auditeur affiche `HEADER_ONLY_NO_INTERVALS`. **Aucun nombre de SNP ALX1/HMGA2 n'a été attribué par le script officiel.**

## Contre-vérification d'assemblage et observation indépendante HMGA2

Source indépendante : Ensembl REST, assemblage `Camarhynchus_parvulus_V1.1` / `GCA_902806625.1`, endpoint `/info/assembly/camarhynchus_parvulus`, et `/lookup/symbol/camarhynchus_parvulus/HMGA2`.

- **Dictionnaire exact : 1 756/1 756 contigs** — mêmes noms et longueurs pour VCF et assemblage Ensembl ; aucun contig supplémentaire ni manquant. Cela démontre une correspondance structurelle, pas une identité nucléotidique bit-à-bit avec le FASTA original.
- Référence Ensembl HMGA2 : `ENSCPVG00000006117`, chromosome `1A`, intervalle **33 408 202–33 520 236**, 1-based fermé, longueur **112 035 bp**.
- Le VCF comporte **21 809 variants sur le chromosome 1A**.
- Un balayage indépendant, en lecture seule, des 261 754 enregistrements donne **36 SNP bialléliques dans le corps du gène HMGA2** (pas les 525 kb de l'haplotype publié).
- Contrôles descriptifs de même largeur, immédiatement adjacents : **35 SNP à gauche** et **39 SNP à droite**. Ces témoins géographiques ne constituent PAS des contrôles négatifs d'association génétique.
- Sur les **64 échantillons × 36 positions** : **2 211 génotypes appelés** et **93 manquants** selon la reconnaissance GT (pas un test d'association ni un filtre de qualité complet).
- Les SNPs HMGA2 restent **observations exploratoires** tant que le FASTA `C_parvulus_sm.fa` exact n'est pas comparé au référentiel versionné au niveau des bases et que le jeu d'intervalles des haplotypes n'est pas revu indépendamment.

## ALX1 : résultat négatif de vérification, pas absence de SNP

Ensembl REST `lookup/symbol/camarhynchus_parvulus/ALX1` n'a pas renvoyé d'annotation exploitable. **Aucun intervalle ALX1 vérifié sur cette version précise** n'a été obtenu. Ne jamais transformer ce manque d'annotation en résultat « zéro SNP ». Le test de l'haplotype ALX1 est **UNVERIFIED**.

## Audit des conclusions

- **PASS :** récupération autorisée dans une session distante ; 3/3 octets/intégrités ; programme Python lancé avec les originaux ; 261 754 enregistrements.
- **PASS (structure seulement) :** dictionnaires de 1 756 contigs strictement identiques au référentiel Ensembl.
- **PARTIAL :** 50 candidats génotype–morphologie ; balayage descriptif du corps du gène HMGA2.
- **UNVERIFIED :** identité nucléotidique complète du FASTA de référence ; intervalle/haplotype ALX1 ; test combiné ALX1/HMGA2 ; association causale, validation prédictive indépendante, phénotype fossile.
- **Dépôt :** ce rapport de preuve seulement, sans originaux, secrets, ni lien FileSender.

**Action prioritaire :** identifier un intervalle ALX1 source-pinné sur GCA_902806625.1 et confirmer l'identité du FASTA originel afin de préparer un auditeur conjoint strict sans changer rétrospectivement les règles d'acceptation.
