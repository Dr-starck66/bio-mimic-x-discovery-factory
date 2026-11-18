# ASTRA Ω — Suite aux réponses scientifiques du 17–18 novembre 2026

**Test local : PASS (12/12 cas synthétiques/fixtures)** ; **données scientifiques originales : UNVERIFIED** ; **validation biologique/physique : NON établie**.

## BIO-MIMIC X — avis Jason Brant

Brant confirme le même modèle de blessure et les mêmes temps de prélèvement pour GSE74387 / GSE113081 ; la divergence de plateforme (array **Mus** GPL16570 utilisée avec cDNA **Acomys** versus RNA-seq aligné sur assemblage **Acomys** Trinity) constitue une hypothèse de biais de liaison, en particulier pour les gènes immunitaires/macrophagiques. **Le gate de réplication antérieur reste FAIL**.

Le nouveau \`validation/acomys_probe_identity_gate.py\` classe des **25-mers vendor-provenance** alignés à \`GSE113081_Trinity.fasta\` via Bowtie 1 (mésappariements 0–3, sans indel) :
- 0 ou 1 mismatch : ≥96 % d'identité ;
- 2 mismatches : exactement 92 % ;
- 3 mismatches : 88 % (<92 %) ;
- aucun hit à ≤3 mismatches : **UNRESOLVED**, et NON « faible identité démontrée » ;
- loci multiples ex aequo : **AMBIGUOUS**, hors des sondes interprétables.

Les empreintes SHA-256 des entrées sont enregistrées. Le module ne teste PAS à lui seul les corrélations ECM × macrophages, l'expression différentielle ou une réplication biologique.

Pour le test réel, après acquisition des vrais 25-mers GPL16570 et du FASTA public :

\`\`\`sh
gunzip -kc GSE113081_Trinity.fasta.gz > GSE113081_Trinity.fasta
python validation/acomys_probe_identity_gate.py --probes GPL16570_25mers.tsv --acomys-fasta GSE113081_Trinity.fasta --out reports/factory/acomys_probe_identity.csv
\`\`\`

Pré-critère de discrimination : comparer séparément les modules ECM/macrophages et les amplitudes d'expression sur sondes à haute identité non ambiguës ; conserver l'issue négative si ces sondes échouent encore à reproduire le signal. Relecture RNA-seq sur une référence Acomys moderne, indépendante, sans fuites ni adaptation a posteriori.

## ASTRA DEEP GEO Ω — avis Mike Vardaro (OOI)

Le fichier existant \`validation/ooi_axial_hydrothermal.py\` contrôle déjà l'identité du capteur Escargot **TRHPHA301** et le QARTOD des vraies températures. Le nouveau \`validation/ooi_hitl_annotation_gate.py\` le **réutilise**, accepte un JSON d'annotations d'instruments (ISO UTC ou \`beginDT/endDT\` Unix millisecondes), et masque de manière conservatrice toutes les fenêtres temporelles annotées avant une interprétation. Il conserve les comptages pré/post et compte spécialement les exclusions **HITL**.

**Contrôle négatif PASS sur fixture :** un pic artificiel dans une mesure QARTOD=1 recouvrant une annotation « HITL sensor outage » disparaît de l'écran des anomalies après filtrage. Il ne s'agit PAS d'une anomalie volcanique réelle.

Exécution réelle, sous réserve des véritables octets NetCDF et export officiel des annotations :

\`\`\`sh
python validation/ooi_hitl_annotation_gate.py --input deployment0009_RS03INT1-MJ03C-10-TRHPHA301-streamed-trhph_sample_20260804T115012.192326-20260804T120152.132220.nc --annotations-json Escargot_annot.json --out reports/factory/OOI-ESCA-HITL-RESULT.json
\`\`\`

Sources : https://thredds.dataexplorer.oceanobservatories.org/thredds/catalog/ooigoldcopy/public/RS03INT1-MJ03C-10-TRHPHA301-streamed-trhph_sample/catalog.html et https://dataexplorer.oceanobservatories.org/ . Important : \`time\` dans le NetCDF est en **secondes depuis 1900-01-01** ; les annotations \`beginDT/endDT\` sont en **millisecondes Unix**. Ne jamais confondre la mesure physique \`vent_fluid_temperature\` avec la variable d'ingénierie \`trhph_thermistor_temp\`.

## Autres preuves et pistes

- **Axolotl :** confirmation du curateur \`AMEX60DD030069 -> HAND1\` et \`AMEX60DD045298 -> HAND2\` ; ce n'est PAS une cartographie génome entier.
- **Pinsons de Darwin :** Peter Grant a transmis la demande de croisement identifiants génotype/phénotype à ses coauteurs. Pas encore de données correspondantes.
- **Melanin shield :** recommandation d'un spécialiste en transport de rayonnements ; comparaison à masse surfacique constante avec polyéthylène, séparation photon/bêta des doses GCR/SEP.
- **Cohere :** documentation d'un essai API gratuit limité pour North Mini Code ; **aucun benchmark authentifié exécuté**.
- **Blue Smart Robotics :** échange de validation envisagé le 23 novembre ; aucune performance matérielle acquise.

## Test reproductible

\`\`\`sh
python -m unittest discover -s tests -p 'test_scientific_replies_20261118.py' -v
\`\`\`

**Observation locale 18/11/2026 : 12 tests, OK.** Les fichiers originaux GEO (107,5 Mo FASTA), les sondes GPL16570, le binaire NetCDF OOI et le JSON des annotations n'étaient pas accessibles depuis le conteneur : aucun effet biologique/géologique réel ne peut être donné PASS. Aucune exécution GitHub Actions, publication scientifique, tâche planifiée, installation payante ou déploiement public n'est revendiqué.
