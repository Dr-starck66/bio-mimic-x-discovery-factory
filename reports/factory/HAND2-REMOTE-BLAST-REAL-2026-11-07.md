# BIO-MIMIC X — premier BLAST distant exécuté, 2026-11-07

## Source primaire exécutable

- GitHub Actions run **42332994348** : https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/42332994348
- Commit exécuté : `54774ee96cb0c945eb443d2a0933531ac2932e84`.
- Job `remote-blast` : **SUCCESS** ; résultat scientifique **PARTIAL**, et non PASS d'unicité.
- Artefact ZIP **13558263350** : https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/42332994348/artifacts/13558263350
- Empreinte SHA-256 du ZIP GitHub : `ea357fb1450c544d40fa9421d635cbf5153779317af2b1a0f753c961c1607ddd`.
- Le ZIP contient deux FASTA, deux XML BLAST réellement retournés, et `manifest.json`. XML analysés avec `xml.etree.ElementTree`, non inférés du statut CI.

## Résultats des deux requêtes indépendantes

| Mesure | Historique chr6q | RefSeq moderne |
|---|---:|---:|
| Intervalle | CM010938.2:884794726-884799066 | NC_090937.1:910028725-910032936 |
| Longueur requête | 4341 nt | 4212 nt |
| RID NCBI | EX5UUX0H016 | EX5VUSWC014 |
| SHA-256 XML | f7299ea48e38a0016f462ac76a8e5f8a8cca0fda3ccfe16701887a7fd35aa49e | d56bce9e4356cdd5f8c251ef4a2e4fe2f195ec94a21297d67d2d9b17a4ecb27e |
| Base réellement annoncée dans XML | core_nt | core_nt |
| Nombre de hits | 9 | 9 |
| Meilleur hit | XM_069631422, HAND2 mRNA | XM_069631422, HAND2 mRNA |
| HSP HAND2 | 2 | 2 |
| Bases de requête couvertes par HSP HAND2 | 2006 / 4341 (46.21 %) | 2007 / 4212 (47.65 %) |
| Identités / colonnes des HSP HAND2 | 2004 / 2007 (99.8505 %) | 2007 / 2007 (100 %) |
| Hit contrôle HAND1 | XM_069653976, 170/205 identités | XM_069653976, 170/205 identités |

Autre hit HAND2 : `KU882016`, mRNA partiel. Les autres hits incluent TCF15, PTF1A, NEUROG1, TCF21 et deux variants scleraxis-like. Les deux requêtes classent le transcrit HAND2 au premier rang parmi les **9 hits retournés**.

**Interprétation :** premier BLAST distant réellement exécuté avec deux RID et XML, concordance positive avec HAND2 et contrôle HAND1 plus faible sur ces régions. **Ce n'est PAS une preuve d'unicité génomique :** la base effective `core_nt` contient ici des hits de transcrits, la couverture des requêtes par les HSP du meilleur transcrit est inférieure à 50 %, et l'exhaustivité de l'assemblage génomique n'a pas été vérifiée. L'alignement génomique local 99,6678 % précédemment mesuré est une preuve distincte et ne doit pas être confondu avec les identités des HSP BLAST.

## Statuts

- **PASS technique** : job GitHub réellement exécuté ; FASTA et XML récupérés ; RID et hashes vérifiés.
- **PARTIAL biologique** : le meilleur hit parmi les transcrits retournés est HAND2 pour les deux requêtes.
- **UNVERIFIED** : best hit sur l'ensemble de l'assemblage génomique, absence d'autres loci paralogues, nomenclature curateur, rajeunissement clinique, valeur commerciale.

Aucun nouveau cron, abonnement, contact sortant ou dépense. Ne pas relancer ce même run sans nouveau protocole qui vérifie réellement l'assemblage complet.
