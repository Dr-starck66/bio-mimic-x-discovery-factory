# BIO-MIMIC X — Audit indépendant des XML BLAST HAND2 — 10 novembre 2026

**Statut : PASS technique (lecture XML, contrôles SHA-256) / PARTIAL scientifique.**

Source primaire : [GitHub Actions run 42771822497](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/42771822497), artefact [13742496052](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/42771822497/artifacts/13742496052) ; ZIP SHA-256 `c81fe3e8cffdf9123c35c9e47e83fc79cf25c8c4baa631256e943870d9c6b8e6` (identique au digest GitHub). Manifest, FASTA et XML vérifiés contre les SHA-256 du manifest.

| Requête génomique | BLAST | Premier hit annoté HAND2 | HSP HAND2 | Couverture de la requête par HSP HAND2 | Contrôle HAND1 |
|---|---|---|---|---|---|
| CM010938.2:884794726–884799066 (4 341 nt) | NCBI `core_nt`, 9 hits | `XM_069631422` | 2 HSP, **2004/2007** colonnes identiques | **2006/4341** bases (46,21 %) | `XM_069653976`, meilleur HSP **170/205** |
| NC_090937.1:910028725–910032936 (4 212 nt) | NCBI `core_nt`, 9 hits | `XM_069631422` | 2 HSP, **2007/2007** colonnes identiques | **2007/4212** bases (47,65 %) | `XM_069653976`, meilleur HSP **170/205** |

**Lecture exacte :** les deux requêtes génomiques retrouvent en tête le transcrit annoté HAND2, devant HAND1, dans les résultats XML réels. Les 2 HSP de HAND2 ne couvrent pas l'intégralité du locus ; les pourcentages d'identité des HSP ne doivent pas être présentés comme une identité génomique globale. Les résultats BLAST de cette expérience interrogent `core_nt` (hits principalement mRNA), **pas** un alignement exhaustif de l'assemblage du génome. Le nombre de 9 hits retournés ne prouve pas qu'il n'existe pas d'autres loci.

**Limites obligatoires :** unicité génomique **UNVERIFIED** ; identité officielle certifiée par curateur **UNVERIFIED** ; fonction et efficacité clinique **UNVERIFIED** ; valeur commerciale **UNVERIFIED**. Ce test est une nouvelle analyse du même artefact, **pas** une réplication indépendante. Les contrôles HAND1 défavorables sont conservés.

**Reproduction sans coût :** télécharger le ZIP de l'artefact ci-dessus, puis exécuter `python validation/hand2_blast_xml_audit.py hand2-remote-blast-evidence.zip`. Aucun accès NCBI ni service payant nécessaire pour cet audit hors ligne.