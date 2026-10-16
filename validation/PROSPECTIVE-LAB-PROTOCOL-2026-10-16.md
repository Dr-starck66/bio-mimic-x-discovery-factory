# BIO-MIMIC X — Demande de validation expérimentale indépendante (non exécutée)
16 octobre 2026 — proposition de protocole pour discussion avec un laboratoire spécialisé.

## Diagnostic actuel (ne pas masquer les résultats)
Deux jeux de mesures biologiques réels ont été retraités par le logiciel, avec une hypothèse consignée **avant** inspection : GSE74387 et GSE113081. Le test préenregistré **ne passe pas dans les deux cohortes**. La validation causale et la découverte originale restent non prouvées. Réf. `validation/PREREG-GEO-2026-10-16.md`; sorties machine dans les artefacts du workflow `geo-realdata-audit`.

## Nouvelle hypothèse causale, prospectivement falsifiable
**Une matrice extracellulaire issue d'Acomys et des facteurs solubles issus de macrophages d'Acomys interagissent de manière non additive pour réduire la différenciation myofibroblastique des fibroblastes de Mus.**

Ceci est une **proposition** d'hypothèse, pas une découverte revendiquée. Avant brevetabilité ou commercialisation, réaliser une revue d'antériorité ciblée. L'effet de sécrétions macrophagiques d'Acomys sur des fibroblastes (Adam et al., Developmental Cell, 2024), et des ECM d'Acomys sur des macrophages (ACS Biomaterials, 2025) sont déjà publiés. Notre hypothèse concerne une **interaction croisée factorielle** dont la nouveauté reste à vérifier.

## Expérience proposée par laboratoire tiers
Système *in vitro* idéalement alimenté par matériaux existants (limiter coûts et nouveaux animaux) ; fibroblastes primaires de Mus dans les quatre conditions factoriellement randomisées :
1. ECM Mus + surnageant macrophages Mus : contrôle.
2. ECM Acomys + surnageant macrophages Mus : effet ECM.
3. ECM Mus + surnageant macrophages Acomys : effet surnageant.
4. ECM Acomys + surnageant macrophages Acomys : interaction.

### Mesure primaire et statistique
Fraction de cellules ACTA2/alpha-SMA positives après culture dans chaque condition, quantifiée sur images par analyse à l'aveugle, normalisée par témoin Mus/Mus. Paramètre **pré-spécifié** : terme d'interaction `beta_ECM_Acomys * macrophage_Acomys` d'un modèle factoriel avec effets aléatoires donneur/lot. Hypothèse directionnelle : interaction <0 ; succès uniquement si intervalle de confiance bilatéral 95% entièrement <0 **et** effet de taille supérieur au seuil minimal défini par le laboratoire avant acquisition des résultats. Réplication indépendante du processus de culture requise.

Critères secondaires séparés (non requalifiables en critère primaire si échec) : production de collagène I, expression COL1A1/FN1, collagène fibrillaire et viabilité cellulaire, sans inférence de cicatrisation *in vivo*.

### Qualité obligatoirement consignée
- Au moins 3 donneurs biologiques indépendants par espèce **si disponibles** ; taille finale fixée après étude de puissance préalable avec comité scientifique, et réplicats techniques non traités comme donneurs indépendants.
- Identité des espèces, indépendance des donneurs, âge/sexe/lot, orientation de culture, concentration des facteurs, rigidité des ECM, dosage protéique, contamination, viabilité et dates tracés.
- Randomisation de l'ordre des quatre conditions ; analyse en aveugle ; scripts et critères d'exclusion verrouillés *avant* décodage des étiquettes.
- Matrice de fibronectine ou contrôle acellulaire standardisé si le partenaire juge nécessaire pour contrôler la rigidité et le support ; possibilité de recours à des protéines recombinantes disponibles si tissus indisponibles, avec indication claire qu'il s'agit d'un autre système expérimental.
- Réplication dans un second lot et si possible dans un second laboratoire. Contrôles négatifs obligatoires ; pas de promotion si contrôles invalides.
- Aucune acquisition nouvelle sur animaux avant approbation éthique institutionnelle quand applicable.
- Dépôt horodaté des données brutes, métadonnées anonymisées et méthode de quantification ; signatures du biologiste responsable ; chaînes d'intégrité des fichiers.

## Décision go/no-go
1. Un laboratoire confirme par écrit qu'il possède le matériel et la compétence pour effectuer une petite étude pilote et que les droits sur les résultats seront négociés par les institutions.
2. Un expert indépendant réalise une recherche d'antériorité et signale toute publication sur l'interaction proposée.
3. Si positif : validation pilote, étude de puissance, puis exécution *prospective* blindée. Si négatif : **FAIL**, conserver l'apprentissage, abandonner la revendication.
4. Ne jamais considérer cette réanalyse ou ce protocole comme un résultat biologique original de BIO-MIMIC X avant nouvelle collecte et analyse indépendantes.

## Partenaires académiques à contacter (non engagés)
- Prof. Ashley W. Seifert, University of Kentucky (correspondance publique : awseifert@uky.edu) : biologie régénérative d'Acomys.
- Prof. Kerstin Bartscherer, Universität Osnabrück (correspondance publique : kerstin.bartscherer@uni-osnabrueck.de) : mécanismes ERK et régénération d'Acomys.
- Recherche collaborative sans financement initial souhaitée, mais **aucune gratuité ou acceptation présumée**.

Références : PMID 38228141 (macrophages), PMID 40407745 (ECM cell-derived), PMID 40534468 (protéomique ECM), GSE74387, GSE113081.
