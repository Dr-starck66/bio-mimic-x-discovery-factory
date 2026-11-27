# BIO-MIMIC X Ω — preuve structurelle 3/6/12 mois après arrêt : audit du 23/11/2026

**Constat reproductible : 0/5 familles d'études satisfont SIMULTANÉMENT le contrat fort** (biopsies appariées avec données analysables, groupe sham/placebo, histomorphométrie quantitative épithélium + ECM, à 3/6/12 mois après la **dernière** intervention, aucune relance du traitement). Ce constat qualifie les **cinq familles examinées**, pas la totalité de la littérature.

| Famille indépendante | Point fort | Limite bloquante | Source |
|---|---|---|---|
| Jacobsen 2026, VagLaser étude I, 26 participantes | élastine 33,1→56,8 %, collagène III 44,5→58,4 %, biopsies appariées | pas de placebo/sham ; suivi 4–6 semaines ; épithélium non quantifiable | doi:10.1007/s10103-026-04829-0 |
| Gaspar 2017, 25/25 femmes ; six biopsies par groupe | biopsies 1/3/6/12 mois post-traitement | histologie surtout qualitative ; bras estriol actif, pré-estriol dans bras laser, pas de sham | doi:10.1002/lsm.22569 |
| LIGHT 2023 + 2026, **même** cohorte | placebo simulé, épaisseur épithéliale et AFM à 1 mois de la dernière séance | à 12 mois biopsies refusées ; aucune supériorité à 6 ou 12 mois ; pas de collagen/élastine chiffrés | doi:10.1001/jamanetworkopen.2022.55697 ; doi:10.1001/jamanetworkopen.2026.38937 |
| Li 2021 + 2023, **même** cohorte | 46 biopsies appariées et sham, catégories histo 2/22 vs 3/24 | pas de supériorité ; biopsie 6 mois après **première** séance, pas de calendrier de suivi post-arrêt documenté | doi:10.1001/jama.2021.14892 ; doi:10.1016/j.ajog.2023.05.005 |
| GSE11622 2008/2009 | 19 biopsies humaines pré/après 3 mois d'estradiol ; accès GEO public pour RNA | transcription seule, pas de suivi après arrêt, pas de témoin | GEO GSE11622 ; PMCID PMC2453134 |

### Observations critiques

- Les indices d'élasticité histologique (proportion de surface colorée) de Jacobsen ne démontrent pas une meilleure fonction mécanique ni la récupération durable. Collagène I, collagène total et morphologie épithéliale sans amélioration statistiquement significative.
- Les données de Jacobsen sont officiellement **disponibles sur demande**, sous protection des patientes : email correspondant `au309162@uni.au.dk` publié par Springer.
- Le suivi LIGHT à 12 mois (publication octobre 2026) n'apporte pas de preuve histologique à 12 mois ; les mesures d'épaisseur longitudinales étaient non estimables à cause de refus de biopsie. Le laser n'était pas supérieur au sham sur les critères cliniques et objectifs mesurables.
- Le protocole VagLaser Study III comporte un **booster**, à contrôler explicitement : une mesure après booster n'est jamais une mesure de durabilité « sans traitement ».
- Les études histologiques sur des survivantes du cancer du sein sous anti-hormonothérapie ne sont pas directement transportables à toutes les femmes ménopausées.
- La numérisation de figures/microphotographies publiées sans calibration et sans appariement individuel ne vaut pas analyse de données tissulaires brutes.

### Étape expérimentale pertinente (pas encore réalisée)

Exploiter d'abord les données histologiques *déjà recueillies*, sans nouvelle biopsie ni dépense : demande ciblée d'export anonymisé/données appariées à Sine Jacobsen, puis LIGHT à Eduard Mension (Barcelone). Vérifier consentement, droits de données, dernière intervention, sham, traitements associés, images histo et données manquantes avant toute reanalyse. Un panel prospectif 0/3/6/12 mois requerrait une étude clinique avec avis éthique et participants volontaires ; elle ne peut être simulée par un pipeline.

### Exécution

Scripts Python et registre : `python vva_duration_registry.py study_registry.json --out audit_result.json` ; `python -m unittest -v test_vva_duration_registry.py`. Audit local 5 familles, éligibles 0 ; 16 tests locaux sur données de métadonnées et synthétiques réussis ; pas de tests biologiques sur données individuelles. Courriers chercheurs rédigés mais **non envoyés**.
