# ASTRA DINO Ω v0.9 — AUDIT DE RÉFÉRENCE ÉQUITABLE (15/11/2026)

**Révision critique de v0.8, sans supprimer les anciens résultats.** La v0.8 opposait le modèle conjoint disposant d'indices anatomiques de la cible à un Mk en étoile qui n'exploitait pas les mêmes indices. Ce n'est pas une comparaison équitable.

### Test réellement exécuté
Matrice originale **Sues et al. 2011**, 42 taxons × 319 caractères, 6 526 évaluations. Objet Git `2c89cac975cdb8e2b13ebe109fd66a0a29a26907` et SHA-256 `8d4ace096e1c0c2cfd7d0a7d9ec40b605395965518c20525516237e226adfff9` vérifiés.

Tous les modèles ont accès aux mêmes colonnes d'ancrage de la cible (`j%5==0`). Paramètres v0.8 inchangés : Mk rate 0,25, mélange 65% Mk/35% voisins, 12 voisins, ≥3 ancrages, graine 20261114, bootstrap par taxon 500 tirages.

| Comparateur | Correct / 6526 | Exactitude | Log-loss | Brier |
|---|---:|---:|---:|---:|
| Vote majoritaire | 4780 | 73,25 % | 0,6484 | 0,3781 |
| Mk étoile | 4779 | 73,23 % | 0,9390 | 0,4434 |
| ASTRA conjoint v0.8 | 4814 | 73,77 % | 0,7608 | 0,3796 |
| **Voisins pondérés seuls, mêmes indices** | **5436** | **83,30 %** | 0,7601 | 0,3648 |
| Voisins à poids uniformes | 5274 | 80,82 % | **0,5816** | **0,2951** |
| Ancrages substitués (témoin) | 4777 | 73,20 % | 0,8819 | 0,4297 |

**ASTRA − voisins pondérés : −9,53 points**, IC bootstrap cluster-taxon à 95 % **[−11,82 ; −7,38]**. Sur **16 états fossiles absents chez tous les autres taxons**, aucune méthode n'a de bonne prédiction.

### Phylogénie externe — source rejetée
Interrogation de **Open Tree of Life** (TNRS + induced_subtree) sur les 42 noms : 41 correspondances exactes, 24 taxons seulement retenus par la synthèse ; le sous-arbre présente une anomalie (*Plateosaurus* près de *Platysaurus* / Squamata). Donc **aucun arbre externe scientifique valide et complet** obtenu ; interdiction de combler arbitrairement les placements inconnus. [Open Tree API](https://api.opentreeoflife.org/v3/tree_of_life/induced_subtree).

### Portée de la preuve
**PASS** : benchmark comparatif réel; 10/10 tests de contrôle distants (non-fuite, SHA, reproduction des scores historiques).  
**FAIL** : supériorité du modèle conjoint face à un concurrent simple disposant des mêmes informations.  
**FAIL** : arbre externe complet/valide 42 taxons.  
**UNVERIFIED** : reconstruction de nucléotides ancestraux, génome dinosaurien et résurrection.

**Important** : le code autonome de reproduction Python et ses 9 tests locaux synthétiques sont livrés en ZIP dans la conversation ChatGPT de ce résultat. L'archive source Sues est publiquement disponible au commit épinglé ci-dessus ; la session cloud d'exécution n'est pas persistante. Cette PR ajoute les constats et les données, sans toucher à `main` ni aux sites.
