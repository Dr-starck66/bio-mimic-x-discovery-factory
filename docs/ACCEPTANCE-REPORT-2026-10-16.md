# BIO-MIMIC X — Rapport d'acceptation du 16 octobre 2026

## Résumé d'exécution

**Résultat QA logiciel : PASS sur les scénarios testés.**
Exécution GitHub Actions de référence : https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/38939277771

Commit de référence : `78029780692fe4da4dfcbd321b6e629d0284f7bc`.

La suite GitHub Actions `BIO-MIMIC X — UI and Scientific Acceptance` a exécuté :

1. **128 tests unitaires, 128 réussis.**
2. **12 scénarios fonctionnels Chromium, réussis**, avec fournisseurs simulés pour garantir la répétabilité : démarrage, navigation, filtre atlas, recherche, audit Morpheus, garde anti-fausse validation scientifique, export et contrôle SHA-256, mémoire négative persistante, injection d'échec API, lecture du dashboard, navigation dashboard-Hunter et rendu mobile.
3. **Test navigateur Chromium avec véritable Europe PMC, réussi** : 18 cartes d'articles visibles dans l'interface, sans interception du fournisseur externe.
4. **Démonstration reproductible Acomys, réussie** : deux processus Python distincts, avec graines de hachage différentes et plus de deux secondes d'écart, rendent un fichier de résultat strictement identique.

## Empreinte reproductible

`3bd96191ba613b4d984590e95f50573788f35109c756312767ec3fc54d2a737d`

Le contrôle de modification d'un enregistrement bibliographique produit une empreinte différente. Les contrôles négatifs empêchent « This study », « Wound healing », « Wnt pathways » et les taxons non confirmés de bénéficier de la même promotion que des espèces documentées (contrôles adaptés aux couches de traitement).

### Reproduire la démonstration

```bash
PYTHONHASHSEED=17 python qa/repro_acomys.py --out replay-a.json
PYTHONHASHSEED=101 python qa/repro_acomys.py --out replay-b.json
cmp replay-a.json replay-b.json
```

La suite complète est dans `.github/workflows/biomimic-acceptance.yml`. Les artefacts de la démonstration sont joints à l'exécution GitHub Actions.

## Cas scientifique : Acomys cahirinus

Hypothèse falsifiable issue du **registre bibliographique curé** : l'association entre état immunitaire et matrice extracellulaire dans la régénération d'Acomys mérite un test causal comparatif, et ne doit pas être réduite à une action isolée d'IL10.

Corpus primaire actuellement répertorié :

- PMID:29892004 (2018) — régénération musculaire.
- PMID:31141508 (2019) — transcriptomique et réparation cutanée.
- PMID:32849592 (2020) — états immunitaires régénératifs.
- PMID:40534468 (2025) — protéomique de la matrice extracellulaire.
- PMID:40883787 (2025) — réponse pulmonaire après lésion par bléomycine.

**Important :** les cinq publications sont des travaux de chercheurs externes et ne constituent pas des découvertes nouvelles de BIO-MIMIC X. La démonstration prouve la traçabilité du tri bibliographique, des contrôles négatifs et la reproductibilité informatique du rapport. Aucune expérience biologique nouvelle, aucun effet clinique et aucune prédiction thérapeutique ne sont validés par cette exécution.

## Correctifs réalisés pendant les tests

- Le Hunter interactif est désormais inclus dans `public/hunter.html`, avec `public/hunter.js` et `public/hunter.css`, et relié au Control Center.
- Une annotation seule ne peut plus marquer un claim `VERIFIED` sans validation taxonomique et indépendante.
- Extraction du genre renforcée contre des expressions anglaises fréquentes confondues avec des espèces.
- Correctif d'intégrité : copie figée des éléments du replay avant modification du statut, afin que le SHA-256 exporté corresponde effectivement aux octets JSON contrôlés.
- Correction de l'empreinte du dossier due diligence : suppression des horodatages volatils imbriqués de la charge utile hachée.

## Frontières de la validation

- **PASS :** tests unitaires, navigateur local Chromium sur le site réel du dépôt, recherche Europe PMC en direct depuis le navigateur, contrôle des flux simulés, conservation et vérification de l'empreinte scientifique.
- **UNVERIFIED :** validation scientifique indépendante d'une hypothèse BIO-MIMIC X ; expérimentation causale ; nouveauté brevetable ; liberté d'exploitation ; clients ou contrats payants.
- **NON DÉPLOYÉ PUBLIQUEMENT PAR CE WORKFLOW :** la tâche GitHub Pages échoue à `configure-pages` avec `Resource not accessible by integration`. La création d'un projet Vercel par le connecteur a renvoyé une erreur de permission HTTP 403. Ne pas prétendre que le dashboard est accessible sur un domaine public tant qu'un déploiement HTTP et SSL n'a pas été prouvé.

**Verdict : PASS logiciel dans le périmètre de tests ; PARTIAL pour la maturité commerciale d'un dossier de vente à 1 M€.**
