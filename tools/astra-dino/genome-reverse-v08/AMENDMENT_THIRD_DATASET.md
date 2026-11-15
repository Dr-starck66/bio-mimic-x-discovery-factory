# ASTRA DINO Ω v0.8 — Amendment d’accès avant lecture des données de test
Date UTC : 2026-11-15. L'ajout documente un blocage de source, **pas** un résultat expérimental.

La matrice Xi et al. (2024), `Dataset_S1.tnt`, 73 OTU, 383 caractères annoncés par Dryad, identifiant de fichier 3749999, SHA-256 publié `4119786f88d33da107e46dbf846117a94cfd4bcab46a1033d62270d7c207a7a2`, est listée publiquement, mais la récupération par `/downloads/file_stream/3749999` renvoie HTTP 403 et `/api/v2/files/3749999/download` renvoie HTTP 401. Zenodo 14491595, dépôt de l'article, ne contient que le PDF supplémentaire, pas la matrice. **AUCUNES données de Xi n'ont été lues ni évaluées**.

### Fallback préenregistré AVANT toute récupération de sa matrice
Si et seulement si Xi reste inaccessible, utiliser **Pulaosaurus** (PeerJ 2025, DOI 10.7717/peerj.19664), `peerj-13-19664-s001.tnt`, Supplément 1, **74 taxons × 380 caractères** d'après la publication. Source indépendante de nos deux matrices de développement. L'échec de récupération de Xi restera documenté, même si ce fallback fonctionne.

Le modèle, les seuils et les métriques de PREREGISTRATION.md sont *inchangés*. Si les symboles de caractères ou le code TNT nécessitent un parseur particulier, l'adaptation est strictement syntaxique ; aucune modification de taux Mk `0.25`, poids `0.35`, règle des ancrages `j%5==0`, 12 voisins, bootstrap par taxon `500`, graine `20261114`, alphabet `01234`.

Les observations de test sont interdites pour l'ajustement. Toute modification des paramètres est un nouveau modèle **v0.9** et requiert une autre matrice vierge. En l'absence de source authentifiée, le verdict reste UNVERIFIED.