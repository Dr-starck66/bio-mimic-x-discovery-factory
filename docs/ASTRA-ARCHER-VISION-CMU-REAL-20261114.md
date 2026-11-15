# BIO-MIMIC X / ASTRA ARCHER VISION Ω — CMU Real Faces

**Statut : PARTIAL** — banc réel prêt et tests locaux reproductibles ; **aucune inférence sur les photographies réelles n'a été exécutée**, le téléchargement réseau autorisé est indisponible dans cette session.

## Dataset et droits

- Source : [UCI CMU Face Images, n°124](https://archive.ics.uci.edu/dataset/124/cmu+face+images), DOI [10.24432/C5JC79](https://doi.org/10.24432/C5JC79), auteur Tom Mitchell, CMU (1997).
- UCI indique **CC BY 4.0**. Le site CMU d'origine précise **usage éducatif gratuit avec attribution** ; les autres usages, en particulier commerciaux, doivent faire l'objet d'une vérification supplémentaire.
- Archives officielles UCI : `https://archive.ics.uci.edu/static/public/124/cmu%2Bface%2Bimages.zip` ; SHA-256 préétabli : `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc` (référence publiée par stable-datasets). Le script rejette les archives dont l'empreinte ne correspond pas.
- 20 identités, 640 prises de vues annoncées (624 valides), pas 44 distracteurs : **19 choix maximum** avec 18 identités inédites et une cible, un autre visage étant réservé à l'apprentissage « foil ».
- Aucune photo, aucune donnée biométrique faciale n'est fournie dans ce paquet et aucune photo n'est publiée sur GitHub.

## Séparation stricte / protocole pré-déclaré

Pour chaque identité cible (rotation de 20 folds), une seconde identité joue le visage appris de comparaison, et les 18 autres sont des distracteurs jamais vus à l'apprentissage de ce fold.

- Apprentissage : `straight_neutral_open`, `straight_happy_open` (deux photographies par identité familière).
- Test frontal changement d'expression : `straight_sad_open`, `straight_angry_open` ; test posture : `left_neutral_open` ; test occultation : `straight_neutral_sunglasses`.
- Sous-sujets dont l'une des six photographies est manquante : exclusions pré-déclarées et consignées, sans sélection selon le score.
- Absence de duplication des chemins d'images **et** des empreintes SHA-256 des images brutes ; aucun visage de distracteur utilisé pour le prototype du fold.
- Comparaison équitable des trois descriptions visuelles existantes : `pixels`, `hog` et `retina_pool`, via la fonction `encode` de BIO-MIMIC X.
- Score : rang du vrai visage parmi 1 cible + distracteurs (top-1), tests 2AFC « sélectionner le familier » et « éviter le familier » et contrôles aléatoires.
- Les comparaisons pairwise partagent les mêmes images : leurs observations ne sont **pas indépendantes**, et le rapport ne déclare aucune supériorité statistique confirmée.

## Exécution

Depuis la racine du projet (Python 3.11+, numpy, scipy, Pillow) :

    python -m unittest discover -s tests -p 'test_archer_vision_real_cmu.py' -v
    python validation/archer_vision_real_cmu.py --download --out reports/factory/ARCHER-CMU-REAL-LATEST.json

Ou avec l'archive officielle UCI déjà obtenue :

    python validation/archer_vision_real_cmu.py --archive /chemin/vers/cmu+face+images.zip --out reports/factory/ARCHER-CMU-REAL-LATEST.json

## Audit enregistré le 14 novembre 2026

- **PASS logiciel** : 8/8 tests (chargeur PGM, dimensions, verrou d'empreinte, séparation, rejets de doublons, taille minimale de la cohorte, reproductibilité, métriques des trois méthodes sur fixtures synthétiques).
- **FAIL accès externe** : la tentative directe d'obtenir l'archive officielle a échoué avec `urlopen error [Errno -3] Temporary failure in name resolution` ; code de sortie 1, aucun JSON de performance réelle créé.
- **UNVERIFIED réel** : ni précision, ni rappel, ni latence, ni supériorité de Retina-Pool sur photographie réelle n'ont été mesurés. La publication GitHub du code ne les démontrerait pas.

**Prochaine action indispensable :** exécuter le script dans un environnement autorisé ayant accès à l'archive UCI d'empreinte vérifiée, avant tout énoncé de performance réelle.