# ASTRA DINO Ω v0.8 — Seconde extension du protocole, avant lecture des données
Date 2026-11-15. Zéro analyse de matrice cible effectuée lors de ce dépôt.

Dryad Xi 2024 `Dataset_S1.tnt` a répondu HTTP 401/403 dans le sandbox cloud, malgré métadonnées et SHA-256 accessibles. Le supplément Zenodo de l'article contient seulement un PDF. Première solution de repli préenregistrée, PeerJ Yang 2025 `peerj-13-19664-s001.tnt` (74×380), n'était pas récupérable via les points d'accès web disponibles et le cloud Vercel est momentanément inaccessible (erreur interne de l'outil), sans test scientifique.

**Seconde solution de repli fixée avant sa première lecture** : un jeu de données théropode codé par une autre équipe, accessible par GitHub public et non utilisé dans v0.1–v0.7 :

- Fichier : `nexus_files/SuesEA11_Theropoda.nex`
- Dépôt : `rossmounce/cladistic-data`
- Source : https://github.com/rossmounce/cladistic-data/blob/ea2a30384cf1654271970d5c8b661c08dcd3158d/nexus_files/SuesEA11_Theropoda.nex
- Référence à auditer : Sues et al., 2011, Theropoda ; ne pas affirmer une absence complète de recouvrement de caractères avec Baron sans confrontation explicite des listes.
- Jeu de test tenu hors du développement jusqu'au présent amendement, aucune observation inspectée.

Les paramètres restent ceux de `PREREGISTRATION.md`: Mk symétrique taux 0.25, ancrages `j%5==0`, mélange 0.35, maximum 12 voisins, minimum 3 ancrages, contrôle négatif mélangé, bootstrap groupé 500, graine 20261114, vote majoritaire. Aucun changement de modèle après lecture. En cas de données invalides, faire échouer la validation plutôt qu'ajuster les hyperparamètres.

**Précaution :** cette substitution introduit une série historique dont les caractères peuvent partager des définitions avec d'autres matrices ; c'est un troisième jeu de fichiers indépendant pour la validation logicielle et statistique, mais l'indépendance phylogénétique forte reste UNVERIFIED tant que la provenance caractère par caractère n'est pas établie.