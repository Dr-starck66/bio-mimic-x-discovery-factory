# ASTRA Ω — exploitation scientifique des correspondances (16 novembre 2026)

**Statut scientifique : PARTIAL.** Reçus Gmail confirmés pour trois réponses envoyées le 16/11 : chercheurs axolotl, équipe des pinsons de Darwin (coauteurs en copie) et CRB INRAE. EHM et ANT Robotics avaient déjà reçu des réponses, aucun doublon. Ce compte rendu ne reproduit pas les mails privés ; **autorisation de citation des chercheurs : en attente**.

## BIO-MIMIC X : correction d'identité HAND1/HAND2
- Selon les précisions scientifiques reçues, modèle historique `AMEX60DD030069` : **HAND1** (correction de l'étiquette auparavant ambiguë `HAND1 [nr]|HAND2 [hs]`). Modèle historique distinct `AMEX60DD045298` : **HAND2**. Transcript `AMEX60DD201045298.1` et scaffold `AMEXG_0030001686` : pistes de recherche, non une preuve de lift-over exact.
- Preuve de séquences **déjà présente** dans le dépôt : `HAND2-ASSEMBLY-SEQUENCE-PROBE-LATEST.json` et `HAND2-HAND1-SEQUENCE-CORRIGENDUM-2026-11-01.md`. Sur 27 332 31-mers distincts de l'ancien locus, 26 858 recoupent HAND1 moderne (98,27 % de recouvrement de k-mers) contre 8 avec HAND2. Il ne s'agit pas de 98,27 % d'identité nucléotidique.
- **Incidence** : l'ancienne observation transcriptomique axolotl `-0,0208` sur `AMEX60DD030069` doit rester archivée mais **ne peut plus être qualifiée de HAND2** ni comparée directement à l'observation humaine HAND2 `-0,1378`. Une hypothèse de régénération clinique n'en découle pas.
- Nouvelle expérience préenregistrable : alignements réciproques FASTA/GTF anciens et UKY_AmexF1_1, recherche d'unicité sur génome entier, contrôles paralogues et orientations, vérification exons/coordonnées et lift-over officiel dès publication. **Crosswalk interassemblages exact : UNVERIFIED**.

## ASTRA DINO Ω : ne pas transformer une orientation vers les archives en cohorte validée
- L'orientation scientifique reçue renvoie aux archives des revues et aux coauteurs. **Aucun nouveau crosswalk individuel transmis** à ce jour.
- **Réemploi sans duplication : PR #52**, branche `astra/dino-omega-ancestry-benchmark-20261114`. Audit préexistant Oslo 2025 / Rubin 2022 : **50** oiseaux avec génotypes et morphométrie appariés, **11** populations ; blocs Data S2 **394** SNP HMGA2, **238** ALX1 (après filtres).
- Modèle initial conjoint : p globale corrigée pour taille du bec **0,0847** : non significatif à 5 %. Fenêtre droite exploratoire : p corrigée **0,0084**, mais **causalité non démontrée** (déséquilibre de liaison, voisinage génomique, sélection).
- Critères pour cohorte vraiment indépendante : provenance/licence/SHA, crosswalk 1:1 génotype–mesures, exclusion de doubles individus/parents, assemblage versionné, train/test par population sans fuite, baseline sans génotype, permutations intra-populations, fenêtres négatives appariées, correction multiplicité sur la famille entière ; rapports des résultats défavorables conservés.

## PHYTOFORGE Ω
- Le CRB INRAE a transmis l'interrogation aux équipes **IGEPP DEBI et RCA**. Pas encore de données partagées ni de mesures de sélénium ; aucune validation biofortification revendiquée.

## Garde d'audit
- Enregistrement structuré : `reports/factory/astra_scientific_returns_20261116.json`
- Contrôle sans dépendance : `node validation/astra_scientific_returns_gate.mjs`
- 1 baseline + 7 contrôles négatifs adversariaux (substitution HAND2, faux PASS lift-over, comparaison humaine interdite, faux significatif DINO, cohorte fictive, citation sans autorisation, données phyto inventées).
- **Un PASS du garde signifie cohérence documentaire et logicielle uniquement, pas de test d'identité génomique, pas de validation biologique et pas de publication revue par les pairs.**
- Aucune nouvelle automation, aucune dépense, aucun fichier génétique privé ajouté au dépôt.
