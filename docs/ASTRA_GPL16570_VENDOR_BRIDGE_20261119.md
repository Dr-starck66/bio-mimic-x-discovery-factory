# ASTRA BIO-MIMIC X Ω — pont Thermo Fisher GPL16570 / Acomys

19 novembre 2026 — sans coût logiciel nouveau. **Statut : PASS (code et tests synthétiques) / UNVERIFIED (données réelles et validation biologique).**

## Réutilisation du moteur ASTRA existant

Le dépôt `Dr-starck66/bio-mimic-x-discovery-factory` possède déjà `validation/acomys_probe_identity_gate.py`, avec Bowtie 1 et tests de contrôles négatifs. Le présent `vendor_probe_bridge.py` ne remplace pas ce moteur : il convertit le ZIP 25-mers fourni par **Arantxa Perez (Thermo Fisher)** au format d'entrée du moteur.

**Sources externes distinctes à conserver :**

- ZIP réel : `MoGene-2_0-st-v1-mm10-probe-tab.zip`, pièce jointe du message Gmail du 19 novembre 2026, 19 701 321 octets annoncés. Le ZIP n'a pas été ouvert ici : le connecteur Gmail n'expose pas son type binaire et le conteneur est privé de DNS sortant.
- Transcriptome réel : `GSE113081_Trinity.fasta.gz`, publié sur [GEO GSE113081](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE113081), ~107,5 Mo comprimés. Non téléchargé dans ce conteneur.
- Données d'expression comparatives de plateforme : [GEO GSE74387](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE74387), non retraitées ici.
- Protocole falsifiable : comparaison d'identité entre sondes 25 bases GPL16570 et transcriptome Trinity Acomys ; la perte de réplication reste **FAIL** jusqu'à un test effectif.

## Utilisation (lorsque les octets originaux sont disponibles)

```bash
python vendor_probe_bridge.py \
  --vendor-zip MoGene-2_0-st-v1-mm10-probe-tab.zip \
  --out artifacts/gpl16570
# En option : --gene-map genes.tsv (colonnes probeset / gene_id ; annotation sourcée/versionnée)

gzip -dc GSE113081_Trinity.fasta.gz > GSE113081_Trinity.fasta
python validation/acomys_probe_identity_gate.py \
  --probes artifacts/gpl16570/gpl16570_probes.tsv \
  --acomys-fasta GSE113081_Trinity.fasta \
  --out artifacts/gpl16570/acomys_probe_bands.csv
```

Le moteur d'alignement exige **Bowtie 1 et bowtie-build**, qui n'ont pas été installés ou exécutés durant cette session. Le moteur existant travaille à au plus 3 substitutions sur des sondes de 25 bases et signale les alignements ambigus. Pour les non-alignés, ne pas conclure qu'ils ont une identité inférieure à 92 % : ils peuvent être absents de la référence ou comporter des différences supplémentaires.

**Important :** `Probe Set Name` n'est pas un identifiant de gène. Sans table d'annotation d'origine documentée, le pont écrit explicitement `UNMAPPED_PROBESET_...` dans le champ `gene_id` demandé par le moteur. Cela autorise le contrôle *technique* des sondes ; toute conclusion au niveau des gènes, de l'ECM ou des macrophages est interdite jusqu'à résolution de ces correspondances.

## Tests réellement exécutés

```bash
python -m unittest -v test_vendor_probe_bridge.py
```

9/9 PASS : lecture d'un format tabulaire représentatif, empreinte SHA-256, détection de doublons, validation de longueur et alphabet 25-mers, fichier ZIP sans tableau, annotation manquante/partielle, correspondance d'annotation versionnée, absence de faux PASS biologique.

Un autre prototype local `probe_bias_audit.py` a aussi passé 9/9 tests sur des données synthétiques, mais **il n'est pas proposé en doublon du moteur existant** dans la branche GitHub.

### Critère réel de succès scientifique

1. SHA-256 des véritables ZIP et FASTA ; intégrité CRC du ZIP et gzip du FASTA ; identification de version GPL16570.
2. Nombre réel de sondes et anomalies documentées ; table probeset→gène versionnée et traçable.
3. Alignements Bowtie 1 sur transcriptome **réel**, mono-/multi-mappings et catégories : 25/25 ou 24/25 = ≥96 %, 23/25 = 92 %, 22/25 = 88 % ; non-alignés = **UNRESOLVED**.
4. Recalcul pré-déclaré de la covariance ECM × macrophages sur **GSE74387**, avec témoins négatifs et séparation stricte des échantillons ; confrontation avec **GSE113081**.
5. Conserver un résultat défavorable si la non-réplication demeure sur sondes adéquatement appariées.

Aucun point 1–4 n'a été exécuté sur les fichiers bruts de ces deux sources dans cette réponse. Les tests PASS portent seulement sur les formats et garde-fous logiciels.
