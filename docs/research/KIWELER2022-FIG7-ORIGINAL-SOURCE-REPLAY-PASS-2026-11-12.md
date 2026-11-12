# BIO-MIMIC X Ω — Kiweler 2022 Figure 7 — source originale et recalcul indépendant
Date : 2026-11-12. **PASS pour la récupération, SHA-256 et la reproduction numérique des quatre tests de Welch ; PARTIAL pour la robustesse biologique ; UNVERIFIED pour toute réplication expérimentale indépendante ou efficacité humaine.**

## Traçabilité
- Kiweler et al., Nature Communications 13:2699 (2022), DOI : https://doi.org/10.1038/s41467-022-30363-y
- XLSX original public : https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-022-30363-y/MediaObjects/41467_2022_30363_MOESM3_ESM.xlsx
- **4 294 922 octets ; SHA-256 ac6f8f8d08055d82838601a1cdef66b5e464c9e392d3b09b85acbfbbcb762a81.**
- GitHub Actions indépendant **PASS** : https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43174821308 . Artefact 13924096056 (disponible jusqu'au 19 novembre 2026).
- Source : feuilles Figure 7C, 7D, 7E et 7G, **72 cellules individuelles**, 67 observations incluses, 5 exclues.
- Livrables de l'artefact : kiweler2022_original_source_data.xlsx, fig7_cell_lineage.csv (traçabilité jusqu'à chaque cellule), fig7_mouse_level.csv, fig7_original_recalculated.json (Welch/Holm/Fisher), manifest SHA-256.
- Relecture locale avec artifact_tool et SciPy, recoupée par une extraction indépendante en ZIP/XML dans le workflow. L'extracteur refuse toute autre empreinte du classeur.

## Résultats sur données individuelles (Welch bilatéral, KD - SCR)
| Panneau | SCR n, moyenne | KD n, moyenne | Différence [IC95%] | p recalculée | p publiée | p Holm sur 4 tests |
|---|---|---|---|---:|---:|---:|
| 7C poids tumoral en mg | 9 ; 1528.55556 | 9 ; 1514.44444 | -14.11111 [-465.77968 ; +437.55746] mg | 0.9473792540 | 0.9474 | 0.94738 |
| 7D protéine Mthfd1l/β-actine | 7 ; 1.3681230 | 8 ; 0.8147135 | -0.5534095 [-0.8393388 ; -0.2674802] | 0.0013716934 | 0.0014 | 0.00549 |
| 7E score de métastases pulmonaires | 9 ; 5.6666667 | 9 ; 1.6666667 | -4.00000 [-7.6073684 ; -0.3926316] | 0.0322222984 | 0.0322 | 0.06444 |
| 7G surface pulmonaire métastatique en % | 7 ; 1.8765764 | 9 ; 0.2514992 | -1.6250772 points [-2.8861694 ; -0.3639849] | 0.0189005879 | 0.0189 | 0.05670 |

**4/4 p-valeurs de Welch reproduites exactement à l'arrondi publié (quatre décimales).** Les intervalles sont calculés séparément sur les données sources : ne pas les attribuer aux auteurs.

## Contrôles négatifs, discordances et incertitudes
1. **Fig 7C résultat négatif : p=0,9474.** L'absence de différence détectée entre poids tumoraux ne démontre pas l'équivalence des deux groupes.
2. **Fig 7E huit scores fractionnaires**, par exemple C6=4,5 et D6=5,5. Les valeurs sont conservées sans arrondi. Pourquoi un « nombre de métastases » prend-il des demi-valeurs ? **UNVERIFIED**, clarification de la définition de mesure requise.
3. **Fig 7E : 6/9 KD sans métastase visible contre 0/9 SCR.** Test exact de Fisher bilatéral recalculé sur ce critère binaire : **p=0,0090497738**. Ce test est distinct de Welch p=0,0322223 sur les scores.
4. **Fig 7G deux témoins exclus pour poumons affaissés** : cellules C11 et C12, n=7 contre n=9. Fig 7D : C4, C11 et D5 exclus selon le tableau source. Les cinq exclusions restent tracées.
5. **Correction de Holm exploratoire** sur les quatre panneaux : Fig 7E p corrigée 0,06444, Fig 7G 0,05670 ; aucune ne reste sous 0,05. La famille de quatre tests n'est pas présentée comme un choix préenregistré par les auteurs.
6. **Scores asymétriques et petits effectifs** : permutation exacte bilatérale de la différence moyenne pour Fig 7E p=0,0326615 et Fig 7G p=0,0038462. Mann–Whitney asymptotique p=0,01917 (7E), p=0,00800 (7G).
7. Sensibilité 7G avec hypothèse de zéro pour les deux SCR exclus : Welch p=0,03736 (imputation *hypothétique*, pas observation).
8. Aucune preuve de nouvel essai animal indépendant, efficacité clinique ou bénéfice de survie.

## Reproduction (branche isolée)
- Exécuter validation/kiweler2022_source_fetch.py pour récupérer le XLSX officiel et enregistrer son SHA.
- Exécuter validation/kiweler2022_xlsx_to_csv.py avec --source-xlsx sur ce XLSX et --out-dir sur le dossier des preuves.
- Exécuter validation/kiweler2022_fig7_reanalysis.py avec --mouse-csv issu de l'étape précédente, --source-xlsx original et --output fig7_original_recalculated.json.
- Voir le workflow .github/workflows/kiweler-2022-fig7-source.yml, terminé avec succès sur le commit a68a3e4e103c3ea1365b10e0c385a2545592c8a1.

Statuts MYTHOS : récupération PASS ; empreinte PASS ; cartographie PASS ; quatre Welch PASS ; négatifs/contrôles multiples PASS ; mécanisme des demi-scores UNVERIFIED ; généralisation thérapeutique UNVERIFIED. Aucun merge, aucun système de production modifié, coût supplémentaire nul.
