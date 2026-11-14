# ASTRA DINO Ω — exploitation de la référence Rubin 2022 transmise par Oslo

**14 novembre 2026** · Branche isolée PR #52 · **audit documentaire PASS ; validation causale/externe UNVERIFIED**.

Jan Terje Lifjeld a communiqué le DOI `10.1126/sciadv.abm5982`. Publication Rubin et al., *Science Advances* (2022) : https://pmc.ncbi.nlm.nih.gov/articles/PMC9269886/ ; référence `GCA_902806625.1`, BioProject `PRJNA743742`, code `https://doi.org/10.5281/zenodo.6639328`.

**Apport** : 28 régions de différenciation génomique correspondent à des blocs haplotypiques ancestraux. ALX1 et HMGA2 appartiennent à des régions distinctes du chromosome 1A, séparées par une zone de forte recombinaison. L'article décrit une expression d'ALX1 dans le bec embryonnaire, pas la causalité de SNP individuels de notre VCF.

**Contrôle négatif décisif** : les 75 oiseaux de la cartographie de 2022 ont reçu une classe de taille *par espèce* (0, 1, 2) parce que les mesures individuelles n'étaient pas disponibles pour chaque oiseau. **Ce n'est pas une cohorte indépendante avec génotypes et morphométries individuelles appariées** ; elle ne valide pas les modèles sur 50 oiseaux Oslo.

## Confrontation automatisée aux deux JSON de preuve existants

| Contrôle | Résultat |
|---|---|
| Concordance assemblage | `GCA_902806625.1` — PASS |
| ALX1 | `ENSCPVG00000017961`, 1A:40 877 644–40 920 855 — preuve existante |
| HMGA2 | `ENSCPVG00000006117`, 1A:33 408 202–33 520 236 — preuve existante |
| Écart entre corps de gènes | **7357407** bases — calcul PASS, **pas des limites d'haplotypes** |
| SNPs Oslo dans corps géniques | 9 ALX1, 36 HMGA2 — **précédent audit**, pas de nouveau scan VCF |
| Modèle conjoint taille, p corrigée globale 8 tests | **0.0847**, non significatif |
| Fenêtres adjacentes droites, p globale | **0.0084**, exploratoire et non indépendant |
| Bornes exactes de l'haplobloc Rubin Data S2 | **UNVERIFIED** — fichier supplémentaire non récupéré |

**Méthodologie désormais verrouillée :** il faut récupérer et authentifier les bornes de `Data S2` avant de décrire le nombre de SNPs appartenant aux *haplotypes publiés*. Ne jamais utiliser les corps de gènes comme substituts silencieux. La validation prédictive exige une cohorte indépendante, non chevauchante, où chaque oiseau possède génotype et dimensions mesurées.

Source : https://pubmed.ncbi.nlm.nih.gov/35857449/ ; archive Oslo https://doi.org/10.5061/dryad.3ffbg79w8 .

**Exécution** : les assertions du manifeste JSON joint ont été vérifiées en lecture de deux fichiers GitHub de la branche ; contrôle de qualification documentaire local en archive séparée : 8/8 tests PASS sur fixture fidèle, **pas** de réanalyse des VCF, pas de nouvelle p-value, aucune fusion et aucune dépense.
