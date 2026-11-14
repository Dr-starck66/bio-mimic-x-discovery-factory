# ASTRA DINO Ω — GENOME REVERSE v0.7 : Mk + morphologie fossile

**Date : 14 novembre 2026 — coût supplémentaire 0 € — pas de fusion en production.**

## Sources originales et intégrité

| Matrice | Taxons | Caractères | SHA-256 |
|---|---:|---:|---|
| Hendrickx et al. 2022, `Ancestral_state_reconstruction_analysis_Jan_2022.nex` | 61 | 71 | `70edf9e9ceb5959f0070911e9cf78e44ff44027043f91c89dc088353ef821c82` |
| Baron et al. 2017, copie corrigée par Joseph W. Brown `Baron_et_al_2017_Nature.NEX` | 75 | 457 | `78e5cf6d2402741151950bdcb12373f86d900d27f4ef6b61b6b983987bcca311` |

Sources : https://zenodo.org/records/5259937 et https://gist.github.com/josephwb/ea9478bd65e370303e8d5008f72bafde. Le fichier Baron est **une réédition** excluant un caractère constant de la matrice publiée (457 au lieu de 458). Il n'inclut **aucun arbre** : l'expérience Baron utilise une topologie étoilée non résolue et ne constitue pas une validation indépendante d'une phylogénie.

## Modèles, expériences et limites

- Référence : **Mk** de caractère discret à transitions symétriques, probabilité d'état prédite par propagation de messages (cavity / leave-one-out); branches de longueur supposée identique, taux de transition fixe 0,25. Ces paramètres **ne sont pas estimés** sur des temps fossiles calibrés.
- Modèle conjoint : 20 % des caractères morphologiques du fossile cible (indices `j % 5 == 0`) sont disponibles comme **ancrages observés** ; les 80 % restants sont cachés. L'association entre ancrages et caractères cachés provient des autres taxons, sans consulter les valeurs cachées de la cible. Mélange Mk / cooccurrence de l'entraînement avec poids `lambda=0.35`, au plus 12 voisins et ≥3 ancrages communs.
- Contrôles : majorité par caractère sur le train, ancrages mélangés, test de mutation des réponses cachées (prédictions inchangées), 6 topologies Hendrickx, bootstrap par taxon, taux Mk 0,08 et 0,60. Les caractères ambigus, inconnus ou inapplicables ne sont pas convertis en zéros.
- **ATTENTION** : ceci n'est **pas** le masquage intégral de toute information morphologique du taxon de v0.6 : ses ancrages restent connus. Ce test examine une *imputation anatomique conditionnelle*, pas une reconstruction génotypique ancestrale.

| Jeu / taux Mk | Majorité | Mk | Joint | IC bootstrap 95 % du gain Joint−Mk (exactitude) |
|---|---:|---:|---:|---|
| Hendrickx, 0,25 (827 observations, 50 taxons) | 66,02 % | 74,73 % | **76,30 %** | [+0,37 ; +3,07] points |
| Hendrickx, 0,08 | 66,02 % | 74,61 % | 75,45 % | [−0,24 ; +2,20] points |
| Hendrickx, 0,60 | 66,02 % | 74,24 % | 76,30 % | [−0,12 ; +4,78] points |
| Baron corrigé, 0,25 (11 564 observations, 75 taxons) | **73,61 %** | 73,50 % | 73,56 % | [−0,062 ; +0,161] points |
| Baron corrigé, 0,08 | **73,61 %** | 73,16 % | 73,57 % | [+0,248 ; +0,589] points |
| Baron corrigé, 0,60 | 73,61 % | 73,27 % | 73,62 % | [+0,209 ; +0,479] points |

Baron 0,60 ne dépasse la majorité que de ~0,009 point ; aucune supériorité établie contre **la meilleure référence**.

La valeur `lambda=0.35` a été fixée dans le prototype avant le calcul principal et n'a pas été sélectionnée sur la matrice Baron. La topologie Hendrickx est fournie par la publication, mais pourrait incorporer indirectement des états fossiles des mêmes taxons (risque de fuite historique). L'intervalle de gain Mk sur Hendrickx dépend du paramètre de branche choisi ; la généralisation scientifique est **FAIL**.

**Vérification intégrée sur la source réellement versionnée GitHub : 14/14 contrôles PASS, exécutés dans Vercel Sandbox gratuit**, y compris intégrité SHA-256, probabilités normalisées, rejet de `BAD` et invariance si on modifie une valeur test cachée. Tests logiciels ≠ validation biologique.

## Reproduction sur Linux / Python 3.13, sans dépendance tierce

```sh
mkdir -p /tmp/astra_v07
curl -fLsS 'https://zenodo.org/records/5259937/files/Ancestral_state_reconstruction_analysis_Jan_2022.nex?download=1' -o /tmp/astra_v07/hendrickx.nex
curl -fLsS 'https://gist.githubusercontent.com/josephwb/ea9478bd65e370303e8d5008f72bafde/raw/4d4ca57fa5c0c6fcf297c6a13ab6c7b66fa8c42a/Baron_et_al_2017_Nature.NEX' -o /tmp/astra_v07/baron_josephwb_edited.nex
sha256sum /tmp/astra_v07/*.nex
python3 runner_mk_joint_v07.py
python3 test_runner_mk_joint_v07.py
```

Ce répertoire contient le code réellement exécuté et `evidence_summary_v07.json`. Le rapport de sensibilité ci-dessus est issu de deux réexécutions explicites aux taux alternatifs, avec conservation de la preuve défavorable.

### Verdict scientifique

**PASS** : deux jeux authentifiés, modèle Mk effectivement calculé, prédiction conditionnelle, 14 contrôles de régression et absence de fuite directe des étiquettes cibles.  
**PARTIAL** : contribution morphologique utile sur certaines tâches lorsque l'on dispose déjà de caractères fossiles du taxon.  
**FAIL** : supériorité robuste sur les deux matrices et sur des taux de substitution différents, davantage encore face à la meilleure référence.  
**UNVERIFIED** : topo indépendante pour Baron, reconstruction d'une information génomique perdue, causalité génétique et résurrection d'une espèce éteinte.

**Prochaine expérience prioritaire** : établir une topologie externe indépendante pour Baron et Hendrickx, calibrer le modèle Mk sur la seule formation, puis évaluer à l'aveugle un jeu non utilisé dans le développement. Une démonstration de reconstruction génomique exige ensuite des séquences génétiques ancestrales vérifiables, pas uniquement des caractères fossiles.
