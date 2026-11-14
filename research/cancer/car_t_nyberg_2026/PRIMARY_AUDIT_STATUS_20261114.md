# ASTRA BIO-MIMIC X — Audit primaire des données expérimentales (14 novembre 2026)

**Publication :** Nyberg et al., *Nature* 652, 712–721 (2026), DOI : https://doi.org/10.1038/s41586-026-10235-x.

**Statut global : PARTIAL (audit réel de mesures animales), NO-GO thérapeutique / sécurité génomique UNVERIFIED.** Il s'agit d'une réanalyse indépendante de fichiers publiés, et non d'une réplication biologique ou d'un essai clinique.

## 1. Acquisition originale : PASS technique

- Un sandbox Vercel isolé (projet de test, région fra1, aucune production modifiée) a téléchargé **21/21 annexes** depuis les URL officielles `static-content.springer.com` : **19 XLSX et 2 PDF**.
- Pour les 19 XLSX : code HTTP 200, signature ZIP et test CRC ZIP sans erreur. Pour les deux PDF : HTTP 200 et signature `%PDF` valide. Taille et **SHA-256 pour chaque fichier** dans [SOURCE_DATA_MANIFEST_20261114.json](./SOURCE_DATA_MANIFEST_20261114.json).
- Les fichiers originaux sont publics chez l'éditeur. La VM utilisée était **temporaire** et a cessé de fonctionner ; **les 21 fichiers binaires ne sont pas archivés sur GitHub**. Le manifeste, les empreintes et l'export de mesures ci-dessous sont persistés dans la branche ASTRA.
- **BioProject PRJNA1412486 :** l'accession est attestée par la publication ; les FASTQ bruts du criblage ne sont **pas** téléchargés et la reproductibilité MAGeCK à partir des séquences reste **UNVERIFIED**.

## 2. Observations individuelles extraites et conservées

[Export des mesures sources par colonne animale — CSV compressé](./derived/MOUSE_LEVEL_SOURCE_OBSERVATIONS.csv.gz) : **649 lignes de mesures authentifiées**, générées en lecture seule depuis trois classeurs XLSX, avec la désignation originale du bras, du donneur (si présente), le temps, la valeur et la feuille/colonne d'origine. **SHA-256 du fichier gzip :** `5f649cb41e3741f2c59c89c8c10a4e6ebfd610328cb4c5af5d596a47433df267`. Le fichier compte 4 789 octets compressés, pour 39 391 octets CSV.

| Table du manuscrit | Source | Mesures numériques | Découpage |
| --- | --- | ---: | --- |
| Figure 4b, bioluminescence NALM6 | MOESM10 / SHA-256 `dc9e13332c044bfdc71b6bdce7831e1179d6a65d5d3cb579b65e31700d8c695e` | 211 | 71 PBS, 140 EDV/AAV |
| Figure 5e, volume MES-SA donneur 1 | MOESM11 / `b700a699e01303fdcf07fe4cc82970986123de42115dfb5475b9a03038031276` | 220 | 28 tumeur seule, 41 PBMC, 151 EDV/AAV |
| Extended Data 10d, volume MES-SA donneur 2 | MOESM21 / `7fe9b1727ba1c31fb56f102ebe22dd2345d012df76fdfe90096b7c1418fd50b5` | 218 | 28 tumeur seule, 46 PBMC, 144 EDV/AAV |

L'identifiant individuel est une **référence de colonne du classeur** : ne pas l'interpréter comme un identifiant animal inter-expériences. Les jours vides ne sont ni des réponses complètes ni des zéros. Deux libellés de donneurs atypiques (`Donor ` et `Donor $`) existent dans la feuille 4b ; interdiction de leur attribuer un donneur sans vérification complémentaire.

## 3. Recalculs sur les mesures observées

**NALM6 :** 20 souris PBS et 20 souris EDV/AAV au départ. À J11, BLI médiane PBS **22 550 000** (n=20), EDV/AAV **929 000** (n=20). À J17, PBS **113 500 000** (**n=2 seulement**) contre EDV/AAV **2 820** (n=20). À J28, les 20 souris traitées ont une mesure BLI : médiane **1 380**, mais valeurs extrêmes allant jusqu'à **27 200 000**. Les cellules PBS J28 sont absentes ; l'attrition des contrôles rend toute comparaison brute tardive invalide. Les 18/20 réponses complètes annoncées par le papier ne sont **pas reclassées indépendamment** sans seuil d'adjudication et règle de censure.

