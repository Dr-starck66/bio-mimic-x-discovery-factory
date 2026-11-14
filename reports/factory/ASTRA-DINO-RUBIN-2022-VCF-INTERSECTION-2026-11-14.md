# ASTRA DINO Ω — confrontation réelle du VCF Oslo avec contrôles sur 1A

**Date :** 2026-11-14 · **Statut : PARTIAL** · **Coût supplémentaire : 0 €**

## Résultat exécuté sur les fichiers originaux

Le VCF Oslo `Prun64_3miss2mafNoZ_1.vcf.gz` (59 719 262 octets), `pPCAeigen.txt` et `Morphometrics.txt` ont été **retrouvés dans une sauvegarde privée ChatGPT Library**, materialisés dans l'environnement de calcul et confrontés à leurs SHA-256 officiels : **3/3 PASS**.

Le scan Python a lu **261 754** lignes de variants, dont **21 809** sur le chromosome `1A` de l'assemblage `Camarhynchus_parvulus_V1.1` / `GCA_902806625.1` ; **64** génotypes au total, dont **50** appariés à des mesures de bec par la règle `SampleID → AccNo` documentée par Jan Terje Lifjeld. Les 14 autres ne sont pas associés de force à une morphométrie.

**Ces bornes proviennent de l'annotation génique déjà validée par Ensembl 116 et non des haploblocs de Rubin 2022.** Contrôles à coordonnées **1-based inclusives** :

| Zone sur chromosome 1A | Début–fin (1-based) | VCF tous variants | SNP bialléliques | SNP passant MAF ≥5 % et call rate ≥80 % chez 50 oiseaux |
|---|---:|---:|---:|---:|
| HMGA2 gauche, largeur égale | 33 296 167–33 408 201 | 35 | 35 | 18 |
| HMGA2 corps du gène | 33 408 202–33 520 236 | 36 | 36 | 23 |
| HMGA2 droite, largeur égale | 33 520 237–33 632 271 | 39 | 39 | 27 |
| ALX1 gauche, largeur égale | 40 834 432–40 877 643 | 8 | 8 | 5 |
| ALX1 corps du gène | 40 877 644–40 920 855 | 9 | 9 | 6 |
| ALX1 droite, largeur égale | 40 920 856–40 964 067 | 14 | 14 | 6 |

Les six nombres de variants ont été recalculés **indépendamment** par tri des 21 809 positions 1A et recherche des bornes par `bisect_left/bisect_right` ; **6/6 correspondances exactes**, sans utiliser les compteurs du premier auditeur.

## Source Rubin 2022 / Data S2 — état réel

**Publication authentifiée :** Rubin et al., *Science Advances*, 8:eabm5982 (2022), DOI `10.1126/sciadv.abm5982` : <https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/>. L'article décrit **28 loci** d'haplotypes ancestraux ; leur tableau est dans `Data S2` du supplément officiel `sciadv.abm5982_sm.pdf`. Les régions ALX1 et HMGA2 sont sur **1A**, séparées par une zone de forte recombinaison. Ces 28 loci ne sont **pas** des intervalles égaux aux corps des gènes.

**Blocage documenté :** le fichier PDF supplémentaire d'AAAS/PMC n'a pas été accessible par les canaux gratuits de cette session (AAAS renvoie HTTP 403 ; PDF PMC inaccessible au service web ; environnement local sans résolution DNS). Il n'existe donc **aucun SHA-256 vérifié de Data S2**, **aucune coordonnée officielle importée**, **aucun nombre de SNPs certifié dans les haploblocs Rubin**. Le champ de résultat est explicitement `BLOCKED_AUTHENTIC_INTERVAL_BOUNDS_UNAVAILABLE` et non `PASS`. Ne pas substituer les bornes géniques.

## Reproductibilité et contrôle de refus

- Auditeur : `validation/astra_dino_rubin2022_vcf_intersection.py`.
- Tests : `tests/test_astra_dino_rubin2022_vcf_intersection.py` : **11/11 PASS** (fixtures synthétiques, erreurs de provenance, coordonnées inclusives, SNP MAF et appels manquants).
- Trace sans données individuelles : `reports/factory/astra_dino_rubin2022_oslo_vcf_intersect_20261114.json`.
- L'auditeur **rejette** une source Data S2 absente, un assemblage discordant, une signature PDF incorrecte, un hash de PDF manquant/non vérifié ou des bornes invalides. **Une correspondance SHA-256 garantit l'identité au PDF fourni, pas à elle seule son authenticité éditoriale** : avant le passage scientifique `PASS`, la provenance AAAS/PMC et les lignes de Data S2 devront être contrôlées.

### Rejeu sur originaux autorisés, sans exposer le VCF

```bash
python -m unittest discover -s tests -p 'test_astra_dino_rubin2022_vcf_intersection.py' -v
python validation/astra_dino_rubin2022_vcf_intersection.py \
  --oslo-dir /chemin/prive/OSLO-2025-ORIGINALS \
  --output reports/factory/astra_dino_rubin2022_oslo_vcf_intersect_20261114.json
```

Une fois le PDF officiel récupéré et contrôlé, créer un manifeste manuellement validé avec `source_doi`, `source_pdf_url`, `source_pdf_sha256`, `assembly`, `coordinate_convention`, `evidence_kind` et `intervals`, puis ajouter `--data-s2-manifest` et `--data-s2-source-pdf` à la commande. **Ne pas déclarer l'authenticité d'une simple table recopiée sans vérification du PDF d'origine.**

## Conclusion scientifique

Le VCF Oslo a réellement été réexaminé et les variants voisins recensés, mais aucune nouvelle association statistique ni causalité ne sont revendiquées. Une étape demeure essentielle : récupérer les vrais intervalles de `Data S2`, puis mesurer leur couverture par les 21 809 variants de 1A et évaluer LD/variants sans modifier le seuil pour rendre artificiellement un résultat positif. À plus long terme, seule une cohorte indépendante avec génotypes et morphométrie individuels permettra la validation prédictive.

**Protection :** aucun fichier individuel original, lien FileSender ni table contenant des identifiants privés n'est publié dans les artefacts ou le dépôt.