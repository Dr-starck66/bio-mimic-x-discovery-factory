# ASTRA Ω — Confrontation des hypothèses avec ANRS RHIVIERA (08/11/2026)

**Périmètre :** sources publiques institutionnelles et articles scientifiques. **Pas** d'examen d'échantillons biologiques, d'accès aux données médicales individuelles, ni d'intervention clinique. **L'élimination définitive du VIH n'est pas démontrée.**

## Piste de preuve
- Registre ASTRA : [source canonique](https://github.com/Dr-starck66/indexation/blob/main/ASTRA_REGISTRY.md). Réemploi des briques ASTRA-234 / ASTRA-235, des fonctions effectives `factory/hypothesis_engine.py`, `factory/debate_engine.py`, `factory/experiment_planner.py` et `factory/scientific_memory.py`.
- Entrées primaires structurées : [rhiviera_public_evidence.json](./rhiviera_public_evidence.json) (6 références, 2 protocoles humains, 3 analyses animales et 1 observation humaine ex vivo).
- Raccordement : [rhiviera_bridge.py](./rhiviera_bridge.py) (hypothèse causale + hypothèses alternatives, objections explicites, proposition conceptuelle et mémoire locale optionnelle). La mémoire n'est **pas** modifiée automatiquement.
- Garde : [tests/test_rhiviera_bridge.py](../../tests/test_rhiviera_bridge.py), contient 11 tests et contrôles négatifs. Le code enregistré n'est **pas** une exécution de ces tests sur l'infrastructure distante.

## Observations confrontées

| Ensemble | Preuve effectivement publique | Ce qui survit comme hypothèse | Contradiction / limite |
| --- | --- | --- | --- |
| ANRS 175 RHIVIERA-01 | [fiche ANRS](https://anrs.fr/infrastructures/donnees-et-echantillons/anrs-175-rhiviera-01/) ; critère VIH-ARN <400 copies/mL à S24, participants avec profil HLA prédéfini | HLA / contexte immunogénétique pourraient prédire un contrôle post-traitement | Pas de résultats de l'essai récupérés ; critère défini ≠ efficacité observée |
| ANRS 176 RHIVIERA-02, NCT05300035 | [fiche ANRS](https://anrs.fr/infrastructures/donnees-et-echantillons/anrs-176-rhiviera-02/) ; essai de phase II placebo contrôlé de 3BNC117-LS + 10-1074-LS et ART en primo-infection | Anticorps pourraient prolonger le contrôle sans ARV | Résultats spécifiques de RHIVIERA-02 **non vérifiés**. Les résultats RIO ne lui appartiennent pas |
| pVISCONTI réservoirs | [Charre et al., Nat Commun 2026](https://www.nature.com/articles/s41467-026-69720-6) : 11 contrôleurs / 11 non-contrôleurs macaques, provirus intact ganglionnaire plus faible avant ATI chez contrôleurs et association avec CD8 | Taille et qualité du réservoir tissulaire + fonction CD8 prédiraient le rebond | Corrélation ≠ cause, SIV macaque ≠ VIH humain, tests tissulaires incomplets |
| pVISCONTI NK | [Chapel et al., Nat Commun 2026](https://www.nature.com/articles/s41467-026-76699-7) : 6 contrôleurs / 6 non-contrôleurs macaques ; phénotypes NK associés au contrôle | Sous-populations NK préexistantes pourraient orienter le contrôle | Cohorte pVISCONTI **non indépendante** de l'étude précédente ; causalité non prouvée |
| pVISCONTI muqueuse | [Hua et al., Nat Commun 2026](https://www.nature.com/articles/s41467-026-69848-5) : phénotype CX3CR1-high des macrophages intestinaux associé au contrôle SIV | Homéostasie muqueuse contribuerait au contrôle | Même programme pVISCONTI, pas une troisième réplication indépendante |
| Latence ex vivo | [Dorman et al., Nat Commun 2025](https://www.nature.com/articles/s41467-025-57290-y) : ARN VIH retenu dans le noyau, 22 cultures ex vivo de personnes sous ARV ; facteurs MATR3/MTR4/Rev | Blocage post-transcriptionnel contribue à la latence | Phénomène ex vivo ; réactivation ≠ destruction de cellules infectées ; pas de guérison démontrée |

**Groupe d'observations réellement distincts : 2** (une cohorte animale pVISCONTI, un ensemble ex vivo humain) ; les deux fiches RHIVIERA-01/-02 sont des protocoles, pas des résultats cliniques récupérés. La présence d'analyses multiples d'une même étude ne constitue pas une réplication externe.

### Comparateur externe, volontairement séparé
Le [RIO trial](https://pubmed.ncbi.nlm.nih.gov/42202839/), phase II randomisée humaine (68 personnes), observe une prolongation du contrôle sans antirétroviraux avec les mêmes anticorps : 75 % sans rebond défini à 20 semaines contre 11 % avec placebo. **RIO est indépendant de RHIVIERA-02**. La rémission n'est pas une élimination totale du VIH.

## Confrontation / objections
1. **Hypothèse réservoir intact + CD8 :** données animales associatives concordantes ; absence de démonstration de causalité et de généralisation humaine. Alternative : faible réservoir = marqueur d'une réponse immunitaire favorable et non moteur autonome.
2. **Hypothèse NK / muqueuse :** mécanismes complémentaires plausibles, mais la même cohorte peut produire des signaux corrélés ; ne pas multiplier artificiellement le niveau de preuve. Alternative : des états immunitaires précèdent la réponse sans en être la cause.
3. **Hypothèse double anticorps :** bénéfice clinique externe plausible (RIO) ; pas de résultats propres RHIVIERA-02. Alternative : effet pharmacologique transitoire et sélection de résistance ; rémission ≠ éradication.
4. **Hypothèse levée de latence :** blocage cellulaire réversible documenté ex vivo ; relance de la transcription ne suffit pas à détruire le réservoir. Risque d'effets biologiques non désirés sans preuve préclinique/clinique rigoureuse.

## Vérification et limites
- **PASS** : fichiers de branche et sources institutionnelles accessibles ; six observations/protocoles documentés avec provenance, groupes de cohorte et contrôles négatifs.
- **PARTIAL** : raccordement Python avec les modules existants et audit de cohérence ; le harnais local de compatibilité (copies reconstruites de modules et jeu de données réduit) a passé 10 tests, ce qui **ne prouve pas** le succès des 11 tests GitHub du code exact.
- **UNVERIFIED** : exécution des 11 tests sur la version GitHub exacte, résultats cliniques RHIVIERA-01/-02, reproduction indépendante des mesures des tableurs supplémentaires, preuve de guérison, persistance en production.
- Les articles [Charre 2026](https://www.nature.com/articles/s41467-026-69720-6) et [Chapel 2026](https://www.nature.com/articles/s41467-026-76699-7) lient des fichiers XLSX **Source Data** ; téléchargements tentés mais non récupérés dans l'environnement local. Les valeurs individuelles n'ont donc **pas** été recalculées. Accession SRA signalée par Charre : **PRJNA1256680**. Les données SRA séquencées n'ont pas été téléchargées.
- Aucun envoi sortant, prélèvement, dépense, nouveau cron ou interruption de traitement.

## Exécution en environnement BIO-MIMIC X

À la racine du dépôt, sans nouvelle dépendance :

```bash
python -m unittest tests.test_rhiviera_bridge -v
python research/hiv_cure_omega/rhiviera_bridge.py --out /tmp/rhiviera_report.json
python research/hiv_cure_omega/rhiviera_bridge.py --memory /tmp/rhiviera_memory.json --out /tmp/rhiviera_report.json
```

L'option `--memory` écrit seulement un nouveau fichier local spécifié, **pas** une mémoire scientifique distante ni un service permanent.

**Prochaine priorité scientifique :** obtenir et vérifier les tableurs Source Data des trois publications pVISCONTI, reconstituer les tableaux contrôleurs/non-contrôleurs, quantifier les corrélations et leurs intervalles d'incertitude sans les confondre avec une causalité ou une validation humaine.
