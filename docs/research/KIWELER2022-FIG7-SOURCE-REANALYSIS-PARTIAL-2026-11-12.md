# BIO-MIMIC X Ω — Kiweler et al. 2022 Fig. 7 : audit borné, négatifs et replay

**Statut global : PARTIAL.** Source : Kiweler N. et al., *Nature Communications* 13, 2699 (16/05/2022), DOI [10.1038/s41467-022-30363-y](https://doi.org/10.1038/s41467-022-30363-y), [PMC9110368](https://pmc.ncbi.nlm.nih.gov/articles/PMC9110368/), PMID 35577770. Date : 12/11/2026.

## Contrôle source
- La version éditeur propose **Source Data (XLSX)** ; la légende de Fig.7 annonce des données sources et des tests de Welch.
- **FAIL acquisition dans cette session** : le réseau DNS du conteneur local ne résout ni Nature ni Europe PMC. Floot VM : quota gratuit quotidien épuisé ; Firecrawl : crédits disponibles insuffisants. Aucun XLSX téléchargé ni SHA-256 du classeur original. **Ne jamais inventer un nom MOESM ni des observations individuelles.**
- **UNVERIFIED** : recalcul des tests de Welch, différences de moyennes et IC95% des Fig.7c/7d/7e/7g.

## Données publiées (pas recalculées)
| Panneau | Mesure | SCR | Mthfd1l KD | p publiée (Welch bilatéral) | Réserve |
|---|---|---:|---:|---:|---|
| 7b | croissance tumeur primaire | 8 | 9 | — | trajectoires individuelles manquantes |
| 7c | masse tumeur primaire | 9 | 9 | 0,9474 | résultat négatif, **non-significativité ≠ équivalence** |
| 7d | protéine Mthfd1l / β-actine | 7 | 8 | 0,0014 | exclusions de lysats de mauvaise qualité |
| 7e | nombre de macrométastases par poumon | 9 | 9 | 0,0322 | requiert les comptes individuels |
| 7g | % de surface pulmonaire métastatique | 7 | 9 | 0,0189 | deux témoins de moins ; poumons collabés exclus |

Les p ci-dessus sont **reportées** depuis la figure publiée, non les sorties d'un calcul BIO-MIMIC X. Sources : [article](https://www.nature.com/articles/s41467-022-30363-y), [version PDF institutionnelle](https://orbilu.uni.lu/bitstream/10993/54549/1/Kiweler%20et%20al%2C%202022.pdf).

## Recalcul indépendant possible sans XLSX : test binaire *différent* de celui des auteurs
Énoncé publié : 9/9 souris SCR présentent des macrométastases pulmonaires ; « over 50% » des neuf KD ne présentent aucune lésion macroscopique. Donc 5 à 9 souris KD sans lésion. **Tous** les scénarios compatibles avec l'énoncé, sans inventer de valeurs par souris :

| KD sans métastases | KD avec métastases | Fisher exact p bilatérale, ASTRA | Différence de risque présence KD−SCR |
|---:|---:|---:|---:|
| 5/9 | 4/9 | 0,029411765 | −55,6 points |
| 6/9 | 3/9 | 0,009049774 | −66,7 points |
| 7/9 | 2/9 | 0,002262443 | −77,8 points |
| 8/9 | 1/9 | 0,000411353 | −88,9 points |
| 9/9 | 0/9 | 0,000041135 | −100 points |

**PASS** pour l'arithmétique de cette analyse conditionnelle ; **UNVERIFIED** pour l'identification du cas exact (5, 6, 7, 8 ou 9). **Ce Fisher binaire ne rejoue PAS le p=0,0322 de la Fig.7e**, qui compare les **comptes de lésions** par un test de Welch. Il n'est pas non plus une réplication indépendante de l'expérience animale.

## Discordances / contrôles négatifs
- 7c : p=0,9474 pour masse tumorale. Maintenir ce résultat défavorable, ne pas proclamer une équivalence.
- 7g : n=7 SCR contre n=9 KD, alors que 7e a n=9/9. Examiner l'effet des exclusions histologiques avant toute interprétation générale.
- Les endpoints **tumeur primaire**, **comptes macroscopiques**, **surface histologique** et **survie humaine** ne sont pas interchangeables.
- Un effet de *silencing* génétique murin de Mthfd1l n'établit pas l'efficacité ni la tolérance d'un inhibiteur chez l'humain.
- Tests multiples, faible n, données individuelles et CI non accessibles : aucune correction statistique et aucun bénéfice clinique inventés.

## Pipeline reproductible testé localement
Un paquet exécutable contient :
- \`validation/kiweler2022_source_fetch.py\` — découvre le lien XLSX explicitement publié dans Nature ou l'XML Europe PMC (aucune URL de fichier inventée), vérifie l'origine HTTPS, la structure XLSX, écrit SHA-256 + manifeste ; échoue fermement si réseau absent ou découverte ambiguë.
- \`validation/kiweler2022_fig7_reanalysis.py\` — sort les cinq bornes Fisher en mode offline ; accepte en mode données individuelles un XLSX avec un CSV d'animaux validé, calcule Welch, SEM et IC95%, vérifie les n et les résultats quantitatifs/qualitatifs attendus.
- \`tests/test_kiweler2022_*.py\` — **8 tests locaux PASS** ; vérification Fisher p=0,0294117647, négatif 7c, refus CSV malformé, URLs rejetées, absence de nom source deviné.

Rapport calculé en local \`KIWELER2022-FIG7-BOUND-AUDIT-2026-11-12.json\` : SHA-256 \`df5c96855379564ecaddcdef487f2a5e709ad1bf4783ef5f2174d67da1055167\`. **Ne pas confondre ce SHA d'un JSON calculé avec celui du XLSX scientifique, absent**.

### Commandes de reproduction
\`\`\`bash
python validation/kiweler2022_source_fetch.py --output-dir reports/kiweler2022
python validation/kiweler2022_fig7_reanalysis.py --output reports/kiweler2022/fig7_bounds.json
python -m unittest discover -s tests -p 'test_kiweler2022_*.py' -v
\`\`\`

**Critère de levée d'UNVERIFIED** : récupérer XLSX original, calculer SHA-256, cartographier chaque cellule originale de Fig.7c/d/e/g vers groupe/animal, recalculer Welch et IC95 %, rapprocher les quatre p à l'arrondi publié, et examiner exclusions. Aucune déclaration PASS quantitatif sans ces étapes.