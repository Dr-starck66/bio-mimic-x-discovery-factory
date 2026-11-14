# ASTRA DINO Ω — Recherche d'une cohorte indépendante pour ALX1/HMGA2
**Date :** 2026-11-14 · **Statut scientifique : PARTIAL — NO_INDEPENDENT_MATCHED_COHORT_OBTAINED**

## Objectif et dénominateur réel
Reproduire les associations ALX1/HMGA2 et la comparaison aux fenêtres adjacentes sans réutiliser les **50** oiseaux du jeu Oslo/Dryad 2025. La preuve actuelle (PR #52) comprend 9 SNPs dans l'orthologue ALX1, 36 dans HMGA2, 10 000 permutations, et **p globale 0,0847** pour la taille du bec après correction des huit comparaisons ; les fenêtres droites donnent **p globale 0,0084**. Ces résultats sont exploratoires et les régions voisines peuvent partager les mêmes haplotypes.

**Un DOI, un VCF ou des observations d'espèces non appariées ne valent pas validation indépendante.** Le nombre de nouveaux couples individu ↔ génotype ↔ dimensions du bec authentifiés dans cette mission est **0**.

## 1. Pistes vérifiées

| Priorité | Source et URL | Contenu scientifiquement établi | Verrou exact |
|---|---|---|---|
| **P0** | **Enbody et al. 2023, Science DOI 10.1126/science.adf6218 ; BioProject PRJNA897926** | **3 955** finches Daphne Major avec génomes basse couverture, **2 543** adultes avec longueur/profondeur/largeur de bec mesurées individuellement ; modèle GLIMPSE imputé ; mêmes thèmes ALX1 et supergène G03/HMGA2 | **Prometteur mais pas encore téléchargé** : Zenodo DOI 10.5281/zenodo.8044096 est cité par les auteurs comme dépôt de code/données associés (fichiers internes non inspectés). La matrice imputée et la table `sample_id ↔ band/specimen ↔ beak dimensions` ne sont pas présentes dans nos fichiers ; provenance/reference/éventuels oiseaux déjà vus doivent être audités. Les 3 438 expériences SRA publiques sont des lectures brutes et ne suffisent pas à elles seules. |
| P1 | Sebastianelli Arbelaez et al., *Nature Communications* 2026, DOI 10.1038/s41467-026-78507-8; Figshare DOI 10.6084/m9.figshare.30284983; code GitHub MatteoSebastianelli/Tree_finches | Étude d'octobre 2026 ; 415 génomes de pinsons de Darwin dont 77 Camarhynchus, alignés sur C. parvulus ; G03 sur 1A près HMGA2 ; observations morphologiques muséales également analysées | **Non prouvé** que la morphométrie et les génotypes appartiennent aux mêmes individus ; fichiers Figshare et étiquettes par spécimen **non téléchargés** ; éventuel chevauchement avec cohorte Oslo 2025 **non contrôlé**. |
| P2 | Chaves et al., *Molecular Ecology* 2016, PMID 27363308; SRA SRP066465 | RAD-seq, 32 569 SNPs ; étude beak/body size, mesures morphométriques de 87 oiseaux rapportées dans le supplément | Matrice génotypique individuelle ↔ morphométrie et assemblage/coordonnées ALX1-HMGA2 **non vérifiés** ; accès SRA de séquençage brut n'est pas un VCF apparié. |
| P3 | Lawson & Petren 2017, Dryad DOI 10.5061/dryad.575md | Feuille 83Hapmap_simple2_filtered.xlsx (32,68 Mo) et tableaux GWAS ; 4 espèces Geospiza | Présence de morphométrie individuelle liée aux 83 profils **non démontrée** et génotypes non inspectés ; n'autorise pas une pseudo-cohorte. |
| Référence, pas validation | Han et al. 2017, Dryad DOI 10.5061/dryad.7155d | 111_sample.vcf.gz (393,09 Mo) et jeux d'haplotypes ALX1/HMGA2 | Pas de dimensions individuelles appariées prouvées ; risque de réutiliser d'anciens échantillons. |
| Contre-exemple de richesse | Dudaniec et al. 2026, Dryad DOI 10.5061/dryad.pg4f4qs0s | VCF RAD-seq 28,31 Mo de pinsons arboricoles/hybrides | Pas de morphométrie individuelle associée explicitée dans la fiche ; pas de preuve de couverture ALX1/HMGA2. |

### Liens de référence
- https://doi.org/10.1126/science.adf6218
- https://doi.org/10.5281/zenodo.8044096 (référence de dépôt citée par les auteurs, contenu exact non vérifié)
- https://www.ncbi.nlm.nih.gov/bioproject/PRJNA897926
- https://www.nature.com/articles/s41467-026-78507-8
- https://doi.org/10.6084/m9.figshare.30284983
- https://github.com/MatteoSebastianelli/Tree_finches
- https://pubmed.ncbi.nlm.nih.gov/27363308/
- https://doi.org/10.5061/dryad.575md
- https://doi.org/10.5061/dryad.7155d
- https://doi.org/10.5061/dryad.pg4f4qs0s

## 2. Démarches réellement effectuées et absence de doublon

- Dépôt GitHub tiers `MatteoSebastianelli/Tree_finches` **accessible en lecture** ; README récupéré via GitHub : confirme que le dépôt ne contient que les scripts d'analyse et renvoie vers Figshare pour les données.
- Accès direct aux fichiers Figshare/figshare API par le navigateur distant **bloqué par le quota gratuit Firecrawl** le 14/11/2026. L'environnement local de calcul n'a pas de résolution DNS sortante. TinyFish a un solde négatif et n'est pas utilisé. **Aucun achat**.
- Gmail a été vérifié : un email **déjà envoyé le 14/11/2026** à `leif.andersson@imbim.uu.se` demandait explicitement les couples génotype–phénotype. Pas de doublon à cet interlocuteur.
- **Trois brouillons Gmail enregistrés et non envoyés** sur le compte principal :
  1. **`erik.enbody@gmail.com`** — contacter l'auteur correspondant de la cohorte Daphne 2023, demander 2 543 couples individuels et 3 955 génotypes imputés/VCF, identifiants, chevauchements et G03 ; vérifier le dépôt Zenodo cité.
  2. `matteo.sebastianelli@imbim.uu.se` — demander fichier Figshare exact, table d'identifiants, preuve de non-chevauchement avec Oslo, génomes 1A/G03.
  3. `jachaves@usfq.edu.ec` — demander la table 87 oiseaux et le lien individuel SRA/RAD SNPs.
- Aucune réponse des trois contacts n'est constatée : les brouillons ne valent pas des emails envoyés.

## 3. Contrat scientifique strict d'admission (FAIL-CLOSED)

La cohorte ne sera déclarée **PASS_INDEPENDENT_MATCHED** qu'après vérification de :

1. **Provenance :** DOI/publication ou autorisation du conservateur, noms et versions des fichiers, SHA-256 local de chaque original, licence et conditions d'accès.
2. **Jointure individuelle :** un identifiant explicite commun (ou une table auteur), relation **1↔1**, unités et champs beak length/height/width, âge/sexe/date/île/population quand connus ; aucun rapprochement par espèce seule.
3. **Indépendance réelle :** table complète des oiseaux Oslo 2025 et identifiants de musée/SRA/biobanque de la nouvelle cohorte ; collision ou appartenance incertaine => REFUS de déclarer « indépendants » ; des codes de différents laboratoires sans table de correspondance ne suffisent pas à prouver l'indépendance.
4. **Assemblage :** accès à la séquence de référence exacte ; coordonnées 1A versionnées ; pour tout autre assemblage, *chain* ou remappage vérifié indépendant avec contrôle des REF nucléotidiques, sinon STOP.
5. **Couverture loci :** si la technologie RAD-seq ne contient aucun marqueur dans le corps de ALX1/HMGA2 et leurs fenêtres/ haplotypes, rapporter **UNTESTABLE_NO_COVERAGE**, pas « aucun effet » ; conserver le contrôle négatif des fenêtres voisines.
6. **Évaluation :** hypothèses/endpoints et critères de signification figés avant de lire les phénotypes ; population/parenté, dépendances entre marqueurs, mécanisme de permutation ; test réellement tenu à l'écart de la découverte et, si possible, calcul d'intervalle de confiance sur les effets.
7. **Aucune inférence causale** sur les seuls SNPs liés ; effets non reproductibles, contre-exemples et limites conservés.

## 4. Décision

**PASS** : identification de sources de données scientifiques réelles ; dépôt code tiers consulté ; vérification des messages déjà envoyés ; 3 brouillons sauvegardés sans dépenses.

**PARTIAL** : deux grandes pistes, en priorité la cohorte Daphne 2023 réellement phénotypée (2 543 adultes) et le nouveau panel 2026. Fichiers nécessaires non récupérés ; appariement et chevauchement non contrôlés.

**UNVERIFIED** : disponibilité réelle d'une cohorte indépendante **appariée**. Nombre de paires admises à la validation aujourd'hui : **0**, **aucun nouveau test prédictif réalisé**.

**Prochaine action unique :** obtenir en priorité auprès d'Erik Enbody la table individuelle authentifiée `sample_id ↔ specimen_id ↔ beak_length/depth/width` et confirmer que ces oiseaux ont été effectivement génotypés, sans recouvrement avec la cohorte 2025, avant de relancer un seul modèle.
