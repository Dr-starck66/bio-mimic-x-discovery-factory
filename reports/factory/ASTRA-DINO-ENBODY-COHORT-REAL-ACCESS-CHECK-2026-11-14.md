# ASTRA DINO Ω — Enbody 2023 : récupération et validation de cohorte (contrôle du 14 novembre 2026)

**Verdict : PARTIAL / NO_INDEPENDENT_COHORT_AVAILABLE.** Aucune nouvelle donnée Enbody reçue ou importée ; par conséquence **aucun SHA-256 de fichier Enbody, aucune jointure individuelle ni couverture ALX1/HMGA2** ne peut être établie.

## Accès et recherche — observations effectives

- Email à Erik Enbody **SENT**, Gmail `1a1da64d5fc50993`, date 14 novembre 2026. Les opérateurs de recherche `from:erik.enbody@gmail.com` et une recherche connexe n'ont trouvé aucune réponse nouvelle lors du présent contrôle. Ne pas envoyer de deuxième sollicitation le jour même.
- Étude : `10.1126/science.adf6218` (3 955 oiseaux séquencés ; les mesures individuelles pour 2 543 adultes rapportées dans la publication). Cela ne vaut pas 2 543 couples disponibles pour ASTRA.
- Dépôt officiel de code `erikenbody/finch_4k_lowpass_code` : scripts lus via le connecteur GitHub ; la sortie `output/combined_genotypes/Darwins_finches_combined_genotype_calls.csv` citée dans `Analysis_Code/06_phenotypic_data/plot_annual_pheno.R` n'est pas présente au chemin indiqué, HTTP 404 du connecteur GitHub.
- Zenodo `10.5281/zenodo.8044096` : API/landing page non lisible dans cet environnement, sans pouvoir vérifier le contenu des fichiers ni leurs licences individuelles. Une URL/DOI ne prouve pas un corps de fichier téléchargeable.
- BioProject `PRJNA897926` : donnée brute mentionnée dans la publication ; ne remplace pas une matrice imputée avec morphométrie individuelle et crosswalk d'identités.
- Recherche dans les fichiers montés du contexte et de la bibliothèque : audit antérieur Dryad/Oslo présent, **aucun fichier Enbody combiné confirmé**.

## Exécution vérifiée du verrou de sécurité

Source testée : archive conversation `ASTRA_DINO_ENBODY_VALIDATION_GATE_20261114.zip`, SHA-256 **`485fd208d6f911e3ee37cbff32d6606d91d33d32cd7bd7e16f159e12b6d3fcfe`**.

Auditeur `astra_dino_cohort_gate.py`, SHA-256 **`2be7ea95e34909e29f1ecebe75082a5fa541ff4e59c214fe20291e98b63be391`**.

Test local exécuté : `python3 -m unittest -v test_cohort_gate.py` → **9/9 PASS** (uniquement fixtures synthétiques, non validation biologique).

Commande exécutée : `python3 astra_dino_cohort_gate.py --data . --manifest manifest_template.json --output admission_status_20261114.json` → **code retour 2**, sortie `{"status":"FAIL_CLOSED_OR_PARTIAL","reason":"SOURCE_DOI_MISSING"}`. C'est le refus attendu d'un manifeste non renseigné et l'absence de données originales ; ne pas forcer un PASS artificiel.

## Contrôles à refaire obligatoirement à la réception

1. SHA-256 réellement recalculés sur chaque fichier source reçu, taille, URL officielle, version, licence, preuve d'autorisation.
2. Crosswalk 1↔1 `specimen_id` ↔ `genotype_sample_id` ↔ bec longueur/profondeur/largeur ; exclusion doublons et valeurs absurdes.
3. Absence de recouvrement biologique avec les 50 oiseaux Oslo 2025 : confrontation des numéros de spécimens, alias connus, registres institutionnels et accession SRA ; les identifiants différents ne suffisent pas.
4. Vérification réelle des SNP ALX1, HMGA2 et fenêtres témoins, assemblage versionné, REF/ALT et contig `1A` ; pas d'approximation de coordonnées.
5. Seulement ensuite analyse statistique tenue à l'écart des données de découverte, correction sur tous les tests annoncés et conservation des résultats négatifs.

**Statut scientifique : UNVERIFIED** pour l'existence de paires individuelles Enbody autorisées et utilisables, l'absence de recouvrement et toute réplication. **Aucune fusion**, aucune dépense, aucun nouvel email en doublon.
