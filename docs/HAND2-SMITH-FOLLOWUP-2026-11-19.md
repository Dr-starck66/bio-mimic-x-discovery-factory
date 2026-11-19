# BIO-MIMIC X — prise en compte de la réponse du Pr Jeramiah Smith (19 novembre 2026)

**Périmètre :** orthologie HAND1/HAND2 chez l'axolotl, comparaison AmbMex60DD / UKY_AmexF1_1. Aucune hypothèse de régénération humaine ni de retour commercial.

## 1. Faits conservés, sans surinterprétation

- Correspondance scientifique reçue le **19 novembre 2026** : l'assemblage plus récent est nettement plus contigu et sa précision nucléotidique est supérieure ; les inversions observées dans AmbMex60DD peuvent être imputables au scaffolding historique. Il s'agit d'une explication plausible **et non d'une inversion biologique démontrée**.
- Deux outils suggérés par le chercheur : [Minimap2](https://github.com/lh3/minimap2) pour les alignements inter-assemblages et [Liftoff](https://github.com/agshumate/Liftoff) pour le transfert de caractéristiques annotées d'un assemblage vers l'autre.
- L'analyse **d'un petit nombre de gènes**, dont HAND1/HAND2, a été explicitement indiquée comme acceptable ; **ce n'est pas** une levée générale des conditions d'utilisation/embargo sur tout l'assemblage. Une diffusion globale ou exploitation commerciale doit faire l'objet d'un examen de droits séparé.
- Si les données sont publiées prochainement, citer le manuscrit de l'assemblage : https://www.biorxiv.org/content/10.64898/2026.10.27.762315v1 (prépublication signalée en cours d'évaluation, non assimilée à un article publié).
- **Ne pas confondre les deux loci historiques :** `AMEX60DD030069` sur `CM010932.2` / chr3q avait un rapprochement HAND1, tandis que `AMEX60DD045298` sur `CM010938.2` / chr6q est le candidat HAND2 à vérifier dans cette étude.

## 2. Résultats antérieurs réellement disponibles

- La comparaison de fenêtres NCBI réelles conservée dans `reports/factory/HAND2-DIRECT-EXPERIMENT-2026-11-05.json` donne **14 éditions** dans un alignement semiglobal ciblé de la fenêtre HAND2 moderne renversée sur l'ancienne (4212 nucléotides) et **148 éditions** en comparaison dans l'autre sens sur des fenêtres de tailles différentes ; les séquences FASTA ont des empreintes SHA-256 archivées. Ces valeurs ne sont **pas** des statistiques de Minimap2 et ne constituent pas un alignement exhaustif des deux génomes.
- Dans l'email sortant du 19 novembre, nous avons indiqué « un locus complet par requête au seuil de 175 éditions ». Cette affirmation doit rester **PROVENANCE NON REPRODUITE DANS CE DOSSIER** tant que la liste complète des cibles, le logiciel, le périmètre de scan, les hits alternatifs et les journaux ne sont pas joints. Ne pas la promouvoir en preuve d'unicité.
- Le BLAST `core_nt` antérieur ne vérifiait pas les copies alternatives sur tout le génome (`reports/factory/HAND2-BLAST-XML-AUDIT-2026-11-10.md`).

## 3. Nouvelle brique ajoutée : audit indépendant PAF

Code : `validation/hand2_smith_paf_audit.mjs` (Node standard uniquement), tests `tests/hand2_smith_paf_audit.test.mjs`, exécuteur `validation/run_hand2_minimap2_parts.sh`.

Pour éviter une demande d'index géant d'emblée, l'exécuteur traite les contigs du jeu complet un par un (y compris les scaffolds non placés), concatène les alignements et archive les SHA-256. Il utilise `-x asm5 -c -N 200 -p 0.5 --secondary=yes` pour fournir les valeurs PAF/NM. **Les fichiers d'entrée doivent réellement couvrir chaque séquence de chaque assemblage : le script ne garantit pas à lui seul cette complétude.**

Exemple **uniquement lorsque les fichiers complets et outils sont réellement accessibles dans un calculateur autorisé** :

```sh
node --test tests/hand2_smith_paf_audit.test.mjs
# Chaque fichier .fa de old_parts/ et new_parts/ contient 1 contig exact, noms d'accession NCBI préservés.
# old_hand2.fa : en-tête >legacy_HAND2 ; 4341 nt ; CM010938.2:884794726-884799066
# new_hand2.fa : en-tête >modern_HAND2 ; 4212 nt ; NC_090937.1:910028725-910032936
bash validation/run_hand2_minimap2_parts.sh old_parts new_parts old_hand2.fa new_hand2.fa evidence/minimap2
```

**Garde d'interprétation :** PAF qstart/qend et NM ne sont pas identiques à une distance Levenshtein globale ; l'alignement et la couverture doivent être interprétés dans leur propre cadre. Le rapport conserve les deux directions, orientation, coordonnées, taux de couverture, classement des loci distincts et éventuels seconds hits. Il rejette toute déclaration d'unicité génomique à partir d'un alignement heuristique, même si le meilleur locus est le seul signalé. Les versions, checksums publiés, logs d'exhaustivité des contigs et témoins négatifs sont toujours indispensables.

**Liftoff — couche indépendante non exécutée :** après obtention des FASTA complets, annotations et leurs droits :
`liftoff -g historical.gff3 -o lifted_to_new.gff3 -u unmapped.txt -p 2 new_complete.fa old_complete.fa`.
Examiner les transcrits/exons HAND2 et voisins, segments partiels, copies dupliquées, orientation et gènes non transférés. Ne pas transformer une projection Liftoff en preuve curatoriale officielle. [Documentation Liftoff](https://github.com/agshumate/Liftoff).

## 4. Contrôles et verdict

- **PASS technique limité** : 9 tests de logique JavaScript exécutés dans l'isolat de préparation de ce correctif (alignement réciproque attendu, alt hit, orientation inversée, alignement trop court, identité erronée, NM absent, coordonnées invalides, duplication et PAF vide) ; tests Node conservés pour reproduction externe.
- **UNVERIFIED intégration** : pas de téléchargement des deux génomes (~dizaines de Go chacun) ni de Minimap2 ou Liftoff dans la session ChatGPT ; aucun calcul PAF sur génomes complets ni transfert d'annotation nouvellement exécuté.
- **PARTIAL scientifique** : appariement ciblé HAND2 déjà documenté ; explication du professeur Smith enregistrée ; tests de concurrence génome entier et revue curatoriale indépendants encore à établir.
- Aucune action GitHub Actions, aucune fusion, aucun paiement, aucun déploiement de production.

**Prochaine preuve déterminante :** jeu PAF conservant tous les contigs + manifest complet de séquences téléchargées + classement des hits alternatifs et contrôle négatif HAND1 ; puis transcription/exons Liftoff et revue indépendante.
