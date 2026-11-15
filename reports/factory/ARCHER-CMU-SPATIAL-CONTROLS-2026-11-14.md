# ASTRA ARCHER VISION Ω — contrôle du contexte, 14 novembre 2026

**Statut global : PARTIAL.** Analyse réelle des images du miroir vérifié localement : PASS. Téléchargement et authentification en octets du ZIP officiel UCI : **FAIL_CLOSED** (DNS / accès non disponible). Validation neurobiologique et généralisation indépendante : UNVERIFIED. **Ne pas fusionner comme preuve de reconnaissance robuste des traits du visage.**

## Provenance
- Catalogue UCI : https://archive.ics.uci.edu/dataset/124/cmu+face+images ; DOI 10.24432/C5JC79 ; métadonnées CC BY 4.0.
- SHA-256 attendu (documenté par stable-datasets) du ZIP UCI : \`01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc\`. Aucun octet du ZIP officiel n'a été récupéré par notre environnement : **ce hash n'est pas localement vérifié**.
- Archive miroir \`faces_4.tar.gz\`, copie GitHub tierce épinglée : 414 060 octets ; SHA-256 **calculé** \`fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4\`.
- 624 photos PGM inspectées, 118 retenues, 18 identités complètes ; \`glickman\` et \`mitchell\` exclus faute de \`straight_angry_open\`.

## Protocole exploratoire
Les trois modèles d'origine (Pixels, HOG, Retina-Pool) ont été évalués avec les mêmes images et un prototype sur deux vues d'apprentissage par identité. Dans chaque pli, une identité cible, une identité familière réservée et 16 distracteurs jamais entraînés ; images d'apprentissage et d'évaluation distinctes et contrôlées par SHA. Les sujets sont réutilisés entre plis : essais non indépendants.

Les images 64×64 ont subi sept traitements appliqués à l'identique :
1. image complète
2. centre facial seul, pixels extérieurs remplacés par gris uniforme 0,5
3. centre facial recadré et redimensionné
4. centre facial recadré et contraste normalisé
5. périphérie seule, centre remplacé par gris 0,5
6. bordure seule (neuf pixels extérieurs)
7. image constante (contrôle négatif)

Région centrale fixée à lignes 14:50, colonnes 17:47. **Choisie après inspection de photos**, non définie par des points de repère annotés : interprétation exploratoire, pas « visage isolé anatomiquement validé ». Les égalités entre scores sont départagées au hasard, avec graine fixée indépendante de l'identité.

## Résultats Top-1 : changement de pose, 18 essais, hasard ~5,9 %

| Transformations | Pixels | HOG | Retina-Pool |
|---|---:|---:|---:|
| Image complète | 13/18 (72,2 %) | 17/18 (94,4 %) | 15/18 (83,3 %) |
| Centre seul, fond uniforme | 5/18 (27,8 %) | 7/18 (38,9 %) | 4/18 (22,2 %) |
| Centre recadré | 5/18 (27,8 %) | 7/18 (38,9 %) | 7/18 (38,9 %) |
| Centre recadré, contraste normalisé | 5/18 (27,8 %) | 9/18 (50 %) | 7/18 (38,9 %) |
| Périphérie seule | **18/18** | **18/18** | **18/18** |
| Bordure seule | **18/18** | **18/18** | **18/18** |
| Uniforme | 2/18 | 2/18 | 2/18 |

Autres résultats du centre recadré : expressions faciales 25/36 (Pixels), 31/36 (HOG), 29/36 (Retina-Pool) ; lunettes 11/18, 17/18, 13/18.

**Résultat négatif crucial :** la bordure seule suffit pour une reconnaissance parfaite sur cet échantillon. Les mesures initiales de l'image complète sont donc très fortement confondues par des indices hors du centre du visage. Impossible d'attribuer ces scores à des mécanismes de reconnaissance du visage ou à une supériorité bio-inspirée. Le recadrage étroit conserve néanmoins un signal supérieur au hasard chez certaines méthodes ; les indices résiduels restent inconnus.

## Preuves et reproductibilité
- Re-test du benchmark existant : 23/23 PASS.
- Nouveaux tests du contrôle spatial et du vérificateur du ZIP : **36/36 tests locaux PASS** ; journal local hash SHA-256 \`93e566f10d555faab45346ad21a185c446c2eb4a7276d8a4811da821e494425b\`.
- Rapport JSON des transformations et statistiques de bootstrap par sujets : SHA-256 \`4a7a8660d56d57c271fe755e66167377be5d3fb1595c23b9ececa261fc1fd994\`.
- Vérificateur strict du ZIP : fail-closed effectif \`FAIL_CLOSED: official UCI ZIP not present; no provenance PASS\`. Six tests logiciels de substitution et de mismatch PASS.
- Source complète, tests, rapport JSON et manifestes SHA-256 : paquet local \`ASTRA_ARCHER_VISION_UCI_CONTEXT_AUDIT_20261114.zip\`, sans octets de portraits/embeddings.

## Suites scientifiques
Obtenir les octets du ZIP UCI original, comparer SHA officiel, SHA TAR interne et hash de chaque PGM. Pour une validation indépendante : nouvelles photographies avec arrière-plans, habillement et cheveux neutralisés ou contrôlés à l'acquisition, séparation des sessions et évaluation par sujets. Contacter des spécialistes pertinents sans sur-vendre ces résultats. Les 4 contacts UCI/CMU/Oxford/UQ déjà sollicités ne doivent pas être relancés en doublon.
