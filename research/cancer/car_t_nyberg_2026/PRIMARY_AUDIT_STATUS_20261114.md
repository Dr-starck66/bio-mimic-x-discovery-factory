# Acquisition et audit primaire — Nyberg et al. (14/11/2026)

**Projet :** BIO-MIMIC X — audit préclinique, DOI 10.1038/s41586-026-10235-x.
**Statut : PARTIAL.** Ce compte-rendu complète AUDIT_20261114.md et ne constitue pas une réplication des animaux individuels.

## Sources vérifiées

- Article et liens des 15 fichiers « Source Data » et quatre tableaux additionnels : https://www.nature.com/articles/s41586-026-10235-x
- Copie open-access PMC (mêmes fichiers) : https://pmc.ncbi.nlm.nih.gov/articles/PMC13083257/
- Séquençage CRISPR : https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1412486
- Code : https://github.com/charwang0440/nature_in_vivo_ht7

Inventaire exhaustif des 21 fichiers annexes officiels dans SOURCE_DATA_MANIFEST_20261114.json (15 sources xlsx, quatre tableaux xlsx, deux PDF).

## Chaîne d'acquisition tentée et résultat réel

| Voie | Résultat | Preuve / limite |
| --- | --- | --- |
| Texte intégral Nature et PMC | PASS | Figure legends, methods, limitations et liens primaires consultés |
| GitHub public des auteurs | PASS | README, runner MAGeCK et docs MiXCR examinés |
| Médias Springer Nature .xlsx via web | FAIL | Les liens existent, mais le backend signale « Cache miss » sur les octets |
| PubMed Central .xlsx via extracteur | FAIL | Page d'accès reCAPTCHA pour téléchargements binaires directs |
| Téléchargement réseau Python du conteneur | FAIL | DNS/réseau externe non résolu |
| Navigateur agent connecté | FAIL | Solde insuffisant ; aucune dépense autorisée |
| Inspection en mémoire des fichiers originaux | UNVERIFIED | Aucun fichier XLSX/FCS/FASTQ original acquis |
| SHA-256 des binaires source | UNVERIFIED | Refus explicite de produire des empreintes imaginaires |

## Audits effectivement possibles

- Résultats descriptifs publiés : NALM6 18/20 souris sur quatre donneurs ; MES-SA 5/6 et 3/8 souris sur deux donneurs ; les intervalles exacts et tests exploratoires sont déjà calculés dans AUDIT_20261114.md.
- Contrôles négatifs : sous l'ancienne combinaison VSVG-EDV/AAV6, aucune CAR-T détectable dans le modèle dépourvu de xéno-GvHD ; un AAV seul ne provoque pas l'intégration CAR et un EDV seul n'apporte pas le transgène complet.
- Limitation de spécificité : l'étude indique une diminution de ciblage HSC / cellules tumorales avec la combinaison optimisée dans les assays testés, mais ne prouve pas la nullité universelle d'une intégration indésirable.
- Biodistribution : ADN AAV détecté dans de multiples tissus dont le foie ; l'infiltration de lymphocytes humains peut expliquer une partie du signal. Cette ambiguïté interdit d'inférer une absence de transduction extralymphocytaire.
- Cytokines : absence de signal systémique à J1 et J7 dans ce modèle selon les auteurs, non extrapolable à une absence de toxicité clinique, rare ou retardée.
- Les auteurs reconnaissent que le modèle immunodéficient humanisé limite l'évaluation de l'immunogénicité et de la sécurité, et demandent des études sur modèles immunocompétents plus grands.

## Demande scientifique sortante

Le 14/11/2026, demande envoyée par Gmail à Justin Eyquem (UCSF), avec copie à William A. Nyberg (Karolinska). La confirmation de l'envoi est conservée dans Gmail. Objet : « Data access and reproducibility questions — Nature 2026 in vivo TRAC-CAR T cells ».

Données sollicitées : mesures individuelles pseudonymisées par souris/donneur/bras/date, définition de rémission, censures/exclusions, FCS + gating, tests HSC/NK/tumeur, biodistribution, cytokines, éventuels résultats de séquençage hors cible/variations structurales, métadonnées PRJNA1412486 et contrastes MAGeCK effectifs.

## Conditions indispensables avant promotion des preuves

1. Télécharger par URL autorisée les originaux et conserver taille, SHA-256, URL, date et licence pour chaque fichier.
2. Réconcilier les identifiants individuels et les donneurs ; vérifier duplications et erreurs de groupe sans compléter les données manquantes artificiellement.
3. Recalculer trajectoires, rémissions et survie par donneur puis tester la sensibilité au groupement et aux exclusions.
4. Séparer spécificité des vecteurs, insertion ciblée, changements hors cible et événements indésirables retardés : une mesure n'en remplace pas une autre.
5. Ne pas coder « pas d'effet négatif » en présence de mesure absente. Maintenir NO-GO hypothèse thérapeutique / application clinique.

**Décision : NO-GO thérapeutique, PARTIAL audit.** Mise à jour purement documentaire sur branche isolée, sans fusion, publication de données personnelles ni dépense.
