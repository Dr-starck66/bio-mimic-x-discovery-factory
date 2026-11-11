# ASTRA Ω — VIH : programme de recherche sur les réservoirs (08/11/2026)

**Statut scientifique : PARTIAL. Guérison stérilisante généralisable : UNVERIFIED / non démontrée.**
Aucune donnée biologique personnelle, aucun prélèvement, aucune proposition d'interruption du traitement, aucune manipulation expérimentale de VIH et aucun nouvel abonnement ou cron.

## Réutilisation des briques existantes
Source canonique : [ASTRA_REGISTRY](https://github.com/Dr-starck66/indexation/blob/main/ASTRA_REGISTRY.md) (276 entrées documentaires, non toutes exécutables).
- ASTRA-234 BIO-MIMIC X DISCOVERY FACTORY, ASTRA-235 BIO-MIMIC X AUTONOMOUS LAB : infrastructure existante pour hypothèses et dossiers scientifiques ; pas de modèle VIH validé.
- ASTRA-242 AION ARC : exploration et discrimination d'hypothèses ; mise en marche sur VIH non démontrée.
- ASTRA-254 THEOS-X Evidence Lab : validation indépendante à vérifier.
- ASTRA-001, ASTRA-002, ASTRA-005, ASTRA-070, ASTRA-083, ASTRA-086, ASTRA-087 : gardes de provenance, exécution contrôlée, coût nul et coordination. Le registre n'établit pas leur branchement effectif pour cette mission.
- Code natif réutilisable dans ce dépôt : `factory/hypothesis_engine.py` (hypothèses falsifiables), `factory/debate_engine.py` (objections), `factory/experiment_planner.py` (tests CONCEPTUELS, jamais considérés exécutés), `factory/scientific_memory.py` (piste d'audit). Ces modules ont été inspectés, pas exécutés sur les données VIH par un runner connecté dans cette mission.

## Faits vérifiés, contrôles défavorables et limites
| ID | Publication | Observation | Ce qui n'est PAS démontré |
| --- | --- | --- | --- |
| RIO-2026 | [Lancet HIV / PMID 41674620](https://pubmed.ncbi.nlm.nih.gov/41674620/) | Essai randomisé n=68 : 75% sans rebond à 20 semaines avec deux bNAbs, 11% avec placebo ; 7 avec contrôle >96 semaines | Éradication ; généralisation aux infections anciennes |
| COMBO-2026 | [Nature / PMID 40166020](https://pubmed.ncbi.nlm.nih.gov/40166020/) | Vaccin thérapeutique + agoniste TLR9 + bNAbs : 7/10 avec contrôle partiel ou complet après intervention | Étude sans groupe témoin ; aucun zéro réservoir |
| Q4-2026 | [Nature Communications / Q4ddPCR](https://pmc.ncbi.nlm.nih.gov/articles/PMC13035820/) | Quantification du réservoir intact dans 95% des échantillons de quatre cohortes ; concordance accrue avec séquençage | Un test négatif n'exclut pas un réservoir ailleurs ; validation limitée au sous-type B |
| GREFFE-2026 | [IAS AIDS 2026](https://iasociety.org/blog/aids-2026-key-takeaways) | Rémissions exceptionnelles après greffe de cellules souches en contexte de cancer | Méthode sûre, générale et reproductible pour personnes sans cancer |
| EXCISION-2026 | [Scientific Reports](https://www.nature.com/articles/s41598-026-64038-1) | Produit investigational fondé sur recombinase : fabrication documentée, étude humaine en préparation | Preuve d'excision complète du VIH chez un patient et innocuité clinique |
| A5413-2026 | [ACTG](https://actgnetwork.org/article/actg-launches-hiv-cure-study-evaluating-novel-approach-targeting-the-hiv-reservoir/) | Essai randomisé d'impact sur réservoir lancé en 2026 | Résultat positif ou guérison |

## Hypothèse prioritaire, non vérifiée
**Une guérison généralisable nécessiterait probablement de combiner** : (i) mesure du réservoir intact plutôt que l'ADN total ; (ii) intervention ciblant ou rendant accessibles les cellules à provirus intact ; (iii) élimination immunitaire et protection contre les échappements ; (iv) confirmation par méthodes orthogonales, y compris suivi prolongé et prise en compte des tissus.

Ce n'est pas un protocole thérapeutique ni une association de médicaments démontrée. Les mécanismes de ciblage et de distribution à toutes les cellules restent non résolus.

### Hypothèses concurrentes et critères de réfutation
1. **Éradication biologique** : tous les provirus compétents ont disparu. *Réfutation* : virus réplicatif détecté par test indépendant, ou rebond virologique sous suivi clinique approprié.
2. **Rémission immunologique** : virus toujours présent mais contrôlé. *Réfutation d'une affirmation d'éradication* : séquences intactes résiduelles, rebond tardif, effet durable des anticorps.
3. **Artefact de mesure** : diminution apparente due à variants non détectés, prélèvements insuffisants, sous-type inadéquat ou génomes défectueux comptés. *Contrôles* : séquençage orthogonal, Q4ddPCR et autres méthodes validées, suivi longitudinal, tissus si autorisés dans la recherche.
4. **Échappement / toxicité** : sélection de variants résistants, toxicité immune ou effets hors cible ; un succès virologique partiel ne compense pas une perte de sécurité clinique.

### Passages obligatoires avant une affirmation de guérison
Source primaire + population/critère précisés → validation indépendante → mesures du réservoir compétent par au moins deux méthodes → absence de signal clinique de rebond avec surveillance appropriée → reproductibilité sur populations et tissus distincts → évaluation sécurité et durée. Aucune étape n'est considérée passée par le seul présent rapport.

## Sécurité et statut
- **PASS** : provenance primaire consultée, matrice d'hypothèses/documentation créée dans une branche isolée.
- **PARTIAL** : priorisation scientifique documentaire.
- **UNVERIFIED** : élimination définitive, données VIH expérimentales indépendantes, intégration automatique des briques, efficacité thérapeutique.
- Les interruptions d'antirétroviraux n'ont leur place que dans des essais autorisés et supervisés. Ne jamais arrêter ou modifier un traitement sur la base de ce document.
- Financement additionnel : 0 € ; GitHub Actions déclenchées volontairement : 0 ; aucun contact sortant.

Contact scientifique institutionnel potentiel (non sollicité) : [ANRS Rhiviera](https://anrs.fr/recherche/projets-de-recherche/consortium-rhiviera/).

**Prochaine expérience documentaire unique :** extraire les critères de succès et les échecs de chaque essai VIH (registre TAG octobre 2026), puis chercher lesquels discriminent l'éradication de la simple rémission.
