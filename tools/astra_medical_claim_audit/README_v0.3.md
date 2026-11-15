# ASTRA MEDICAL CLAIM AUDIT Ω — v0.3 : PubMed réel + inférence SciFact

**Date d'exécution :** 12 novembre 2026 (UTC). **Objet : recherche hors décision clinique ; données publiques et synthétiques seulement.** Branche : `astra/medical-claim-audit-20261112`. PR brouillon #48, **aucun merge**, aucune publication de service clinique. Exécution Vercel Hobby sandbox isolée `sbx_m8QG609oiMpcPAl8JOujXaUaHztC`, arrêtée après les essais.

## 1. Connecteur PubMed réel — PASS bibliographique

Commande exécutée réellement avec Python 3.14.4 depuis `tools/astra_medical_claim_audit/` :

```bash
python3 -m unittest discover -s tests -v       # 37/37 PASS
python3 literature.py examples/pubmed_bibliography_case.json --allow-network --out /tmp/astra_medical_ncbi_live.json
```

Récupération NCBI EFetch HTTPS à domaine limité : PMID `22911011`, titre et DOI `10.1371/journal.pmed.1001270` : PASS. Résumé présent : PASS. Source XML SHA-256 `4b24e6070e0e275cee3f1271f19daac6319fb939d00be489359969bef5953445`. SHA-256 logique du rapport `0625b27d57e1ed59878175d89d849b0e18449b94fb55d278919615503d6423ec`. Preuve conservée dans [reports/pubmed_live_22911011_20261112.json](reports/pubmed_live_22911011_20261112.json). **Pertinence scientifique, causalité et validité clinique : UNVERIFIED.**

## 2. Inférence scientifique réelle — FAIL pour fiabilité

Données téléchargées directement depuis la [source officielle SciFact](https://github.com/allenai/scifact) (archive [data.tar.gz](https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz), SHA-256 `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`). Corpus : 5 183 abstracts scientifiques, 300 claims dev, labels : 124 SUPPORT, 64 CONTRADICT, 112 NEI. SHA-256 `claims_dev.jsonl` : `86f0435d08fdb65d1aa41d1472684f57e6e71930626497bdf4d7a9ec1a632217` ; `corpus.jsonl` : `b8d6c89624cb2ed74dee8938effc4f5d8bd2086887880af8110d64be4ceade62`.

Véritable modèle `onnx-community/EttinX-nli-xxs-ONNX`, commit source `73b90d860eddcece951b2f6776145fbc4df5be77`, poids `onnx/model_int8.onnx` (17 139 627 octets, SHA-256 `8a911863f5e9357d753102081ba30aa85129de9cea1cb2cff6e3f414415e4441`). Inférence CPU réelle, bibliothèque `@huggingface/transformers 4.3.2`, 300 paires claim–rationale et 300 paires claim–abstract, max 384 tokens. [Code source](nli_scifact_official.mjs) · [rapport complet, erreurs et matrices](reports/nli_official_scifact_dev300_v03_20261112.json).

| Indicateur | Rationale annotée (oracle) | Abstract |
| --- | ---: | ---: |
| Exactitude trois classes | 36,00 % | 45,33 % |
| TP (CONTRADICT) | 22 | 26 |
| FP | 60 | 76 |
| FN | 42 | 38 |
| TN | 176 | 160 |
| Précision | 26,83 % | 25,49 % |
| Rappel | 34,38 % | 40,63 % |

**Important** : `oracle` signifie que le document et les phrases probantes ont été sélectionnés via les labels de référence pour SUPPORT/CONTRADICT ; pour NEI, l'abstract du premier document cité. La deuxième condition utilise le même document sélectionné avec son abstract entier. **Aucune des deux ne mesure un pipeline autonome de recherche d'articles.** Les différences ne sont pas un comparatif clinique. Le modèle NLI générique n'est pas calibré pour la médecine. Un contrôle négatif élémentaire a prédit CONTRADICT au lieu de NEI (1 FAIL sur 3 tests de bon sens), conservé dans le rapport. Cette v0.3 **ne doit pas alimenter un avis médical**.

Deux processus Node séparés, même code/données/poids : matrices, erreurs, provenance et protocole identiques **PASS**, mais pas une réplication par un laboratoire externe. SHA-256 du premier rapport `c12e0ff186ad426a96638b87602cd85aab3fc7b4d67a671b8a00ec27f4e59c58`, SHA-256 du second (horodatage/durée différents) `eedf1ea0bdc7654a66418001f3a2016c19f0108b14b25d4a327aa8dbacb5f9e4`.

## 3. Reproduction (recherche uniquement, pas de patient)

```bash
mkdir -p /tmp/astra-nli-retest && cd /tmp/astra-nli-retest
npm install --no-audit --no-fund --save-exact @huggingface/transformers@4.3.2
curl --fail --location -o data.tar.gz https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
printf '11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be  data.tar.gz\n' | sha256sum -c -
tar -xzf data.tar.gz
cp /CHEMIN/DU/REPO/tools/astra_medical_claim_audit/nli_scifact_official.mjs .
node nli_scifact_official.mjs
```

Contrôler à chaque essai l'empreinte des poids récupérés et le commit modèle : le script affiche la révision du dépôt au moment de l'essai et le SHA-256 local des poids, mais ne force pas encore une révision immuable ; en cas de dérive, **ne pas comparer les métriques sans rétablir les poids exacts**.

**Statut global :** connecteur PubMed LIVE **PASS**, tests de régression **PASS**, inférence matérielle **PASS**, reproductibilité même environnement **PASS**, précision scientifique **FAIL**, recherche documentaire autonome **UNVERIFIED**, validation médicale **UNVERIFIED**, CI GitHub **UNVERIFIED**. SciFact CC BY-NC 2.0 : usage non commercial, vérifier les droits avant toute valorisation. Aucun coût ni abonnement supplémentaire demandé ; exécution dans un quota Hobby existant, montant de facturation non audité.