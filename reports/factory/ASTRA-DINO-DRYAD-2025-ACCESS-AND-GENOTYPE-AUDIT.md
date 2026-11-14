# ASTRA DINO Ω — audit d'accès aux données nucléaires des pinsons

**Date :** 14 novembre 2026. **Projet :** BIO-MIMIC X. **Objectif :** identifier les individus et déterminer les variants réellement présents dans les régions ALX1/HMGA2, sans inventer d'ADN, de position ou de résultat.

## Sources et intégrité

- Dépôt Dryad public CC0, DOI **10.5061/dryad.3ffbg79w8**, étude Lifjeld et al. (2025), *Weak sperm differentiation in Darwin's finches*.
- Fichiers de la version publiée du 20 octobre 2025 :
  - `Morphometrics.txt` — 5,30 Ko — URL officielle `https://datadryad.org/downloads/file_stream/4416574` — accès actuel HTTP **403**.
  - `pPCAeigen.txt` — 6,42 Ko — URL officielle `https://datadryad.org/downloads/file_stream/4416577` — accès actuel HTTP **403**.
  - `Prun64_3miss2mafNoZ_1.vcf.gz` — 59,72 Mo — URL officielle `https://datadryad.org/downloads/file_stream/4416598` — accès actuel HTTP **403**.
- Autre source évaluée : API Dryad v2 (`/api/v2/datasets/...`), page documentation accessible mais contenu de l'API inaccessible depuis les outils disponibles. Le navigateur d'agent connecté n'a pas pu être lancé, crédits du fournisseur insuffisants, **aucune dépense**.
- L'environnement local de calcul n'a pas d'accès réseau sortant ; le téléchargement direct échoue par résolution DNS.

## Métadonnées scientifiques vérifiées

L'étude a appelé **261 754 SNP bialléliques chez 64 oiseaux** : 50 échantillons nouveaux, 14 issus de SRA. Pour les premiers 50 seulement, le préfixe de six chiffres de `SampleID` de PCA représente `AccNo`, identifiant de la banque ADN du musée d'histoire naturelle d'Oslo. Les 14 autres ne doivent pas être rapprochés par une convention inventée.

Les trois fichiers ne sont **pas récupérés**. Par conséquent :

- **Identifiants individuels vérifiés sur les fichiers : 0** (absence de données lisibles, pas preuve d'absence d'appariements).
- **Variants ALX1 identifiés dans le VCF Dryad : UNVERIFIED**, **variants HMGA2 : UNVERIFIED** (ne pas afficher « 0 variant »).
- **Analyses SNP↔bec : NON EXÉCUTÉES**. Les scores de tests synthétiques ne constituent pas de résultats scientifiques.
- Assemblage de référence confirmé par Rubin et al. (2022) et le protocole 2025 : **Camarhynchus_parvulus_V1.1, GenBank GCA_902806625.1** ; ALX1 et HMGA2 associés au **chromosome 1A** dans cette étude, séparés d'environ 7 Mb. Les coordonnées exactes contig+début+fin de la bonne version ne sont pas ici établies.
- Les loci haplotypiques publiés couvrent environ 240 kb (ALX1) et 525 kb (HMGA2) : la portée de l'étude n'est **pas** limitée aux exons codants. Une annotation de gène seule ne couvre pas nécessairement ces régions.

## Outil livré

- `validation/astra_dino_dryad2025_audit.py` : lecture sûre des tables, reconnaissance des candidats `SampleID`/`AccNo` **non déclarés validés indépendamment**, lecture stream VCF gzip, vérification de référence et de contigs, comptage SNP bialléliques sur intervalles **strictement appariés** à GCA_902806625.1, sortie JSON avec SHA-256 des fichiers fournis.
- `tests/test_dryad2025_audit.py` : 11 tests standards Python **PASS LOCAL**, y compris CLI et refus des génomes ou intervalles incompatibles. Données de test entièrement synthétiques et identifiées comme telles.
- Un fichier d'intervalles **réels et sourcés** est indispensable à la phase SNP. Aucune coordonnée réelle n'est inventée. Les coordonnées de test sont fictives.

### Commandes reproductibles (une fois les données présentes)

```bash
python -m unittest discover -s tests -v
python validation/astra_dino_dryad2025_audit.py \
  --morph Morphometrics.txt \
  --pca pPCAeigen.txt \
  --vcf Prun64_3miss2mafNoZ_1.vcf.gz \
  --intervals ALX1_HMGA2_GCA_902806625.1_VERIFIED.json \
  --output evidence.json
```

**Le script doit rester bloqué tant que la correspondance d'assemblage et les deux intervalles réels ne sont pas vérifiés.**

## Statuts

| Contrôle | Statut | Preuve |
| --- | --- | --- |
| Métadonnées de 2025 et DOI | PASS | Dryad + article publié |
| Assemblage GCA_902806625.1 | PASS | Rubin 2022, Lifjeld 2025 |
| Téléchargement des fichiers originaux | FAIL/ACCESS_BLOCKED | liens officiels HTTP 403, local sans DNS |
| Code de lecture et garde-fous | PASS local | 11/11 tests Python |
| Appariements d'individus originaux | UNVERIFIED | fichiers indisponibles |
| SNP dans ALX1/HMGA2 du VCF Dryad | UNVERIFIED | fichier et intervalles indisponibles |
| Modèle prédictif nucléaire | UNVERIFIED | aucun apprentissage réel |

**Action prioritaire** : accès normal autorisé aux trois fichiers originaux, suivi de l'obtention des coordonnées du chromosome 1A strictement sur GCA_902806625.1 ; pas de remappage approximatif, pas de contournement d'authentification, pas de dépense sans accord.

**Références :** https://doi.org/10.5061/dryad.3ffbg79w8 ; https://doi.org/10.1093/biolinnean/blaf103 ; https://doi.org/10.1126/sciadv.abm5982 ; https://datadryad.org/api .