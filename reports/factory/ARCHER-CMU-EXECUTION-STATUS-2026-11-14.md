# ASTRA ARCHER VISION Ω — audit d'exécution réel (2026-11-14)

## Résultat et preuve
- **PASS (logiciel local)** : `PYTHONPATH=. python -m unittest discover -s tests -p 'test_archer_vision_*.py' -v` → **17 tests exécutés, 17 OK**, 3.653 s.
- SHA-256 du journal de retest : `b503548c54620bad9f4ffc3f0a7141e92916be2f794d7e09b4444a2b7bf41af9`.
- **FAIL (récupération du dataset)** : `requests` → échec de résolution DNS locale ; tentative de téléchargement direct → échec.
- **FAIL (Vercel, accès)** : création d'un déploiement preview isolé refusée : HTTP 403 `You don't have permission to create a project`. **Aucun nouveau site déployé.**
- **UNVERIFIED** : aucun fichier archive UCI officiel reçu dans l'environnement, donc aucune validation locale du SHA-256 de ses octets ni aucune précision sur visages réels.

## Jeu de données visé
- UCI CMU Face Images, DOI https://doi.org/10.24432/C5JC79
- URL officielle : https://archive.ics.uci.edu/static/public/124/cmu%2Bface%2Bimages.zip
- Empreinte **attendue**, documentée par la source indépendante stable-datasets : `01a8b6cc58ac2f825f72abd6cf2b393df067c6529d96f7a90b22dede71b142cc`. L'empreinte téléchargée **n'a pas été vérifiée**, car aucun téléchargement ne s'est achevé.
- Source UCI : licence CC BY 4.0. Pas de photographie de visage ajoutée au dépôt.

## Outreach (envoi confirmé par l'outil Gmail)
Quatre messages de recherche personnalisés expédiés le 14 novembre 2026 aux contacts institutionnels suivants : support UCI, Tom Mitchell (CMU), Cait Newport (Oxford), Ulrike Siebeck (UQ).
Demandes : accès alternatif à l'archive avec checksum, protocole, mesures individuelles et contrôles négatifs, permissions des stimuli. **Aucun accord ni réponse ne sont présumés.**

## Prochain verrou
Exécuter l'évaluateur existant sur l'archive UCI authentique et publier le manifeste de SHA-256, le comptage des échantillons retenus/exclus, la séparation train/test, les scores des trois modèles et les contrôles négatifs. Ne pas publier de score issu de fixtures ou de jeux synthétiques en guise de résultat sur visages humains.
