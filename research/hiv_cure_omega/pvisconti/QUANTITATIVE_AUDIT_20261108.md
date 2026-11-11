# ASTRA Ω — Réanalyse statistique pVISCONTI, 8 novembre 2026

**Statut : PARTIAL.** Les quatre liens XLSX originaux de trois études ont été retrouvés chez Springer Nature. Mais **aucun classeur binaire n'a été récupéré** dans le conteneur : DNS `static-content.springer.com` indisponible, `container.download` en échec et moteur web ne prenant pas en charge les réponses binaires. L'équipe n'a **pas** recalculé les corrélations à partir des données individuelles. Les tests qui suivent recalculent **uniquement des corrections de Holm sur les p publiés dans les textes**.

## Inventaire exact

- [Charre — Source Data XLSX](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69720-6/MediaObjects/41467_2026_69720_MOESM6_ESM.xlsx) ; [Supplementary Data 1 XLSX](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69720-6/MediaObjects/41467_2026_69720_MOESM4_ESM.xlsx) ; [article](https://www.nature.com/articles/s41467-026-69720-6).
- [Chapel — Source Data XLSX](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-76699-7/MediaObjects/41467_2026_76699_MOESM4_ESM.xlsx) ; [article](https://www.nature.com/articles/s41467-026-76699-7).
- [Hua — Source Data XLSX](https://static-content.springer.com/esm/art%3A10.1038%2Fs41467-026-69848-5/MediaObjects/41467_2026_69848_MOESM4_ESM.xlsx) ; [article](https://www.nature.com/articles/s41467-026-69848-5).

Les originaux ne sont pas republiés ; la publication Charre est sous CC BY-NC-ND et exige une attention particulière à ses conditions de réutilisation.

## Calculs effectivement réalisés (valeurs publiées, sans fichier brut)

**Holm post hoc sur familles choisies pour la sensibilité.** Les auteurs n'ont pas nécessairement préenregistré ces mêmes familles de tests. Les associations peuvent être fortement dépendantes.

| Famille de tests | p non ajustés dans l'ordre | p ajustés Holm recalculés | Interprétation conditionnelle |
|---|---|---|---|
| Charre Fig. 6 : trois associations réservoir/CD8 | 0.003 ; 0.006 ; 0.047 | 0.009 ; 0.012 ; 0.047 | 3/3 < 0.05 *dans cette famille restreinte* |
| Charre Fig. 7 : PBMC, CD4 D7 et virémie D7 (contrôle négatif) | 0.048 ; 0.019 ; 0.900 | 0.096 ; 0.057 ; 0.900 | 0/3 dans cette famille |
| Charre Fig. 6 + Fig. 7 réunis, **six tests** | 0.003 ; 0.006 ; 0.047 ; 0.048 ; 0.019 ; 0.900 | 0.018 ; 0.030 ; 0.141 ; 0.141 ; 0.076 ; 0.900 | 2/6 ; l'association CD8 p=0.047 devient p-ajusté=0.141 |
| Chapel : six comparaisons de haplotypes/microsatellites avec phénotypes NK | 0.0491 ; 0.0325 ; 0.0238 ; 0.0161 ; 0.0033 ; 0.0233 | 0.0932 ; 0.0932 ; 0.0932 ; 0.0805 ; 0.0198 ; 0.0932 | 1/6 ; ne mesure pas un effet thérapeutique |
| Hua : quatre liens macrophages CX3CR1/Treg/Th17 | 0.0012 ; 0.0013 ; 0.0068 ; 0.0073 | 0.0048 ; 0.0048 ; 0.0136 ; 0.0136 | 4/4 ; corrélations et non causalité |

### Résultats défavorables conservés
- Charre : virémie D7 groupes p=0.900 (aucune différence détectable), **non supprimée** du tableau.
- Charre : la conclusion concernant CD8 dépend du nombre de comparaisons retenues (p ajusté 0.047 ou 0.141 selon la famille **post hoc**).
- Chapel : 5/6 signaux exploratoires MHC/NK passent au-dessus de 0.05 après Holm dans cette famille.
- Hua : signaux de corrélation possibles, mais pas de manipulation causale et fortes dépendances entre mesures.

### Une seule étude animale sous-jacente
Les trois publications pVISCONTI ne sont **pas** trois validations indépendantes : Charre analyse 11 contrôleurs/11 non-contrôleurs, Chapel une sous-sélection de 6+6, Hua un ensemble partiellement partagé avec témoins supplémentaires. Les identifiants animaux des fichiers XLSX doivent être comparés avant toute fusion. **Nombre de cohortes animales indépendantes comptées : 1**, sans combinaison de p-values entre études, sans méta-analyse trompeuse.

## Raccordement BIO-MIMIC X
- Données source publiées : [published_aggregates.csv](./published_aggregates.csv), 16 lignes avec un `cohort_id` partagé.
- Calculs `sensitivity.py` : correction de Holm monotone + export d'un JSON de contrôles sur p publiés seulement.
- Tests de non-réplication, refus des données brutes fictives, contrôle négatif, stabilité du calcul : [10 tests ajoutés](../../../tests/test_pvisconti_sensitivity.py).
- [source_files.json](./source_files.json) : 4 URL, statut `NOT_RETRIEVED_DNS_FAILURE`.
- [fetch_originals.py](./fetch_originals.py) : récupérateur *à exécuter uniquement en environnement réseau autorisé*, en mode local et sans publication des fichiers originaux ; vérifie taille/ZIP/SHA256.

### Preuves et limites
- **PASS (local, calculs agrégés)** : un script de calcul autonome équivalent a traité les 16 p-values et passé **8/8 tests** dans le conteneur, incluant le scénario défavorable CD8.
- **PASS (GitHub)** : les sources, le code et les contrôles sont enregistrés sur une branche de travail isolée, réutilisant la PR #43.
- **UNVERIFIED** : exécution de la version *exacte* des 10 tests GitHub, téléchargements des fichiers binaires, vérification des identifiants individuels, recalcul brut des coefficients / IC / valeurs p, déploiement permanent.
- **Aucune preuve de guérison humaine ni d'éradication SIV**, aucune modification du traitement ARV, aucune dépense, aucun cron, aucune action GitHub déclenchée.

**Prochaine action prioritaire :** sur un environnement réseau gratuit déjà autorisé, récupérer ces quatre XLSX, établir leurs empreintes, inspecter les identifiants et les unités, puis refaire les statistiques individuelles avec correction de multiplicité fixée avant analyse.


## Complément indépendant : tests exacts sur les effectifs publiés

Un second calcul décrit l'association entre précocité du traitement et contrôle du SIV (et non l'éradication). Le script ajouté [published_counts.py](./published_counts.py) utilise la formule hypergéométrique exacte (Fisher bilatéral), et des intervalles Newcombe/Wilson à 95 %. Les [tests correspondants](../../../tests/test_pvisconti_published_counts.py) vérifient notamment le comptage des cohortes. Un script local équivalent a été exécuté avec 11 tests de calcul/contrôle au total réussis ; l'exécution du code byte-identique sur le commit GitHub reste UNVERIFIED.

| Échantillon publié | Contrôle après ART précoce | Contrôle après ART tardif | OR | Fisher exact bilatéral | Différence de risque (IC Newcombe 95 %) |
| --- | ---: | ---: | ---: | ---: | --- |
| Référence pVISCONTI reprise par Charre, [source](https://www.nature.com/articles/s41467-026-69720-6) | 9/11 (81,8 %) | 2/11 (18,2 %) | 20,25 | 0,008922 | +63,6 points (+21,9 à +82,1) |
| Sous-ensemble traité de Hua, [source](https://www.nature.com/articles/s41467-026-69848-5) | 8/9 (88,9 %) | 2/4 (50,0 %) | 8,0 | 0,202797 | +38,9 points (−8,8 à +75,1) |

La deuxième ligne n'est pas une réplication indépendante de la première ; le groupe Hua est un sous-ensemble du programme pVISCONTI, avec un échantillon trop restreint pour confirmer le contraste. La présence de 3 articles et de 16 valeurs p ne doit jamais être interprétée comme 3 cohortes indépendantes ou 16 validations de guérison.

**Contrôle de sensibilité élargi :** dans la famille *post hoc* réunissant les seize p-valeurs sélectionnées, seules 4 valeurs de p restent <0,05 après Holm (Charre intact vs virémie cumulée 0,042 ; Chapel combinaison microsatellites 0,0429 ; Hua CX3CR1-high/Treg 0,0192 ; CX3CR1-low/Treg 0,0195). Cela ne reproduit pas les tests sur les animaux et ne fait pas disparaître le biais de sélection des tests.
