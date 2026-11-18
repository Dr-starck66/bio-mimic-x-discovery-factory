# ASTRA BIO-MIMIC X — Site 2, écarts des sexes et robustesse du poids

**Statut : PARTIAL ; données individuelles réellement analysées en JavaScript, 15 tests Python sur données synthétiques PASS. Aucun effet causal ni mécanisme de rajeunissement démontré.**

## Résultat 1 — Source de la réduction de l'écart à UM

L'échantillon étudié contient 6 438 souris, dont 5 242 dans les 5 années communes aux trois sites. Après standardisation directe des proportions d'années et de catégories de traitement, les espérances descriptives (âge au décès mesuré) sont (F/M, jours) : Jackson 857,88/740,96 ; Michigan 888,20/850,01 ; UT 918,38/840,76. L'écart des sexes est de 116,93 / 38,19 / 77,62 jours respectivement. Par rapport à JL, la différence du site UM est plus forte pour les mâles (+109,05 jours) que pour les femelles (+30,32) ; ce différentiel de 78,74 jours explique **comptablement**, et non causalement, la réduction de l'écart. Bootstrap par cellules, n=2 200 : IC95 exploratoire [51,91 ; 105,04].

## Résultat 2 — Contrôles défavorables à une généralisation simple

L'écart des sexes persiste à UM avec les seuls contrôles (33,79 jours contre 106,06 à JL et 128,60 à UT). La différence JL−UM subsiste dans les cohortes 2004–2006 (83,93 jours) et 2007/2009 (71,83). Mais, pour 2007 seulement, UT présente un écart **inférieur** à UM de 45,04 jours : une généralisation de l'ordre fixe JL > UT > UM à chaque année serait fausse. Les seules années communes sont 2004, 2005, 2006, 2007 et 2009 ; aucun résultat comparatif des 3 sites ne doit inclure mécaniquement les cohortes non communes de 2010 à 2013.

## Résultat 3 — Poids corporel : une association non causale, sensibilité quantifiée

Une analyse de 1 589 mâles ayant survécu à la pesée à 183 jours et pesés, dans les cohortes 2005, 2006 et 2009, avait déjà trouvé une atténuation de 74,5% du coefficient UM−JL après ajout linéaire du poids (rapport antérieur dans le dépôt). Ici, une standardisation non paramétrique n'utilise que les cellules année×catégorie de traitement×tranche de poids dans lesquelles les trois sites ont au moins 3 mâles. Pour des tranches de 6g : **1 415 souris**, 17 cellules de support commun, contraste UM−JL +87,50 jours **avant standardisation du poids, mais sur les mêmes individus**, puis +27,43 jours après, IC95 exploratoire [−4,32 ; 57,90]. Atténuation descriptive 68,6% (CI bootstrap large [46,1% ; 107,3%]).

Changer la largeur/l'origine des tranches modifie le support et l'estimation : chez les mâles, +27,4 à +53,4 jours résiduels pour diverses largeurs et origines, alors que les contrôles seuls fluctuent entre environ −10,5 et +35,0. Il n'est donc pas scientifiquement défendable de présenter « 74,5% expliqués par le poids » comme un pourcentage causal identifié. La nécessité d'avoir survécu jusqu'au 183e jour et d'avoir été pesé peut produire un biais de sélection (collider).

## Vérification de provenance à soumettre aux auteurs

Le code `Figures/Figure1.R` de l'étude définit `sex==1` comme mâle, et le CSV contient 3 401 lignes de code 1, contre 3 037 de code 0. Pourtant le texte des méthodes de l'article *Nature* 2026 indique 3 401 femelles et 3 037 mâles. Il faut vérifier les métadonnées originales auprès des auteurs avant de qualifier la discordance comme erreur d'article.

## Valeur démontrée de la nouvelle méthode

Nous avons construit un **audit de robustesse à support commun**, plus strict qu'une comparaison brute : rééquilibrage année/traitement, comparaison sur mêmes souris avant/après standardisation du poids, trois sites simultanés, sensibilité à la largeur et phase des tranches de poids, contre-exemple par année, prise en compte explicite de l'entrée à 42 jours et de la sélection à 183 jours. La valeur actuelle est méthodologique, non thérapeutique.

## Sources

- Fichier primaire et code original : https://github.com/DannyArends/UM-HET3 , blob `4b23a79950182df8564af63803b481179f6e8d17`.
- Source dérivée 6 438 : BIO-MIMIC X, blob `dea9bfa0086228b40e450c0e235f252c83eea528`.
- Arends et al. Nature (2026), DOI https://doi.org/10.1038/s41586-026-10407-9.
- Cheng et al. Aging Cell (2019), DOI https://doi.org/10.1111/acel.12905.
- Rapports chiffrés JSON persistés dans la branche BIO-MIMIC X `astra/longevity-sex-audit-20261118`.