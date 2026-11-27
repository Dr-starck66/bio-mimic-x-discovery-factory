# BIO-MIMIC X Ω — Audit de sources humaines indépendantes et d'une période après arrêt

**2026-11-23 — Statut PARTIAL (biologie réelle publiée, calcul descriptif local, aucune réparation permanente prouvée)**.

L'adaptateur validation/vva_published_aggregate_bridge.py analyse des agrégats publiés. Il ne remplace PAS le moteur patient-level validation/vva_repair_gate.py. Aucun patient ne peut être artificiellement recréé à partir des moyennes ± écarts-types : aucun bootstrap, p-valeur ou intervalle de confiance par patient n'est calculé ici.

## Chen et al. 2018

Source primaire : https://onlinelibrary.wiley.com/doi/10.1155/2018/6452709 (tableaux 2, 3, 4). Essai randomisé placebo, 12 semaines de formulation phytothérapeutique *Erzhi modifiée*, 4 semaines d'observation **après arrêt**. 88 incluses, 75 ont terminé (39 intervention, 36 placebo), 11 perdues de vue + deux exclusions. Ni estradiol ni hydrogel ECM ne sont testés dans ce volet.

La différence-des-changements sur moyennes est orientée selon l'amélioration préspecifiée : (T_t−T_initial)−(P_t−P_initial) multiplié par la direction. Le pourcentage ci-dessous est le ratio descriptif signal sem16/signal sem12, PAS un taux de guérison.

| Critère | Signal à S12 pendant traitement | Signal à S16 (4 semaines après arrêt) | Part maintenue |
|---|---:|---:|---:|
| Cellules superficielles, points de % | +5,02 | +4,12 | 82,1 % |
| Cellules basales, points de %, orientation inversée | +23,02 | +17,97 | 78,1 % |
| Santé vaginale, score | +4,82 | +3,56 | 73,9 % |
| Hydratation, score | +1,05 | +0,82 | 78,1 % |
| Élasticité clinique, score | +0,67 | +0,62 | 92,5 % |
| Aspect muqueux, score | +1,08 | +0,98 | 90,7 % |
| Vaginite, score orienté | +3,14 | +2,41 | 76,8 % |

**Résultat négatif obligatoire :** les 7 indicateurs ont reculé entre S12 et S16. Quatre semaines ne démontrent pas une régénération durable. L'élasticité clinique n'est pas une mesure histologique de la matrice extracellulaire. Aucune donnée patient-level ni covariance disponible dans ces tableaux.

## Mitchell et al. 2018 — contrôle externe symptômes vs cytologie

Source primaire : https://pmc.ncbi.nlm.nih.gov/articles/PMC5885275/ . 302 randomisées (estradiol 102, hydratant 100, double placebo 100), sans suivi après arrêt. Changement moyen du symptôme le plus gênant à 12 semaines : estradiol −1,4 vs placebo −1,3 ; comparaison principale non significative. Une maturation cytologique au-delà du seuil de 5 % de cellules superficielles est obtenue pour 57 % des échantillons évaluables sous estradiol, 11 % sous placebo et 11 % sous hydratant. Les effectifs randomisés ne sont PAS les dénominateurs de ces cytologies. Les deux études ont des interventions différentes : pas de méta-analyse commune.

## Verdict

- **PASS calcul local** : vrais tableaux publiés retranscrits, sept contrastes groupe-placebo et deux critères de contrôle négatif calculés ; 12 nouveaux tests sur 12 et 10 tests antérieurs sur 10 réussis localement.
- **PARTIAL biologie** : persistance partielle de maturation cytologique à quatre semaines hors intervention, sans statistiques patient-level, à risque de biais d'attrition.
- **UNVERIFIED** : épaisseur histologique, barrière TEER, organisation collagène/élastine, antifibrose, régénération tissulaire durable à 3/6/12 mois après arrêt, efficacité de BIO-MIMIC X.

Cette PR est une validation exploratoire en branche et ne modifie ni un traitement de patientes, ni un site de production. Avant publication scientifique : double extraction indépendante des tableaux et accès à données appariées par personne ou animal.
