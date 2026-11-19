# BIO-MIMIC X — vraie comparaison des assemblages complets HAND2 (19/11/2026)

**Niveau des résultats : PASS contrôle des données et balayage des 2 assemblages ; PASS alignements ciblés ; PARTIAL concurrence génomique à 175 éditions.** Aucune preuve d'orthologie fonctionnelle, médicale ou de transférabilité humaine.

## Données et contrôles exécutés

Archives NCBI téléchargées en entier dans un Vercel Sandbox Hobby existant et temporaire, vérifiées contre les **MD5 authentiques des fichiers `md5checksums.txt`** :

| Référence | FASTA compressé | MD5 constaté et attendu | Bases traversées (strict) | Séquences / dont non placées ou non localisées |
| --- | ---: | --- | ---: | ---: |
| GCA_002915635.3 / AmbMex60DD | 8 946 044 907 octets | `a1eead5b530de52ad8c88c385b302db4` | 28 206 905 576 | 27 157 / 27 129 |
| GCF_040938575.1 / UKY_AmexF1_1 | 8 871 576 465 octets | `bbcffc138dcd879d45227ad9beaf770b` | 29 117 864 639 | 221 / 199 |

L'ensemble des accessions figure dans les rapports d'assemblage NCBI. Les compteurs après décompression et suppression des entêtes correspondent **exactement** aux sommes des longueurs annoncées. Les résultats des deux FASTA sont audités, pas seulement un chromosome.

Les trois fenêtres EFetch épinglées (HAND2 ancien 4 341 bp ; HAND2 nouveau 4 212 bp ; témoin négatif HAND1 28 850 bp) ont retrouvé les empreintes SHA-256 archivées.

## Deux balayages distincts et résultats

1. **Balayage exploratoire à 31-mer** : 90/88 ancres espacées. Sur les 221 et 27 157 séquences : HAND2 attendu trouvé sur les deux chromosomes 6q, respectivement **27** et **25** décalages d'ancres distincts. Quatre positions isolées sur la nouvelle référence n'ont pas montré d'alignement semiglobal à ≤175 éditions dans les fenêtres NCBI testées. Distances **14 et 14 éditions**, cible contre fenêtre génomique étendue, reproduites dans les deux directions après correction du décalage permis dans l'alignement. Le premier balayage n'est pas exhaustif.
2. **Balayage renforcé à 176 blocs disjoints par brin** : pour une requête alignée en entier avec **≤175 éditions**, au moins un des 176 blocs doit être inchangé (principe des tiroirs). Blocs de 24 bp (requête historique 4 341 nt), de 23 bp (requête moderne 4 212 nt), avec les deux orientations. Les entrées sont streamées en chunks chevauchants de 31 bases pour minimiser la perte aux jointures des blocs techniques. **7 887** occurrences dans la référence moderne et **184 762** dans l'ancienne ; SHA-256 des deux sorties `362720ce41c29bcfb65c3eb226ee70d09c77a31e2d9f8e4faf4a7e063903e8bf`, `94daa5e34651b5569979ced75c99706b226568bb8b98537223f980de06a69517`. Aucun nombre de hits ne constitue à lui seul un nombre de gènes.
3. Projection sur les 221 et 27 157 accessions réelles ; coordonnées globales et locales recalculées depuis l'inventaire NCBI : **7 665** fenêtres candidates en moderne, **140 720** en ancien (forte fréquence des motifs peu complexes et répétés). **3** contigs anciens plus courts que la longueur requise à 175 éditions ont été exclus ; une erreur de troncation de fenêtre à l'extrémité des contigs a été décelée, corrigée, puis les candidats ont été recalculés. Les 27 129 scaffolds non placés de l'ancien et les 199 séquences non placées/non localisées du moderne figurent dans l'inventaire.
4. **Point de contrôle de calcul enregistré** : fichiers `HAND2-STRICT-NEW-GENOME-PARTIAL-SCORE-2026-11-19.json` et `HAND2-STRICT-OLD-GENOME-PARTIAL-SCORE-2026-11-19.json`. À cette étape, respectivement 2 655 / 7 665 et 35 762 / 140 720 fenêtres testées, toutes rejetées par une **borne nécessaire 12-mer**. Les autres fenêtres restent à traiter ; ces préfixes ne suffisent donc pas à conclure à l'unicité.

## Code et audit

- `validation/hand2_full_assembly_seeds.py`, `validation/hand2_bounded_candidates.py` : premier balayage et validation sur les vraies fenêtres NCBI.
- `validation/hand2_pigeonhole_seeds.py`, `validation/hand2_overlap_chunker.cjs` : construction d'ancres nécessaires et lecture couvrante des FASTA.
- `validation/hand2_strict_candidates.py`, `validation/hand2_window_extractor.cjs` : classement des fenêtres en conservant les scaffolds, avec repli sur les débuts/fins de contigs.
- `validation/hand2_all_strict_windows.py`, `validation/hand2_partial_windows.py` : rejet par borne nécessaire sur les 12-mers puis distance d'édition semiglobale bitparallèle exacte, avec point de contrôle de préfixe.
- Contrôles positifs et négatifs effectivement exécutés : vérifications de SHA/MD5 et de longueur, résultats réels 14 éditions, quatre candidats isolés négatifs, contrôle de sens, tests sur substitutions ≤175 et faux candidats aléatoires, calcul d'inventaire complet.

## Limites scientifiques cruciales

- **UNVERIFIED** : tous les candidats du second balayage n'ont pas été alignés et départagés. Les correspondances absentes du premier balayage ne sont pas nécessairement absentes du génome. Le moteur `rg -o` ne signale pas nécessairement les matchs exacts **chevauchants**, d'où nécessité de valider une couverture sans faux négatifs avant toute preuve d'unicité à ≤175 éditions.
- Le balayage concerne l'alignement **complet** des fenêtres HAND2, non les gènes partiels, exon par exon, homologues lointains, gros indels, inversions structurales ou situations >175 éditions.
- **Minimap2 et Liftoff NON exécutés** dans cet environnement : le compilateur GCC manquait ; la tentative de téléchargement du binaire Minimap2 a échoué sur le domaine `release-assets.githubusercontent.com`. Les nouveaux résultats viennent d'un balayage de k-mers et de comparaisons de distance d'édition, pas de Minimap2.
- Les fenêtres et rapports privés de correspondance ne sont pas redistribués ; le chercheur a indiqué que l'étude limitée à quelques gènes est acceptable, ce qui ne règle pas les droits de republication du génome entier.
- Aucune inférence de régénération humaine, propriété industrielle ou performance commerciale ; aucun workflow GitHub Actions exécuté, aucun achat réalisé, aucun déploiement public modifié.

**Décision de qualité :** conserver `PARTIAL` jusqu'à preuve qu'aucun candidat génomique complet à ≤175 éditions n'a été manqué, et aligner toutes les fenêtres retenues ; conserver HAND1 et les témoins défavorables. Ensuite valider avec Minimap2/Liftoff et idéalement une revue curatoriale indépendante.
