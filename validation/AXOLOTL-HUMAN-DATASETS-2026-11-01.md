# BIO-MIMIC X — Jeu d'essais reproductibles axolotl → humain (1 novembre 2026)

## Prérequis scientifiques

Ce dossier ne prétend pas reproduire la régénération d'un membre humain. Les séries sont des **sources identifiées**, non des réanalyses exécutées. Un modèle embryonnaire de membre humain ou une plaie cutanée adulte ne prouve pas la repousse d'un membre adulte.

| Série | Espèce / système | Ce qu'elle permet d'éprouver | Limite / contrôle |
| --- | --- | --- | --- |
| [GSE243137](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243137) | Axolotl, cellules dermiques antérieures (n=2) et postérieures (n=3), membre non blessé | Vérifier l'identité spatiale et Hand2 au niveau transcriptomique | 5 échantillons, non blessé, même groupe que l'article fondateur (PMID 40399677), pas une réplication indépendante |
| [GSE284768](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE284768) | Axolotl, cellules antérieures/postérieures de blastème et autres conditions | Explorer changement de programme Hand2–Shh pendant régénération | Étude source elle-même : peut vérifier la reproductibilité, non valider indépendamment sa causalité |
| [GSE241132](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE241132) | Humain, plaies cutanées : peau saine / J1 / J7 / J30, 3 donneurs avec mesures répétées | Tester état des macrophages et fibroblastes humains ; témoin intra-donneur et temps | **Pas un membre**, données brutes en accès contrôlé EGA EGAS50000000571 ; pas de réanalyse avant accès autorisé |
| [GSE243225](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE243225) | Atlas multi-espèces axolotl / humain / souris / poulet / grenouille | Comparer modules d'expression du développement, homologies cellulaires et signaux de bourgeon | Cellules de membre humain **embryonnaire** dans les jeux réanalysés (GSE143753, GSE157329) ; pas de régénération adulte |

## Programme préenregistrable sans modification des résultats historiques

1. **Question principale nouvelle**, à déposer séparément du préenregistrement GEO du 16 octobre : les fibroblastes et macrophages humains présentent-ils, après blessure, des modules d'expression orthologues du système régénératif axolotl ? L'hypothèse ne présuppose pas une repousse fonctionnelle.
2. **Sources / sélections à verrouiller avant analyse** : types cellulaires, donneurs biologiques, identités orthologues un-à-un vérifiées, marqueurs HAND2, SHH et modules ECM/immunitaires, frontières développement/plaie, exclusions et seuils. Ne pas choisir les gènes sur la cohorte test.
3. **Contrôles négatifs** : permutation des étiquettes blessure/contrôle **à l'intérieur des donneurs**, appariement de types cellulaires, jeu de gènes témoins non liés, variation temporelle, effets de plateforme, et contrôle de similarité avec tissu non apparenté.
4. **Porte de validité** : refuser une comparaison directe de niveaux d'expression entre espèces ou technologies sans mapping un-à-un et normalisation propre à chaque jeu ; rapporter disponibilité, n effectif, données manquantes, multiplicité, IC et résultats défavorables.
5. **Porte de preuve** : un signal humain = seulement une **conservation moléculaire observationnelle**. Une interaction ECM × macrophages exige une perturbation causale indépendante sur cellules humaines. La régénération complète d'un membre reste **UNVERIFIED** jusqu'à démonstration anatomique et fonctionnelle directe indépendante.

## Statut opérationnel au 1 novembre 2026

- **PASS — Source discovery** : quatre fiches GEO identifiées publiquement.
- **UNVERIFIED — Data access and QA** : aucun téléchargement des matrices requis à ce stade n'a été exécuté dans cette intervention.
- **UNVERIFIED — Human functional experiment** : aucune intervention cellulaire ou biologique exécutée.
- **UNVERIFIED — Human limb regrowth** : aucune preuve humaine directe enregistrée.
- **FAIL préexistant maintenu** : GSE74387 non répliqué aux critères du 16 octobre. Voir `NOTE-INTERPRETATION-GEO-2026-10-27.md`.

Ce document ne remplace aucune validation précédente et ne sert pas d'autorisation d'expérimenter chez l'humain.
