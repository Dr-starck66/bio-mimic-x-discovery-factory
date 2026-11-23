# ASTRA Ω — import scientifique ZIP autorisé (22 novembre 2026)

Statut **PASS LOCAL (12/12 tests)** ; récupération du ZIP Thermo Fisher original par le connecteur Gmail : **FAIL / UNSUPPORTED** ; intégration biologique sur données authentiques : **UNVERIFIED**.

Cette capacité est conservée dans la branche existante BIO-MIMIC X PR #69, sans nouveau serveur, cron, GitHub Actions ni dépense. Elle complète `validation/vendor_probe_bridge.py` et ne crée pas un moteur parallèle d'analyse.

## Usage

Archive locale obtenue via un transfert explicitement autorisé :

```bash
python validation/approved_archive_ingest.py --input /path/MoGene-2_0-st-v1-mm10-probe-tab.zip --out artifacts/vendor --expected-size 19701321 --convert-probes
```

Archive publique avec **vraie URL HTTPS directe confirmée** :

```bash
python validation/approved_archive_ingest.py --url 'https://sec-assets.thermofisher.com/CHEMIN_OFFICIEL_A_REMPLACER.zip' --out artifacts/vendor --convert-probes
```

Le deuxième exemple est volontairement NON exécutable tant que l'URL exacte n'est pas connue. Option `--expected-sha256` recommandée quand une empreinte officielle existe. Hôtes supplémentaires via `--allow-host`, explicitement approuvés uniquement. Ne pas versionner les octets originaux dans GitHub.

## Garanties

- Source locale ou URL publique HTTPS autorisée, interdiction des redirections et des identifiants dans l'URL.
- Limites de téléchargement, nombre de membres et expansion, contrôles SHA-256, taille, CRC, traversée de chemin, symlinks, chiffrement, ratio de compression.
- `source_manifest.json` et `source.zip` conservés dans le répertoire de sortie local, SHA-256 inclus ; aucune publication automatique.
- `--convert-probes` appelle le pont de sondes déjà existant, en conservant `UNMAPPED_PROBESET` lorsqu'aucune correspondance gène autoritative n'est disponible.

## Limites vérifiées

Le connecteur Gmail affiche `read_attachment_supported=false` sur le ZIP Thermo Fisher de 19 701 321 octets. **Cette bibliothèque ne modifie pas le connecteur ChatGPT et n'accède pas automatiquement aux fichiers de Gmail**. L'infrastructure locale de test n'a pas de DNS sortant : aucun téléchargement public réel n'a été validé durant cette intervention. Le code GitHub reste durable ; son exécution régulière n'est pas configurée.

Test : `python -m unittest discover -s tests -p 'test_approved_archive_ingest.py' -v`. Premier essai FAIL sur test ZIP-bomb (seuil initial trop permissif), corrigé ; second essai 12/12 PASS. Tests sur archives synthétiques uniquement, pas sur le ZIP original.

## Mise à jour vérifiée — 23 novembre 2026 (Dre Arantxa Perez)

Le support technique Thermo Fisher (réponse du 23/11/2026, dossier 03854821)
a communiqué **l'URL officielle exacte** de l'archive `MoGene-2_0-st-v1-mm10-probe-tab.zip`
pour la puce Mouse Gene 2.0 ST / GPL16570 :

```text
https://www.thermofisher.com/store/v3/products/sec/assets?url=TFS-Assets/LSG/Support-Files/MoGene-2_0-st-v1-mm10-probe-tab.zip
```

Le système d'import `validation/approved_archive_ingest.py` autorise déjà
`www.thermofisher.com`. Il peut donc accepter cette adresse **sans changement de
moteur et sans nouveau cron**. Invocation reproductible sur un exécuteur disposant
d'un accès HTTPS sortant :

```bash
python validation/approved_archive_ingest.py \
  --url 'https://www.thermofisher.com/store/v3/products/sec/assets?url=TFS-Assets/LSG/Support-Files/MoGene-2_0-st-v1-mm10-probe-tab.zip' \
  --expected-size 19701321 \
  --out artifacts/vendor/gpl16570 \
  --convert-probes
```

La taille `19701321` octets est celle de la **pièce jointe originelle indiquée
par Gmail le 19/11**, non une taille indépendante du fichier téléchargeable.
Une discordance n'est pas silencieusement acceptée : elle doit être auditée
(variations de fichier/versions), et non contournée en supprimant toute vérification.
Empreinte SHA-256 officielle : non communiquée ; calculer et épingler celle des
octets réellement obtenus.

Pour l'alignement interespèces, exploiter le moteur déjà existant
`validation/acomys_probe_identity_gate.py` avec le FASTA transcriptomique
`GSE113081_Trinity.fasta.gz` disponible sur GEO. Le mapping versionné
probeset→gène et les identifiants réels des caractéristiques GSE74387 doivent
être vérifiés avant toute statistique au niveau du gène. Aucun `PASS` de
réplication GSE74387/GSE113081 n'est autorisé par cette étape.

**État lors de cette mise à jour :** lien officiellement reçu = PASS ;
accès ZIP distant depuis la session = FAIL réseau (DNS sortant indisponible) ;
CRC/SHA256 du ZIP authentique = UNVERIFIED ; comparaison Bowtie 1 sur données
authentiques = NOT_PERFORMED. La précédente étude préenregistrée reste FAIL.
Les données brutes ne doivent pas être commitées dans le dépôt public.
