# BIO-MIMIC X — Le site Michigan et la longévité : réanalyse critique

**18 novembre 2026 | Dossier de recherche reproductible | Statut PARTIAL.**

## Question et décision

L'écart de longévité entre mâles et femelles est bien plus faible dans le groupe numérique `site=2.0` du fichier UM-HET3 que dans les autres sites. Le code de site est identifié par **les préfixes de 6 438 identifiants animaux**, sans hypothèse sur l'ordre alphabétique : `1.0` → **JL** (1 953), `2.0` → **UM** (2 634), `3.0` → **UT** (1 851). Les correspondances sont également compatibles avec la géographie des cohortes 2012–2013, produites à UM uniquement.

**Le caractère « site-dépendant » est connu depuis Cheng et al., Aging Cell 2019 (DOI: 10.1111/acel.12905).** Le résultat exploitable ici est un approfondissement quantitatif des covariables poids/cohorte/traitement, non une nouvelle découverte scientifique.

## Données et comparabilité

Dépôt auteur : https://github.com/DannyArends/UM-HET3 ; blob source GitHub `4b23a79950182df8564af63803b481179f6e8d17` (`DataSet/um-het3-rqtl.csvr`).

- **6 438 souris** individualisées, 3 centres, 9 cohortes ; toutes ont une longévité numérique et un identifiant distinct.
- `sex=1` est utilisé comme « mâle » dans `Figures/Figure1.R` de l'auteur ; `sex=0` correspond aux femelles. Une phrase du texte *Nature* 2026 présente les effectifs inversés — **discordance de documentation non résolue, à confirmer auprès des auteurs**.
- `treatment=0` = témoins ; `treatment=1` = plusieurs médicaments considérés individuellement sans effet significatif. **Ce n'est pas un bras de traitement unique, ni une randomisation homogène.** Les auteurs précisent que les molécules de cette classe peuvent avoir un effet collectif sur la longévité.
- Les seules années communes aux trois centres sont **2004, 2005, 2006, 2007 et 2009** ; les analyses de comparabilité sont limitées à **5 242 individus**. À partir de 2010, l'absence structurelle de JL et ensuite d'UT fausse les comparaisons naïves.

## Test 1 — Comparaison directe standardisée

Au sein de chaque centre, on calcule le contraste femelles–mâles dans les cellules `année × catégorie de traitement`, puis on utilise des **poids de cellules communs calculés sur les 5 242 souris**, avec un bootstrap de 3 000 rééchantillonnages au sein des cellules :

| Centre | F−M (jours) | IC bootstrap exploratoire 95 % |
|---|---:|---:|
| JL (Jackson Laboratory) | +116,93 | [98,84 ; 134,93] |
| UM (Michigan) | +38,19 | [19,55 ; 58,50] |
| UT (San Antonio) | +77,62 | [58,43 ; 98,50] |

Contraste des différences de sexes : **JL−UM = +78,74 jours** [52,30 ; 104,89] ; **UT−UM = +39,43 jours** [11,53 ; 67,91]. L'hétérogénéité persiste dans le sous-ensemble des témoins non traités : JL +106,06 ; UM +33,79 ; UT +128,60 jours. Les intervalles supposent une indépendance conditionnelle des individus ; les dépendances par cage/portée ne sont pas modélisées.

## Test 2 — Survie précoce dans les témoins mâles

Pour les cinq cohortes communes, proportion brute d'âges de décès rapportés **<365 jours** :

| Centre | Effectif mâle témoin | Morts enregistrées <365 jours | % |
|---|---:|---:|---:|
| JL | 363 | 26 | 7,16 % |
| UM | 413 | 11 | 2,66 % |
| UT | 470 | 42 | 8,94 % |

UM possède nettement moins de décès masculins précoces enregistrés. **Attention :** le fichier ne contient pas de statut de censure explicite ; ces chiffres sont des fractions observées, **pas des estimateurs Kaplan–Meier ou des risques causaux**.

## Test 3 — Poids à six mois : meilleure piste explicative mesurable

On restreint aux **cohortes 2005, 2006 et 2009** où les trois centres possèdent des poids à six mois, et aux mâles mesurés ayant vécu au moins 183 jours : **n = 1 589**.

Poids mâles moyen : **41,77 g (JL)**, **36,16 g (UM)**, **41,59 g (UT)**.

Régression 1 : `durée de vie ~ site + cohorte + catégorie de traitement` : **UM−JL = +118,25 jours**.

Régression 2 : `durée de vie ~ site + cohorte + catégorie de traitement + poids à 6 mois` : **UM−JL = +30,18 jours** ; pente poids : **−15,62 jours/g**. Le coefficient UM−JL est donc réduit de **74,5 %**. Bootstrap stratifié 1 100 répétitions : atténuation [58,3 % ; 97,7 %], pente [−17,81 ; −13,36] jours/g.

