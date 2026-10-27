# BIO-MIMIC X — Note de clarification scientifique sur les réanalyses GEO
**Date : 27 octobre 2026** · **Statut : PARTIAL (résultat observationnel non répliqué au seuil préenregistré)**

## Objet et intégrité
Ce document **complète**, sans modifier, remplacer ou réinterpréter rétroactivement, le protocole daté du 16 octobre 2026 : [PREREG-GEO-2026-10-16.md](PREREG-GEO-2026-10-16.md).
Il distingue une signature descriptive de réponse transcriptomique de la question mécanistique prospectivement proposée sur l'interaction matrice extracellulaire (ECM) × signaux macrophagiques. Ni l'une ni l'autre ne constituent une découverte biologique causale validée.

## Résultats calculés sur les données publiques
Source traçable : exécution GitHub Actions du 18 octobre 2026, [GEO Data Audit #39138691418](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/39138691418) ; script [run_geo_validation.py](run_geo_validation.py). Les valeurs suivantes proviennent des lignes `REAL_GEO_RESULT` des journaux, et non d'une nouvelle analyse.

| Cohorte | Technologie | Δ proportion de réponses « vers le basal » Acomys − Mus | IC 95 % bootstrap animaux / échantillons biologiques | Contrôle négatif : permutation jours 7/14, p descriptif | Critère préenregistré |
| --- | --- | ---: | --- | ---: | --- |
| GSE74387 | Microarray | +0,1006368 | [−0,0724913 ; +0,1930771] | 0,66337 | **FAIL** (l'IC inclut zéro) |
| GSE113081 | RNA-seq | +0,1234107 | [+0,0294586 ; +0,1897169] | 0,31683 | **PASS individuel**, sous le critère prévu |

Le critère d'annonce « **répliqué indépendamment** » exigeait **dans chaque cohorte** Δ ≥ 0,05, IC 95 % strictement supérieur à zéro et aucun défaut qualité critique. Il **n'est PAS satisfait**. Les deux estimations ponctuelles sont orientées dans le même sens, mais leur compatibilité en direction ne suffit pas à valider une réplication. Les contrôles négatifs descriptifs ne constituent pas une confirmation indépendante et ne doivent pas être omis.

Métadonnées originales : [GSE74387](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE74387) (puces Affymetrix conçues pour *Mus*, également utilisées sur *Acomys*, 5 à 6 réplicats biologiques par condition) et [GSE113081](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE113081) (RNA-seq par espèce, 3 à 4 réplicats par condition). Les risques de comparabilité interespèces, de biais de sondes, de normalisation et de couverture génétique nécessitent une revue indépendante ; leur impact exact sur les estimations affichées **n'a pas été démontré ici**.

## Limite de pertinence du critère
Le critère original est la *proportion de caractéristiques transcriptionnelles se rapprochant du niveau basal entre jours 7 et 14*. Ce n'est **ni une mesure directe de cicatrisation sans fibrose, ni une mesure de différenciation myofibroblastique, ni une preuve d'interaction ECM × macrophages**.

La littérature comparant l'évolution du protéome cutané chez *Acomys* et *Mus* suggère que le retour au profil basal au jour 14 peut accompagner une cicatrisation terminée chez *Mus*, alors que des processus régénératifs continuent chez *Acomys* : [Comparative Proteomic Analysis in Scar-Free Skin Regeneration](https://pmc.ncbi.nlm.nih.gov/articles/PMC6957500/). Cette observation **justifie une critique biologique de l'indicateur**, non l'effacement ou la requalification de son résultat préenregistré.

## Question scientifique distincte à soumettre à un laboratoire
La proposition [PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md](PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md) demande de tester **l'interaction non additive** entre ECM déposée par les cellules d'*Acomys* vs *Mus* et milieux conditionnés macrophagiques d'*Acomys* vs *Mus* sur la fraction de fibroblastes *Mus* ACTA2/alpha-SMA positifs. Ce pilote factoriel 2×2 randomisé et aveugle **n'a pas été exécuté**. Sa nouveauté, sa faisabilité, sa puissance statistique et ses contrôles doivent être examinés indépendamment avant collecte de nouvelles données. Les résultats GEO ci-dessus ne sont **pas** des résultats de ce pilote.

## Demande de revue critique (sans prétendre à une collaboration acquise)
1. L'indicateur temporel préenregistré avait-il une pertinence biologique suffisante et quels biais techniques pourraient expliquer l'incertitude ou les contrôles négatifs ?
2. L'interaction ECM × macrophages est-elle déjà démontrée ou infirmée dans la littérature ?
3. Existe-t-il des jeux de données ou matériaux **préexistants**, accessibles sous les autorisations appropriées, permettant une vérification *in silico* ou un pilote raisonnablement dimensionné ?
4. Quels témoins de matrice, de viabilité, de dose, de lot, de donneurs indépendants et de signalisation ERK seraient indispensables ?

**Ligne de communication :** « Réanalyse rétrospective transparente, signal ponctuel de même direction dans deux cohortes, critère de réplication globale non atteint. Nous recherchons une appréciation critique indépendante de la pertinence d'une question mécanistique distincte et falsifiable. » 

**Aucune revendication** de validation biologique indépendante, efficacité humaine, brevetabilité, engagement d'un laboratoire ou financement acquis.
