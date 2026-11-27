# ASTRA DINO Ω — vérification des données Enbody 2023

Date: 2026-11-14. Statut: PARTIAL.

Source: https://github.com/erikenbody/finch_4k_lowpass_code

GitHub connector: dépôt public et README accessibles (PASS).
Script consulté: Analysis_Code/06_phenotypic_data/plot_annual_pheno.R.
Il lit output/combined_genotypes/Darwins_finches_combined_genotype_calls.csv.
Colonnes observées dans le code: meaningful.unique, Species, bill.length, bill.depth, bill.width.
Ce chemin CSV retourne HTTP 404 au connecteur GitHub (FAIL, non téléchargé).
Le chemin output/phenotypic_data/annual_plots/annual_phenotype_summaries.csv retourne également HTTP 404.

Publication primaire: DOI 10.1126/science.adf6218.
Cohorte décrite: 3 955 pinsons séquencés, 2 543 adultes avec mesures du bec.
BioProject de lectures brutes: PRJNA897926.
Dépôt associé cité dans la publication: DOI 10.5281/zenodo.8044096. Contenu non inspecté.

Brouillon Gmail préparé pour erik.enbody@gmail.com, non envoyé; demande explicite du CSV ou d'un sous-ensemble authentifié.

Verdict: 0 nouvel individu génotype-morphologie admis pour une réplication indépendante.
À obtenir: octets du CSV, SHA-256, métadonnées de provenance, preuve de non-chevauchement avec les 50 oiseaux Oslo 2025, génotypes ALX1/HMGA2 et voisins sur assemblage de référence vérifié.
Aucun nouveau test prédictif ni effet causal démontré.
