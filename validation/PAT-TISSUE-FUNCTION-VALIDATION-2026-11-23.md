# BIO-MIMIC X — PAT et qualité fonctionnelle des tissus

Audit documentaire et protocole falsifiable — 23 novembre 2026. **Aucun effet expérimental propre à ASTRA n'a été mesuré.**

## Éléments externes contrôlés

1. Owusu et al., *Gene* 2026, DOI 10.1016/j.gene.2026.150074, PMID 41763503 : culture microfluidique d'organoïdes intestinaux en boucle fermée avec contrôle pH/O2 et rétroaction morphodynamique ; >95 % de viabilité, -50 % de noyaux hypoxiques comparés à culture statique, différenciation rapportée. **Ne démontre pas l'effet isolé d'un prédicteur sur la perméabilité, TEER ou la matrice extracellulaire.**
2. *A platform to reproducibly evaluate human colon permeability and damage*, 2023, PMCID PMC10235044 : TEER et perméabilité moléculaire mesurées ensemble ; TEER ~400 Ohm·cm² sur modèle colique, programme de différenciation accompagné d'une baisse de KI67. **Démontre la pertinence des critères de fonction, pas un avantage du pilotage prédictif.**
3. *A scalable long-term in vitro model of human colonic epithelium with continuous barrier function*, PMCID PMC12485924 : barrière fonctionnelle et analyse d'images monocellulaires, jusqu'à 30 jours de culture et 14 jours de suivi TEER. **Pas d'essai contrôlé de prédiction.**

## Expérience décisive (non réalisée)

- **Groupe A :** culture statique de référence.
- **Groupe B :** réacteur perfusé et instrumenté, régulation réactive (seuils fixes), actionneurs identiques au groupe C.
- **Groupe C :** même réacteur et instrumentation que B, mais régulation prédictive utilisant uniquement les signaux déjà accessibles avant l'action.

Comparaison principale **C vs B**, afin de ne pas attribuer à un algorithme l'avantage physique de la perfusion. A vs B quantifie les autres effets. Randomisation par donneur et lot ; unités biologiques indépendantes ; analystes des mesures fonctionnelles aveugles aux groupes ; horodatage du verrouillage de l'algorithme avant l'essai. Les procédures exactes et les marges doivent être validées avec un biologiste avant le recueil des données.

**Critères fonctionnels co-primaires :** résistance transépithéliale (TEER, Ohm·cm², après correction des blancs) et coefficient apparent de perméabilité d'un traceur moléculaire adapté (Papp, cm/s). Contrôle orthogonal : continuité ZO-1/OCLN, production mucus MUC2 lorsque pertinent, architecture, différenciation, matrice extracellulaire. Décompte des cellules viables et confluence comme contrôles de croissance, non comme preuve de réparation. Le temps de mesure, le traceur, le substrat, l'étalonnage et l'endommagement initial doivent être identiques.

## Analyse informatique disponible

Un analyseur Python local, fourni avec la présente mission mais **pas encore intégré au dépôt**, ingère un JSON avec exactement ces clés par enregistrement : `donor_id`, `arm` (`static`, `feedback`, `predictive`), `teer_ohm_cm2`, `permeability_cm_s`, `viable_cell_count`, `confluence_pct`. Chaque donneur doit être mesuré dans les trois groupes ; les puits techniques sont agrégés en une médiane par donneur et groupe, jamais comptés comme individus indépendants. Un minimum de 6 donneurs indépendants est imposé pour éviter un test de signe sous-puissant.

Critères de filtrage exploratoires **non validés biologiquement** : gain médian TEER d'au moins 10 %, réduction médiane Papp d'au moins 10 %, tests de signe appariés unilatéraux p ≤ 0,05 pour les deux critères, comptes cellulaires à ±10 % et confluence à ±5 points de pourcentage. La règle des deux co-critères est une procédure intersection-union ; ces seuils et le plan d'étude doivent être pré-enregistrés avant l'expérience, avec calcul de puissance et justification tissulaire. Un résultat positif sort au mieux `PARTIAL` tant que les déclarations de provenance, de randomisation, de traitement en aveugle et de répétition indépendante ne sont pas auditées.

**Contrôles négatifs :** croissance sans amélioration TEER/Papp ; groupe `feedback` absent ; seulement 3 donneurs répétés en multiples puits ; essais non aveugles ; retard artificiel et données futures injectées dans le prédicteur (fuite temporelle) ; historique aléatoirement permuté ; perte de calibration capteur. Écarter tout avantage dû à un changement de perfusion, substrat, capteur ou actionneur entre B et C.

## Audit au 23/11/2026

- Recherche de littérature primaire : PASS (sources ci-dessus).
- Algorithme de lecture et tests négatifs : PASS local uniquement, 8 tests de programmation ; aucun test de laboratoire.
- Données originales de trois bras strictement appariés : **UNVERIFIED / non disponibles dans cet audit**.
- Supériorité causale du pilotage prédictif sur la fonction tissulaire : **UNVERIFIED**.
- Reproductibilité industrielle et preuve de régénération chez l'humain : **UNVERIFIED**.

Il est interdit de présenter les sorties synthétiques du test informatique comme des mesures de cellules réelles.