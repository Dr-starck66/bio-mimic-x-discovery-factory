# BIO-MIMIC X — contrôle réel axolotl / humain (2026-11-01)

**Statut scientifique : PARTIAL — contrastes biologiques non comparables.**

## Preuves d'exécution

- [Job scientifique du run #41316380241](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41316380241) : 150 tests de code **PASS**, données réelles téléchargées et relecture des échantillons et de l'annotation.
- Rapport de calcul complet : [AXOLOTL-HUMAN-TRANSCRIPTOMIC-LATEST.json](AXOLOTL-HUMAN-TRANSCRIPTOMIC-LATEST.json), SHA-256 `9e5dcc8e259b3585ea4ee8f26c05c304e9bf526853292f57ba66640f89d0df08`.
- GSE284768 : axolotl, 99 091 gènes mesurés / 25 échantillons, sélection explicite 4 blastèmes antérieurs et 4 postérieurs à 15 jours post-amputation.
- GSE28914 : humain, 54 675 sondes / 25 échantillons ; **6 patients** disposant de biopsies appariées intacte / jour 3.
- GPL570 : annotation de sondes humaines ; AmexT_v47–AmexG_v6.0-DD : noms annotés sur le génome d'axolotl. Chaque source possède son URL et son SHA-256 dans le JSON.
- Le job navigateur du même workflow a échoué sur un problème d'exécution Chromium distinct ; cela **n'invalide ni ne convertit** le résultat scientifique.

## Contrastes exploratoires réellement quantifiés

Les colonnes suivantes représentent des expériences **différentes**. Elles ne mesurent pas le même effet causal et ne doivent pas être corrélées directement.

| Gène | Axolotl : log2(CPM + 1) postérieur − antérieur, 15 dpa | Humain : intensité log2 jour 3 − peau intacte (médiane des différences appariées) | Annotation |
|---|---:|---:|---|
| HAND2 | −0,0208 | −0,1378 | AMEX60DD030069, orthologie NCBI soutenue pour le symbole ; liaison d'identifiant exact AMEX→NCBI non démontrée |
| IL10 | −0,7072 | +1,9511 | AMEX60DD009000, aucune orthologie indépendante vérifiée dans cette exécution |
| CTHRC1 | +0,3777 | −0,3216 | AMEX60DD040253, aucune orthologie indépendante vérifiée dans cette exécution |
| MMP9 | Non attribué de façon univoque | +3,8976 | Signal humain descriptif uniquement |
| CXCL8 | Cinq identifiants axolotl candidats, ambigu | +7,1374 | Ne pas agréger les paralogues comme des réplicats |

**Important :** l'étude GSE284768 mesure l'identité positionnelle antérieure/postérieure du blastème, tandis que GSE28914 mesure la cicatrisation cutanée humaine, intacte contre J3. Les tissus, contextes, plateformes et temps diffèrent. On ne peut pas conclure sur la conservation de la réponse à une blessure, ni sur une capacité humaine à régénérer un membre. Les valeurs ci-dessus ne sont **pas des tests confirmatoires** et aucun score de concordance interespèces n'est calculé.

## Sécurité méthodologique et limites

- Les 12 gènes ont été fixés dans le code avant lecture des résultats du run. Le système refuse les annotations ambiguës, les bibliothèques nulles et les groupes de réplicats incomplets.
- Les symboles `[hs]` du GTF axolotl ne constituent pas, seuls, une preuve d'orthologie un-à-un. HAND2 obtient un soutien NCBI orthology, mais le lien exact entre AMEX60DD030069 et le gène NCBI de référence reste à établir.
- Les signaux humains proviennent de données microarray déjà normalisées : il ne faut pas les présenter comme du RNA-seq humain.
- Le **FAIL préenregistré GSE74387** (16 octobre) est conservé ; il n'est pas « réparé » par une autre comparaison exploratoire.
- Étude antérieure : PMID 31305215 rapporte déjà 95 signatures de variation inverse humain/axolotl ; aucune priorité de découverte originale n'est revendiquée.
- **Validation biologique indépendante sur cellules humaines : UNVERIFIED.**
- **Régénération anatomique/fonctionnelle complète d'un membre humain : UNVERIFIED.**

## Prochaine porte de preuve

Rattacher les identifiants AMEX60DD à des entrées homologues exactes traçables et établir des contrastes réellement appariables (même état blessé/témoin, tissu et stade), puis reproduire sur cohortes et équipes indépendantes avec contrôles négatifs et seuils préenregistrés. Une éventuelle intervention sur des cellules humaines devra être effectuée par un laboratoire habilité, avec autorisations et protocole indépendant.

**Reproduction (sur runner scientifique connecté avec accès public GEO) :**
`python -m unittest tests.test_axolotl_human_reanalysis -v`
`python validation/axolotl_human_reanalysis.py --write`
