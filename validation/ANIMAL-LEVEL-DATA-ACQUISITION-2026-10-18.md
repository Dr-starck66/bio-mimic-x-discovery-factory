# BIO-MIMIC X — Acquisition vérifiée de mesures individuelles de régénération (2026-10-18)

Statut scientifique : **PARTIAL — 4 animaux avec phénotypes observés ; 0 animal avec phénotype ET transcriptome dont l'appariement est démontré**.

## Source 1 : régénération neuronale mesurée, réellement individualisée

- Publication : Varholick, Kondapaneni & Maden, *Spiny mice (Acomys) regenerate wounded whisker pad skin with whisker follicles, muscles, and targeted innervation*, npj Regenerative Medicine (2025).
- Données originales : https://github.com/javarhol/AcomysWhiskerRegeneration/blob/main/data/acomys_regenerated_axon_counts.xlsx
- Blob Git SHA : `726f6e3469020d20a494aee5bcf7818d142b1b9e`.
- Extraction contrôlée des données XLSX via l'API GitHub : **20 comparaisons appariées de nombres d'axones** (vibrisse régénérée / vibrisse non blessée) appartenant à **4 animaux**.
- Les différentes vibrisses d'un animal sont des sous-mesures imbriquées, **pas 20 souris indépendantes**.
- Les deux temps (44 et 90 jours) ne doivent pas être regroupés pour estimer un effet de temps.
- Ratio ci-dessous : 100 × somme des axones « regen.count » / somme « uninj.count » **par animal** ; n'est pas une proportion de blessure guérie et peut dépasser 100 %.

| Animal | Jour | Vibrisses appariées | Axones régénérés | Axones non blessés | Ratio pondéré |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1343610-1 | 44 | 12 | 715 | 1371 | 52,152 % |
| wp1 | 90 | 3 | 548 | 479 | 114,405 % |
| wp2 | 90 | 2 | 287 | 296 | 96,959 % |
| wp3 | 90 | 3 | 504 | 505 | 99,802 % |

## Source 2 : signatures moléculaires RNA-seq vérifiables, SANS jonction aux animaux source 1

- GEO : https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE224879
- Etude : Tomasso et al., *An ERK-dependent molecular switch antagonizes fibrosis and promotes regeneration in spiny mice*, Science Advances (2023).
- **17 échantillons Acomys** publiés sous les identifiants GSM7034846–GSM7034862 : 10 échantillons D15 (5 inhibiteur MEK/ERK, 5 DMSO), 7 échantillons D1 (3 inhibiteur, 4 DMSO).
- Des tableaux de comptages géniques par échantillon sont publiés chez GEO mais **non téléchargés/analysés durant cet audit**.
- Aucun identifiant confirmé ne rattache ces échantillons aux 4 animaux du jeu de vibrisses. Les mesures de fermeture d'oreille de la publication ne démontrent pas non plus une correspondance individuelle avec les 17 bibliothèques RNA-seq.
- **Interdiction de joindre par espèce, traitement, numéro de réplicat ou ordre de ligne**.

## Source 3 : une opportunité de vraies paires individuelles, mais données non directement publiques

- Qin et al., 2025, DOI https://doi.org/10.1111/wrr.70038
- Huit souris séquencées individuellement (2 par condition) ; sélectionnées d'après leur cicatrisation parmi huit animaux par condition, avec mesures longitudinales de surface de plaie.
- Les auteurs indiquent que les données de soutien sont disponibles sur demande raisonnable et ne fournissent pas une matrice individuelle GEO complète.
- Une demande de données avec table de correspondance scRNA-seq ↔ mesure de plaie et identifiants anonymisés a été **préparée en brouillon Gmail, non envoyée**.

## Verrou scientifique à lever

Pour ajuster/comparer les modèles ERK, immunité, ECM et la combinaison, il faut un identifiant **animal** vérifiable qui relie au moins une signature moléculaire mesurée **avant ou au moment approprié** à un phénotype quantitatif *observé chez ce même animal* (ou un design expérimental temporel justifié), avec un nombre suffisant d'animaux indépendants et des groupes biologiques cohérents.

La présence séparée de phénotypes et de transcriptomes dans deux études ne constitue pas cet appariement. AUC, delta de performance et mécanisme régénératif original : **UNVERIFIED**.

Relecture antérieure BIO-MIMIC X : `reports/independent-data-validation/2026-10-16.json` : une hypothèse transcriptomique préenregistrée a **échoué à être répliquée sur deux cohortes** ; ce résultat négatif doit être conservé.
