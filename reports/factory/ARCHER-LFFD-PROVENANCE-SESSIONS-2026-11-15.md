# ASTRA ARCHER VISION Ω — acquisition vérifiée des métadonnées LFFD (15 novembre 2026)

**Statut : PASS — métadonnées officielles accessibles et vérifiées. PARTIAL — images 2D soumises à licence, non acquises.** Ne pas confondre cette preuve d'identité/session avec une évaluation réelle des trois modèles.

## Provenance et exécution
- Fournisseur officiel : https://lffd.eurecom.fr/ (IST-EURECOM LFFD, moitié EURECOM du jeu complet de 100 personnes).
- Exécution du téléchargement sans photos : https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/43669986715 — job `verify-public-metadata`, conclusion `success`.
- Artefact GitHub Actions `14143737159`, SHA-256 archive `4642f5955784b83644f0a01b0116f72e9965c31499d0d7dcea4df01b8aad44a5`, téléchargé et contrôlé localement (`ZipFile.testzip() = None`), non commité ; conservation courte (1 jour).
- Trois fichiers publiés officiellement, contrôles de checksum sur leurs octets réels :
  - `Metadata.xlsx` — 14 442 octets, SHA-256 `61ad88fd895634928125ec8294940f112c93a585ae88b694f6bab06e7828fa04`.
  - `LandMarks_Session1.xlsx` — 13 214 octets, SHA-256 `ceea9e3534bd9711bd0c704eb51615b8ad782c1ccdf912ce780546a4721b7e74`.
  - `LandMarks_Session2.xlsx` — 14 813 octets, SHA-256 `dbb689977fe0af8e1c5f048cc437fed47ab19106a6a525aad6425e68590bc6a1`.
- Audit effectué avec `artifact_tool` sur le premier onglet de chaque classeur. Rapport local `ASTRA_LFFD_METADATA_VERIFIED_SUMMARY_20261115.json` SHA-256 `d08d64c1b7071b5f87b93a8324c04397755433af5b7cca78145d80e5c79cd010`.

## Contrôles négatifs et effectifs
- `Metadata.xlsx` identifie exactement **50 personnes anonymisées 051–100**.
- `LandMarks_Session1.xlsx` : 50 enregistrements, nommés `051_1_01_NFF` à `100_1_01_NFF`.
- `LandMarks_Session2.xlsx` : 50 enregistrements, nommés `051_2_01_NFF` à `100_2_01_NFF`.
- Ensemble d'identifiants : **égalité stricte 50/50/50** ; 50 paires de dates effectivement renseignées, 0 date absente et 0 intervalle non positif.
- Intervalles réels entre séances : minimum **31 jours**, médiane **74,5 jours**, maximum **99 jours**. Plage calendaire globale **2016-07-12 au 2016-11-03** ; les dates Excel (nombres de série) ont été converties avec origine 1899-12-30.
- Deux sessions × 50 personnes × 5 boîtes (visage / oeil gauche / oeil droit / bouche / nez) = **500 boîtes**. Vérification géométrique : **0 invalide** en interprétant les 4 composantes comme `x1_y1_x2_y2`. **Attention : l'en-tête du classeur indique «X1_X2_Y1_Y2» ; divergence à clarifier par les auteurs avant exploitation géométrique.**
- Conditions enregistrées par séance : chevelure identique pour **47/50**, pilosité faciale identique pour **46/50**, maquillage identique pour **42/50**, écharpe identique pour **49/50**. Ces égalités sont calculées à partir des codes d'origine, sans inférer d'identité réelle.
- Les annotations sont des *rectangles* pour le visage frontal neutre (`01_NFF`), **pas** des masques sémantiques de peau ou de cheveux et pas nécessairement disponibles pour les vingt variations.

## Limites d'accès (ne pas fabriquer de PASS)
- Aucune photographie, aucune séquence raw et aucun dataset protégé n'ont été téléchargés. Les images 2D de LFFD sont protégées par un accord de licence signé et mot de passe.
- Les 50 personnes de l'autre moitié du jeu, collectées à Lisbonne (001–050), ne sont pas présentes dans ces classeurs publics.
- Cette étude **n'a pas encore produit de score de reconnaissance sur les nouvelles photos** ; les trois descripteurs Pixels, HOG et Retina-Pool restent figés sur la PR #54.
- La distinction séance 1/séance 2 est **authentique**, contrairement aux contrôles artificiels par photographie/âge utilisés précédemment.

## Démarches faites
- Gmail primaire : **SENT** vers `lffd@eurecom.fr`, reçu `1a1dd250f655ce99` : accès autorisé à un petit sous-ensemble 2D, conditions d'accès pour chercheur indépendant, vérification ordre de coordonnées et masques.
- Gmail primaire : **SENT** vers `jld@eurecom.fr`, reçu `1a1dd2514cd35ddc` : alternatives Kinect Face (52 sujets, 2 vraies séances, 6 points), accès institutionnel ou collaboration.
- Gmail primaire : **SENT** vers `sebastien.marcel@idiap.ch`, reçu `1a1dd251b988ab52` : MOBIO (150 sujets, 12 séances) et protocole évaluant les mêmes descripteurs figés.
- Les contacts CelebAMask-HQ déjà sollicités n'ont pas été relancés en doublon. La confirmation `SENT` ne démontre ni réception effective, ni accord de licence, ni réponse.

**Unique blocage restant pour l'exécution du test LFFD :** autorisation de traiter les photographies 2D pour les mêmes 50 sujets aux deux séances, puis protocole préenregistré de dissociation visage/contexte. Aucun coût engagé et aucune modification de production.
