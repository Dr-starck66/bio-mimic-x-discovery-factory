# ASTRA DINO Ω — GENOME REVERSE Ω v0.7
## Réplication indépendante sur la matrice fossile de Baron : résultat négatif conservé

**Exécution :** 14 novembre 2026 UTC (session cloud temporaire). **Budget additionnel : 0 €**.  
**Statut exécution : PASS** — script exécuté, code de sortie 0, source authentifiée, 30 permutations négatives et audit anti-fuite direct.  
**Statut scientifique : FAIL** — la supériorité d'ASTRA sur la parcimonie ne se reproduit pas.  
**Indépendance stricte de la phylogénie : PARTIAL** — les arbres publiés ont été ajustés sur la matrice morphologique complète.

### 1. Sources publiques authentifiées

La seconde étude est différente de Hendrickx : elle concerne principalement des **caractères anatomiques squelettiques** de dinosaures fossiles, pas seulement des caractères tégumentaires.

- Données : **Černý D. & Simonoff A.L. (2023)**, *Statistical evaluation of character support reveals the instability of higher-level dinosaur phylogeny*, *Scientific Reports* 13, 9273. DOI : https://doi.org/10.1038/s41598-023-35784-3.
- Archive exacte : https://zenodo.org/records/7979718, DOI https://doi.org/10.5281/zenodo.7979718.
- Matrice publiée de Baron, Norman & Barrett (2017) : `baron.nex`, **37 128 octets**, MD5 Zenodo et calculé = `f7f0270ca0a524ebc49fa98b6a8540c5`, SHA-256 réel = `aa38d15274fc9272f00a7ea818a15502ee3cdec93c3303c79cf9045fed38aff1`.
- Deux archives d'arbres correspondantes de la même publication : `ML_unconstrained.zip` (MD5 publié `a815016680d6b5d55cf2456f53fab7bc`) et `Tree_comparisons.zip` (MD5 publié `dd229989cfca8861817b0ac86192a583`). Quatre arbres présélectionnés sont listés dans le code.
- Les quatre arbres ont été contrôlés : **74 extrémités, exactement les 74 taxons de la matrice, aucun doublon**.

**Dimension analysée :** 74 taxons × 457 caractères ; **14 200 états connus et non ambigus**, **19 618 inconnus**. Distribution connue : 0 : 8 517, 1 : 4 957, 2 : 671, 3 : 54, 4 : 1.

### 2. Modèle figé avant la consultation des résultats

Le modèle réutilise **sans modification des coefficients ni des heuristiques** l'algorithme Hendrickx v0.6 : majorité hors cible ; plus proche voisin phylogénétique ; parcimonie Fitch–Sankoff avec résolution des égalités par majorité ; ASTRA (somme des états donneurs pondérée en `1 / distance_topologique^2` puis vote majoritaire des arbres). Les paramètres ne sont pas réoptimisés sur Baron ; le nombre d'arbres est dicté par les fichiers publiés retenus **avant l'exécution**, et non par leur résultat.

- Code original v0.6 SHA-256 : `860bf1bc8909b58e01aab5f4f78e0ac2f71700d4d77af34ba30fe500032f617d`.
- Adaptateur v0.7 SHA-256 **identique en local et lors de l'exécution cloud** : `f42a15764dd7d85590f2d423f1f708f3f2681f8d05f7b5d6eedecb2afb04c445`.
- Seules modifications : lire NEXUS `BEGIN DATA`, 457 colonnes au lieu de 71, ouvrir quatre arbres Newick de la publication au lieu des six arbres Mesquite de Hendrickx. **Le jeu des états possibles original (`0` à `6`) et les règles d'inférence sont inchangés.**
- À chaque prédiction, les 457 cellules du taxon cible sont supprimées des données accessibles directement aux prédicteurs. Les seules cellules notées sont les états documentés en entrée.

### 3. Résultats réels — 14 200 observations