**Contrôle négatif :** 600 permutations des poids au sein de chaque cellule `site × année × traitement`, détruisant le lien poids individuel–durée de vie mais conservant la distribution de poids du centre. La pente nulle permutée tombe entre **−3,93 et +0,39 jours/g** (95 %), alors que la pente observée est **−15,62 jours/g** ; `p` unilatéral empirique ≈ 0,00166. Ce contrôle démontre une association individuelle plus forte que celle attendue sous ce mélange, **pas une médiation causale ni un effet bénéfique de la perte de poids**.

Sensibilité : après suppression de 1 % des poids extrêmes de chaque queue, le coefficient UM−JL est +112,41 jours sans poids / +31,16 avec poids. Témoins uniquement : +100,17 / −8,60 ; catégorie de traitements sans effet individuel significatif : +117,18 / +57,22. Ces résultats hétérogènes soulignent l'impossibilité de prétendre qu'un seul mécanisme explique tout.

## Contrôles critiques et limites

- **Biais de survie à six mois :** pour être pesé à six mois, l'animal a dû survivre jusque-là. L'analyse conditionne donc sur un résultat intermédiaire ; le poids n'a pas été assigné aléatoirement. Risque de sélection/collider et de causalité inverse.
- **Manquants non aléatoires :** les poids à six mois sont absents pour toutes les souris JL et UT de 2004, et toutes les UT de 2007 ; absence UM 2011–2013. On a exclu ces années plutôt que d'imputer arbitrairement.
- **Confusion résiduelle :** génétique (891 marqueurs), cages, portées, alimentation avant sevrage, traitements spécifiques, état de santé avant pesée, calendrier et pratiques locales peuvent intervenir.
- **Données primaires étendues :** GeneNetwork annonce 24 296 individus, mais seul le sous-ensemble validé de 6 438 génétiquement caractérisés a été utilisé ici ; pas de validation indépendante sur 24 296.
- **Survie/censure :** sans drapeau explicite d'événement/censure, pas de Cox ou de Kaplan–Meier revendiqué dans ce dossier.
- **Littérature :** Cheng et al. 2019 ont déjà rapporté la modulation âge/site ; Arends et al., *Nature* 2026 ont déjà rapporté la relation sexe/poids/longévité et de nombreux effets génétiques. Nous quantifions une piste de vérification, sans prétention de priorité ni d'effet thérapeutique humain.

## Preuves et reproduction

Le fichier dérivé `research/longevity_sex_audit/umhet3_individual/data/UMHET3_6438_PHENOTYPES.csv` est conservé sur la branche `astra/longevity-sex-audit-20261118` (Git blob `dea9bfa0086228b40e450c0e235f252c83eea528`). Les statistiques empiriques, le bootstrap et la permutation ont été **réellement exécutés sur les 6 438 lignes via JavaScript** avec source récupérée par le connecteur GitHub ; les nombres sont enregistrés dans le JSON joint.

`umhet3_site_audit.py` implémente une reproduction libre sur le CSV dérivé. Les **12 tests locaux sur données synthétiques ont été exécutés et réussis**, après correction d'une fixture initialement erronée. **L'exécution intégrale du script Python sur les 6 438 lignes dans le conteneur est UNVERIFIED**, celui-ci ne pouvant télécharger le fichier depuis GitHub. Les intervalles de rééchantillonnage Python utilisent un autre générateur pseudo-aléatoire que les statistiques JavaScript originales et ne sont pas garantis identiques au bit près.

Commandes après extraction du dépôt :

```bash
cd research/longevity_sex_audit/umhet3_individual
python -m unittest discover -s tests -p 'test_umhet3_site_audit.py' -v
python analysis/umhet3_site_audit.py data/UMHET3_6438_PHENOTYPES.csv --bootstrap 1100 --permutations 600 --out reports/umhet3_python_replay.json
```

## Bibliographie

- Cheng CJ et al. *Genetically heterogeneous mice exhibit a female survival advantage that is age- and site-specific*. Aging Cell (2019). DOI: 10.1111/acel.12905. https://pmc.ncbi.nlm.nih.gov/articles/PMC6516160/
- Arends D et al. *Dynamics of genetic and somatic trade-offs in ageing and mortality*. Nature (2026). DOI: 10.1038/s41586-026-10407-9. https://pmc.ncbi.nlm.nih.gov/articles/PMC13253337/
- Korstanje R et al. *Astaxanthin, meclizine ... do not increase lifespan in UM-HET3 mice*. GeroScience (2026). DOI: 10.1007/s11357-026-02201-2. https://pmc.ncbi.nlm.nih.gov/articles/PMC13356140/