# ASTRA OCTOPUS CONTROL Ω — Fiche rendez-vous Blue Smart Robotics
**Lundi 23 novembre 2026, 17 h France (CET) — Teams, lien en attente de l'invitation d'Alexandre Chalin.**
**État de convocation :** créneau accepté par Gmail `SENT` (message `1a1ea042da3aabcf` du 17/11) ; pas de réponse finale ni de lien Teams retrouvé lors du contrôle le 17/11.

## Pitch (45 secondes, sans surpromesse)
« ASTRA OCTOPUS CONTROL est actuellement un **proxy décisionnel déterministe** de navigation bio-inspirée, et non un robot, un jumeau numérique physique ou un contrôleur certifié. Nous avons comparé, dans 400 configurations *synthétiques*, une stratégie directe et une stratégie qui mobilise plusieurs appuis. L'amélioration de franchissement dans certains cas découle d'une **hypothèse explicite de traction**, pas d'une mesure de forces. Nous cherchons aujourd'hui **un cas d'inspection non armée réaliste**, les critères d'exclusion et un test indépendant à coût nul si vos moyens le permettent. »

## Preuves remesurées sur code authentifié le 17 novembre
- Source GitHub: [octopus_control.py](./octopus_control.py), Git blob SHA-1 `adde3db27b91be32bacc97c0fae4ee247bb0f0a2`.
- Tests: [test_octopus_control.py](./test_octopus_control.py), Git blob SHA-1 `4156a928afb7a321d894dc150f19b6e2934caba8`.
- Environnement local temporaire Python 3 : **16/16 tests PASS** (`python -m unittest -q test_octopus_control.py`) ; rapport recalculé correspond au [reçu épinglé](./report-reference-20261114.json).
- 400 scénarios = 10 ouvertures × 4 résistances × 5 qualités d'appui × 2 orientations.
- Succès **direct 125/400**, **par étapes 253/400** dont **128 uniquement par étapes**. Ce différentiel est une conséquence du modèle mécanique **non calibré** (plus de force fictive si présence d'appuis).
- Dans les **125 scénarios réussis par les deux politiques**, la stratégie **directe est toujours plus rapide**, ce qui préserve un résultat défavorable à la complexité.
- **40 configurations impossibles géométriquement** ; **80 cas sans appui** ; absence d'amélioration sans appui (contrôle négatif).
- Empreinte SHA-256 des **observations canoniques** `4eca4532c9c19b51906ba38e93786967953e71b76493f95887914da20ecc3625` ; calcul identique au reçu initial.

**Statuts :** logiciel reproductible PASS ; fidélité mécanique, robot réel, gain industriel, sûreté et performance énergétique **UNVERIFIED**. La note initiale PDF de deux pages a été envoyée en PJ le 14 novembre (présence du PDF confirmée dans Gmail).

## Déroulé de 20 minutes
**0–3 min :** besoin industriel précis chez Blue Smart (un seul geste d'inspection et sa contrainte).
**3–7 min :** montrer le modèle, le code et le compteur reproductible 400/16 ; exposer les hypothèses non calibrées.
**7–12 min :** examiner les contre-exemples (aucune adhérence, trou trop petit, temps supplémentaire, collisions).
**12–17 min :** figer la géométrie, matériau, capteurs, seuil d'échec, protocole de répétition, baseline directe et coûts.
**17–20 min :** accord éventuel sur un jeu de mesures **non confidentiel** ou une revue écrite de la faisabilité ; décider qui fait quoi et à quelle date, **sans engagement financier automatique**.

## Questions prioritaires au partenaire
1. Quel **seul cas d'inspection civile** pose un problème de passage réel : taille de l'ouverture, virages, rugosité, orientation, câbles, débris ?
2. Quelles surfaces sont **interdites au contact** ; quelles forces/pressions maximales, charge utile, fatigue et risques FOD/contamination ?
3. Quelle **baseline mécanique existante** (caméra endoscopique, crawler, bras, serpentin) comparer ? Quels essais seraient pertinents pour conclure à un échec ?
4. Quel dispositif de mesure *indépendant et autorisé* permet de relever effort, adhérence, collisions, temps et répétabilité **sans coût** initial ?
5. Une petite revue contradictoire du code et des contrôles négatifs est-elle réaliste ? Y a-t-il un exemple de géométrie public/anonymisable que nous pourrions utiliser ?

## Préparation technique de la démo
```sh
cd research/octopus_control
python -m unittest -v test_octopus_control.py
python octopus_control.py
```
Ne pas annoncer un `PASS` obtenu sur un autre environnement comme si l'exécution avait été faite en direct. Les sorties `report.json` et `observations.json` produites sont **synthétiques**. Ces commandes sont en lecture/écriture **locale** uniquement, pas une commande robot.

## Clôture et décision
Chercher **un benchmark physique négatif/positif avec variables mesurées**, et non une promesse d'intégration. Aucun achat, exclusivité, transfert de propriété intellectuelle ni contrat n'est autorisé par ce premier rendez-vous. Le lien Teams reste le seul blocage logistique reconnu le 17/11.
