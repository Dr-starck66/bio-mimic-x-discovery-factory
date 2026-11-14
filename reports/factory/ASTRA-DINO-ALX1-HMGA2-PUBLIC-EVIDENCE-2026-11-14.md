# ASTRA DINO Ω — ALX1/HMGA2 : preuve nucléaire et audit des données ouvertes

**Date** : 14 novembre 2026. **Projet existant** : BIO-MIMIC X / PR #52, branche `astra/dino-omega-ancestry-benchmark-20261114`. Zéro dépense supplémentaire, pas d'automatisation, pas de fusion.

## 1. Résultat nucléaire réellement calculé

Six séquences protéiques RefSeq issues des réponses FASTA de **NCBI E-utilities** (`db=protein`), chacune contrôlée contre l'accession versionnée, l'espèce et la description protéique. Empreintes d'identité exactes calculées par comparaison positionnelle de séquences de longueur identique : 

| Locus | Espèce | Accession | Acides aminés |
|---|---|---|---:|
| ALX1 | Geospiza fortis | XP_005421635.1 | 328 |
| ALX1 | Taeniopygia guttata | XP_002196043.1 | 328 |
| ALX1 | Gallus gallus | XP_040516271.1 | 328 |
| HMGA2 | Geospiza fortis | XP_030911403.1 | 109 |
| HMGA2 | Taeniopygia guttata | XP_004176139.1 | 109 |
| HMGA2 | Gallus gallus | NP_990332.1 | 109 |

**Comparaisons exactes** :
- ALX1, Geospiza–Taeniopygia : **324/328 = 98,7805 %** ; Geospiza–Gallus et Taeniopygia–Gallus : **317/328 = 96,6463 %**.
- HMGA2, Geospiza–Taeniopygia : **109/109 = 100 %** ; Geospiza–Gallus et Taeniopygia–Gallus : **106/109 = 97,2477 %**.

**Contrôle négatif conceptuel** : le même HMGA2 RefSeq est codé par exactement la même séquence protéique chez les deux passériformes comparés, alors que leurs becs diffèrent. Une séquence protéique hautement conservée ne permet donc pas, seule, de déduire une forme ou une dimension de bec. Le contexte évolutif, les variants non codants, la régulation, le développement et les autres loci importent. Ce n'est **pas** une preuve d'identité de leurs haplotypes génomiques.

Données originales avec séquences : `data/astra_dino_alx1_hmga2_protein_refs_20261114.json`. Calcul de contrôle : `validation/astra_dino_nuclear_audit.mjs`. Tests : `tests/test_astra_dino_nuclear_audit.mjs` (**6/6 PASS en exécution Node locale avant publication**).

## 2. Pourquoi il faut étudier les haplotypes complets

- Nature 2015 (doi:10.1038/nature14181) : région **ALX1 d'environ 240 kb**, associée à la **forme** du bec chez les pinsons, y compris variation intraespèce de Geospiza fortis.
- Science 2016 (doi:10.1126/science.aad8786) : région **HMGA2 d'environ 525 kb** associée à la **taille** du bec ; région également liée à MSRB3, LEMD3 et WIF1. SNP diagnostique de l'étude : scaffold **JH739900**, base **7 003 776**, assemblage de l'étude, **pas transposable** sur GeoFor_1.0 sans table de correspondance. Le chiffre de 27 % de variance phénotypique expliqué dans la population étudiée est une **estimation publiée**, non recalculée ici.
- Genome Research 2017 (doi:10.1101/gr.212522.116) : haplogroupes anciens, recombinaison faible et flux de gènes ; la simple mutation de la protéine ne représente pas le locus fonctionnel entier.

## 3. Trois ressources publiques identifiées — accès réel strictement distingué

| Dépôt | Contenu confirmé | Situation |
|---|---|---|
| SRA BioProject PRJNA263122 | Lectures du séquençage des pinsons, source Nature 2015 | **METADATA_CONFIRMED**, non retraitées |
| Dryad DOI 10.5061/dryad.7155d | VCF `Sample_GT_1.vcf.gz` 264,78 MB (2018) ; `111_sample.vcf.gz` 393,09 MB (2021) ; notices et README | **METADATA_CONFIRMED**, VCF non lu ; téléchargement direct protégé |
| Dryad DOI 10.5061/dryad.3ffbg79w8 | `Morphometrics.txt` 5,30 KB : AccNo / dimensions bec individuelles ; `pPCAeigen.txt` 6,42 KB ; `Prun64_3miss2mafNoZ_1.vcf.gz` 59,72 MB, SNPs de 64 oiseaux (50 nouveaux + 14 SRA), origine 2025 | **CROSSWALK_METADATA_CONFIRMED** ; table et VCF non téléchargés (protection de la page) |

**Point décisif du dépôt 2025 :** l'identifiant `AccNo` appartient à la banque ADN du Museum of Natural History d'Oslo ; selon la documentation, les six premiers chiffres du `SampleID` dans le fichier PCA correspondent aux individus du jeu de 50 séquences nouvelles. Ceci permet de définir *une procédure de correspondance à vérifier*, pas d'affirmer qu'un VCF a été effectivement apparié.

Le test d'appariement `phenotypeGenotypeCrosswalk` **refuse** toute association sans table d'IDs indépendante, ainsi que les doublons, les mesures manquantes et les associations inventées. Il a été éprouvé sur des fixtures synthétiques ; aucun nombre de paires véritables n'a été revendiqué.

**Portée scientifique** : les VCF de 2025 pourraient être utiles pour des analyses SNP–morphologie, sous réserve d'annoter leurs contigs et de confirmer la présence des deux régions ALX1/HMGA2 dans l'assemblage *Camarhynchus parvulus* employé. **Aucune présence de variants ALX1/HMGA2 n'est prouvée** à ce stade.

## 4. Tests et limites

- **PASS** : source NCBI, séquences versionnées et comparaisons 6 protéines / 6 paires, résultat source-pinned.
- **PASS LOCAL** : 6 tests Node (références, erreurs, absence de correspondance et refus de doublons). Les séquences comparées par l'auditeur local simulé ne constituent pas une exécution complète des FASTA par le module GitHub ; les calculs FASTA ont été exécutés séparément via connecteur.
- **PARTIAL** : couplage individuel génotype↔bec — fichiers ciblés et contrat strict définis, mais valeurs réellement appariées **NON LUES**.
- **UNVERIFIED** : effet indépendant d'ALX1/HMGA2 sur des échantillons tenus à l'écart et toute prédiction de morphologie fossile par ces gènes.
- **UNVERIFIED** : reproductibilité sur CI/runner externe du commit publié.
- **Aucun génome non avien**, pas de séquence fonctionnelle de dinosaure éteint ni de résurrection.

## 5. Action prioritaire reproductible

Obtenir un accès autorisé et sûr aux *petits* fichiers publics Dryad 2025 (`Morphometrics.txt`, `pPCAeigen.txt`) et au VCF pour un environnement de traitement à distance ; verrouiller ensuite les correspondances `SampleID`↔`AccNo`, puis déterminer sur l'assemblage exact si des SNP couvrent réellement ALX1/HMGA2. Refuser toute affirmation d'effet si les régions sont absentes ou les identifiants ambigus.

Sources : https://doi.org/10.5061/dryad.3ffbg79w8 ; https://doi.org/10.5061/dryad.7155d ; https://doi.org/10.1038/nature14181 ; https://doi.org/10.1126/science.aad8786 ; https://doi.org/10.1101/gr.212522.116 .
