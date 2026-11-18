# BIO-MIMIC X — Laurent Simons, physique des polarons et test biomédical quantique simulé

**Date UTC :** 2026-11-18  
**Statut :** PASS (vérification bibliographique du sujet et banc d'essai CPU local) ; PARTIAL (comparaison biomédicale de faisabilité) ; UNVERIFIED (vieillissement, thérapie, clinique, avantage quantique matériel, transférabilité axolotl).

## Question testable et verdict

La thèse de Laurent H. A. Simons, *Bose polarons in superfluids and supersolids*, soutenue le 17 novembre 2025 à l'université d'Anvers, étudie les impuretés dans des gaz de Bose ultrafroids. Ses publications calculent les propriétés et la réponse optique de polarons en phase supersolide. **Aucune de ces publications n'établit de ralentissement du vieillissement, de régénération tissulaire ni d'effet thérapeutique.** L'ambition annoncée de prolonger la vie n'est pas une validation expérimentale.

Pour rendre l'intuition falsifiable, le benchmark compare un noyau de fidélité de quatre qubits *simulés analytiquement* à des modèles classiques sur un jeu de données biomédical accessible hors ligne. **Ce n'est ni une reproduction des équations de Simons, ni une expérience sur matériel quantique.**

## Sources primaires et comparaison défavorable

1. University of Antwerp, défense publique du 17/11/2025 : https://www.uantwerpen.be/en/about-uantwerp/faculties/faculty-of-science/news-and-calendar/phd-defences/public-defences-2025/ — thème et superviseurs Jacques Tempere / Michiel Wouters.
2. Simons, Klemt, Pfau, Wouters, Tempere (2025), *Optical response of the supersolid polaron*, *Physical Review Research* 7, L032033, DOI https://doi.org/10.1103/kl1y-pj63 — spectroscopie/énergies d'excitation supersolide, sans biologie.
3. Simons, Wouters, Tempere (2025), *Polarons in supersolids: Path-integral treatment...*, *Physical Review B* 111, 054524, DOI https://doi.org/10.1103/PhysRevB.111.054524 — physique des polarons, sans longévité.
4. *A systematic review of quantum machine learning for digital health* (2025), https://doi.org/10.1038/s41746-025-01597-z — synthèse rapportant des différences globalement négligeables face aux méthodes classiques ; **contre-exemple essentiel à l'hypothèse d'un avantage quantique acquis**.
5. *Advancing single-cell omics and cell-based therapeutics with quantum computing* (2026), https://www.nature.com/articles/s41580-025-00918-0 — feuille de route, non démonstration thérapeutique.

## Données, calcul et contrôles

- `sklearn.datasets.load_breast_cancer` : **569 observations de cytologie diagnostique**, 30 variables initiales et 2 classes. **Ce n'est PAS un jeu de données de longévité, d'âge biologique, ni d'axolotl.** Aucun téléchargement ni partage de dossiers patients privés.
- Sélection `SelectKBest(f_classif, k=4)` et standardisation **réapprises pour chaque pli d'entraînement**, jamais sur les observations de test.
- Référence commune : 5 plis stratifiés répétés 2 fois, seed `20261118`, 10 évaluations. Classifieur majoritaire, régression logistique, SVM RBF, SVM à noyau de fidélité d'états produit. Les trois modèles apprenants voient les **mêmes quatre variables par pli**.
- Noyau : `K(x,y) = ∏_j cos²((θ_j(x)−θ_j(y))/2)` ; `θ_j(x)=π/2 tanh(x_j/2)`. Il correspond à la fidélité de qubits en état produit avec rotations Ry, et il est **facilement calculable classiquement**. Il ne représente pas les supersolides de Simons.
- Contrôle négatif : 5 permutations indépendantes des étiquettes, 5 plis par permutation, même classification à noyau de fidélité. Diagnostic d'absence de signal après rupture de la relation entrée-étiquette.
- Contrôles logiciels : positivité semi-définie, symétrie/diagonale du noyau, entrées invalides, absence d'influence des données test sur transformation train, reproductibilité du seed et blocage des déclarations cliniques.

## Résultats réellement exécutés — machine locale CPU, 18/11/2026

| Méthode | AUROC moyenne | Écart-type descriptif sur plis | Balanced accuracy moyenne |
|---|---:|---:|---:|
| Majoritaire | 0.50000 | 0.00000 | 0.50000 |
| Régression logistique | **0.98739** | 0.00439 | **0.94106** |
| SVM RBF classique | 0.98213 | 0.00876 | 0.93612 |
| SVM fidélité quantique **simulée** | 0.98428 | 0.00700 | 0.94079 |
| Étiquettes permutées (fidélité, 25 plis) | **0.48604** | non calculé | 0.50125 |

Différence de l'AUROC simulé moins RBF : **+0.00214** (descriptive, pas test de supériorité). La régression logistique classique est meilleure en AUROC moyenne sur ce protocole. La proximité entre les méthodes, la petite taille de l'échantillon et la corrélation entre plis répétés **interdisent** de conclure à une supériorité statistique ou à un avantage quantique. Aucun essai clinique, aucune donnée de sénescence cellulaire, aucune machine quantique.

## Reproduction et artefacts

Dans la racine de `Dr-starck66/bio-mimic-x-discovery-factory` avec `numpy` et `scikit-learn` installés :

```bash
python validation/quantum_biomed_feasibility.py
python -m unittest discover -s tests -p test_quantum_biomed_feasibility.py -v
```

Sources : `validation/quantum_biomed_feasibility.py`, tests : `tests/test_quantum_biomed_feasibility.py`, sortie générée : `reports/factory/QUANTUM-BIOMED-FEASIBILITY-20261118.json`. Ce JSON contient les métriques par pli, les contrôles permutés, les versions de dépendances, le seed et le hash du tableau de données natif scikit-learn. Preuve de calcul local : 6 tests exécutés sans échec, le 18/11/2026. Ne pas interpréter cela comme un passage de CI GitHub ou une validation sur serveur.

## Décision BIO-MIMIC X — condition de passage à l'étape translationnelle

**Conserver comme outil de comparaison exploratoire, pas comme technologie de longévité.** La priorité scientifique sur l'axolotl reste l'unicité génomique complète HAND1/HAND2 (non résolue) ; ce benchmark n'apporte **aucune** preuve sur cette unicité. L'étape prospective sur vieillissement serait un jeu de données public de sénescence ou de transcriptomique explicitement sourcé avec séparation par donneur, contrôle des lots, comparaison logistique/RBF/forêt, permutation de labels et critères de puissance préenregistrés. Ne pas réutiliser les scores diagnostiques ici comme des scores de rajeunissement. Aucune réclamation commerciale/clinique autorisée par ces résultats.