**MES-SA, donneur 1 :** 6 souris EDV/AAV, 5 PBMC, 4 « Tumor Only ». À J17, volume médian EDV/AAV **341,12** (n=6) contre PBMC **910,11** (n=5). À J23, EDV/AAV **93,38** (n=5) contre PBMC **1 876,07** (n=4).

**MES-SA, donneur 2 :** 8 souris EDV/AAV, 5 PBMC, 4 « Tumor Only » (témoins déjà repris). À J17, volume médian EDV/AAV **719,53** (n=8) contre PBMC **521,53** (n=5) : **signal défavorable à cette échéance**, important à conserver. À J23, EDV/AAV **561,69** (n=5) contre PBMC **1 163,91** (n=4). À J34, EDV/AAV **88,05** (n=4) contre PBMC **2 125,57** (n=2), mais l'attrition empêche une inférence robuste.

**Contrôles communs :** les quatre colonnes « Tumor Only » du donneur 1 et du donneur 2 sont exactement identiques aux **29 dates communes**, en conservant les valeurs manquantes. Il s'agit d'un même profil de référence recopié : aucun test combiné ne doit les traiter comme deux séries témoins indépendantes.

Aucune conclusion de significativité confirmatoire, de rapport de risque de survie ou de réponse complète par animal n'a été produite ici. Les tailles d'échantillon, la censure et la variabilité entre donneurs doivent être modélisées explicitement.

## 4. Audit de sécurité et limites

- **PASS documentaire :** la Figure 2 et ses données complémentaires évaluent la sélectivité de délivrance/édition dans certains types cellulaires, notamment cellules T, HSC, NK et lignées tumorales ; la Figure complémentaire 5e-f contient des mesures de cytokines avec des valeurs « NA » à préserver comme manquantes.
- **PARTIAL :** les auteurs rapportent l'absence de signal inflammatoire systémique sur une fenêtre courte, et détectent de l'ADN AAV dans plusieurs organes. Ces mesures ne prouvent ni l'absence de toxicité retardée, ni l'absence d'édition dans toutes les populations cellulaires.
- **UNVERIFIED :** aucune preuve individuelle validée ici de séquençage hors cible, de grandes délétions, de translocations, de sites d'intégration non voulus ou de surveillance à long terme. La table MAGeCK du criblage CRISPR vise les **facteurs de transduction** ; elle ne constitue **pas** une mesure des mutations hors cible du traitement.
- **NO-GO :** aucune extrapolation d'efficacité clinique ou d'innocuité génomique humaine.

## 5. Correspondance scientifique

Le 14/11/2026, demande d'accès ciblée envoyée par Gmail à **Justin Eyquem** avec copie à **William Nyberg** : identifiants anonymisés des souris/donneurs, seuils de réponse, censure/exclusions, cytométrie FCS, génotoxicité hors cible/variants structuraux et métadonnées de PRJNA1412486. Identifiant Gmail confirmé : `1a1d7ac271819d87`. Deux boîtes vérifiées après l'envoi : **aucune réponse nouvelle** trouvée lors du présent contrôle.

## 6. Contrôles d'exécution

- Exécution à distance : 21 réponses HTTP 200 et validations de format ; téléchargements temporaires effectifs, sans fusion ni changement de site en production.
- Extraction XLSX XML par script Python standard library : exécution exit code 0, 649 valeurs non manquantes dans les trois feuilles précitées, export gzip SHA-256 ci-dessus.
- Relecture GitHub : objet binaire `92fa973479b11d99aec21e4bbae5c800ef869c0f` et manifeste de 21 empreintes vérifiés sur la branche de la PR #55.
- Ancienne batterie de tests des **agrégats publiés : 10/10 PASS**, réexécutée localement ce jour. Ce test ne vaut **pas** validation des mesures génomiques ou des endpoints de survie.

**Décision : audit primaire PARTIAL, acquisition PASS, observations individuelles analysées PARTIAL, sécurité génomique UNVERIFIED.** Prochaine action : obtenir des auteurs les données d'événements/censures et le séquençage de sécurité primaire, puis compléter les analyses par donneur sans déduire des réponses complètes de simples seuils ad hoc.
