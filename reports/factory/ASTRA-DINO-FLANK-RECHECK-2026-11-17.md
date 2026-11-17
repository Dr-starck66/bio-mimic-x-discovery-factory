# ASTRA DINO Ω — réanalyse comparative indépendante des sorties existantes (17 novembre 2026)

**Statut : PASS calcul de cohérence documentaire / PARTIAL valeur scientifique.** Ce rapport ne revendique **pas** une nouvelle exécution du VCF brut, ni une validation externe ni un effet causal.

## Source relue indépendamment dans GitHub
- PR de base [#52](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/52), branche `astra/dino-omega-ancestry-benchmark-20261114`.
- `reports/factory/astra_dino_joint_flank_sensitivity_20261114.json`, blob Git `617bbe52d9d3214e9a3b16805bcd0c0b641a05d2`.
- `reports/factory/astra_dino_alx1_hmga2_joint_real_evidence_20261114.json`, blob Git `5453b3c4bd471c9fd4ace914e719ae4b01da1fc8`.

## Recalculs sur les valeurs **publiées dans les reçus existants**
Pour le caractère « taille du bec, log-moyenne géométrique 3D », après prise en compte des groupes de population :
- R² intra-populations **modèle principal des corps de gènes** ALX1/HMGA2 : **0,18450212**.
- R² intra-populations **modèle exploratoire des flancs droits** : **0,28766202**.
- Différence arithmétique : **+0,10315990 de R²** (+**55,91 %** relativement au modèle principal). La comparaison est *post hoc* et non une estimation de gain prédictif externe.
- P corrigée sur les huit comparaisons exploratoires (4 modèles × 2 caractères) : **0,0846915308469153** pour le modèle principal ; **0,008399160083991601** pour le flanc droit. Le premier résultat n'atteint pas 5 %, le second est une association exploratoire.
- Avec les **10 000 permutations** et la convention publiée `p=(k+1)/(10000+1)`, ces valeurs correspondent exactement à **846** et **83** tirages nuls au moins aussi extrêmes que les observations respectives ; calcul arithmétique refait dans cette session.
- Contrôle négatif documentaire préexistant : `VCF_REF_FASTA_MISMATCH:1`, rejet d'allèle REF muté.

## Analyse critique indépendante
Le modèle exploratoire au flanc droit est plus associé à la taille du bec, dans cet échantillon, que le modèle utilisant les SNP présents dans les corps de gènes. **Hypothèses concurrentes** : variant régulateur externe, déséquilibre de liaison (LD) avec un autre locus, structure de population résiduelle, instabilité de petit effectif, sélection du meilleur modèle après inspection. Ce différentiel de R² **ne localise pas un mécanisme causal** et n'est **pas** une performance prédictive validée hors cohorte.

**Plan de falsification avec les briques déjà créées :** appliquer *sans réentraînement* le modèle gelé `validation/astra_dino_external_locked.py` à des oiseaux indépendants possédant génotype et mesures du *même individu*, puis comparer contre la baseline Oslo, avec permutations intra-cluster, contrôle des variants/allèles et correction multiplicité. Les coauteurs ont été mis en copie du contact scientifique ; **aucun nouveau crosswalk individuel n'a été reçu**. Ne pas inventer d'appariements, ne pas transférer les spécimens privés sur GitHub.

**Conclusion :** nouvelle comparaison arithmétique contrôlée et conservée, mais aucune preuve neuve d'un effet biologique causal ou d'une généralisation externe. Aucun coût, aucune automation, aucune fusion de PR.
