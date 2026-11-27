# ASTRA MEDICAL CLAIM AUDIT Ω v0.4 — recherche sans oracle, modèle scientifique et abstention

**12 novembre 2026 · recherche non clinique uniquement.** Aucun patient, aucune recommandation thérapeutique, aucun abonnement ou service permanent créé. Les données SciFact sont réservées à une évaluation **non commerciale** (CC BY-NC) ; le checkpoint VeriSci annonce une licence `other` dont les droits de redistribution et de valorisation restent à clarifier. Ce dépôt ne redistribue **aucun poids** du modèle.

## 1. Périmètre réalisé et sources

- Réutilisation de BIO-MIMIC X / Claim Ledger / contrôle de provenance et des statuts PASS, PARTIAL, FAIL, UNVERIFIED dans la PR #48.
- Téléchargement vérifié du SciFact officiel : archive SHA-256 `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`; 5 183 documents, 300 affirmations de développement. `claims_dev.jsonl` SHA-256 `86f0435d08fdb65d1aa41d1472684f57e6e71930626497bdf4d7a9ec1a632217` ; `corpus.jsonl` SHA-256 `b8d6c89624cb2ed74dee8938effc4f5d8bd2086887880af8110d64be4ceade62`.
- `retrieval_scifact.py` classe les résumés via BM25 (k1=1.2, b=0.75) sur **l'affirmation seule** : ni `evidence`, ni `cited_doc_ids` ne servent au classement. Les gold labels n'interviennent qu'**après** pour calculer les performances.
- `scifact_specialized_open_v04.py` : sur chaque affirmation, récupère uniquement le document classé premier par BM25 et **trois phrases** de son résumé choisies par chevauchement lexical avec la question, puis exécute une véritable inférence PyTorch CPU sur le modèle SciFact `rishhh/verisci-claim-verifier-retrieval-adapted-seed123` (révision épinglée `5bed61128b128f6f960aa80d1aa8ac3d1bdd9b0f`). L'entrée est **claim d'abord, evidence ensuite**, conformément au [code officiel du classifieur](https://huggingface.co/spaces/rishhh/verisci-claim-space/blob/main/src/verisci/verification/predict.py) et à son [code d'entraînement](https://huggingface.co/spaces/rishhh/verisci-claim-space/blob/main/src/verisci/verification/train.py).
- SHA-256 des poids locaux `model.safetensors` : `0c7441331a884980a6f630159c292bdff85df6f3a3a261117def26b7b7e5b62e`. SHA-256 du code d'inférence exécuté : `e533c41e91fd292a67f83ee2bca90866e0e3ab5a127f59c9b1d9d0bba7431389`.

## 2. Recherche documentaire : PASS technique

| Rang | Trouvés / 188 cas avec au moins une preuve annotée | Rappel |
|---|---:|---:|
| Top 1 | 133 | 70,74 % |
| Top 3 | 158 | 84,04 % |
| Top 5 | 166 | 88,30 % |
| Top 10 | 176 | 93,62 % |

MRR@10 = 0,78447. Les 112 affirmations NEI sans preuve annotée ne sont pas incluses dans le dénominateur. **Il ne faut pas interpréter cette métrique comme une exactitude médicale ou la capacité à détecter une fausse affirmation.**

Archive : [reports/bm25_scifact_open_dev300_v04_20261112.json](reports/bm25_scifact_open_dev300_v04_20261112.json). SHA-256 des résultats BM25 originaux : `ea76b8bbd2d22e3e2ba4efbb41f0a62122aa26e30ba7cc4f4f9e7cf62939399f`.

## 3. Modèle scientifique : seuils fixés AVANT l'évaluation

Version de travail vérifiée en commit préalable au deuxième essai, sans ajustement post-hoc des seuils :
- Accepter uniquement un verdict **SUPPORT** ou **CONTRADICT**.
- Score BM25 premier document au moins **8,0**.
- Probabilité softmax maximale au moins **0,90**.
- Marge entre les deux premières classes au moins **0,20**.
- Sinon : **ABSTAIN** (ne pas conclure, conserver le motif).

Ces scores ne sont **pas calibrés** pour un patient, ni même calibrés statistiquement pour l'ensemble du domaine scientifique.

| Critère sur les 300 affirmations SciFact dev | Modèle brut | Avec abstention |
|---|---:|---:|
| Exactitude 3 classes sur tous les cas (abstentions non correctes) | 65,00 % | 31,33 % |
| Prises de position SUPPORT/CONTRADICT | 185 | 122 |
| Exactitude des prises de position | 64,86 % | 77,05 % |
| TP contradictions | 33 | 17 |
| FP contradictions | 26 | 9 |
| FN contradictions | 31 | 47 |
| TN contradictions | 210 | 227 |
| Abstentions | 0 | 178 |

Avec le filtre, **28 des 122 positions acceptées restent fausses** (94 correctes), dont 9 faux positifs de contradiction. Le rappel des contradictions tombe de 51,56 % à 26,56 %. **Statut fiabilité/acceptation clinique : FAIL**.

Rapport reproductible compressé logiquement : [registre de 300 sorties](reports/scifact_bm25_verisci_300_case_ledger_v04_20261112.json). Il comprend chaque identifiant, le gold label, la prédiction brute et filtrée, l'ID du document BM25, les scores et des drapeaux de motifs d'abstention. Les valeurs de confiance et marge y sont arrondies ×10 000, les scores BM25 ×100. **SHA-256 du registre relu depuis GitHub et recalculé indépendamment :** `a22d380d587dda658f6b6adea23a1b90bdf9d31849eec26cafe13ca431a52027`. SHA-256 du rapport JSON intégral original en sandbox : `6716b0c48e36c879bea856ff8940210464c351231dc8bf8a300a88b84bac2aeb`.

**Audit rétrospectif indépendant depuis le fichier GitHub : PASS** (300 IDs uniques, matrices raw/selective recalculées, garde d'abstention cohérente pour chaque sortie). Il n'y a **pas** eu de réplication externe sur une autre infrastructure.

## 4. Contrôle négatif et correction

Le **premier essai** avait inversé l'ordre des deux textes pour le tokenizer et envoyé le résumé entier au lieu d'un extrait pertinent : 37,67 % d'exactitude et aucune contradiction détectée. Son rapport a été validé structurellement mais sa méthode était **FAIL_PROTOCOL** ; les résultats sont conservés dans [reports/verisci_scifact_invalid_input_order_negative_control_20261112.json](reports/verisci_scifact_invalid_input_order_negative_control_20261112.json) et ne servent pas à évaluer les performances du modèle. Le second essai corrige les entrées selon la source officielle, **sans changer les seuils**.

Tests Python : **50/50 PASS** (`python3 -m unittest discover -s tests -v`, Python 3.14.4) ; modèle exécuté en CPU avec PyTorch 2.15.0+cpu et Transformers 4.57.6. Le rapport initial corrigé est complet malgré une limite d'exécution du premier essai ; la sandbox Vercel a ensuite été arrêtée automatiquement. Les résultats versionnés sont conservés sur GitHub, pas comme un processus permanent.

## 5. Reproduction sur une machine de recherche autorisée

```bash
cd tools/astra_medical_claim_audit
python3 -m unittest discover -s tests -v
# Dans un dossier de données non productif :
curl -fL -o data.tar.gz https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
echo '11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be  data.tar.gz' | sha256sum -c -
tar -xzf data.tar.gz
python3 /CHEMIN/DU_DEPOT/tools/astra_medical_claim_audit/retrieval_scifact.py --root . --out retrieval.json
# Env Python isolé possédant torch et transformers, quotas gratuits :
python3 /CHEMIN/DU_DEPOT/tools/astra_medical_claim_audit/scifact_specialized_open_v04.py --root . --out specialist_results.json
```

**Limites non levées :** SciFact dev est public et connu du créateur du modèle, avec un **risque de chevauchement avec les phases d'évaluation externes** ; ce n'est pas un véritable blind test indépendant. Le corpus ne comporte pas de dossiers réels de patients, d'avis d'oncologues ni d'issues cliniques. L'obtention des extraits se fait par chevauchement lexical, et une partie des documents pertinents échappe au top 1. La reproductibilité sur une seconde machine, la calibration hors domaine, l'évaluation en aveugle et toute validation clinique restent **UNVERIFIED**.

**Gate ASTRA :** corpus/recherche PASS ; tests PASS ; téléchargement PubMed réel PASS hérité v0.3 ; inférence spécialisée réelle PASS (exécution), registre GitHub PASS ; fiabilité scientifique FAIL ; application à la décision médicale et déploiement clinique interdits. Pas de fusion ni déploiement de production.

**Prochaine action prioritaire** : évaluer en aveugle, sur un corpus biomédical externe distinct avec labels vérifiés et règles d'abstention gelées, puis faire auditer les faux positifs/faux négatifs par des cliniciens indépendants, avec autorisation et droits appropriés.