| Modèle | Correct | Exactitude globale | Exactitude moyenne par taxon |
|---|---:|---:|---:|
| Majorité triviale | 10 492 | 73,887 % | 73,100 % |
| Plus proche voisin, ensemble | 11 908 | 83,859 % | 84,712 % |
| **ASTRA, poids figés** | **11 998** | **84,493 %** | **84,931 %** |
| **Fitch, ensemble avec résolution** | **12 092** | **85,155 %** | **85,843 %** |

**Différence externe ASTRA − Fitch = −94 / 14 200 = −0,662 point de pourcentage**. Bootstrap apparié par taxon (**74 taxons, 6 000 tirages**) : différence macro **−0,912 point**, IC95 **[−1,452 ; −0,405] points**. ASTRA gagne sur 17 taxons, perd sur 43 et fait jeu égal sur 14.

À titre de comparaison, dans le **benchmark Hendrickx v0.6** : 849/1 121 correct pour ASTRA et 837/1 121 pour Fitch en ensemble ; 845/1 121 pour le meilleur arbre Fitch isolé, mais ce dernier était choisi d'après les résultats. **Cette comparaison historique n'est pas une validation externe et ne justifie pas de sélectionner un arbre favorable dans v0.7.**

### 4. Contrôles négatifs et tests

- **30 permutations** des états des donneurs avec arbre 1 fixé : exactitude moyenne **71,5437 %**, minimum **70,9155 %**, maximum **72,1127 %**. Elles confirment la perte de signal sous mélange ; elles ne constituent pas un test formel de supériorité d'ASTRA sur Fitch.
- **Contrôle dynamique anti-fuite directe** : les 457 états de `Euparkeria_capensis` ont été remplacés par `?`. Pour les quatre arbres, **0 prédiction modifiée** chez ce taxon dans les méthodes Fitch, ASTRA et voisin. **PASS pour la lecture directe du libellé cible**.
- **8/8 tests logiciels locaux PASS**, incluant l'immutabilité d'un taxon caché, les distances, les égalités, le mode de calcul et le SHA-256 du code exécuté. Le programme en ligne Vercel a terminé avec **exit code 0** pour le benchmark et les 30 permutations.

### 5. Limitations qui interdisent un PASS scientifique

1. **Fuite possible par la topologie :** les phylogénies ont elles-mêmes été estimées à partir de la matrice complète, donc leurs placements peuvent refléter les caractères cachés. L'expérience teste la prédiction des états sous arbre publié fixé, pas une prédiction indépendante de tous les signaux morphologiques du taxon.
2. **Caractères différents :** Hendrickx étudie principalement le tégument, Baron le squelette. L'échec externe peut dépendre du domaine d'application et de la phylogénie ; aucune causalité unique n'est inférée.
3. **Données incomplètes :** 19 618 des 33 818 cases n'ont pas de valeur observée. Le benchmark ne mesure pas la « vérité » des cases jamais connues.
4. **Génome non testé :** ces scores concernent des états anatomiques fossiles catégoriels. Aucun nucléotide perdu n'a été reconstruit, et aucune possibilité de résurrection d'une espèce n'a été démontrée.
5. **Persistance du résultat brut :** le JSON cloud intégral (274 083 octets ; SHA-256 `bbd65d59320e34b00a2b8852e5ffa31e8566f106f36e10d13d22f6176d0bcd88`) n'a pas été copié dans ce paquet avant l'arrêt de la session temporaire. Les sorties de calcul ont été réellement vues, et le résumé chiffré et le code exact sont conservés ; un nouveau lancement depuis Zenodo régénère le JSON complet. **Ne pas dire que le JSON intégral est archivé ici.**

### Conclusion et prochaine épreuve

**FAIL pour l'hypothèse de supériorité généralisable d'ASTRA.** La nouvelle matrice est authentique, la comparaison a été effectuée sans retoucher les paramètres, et le contrôle anti-fuite directe passe. **L'unique amélioration méthodologique prioritaire** est de refaire les exclusions avec une phylogénie dont l'estimation n'a pas exploité les états du taxon caché (inférence au sein de chaque pli ou contraintes phylogénétiques externes vérifiables). Cette expérience sera **une nouvelle version**, jamais une réécriture a posteriori du résultat v0.7.