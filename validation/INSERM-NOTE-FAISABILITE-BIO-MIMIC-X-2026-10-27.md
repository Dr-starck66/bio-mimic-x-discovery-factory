# BIO-MIMIC X — Note scientifique de faisabilité
**Document pour avis critique préliminaire — 27 octobre 2026**  
**Objet :** interaction entre matrice extracellulaire et facteurs sécrétés par les macrophages dans la différenciation myofibroblastique comparée *Acomys* / *Mus*  
**Statut :** question expérimentale proposée, **non validée**, aucun partenaire ou financement acquis.  
**Porteur :** projet informatique de recherche indépendant, sans affiliation institutionnelle revendiquée.

## 1. Question scientifique (ce que nous proposons réellement)
Les fibroblastes *Mus* exposés à une matrice extracellulaire (ECM) déposée par des cellules d'*Acomys* **et** à un milieu conditionné par des macrophages d'*Acomys* présentent-ils une réduction **non additive** de la différenciation myofibroblastique par rapport aux effets de chacune des deux interventions considérée seule ?

Cette interaction factorielle est une **hypothèse à falsifier**, pas un mécanisme déjà démontré, ni une proposition thérapeutique pour l'humain. Son **originalité reste à vérifier** par revue d'antériorité indépendante.

## 2. Fondement dans la littérature (sans appropriation des découvertes d'autrui)
- **Simkin et al., *Developmental Cell* (2024), PMID 38228141 :** sécrétions de macrophages d'*Acomys*, réponse de fibroblastes et implication de VEGFC / lactotransferrine dans le contexte de la régénération auriculaire. [DOI 10.1016/j.devcel.2023.12.017](https://doi.org/10.1016/j.devcel.2023.12.017).
- **Dill et al., *ACS Biomaterials Science & Engineering* (2025), PMID 40407745 :** matrice déposée par des fibroblastes *Acomys* / *Mus*, différences de composition et modulation de marqueurs macrophagiques. [DOI 10.1021/acsbiomaterials.5c00810](https://doi.org/10.1021/acsbiomaterials.5c00810).

Ces deux publications **ne suffisent pas à démontrer** l'interaction ECM × milieu conditionné macrophagique sur l'endpoint choisi. La vérification des expériences déjà menées est une condition préalable.

## 3. Proposition minimale pour discussion (non exécutée)
Plan factoriel **2 × 2** sur fibroblastes *Mus*, avec (i) ECM *Mus* ou *Acomys* et (ii) milieu conditionné macrophagique *Mus* ou *Acomys* : quatre conditions, randomisées et évaluées à l'aveugle.  
**Mesure primaire envisagée :** proportion de cellules ACTA2/α-SMA positives, avec estimation du terme d'interaction ECM × milieu conditionné dans un modèle tenant compte des donneurs biologiques et des lots. Seuil d'effet minimal pertinent, effectif et plan statistique **à fixer avant toute collecte** avec le laboratoire. Contrôles : viabilité, rigidité/composition/lot d'ECM, dose/normalisation du milieu, témoins négatifs, reproductibilité interlots, indépendance des donneurs. 
Aucune donnée de ce pilote n'a été produite. Toute éventuelle expérimentation requerra des accords institutionnels et autorisations applicables.

## 4. Données informatiques déjà disponibles — limites explicites
Deux jeux publics ont été réanalysés selon des critères enregistrés le 16 octobre 2026 : [GSE74387](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE74387) (puce ADN) et [GSE113081](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE113081) (RNA-seq). L'écart ponctuel descriptif *Acomys − Mus* va dans le même sens (+0,101 et +0,123), mais le critère **global de réplication préenregistré n'a pas été satisfait**, car l'IC bootstrap 95 % de GSE74387 recouvre zéro [−0,072 ; +0,193]. Les permutations négatives rapportées n'apportent pas de confirmation convaincante. Des problèmes potentiels de sondes interespèces, d'orthologie et d'indépendance des cohortes imposent des vérifications complémentaires.

**Ces données n'évaluent pas directement la question ECM × macrophages.** Aucun résultat causal original, aucune application clinique et aucune validation indépendante de cette interaction ne sont revendiqués. [Préenregistrement](PREREG-GEO-2026-10-16.md) · [Rapport chiffré et contrôles négatifs](NOTE-INTERPRETATION-GEO-2026-10-27.md) · [Exécution reproductible et journaux](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/39138691418).

## 5. Trois questions précises pour l'équipe de recherche
1. **Pertinence et nouveauté :** l'interaction ECM × signaux macrophagiques ainsi définie est-elle biologiquement défendable et encore ouverte dans la littérature ?
2. **Faisabilité et contrôles :** un modèle cellulaire à quatre conditions et son endpoint α-SMA vous semblent-ils adéquats ? Quels contrôles ou critères d'abandon imposeriez-vous ?
3. **Voie la moins coûteuse :** des données ou matériaux **déjà disponibles** permettraient-ils d'abord une revue computationnelle indépendante ou une étude pilote restreinte, *uniquement si* un laboratoire volontaire le juge possible ?

**Demande actuelle :** avis critique préliminaire ou orientation vers un interlocuteur adapté, **sans présumer d'un engagement, de moyens gratuits ou d'une collaboration acceptée**.  
**Document technique complet :** [Protocole prospective in vitro](PROSPECTIVE-LAB-PROTOCOL-2026-10-16.md).  
**Dépôt et historique public :** [Dr-starck66/bio-mimic-x-discovery-factory](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory).
