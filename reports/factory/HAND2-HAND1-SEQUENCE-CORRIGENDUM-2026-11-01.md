# BIO-MIMIC X — Rectificatif d'identité génétique HAND1/HAND2

**Date de contrôle : 1er novembre 2026.** **Statut : PARTIAL** — rapprochement de séquences fortement favorable à HAND1 ; identité exacte interassemblages **UNVERIFIED**.

## Faits reproductibles et provenance

L'ancien locus d'axolotl `AMEX60DD030069` est annoté `HAND1 [nr]|HAND2 [hs]` dans AmexT_v47 / AmexG_v6.0-DD (`chr3q:632140538-632169448`, brin +). Le rapport d'assemblage de `GCA_002915635.3` relie `chr3q` à `CM010932.2`.

Les séquences proviennent des appels officiels NCBI EFetch exécutés dans [l'acceptation scientifique #41320421647](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41320421647) (164 tests PASS, 2 jobs PASS). Le script [hand2_assembly_sequence_probe.py](../../validation/hand2_assembly_sequence_probe.py) conserve les URL des appels, les empreintes des fichiers et les 31-mers dans le [reçu JSON d'exécution](HAND2-ASSEMBLY-SEQUENCE-PROBE-LATEST.json) ; SHA-256 du rapport `fc4935c5e3c2fbf06ae20dc8a0c0505de3e3703db18a2107c6606e2ffc64c517`.

| Source NCBI | Région testée | 31-mers distincts communs à l'ancien locus | Direction |
| --- | --- | ---: | --- |
| Ancien `CM010932.2` | `632140538–632169448` (28 911 nt) | Référence : 27 332 distincts | + |
| Nouveau **HAND1** (`Gene 138582569`, `NC_090926.1`) | `348891291–348920140` | **26 858** | Avant |
| Nouveau **HAND2** (`Gene 138516365`, `NC_090937.1`) | `910028725–910032936` | **8** | Complément inverse |

Calcul : 26 858 / 27 332 ≈ 98,3 % des 31-mers distincts de l'ancien locus sont retrouvés dans HAND1 actuel (recouvrement en chaîne directe) ; 8 seulement dans HAND2 actuel (sens inverse). C'est une indication **très forte** que le vieux locus était étiqueté HAND2 par erreur et ressemble à HAND1. Les compteurs de 31-mers ne sont pas des pourcentages d'identité nucléotidique ni une preuve d'alignement global.

**Contrôles négatifs conservés :** comparaison avec HAND2, orientation des brins, intégrité des accès GenBank/RefSeq, refus des annotations discordantes. **Non encore réalisé :** alignement nucléotidique couvrant les deux loci, recherche d'unicité contre tout le génome, vérification des exons et contrôle de paralogues dans un alignement réciproque. L'identité juridique/scientifique exacte de locus reste `UNVERIFIED`.

## Incidence scientifique et commerciale

La valeur axolotl `−0,0208` du premier rapport transcriptomique, calculée sur `AMEX60DD030069`, n'est **plus attribuable à HAND2** comme résultat établi. Le contraste humain `HAND2 −0,1378` dans GSE28914 demeure une observation humaine séparée. Leur présentation appariée dans un tableau ancien était erronée ; les deux expériences restent de toute façon `NOT_COMPARABLE` biologiquement.

Le gène moderne NCBI axolotl HAND2 (`138516365`) est bien un orthologue du HAND2 humain (`ENSG00000164107`) d'après NCBI Ortholog, mais **ce pont ne s'applique pas automatiquement à AMEX60DD030069**. Aucune revendication de repousse de membres humains, nouveauté thérapeutique, brevetabilité ou exclusivité n'est justifiée par ce résultat.

Pour toute présentation à un industriel, transmettre ce rectificatif **avec** l'analyse originale. Ne pas supprimer ni réécrire le fichier de résultats JSON historique : il est la trace de l'erreur détectée, pas une conclusion validée.

## Prochaine preuve

Effectuer un alignement des loci avec contrôles génome entier et HAND1/HAND2, puis obtenir une annotation d'accès stable publiée (chercheur ou consortium) pour les données HAND2 réellement utilisées dans GSE284768. La demande est préparée en brouillon à L. Otsuki et **non envoyée**.
