# ASTRA MEDICAL CLAIM AUDIT Ω v0.2 — audit bibliographique + benchmark indépendant

**Prototype de recherche, non médical, non diagnostique et non validé cliniquement.** Aucune recommandation thérapeutique. Aucun dossier patient réel. Bibliothèque standard Python, sans API payante.

## Objectif et périmètre

Ce module **réutilise la v0.1** `audit.py` et son registre de preuves (Claim Ledger / Negative Knowledge Graph). `literature.py` ajoute un connecteur strictement limité à l'API officielle PubMed NCBI E-utilities *efetch*, paramétrée uniquement par un PMID numérique extrait de l'URL `https://pubmed.ncbi.nlm.nih.gov/<PMID>/`. Les domaines arbitraires, les redirections et les autres paramètres réseau sont interdits.

L'audit vérifie la concordance **PMID, titre, DOI**, la présence d'un abstract et les **SHA-256 des octets XML téléchargés**. Un succès d'identité bibliographique ne dit **RIEN** sur l'applicabilité clinique ni même sur la pertinence de cet article pour la proposition. Ces deux dimensions demeurent `UNVERIFIED`.

`benchmark.py` calcule des matrices de confusion à trois classes et une table binaire de détection des contradictions (TP, FP, FN, TN, précision, rappel, spécificité) sur les **300 lignes du SciFact dev utilisées par un dépôt tiers**. Les labels ont été créés indépendamment d'ASTRA. Pour montrer les limites d'un moteur sans lectures des études, on compare un **contrôle négatif volontairement faible** (mots-clés dans la seule affirmation) aux prédictions RoBERTa du **dépôt tiers**. **Ce modèle externe n'est ni entraîné, ni exécuté, ni fourni par ASTRA.** Ces FP/FN sont relatifs à la classe `CONTRADICT` de SciFact, **pas des taux d'erreur sur des décisions médicales**.

## Exécution

```bash
cd tools/astra_medical_claim_audit
python -m unittest discover -s tests -v
python literature.py examples/synthetic_case.json --out literature_report.json
# Appel NCBI réel UNIQUEMENT après opt-in explicite :
python literature.py examples/pubmed_bibliography_case.json --allow-network --out pubmed_literature_report.json
# Télécharger séparément les sorties de l'équipe externe ; contrôler leur empreinte :
# https://github.com/Karthikvenugopal/Claim-Level-Halluciantion-Detection/blob/main/results/benchmark_results.json
python benchmark.py /chemin/vers/benchmark_results.json --out benchmark_report.json
```

Le JSON SciFact tiers reste **en dehors de ce dépôt** en raison du copyright et des conditions de licence. Un rapport d'agrégats est conservé dans `reports/scifact_dev300_metrics_20261112.json` avec lien, SHA-1 Git blob + **SHA-256 du fichier source**, effectifs, matrices et méthodologie pour audit. L'empreinte doit être recalculée sur les octets exacts avant reproduction.

## Statuts

| Contrôle | Statut |
|---|---|
| 37 tests hors ligne (15 hérités, 22 nouveaux) | PASS local |
| Reconnaissance de faux PMID, DOI, titres et XML | PASS sur mocks / fixtures |
| Récupération PubMed automatisée live depuis le runtime disponible | **UNVERIFIED** (réseau indisponible) |
| Lecture de la page PubMed 22911011 et DOI officiel via recherche indépendante | PASS manuel sur site public (ne valide pas le connecteur) |
| Recalcul de la matrice 300 lignes via GitHub tiers | PASS, calcul externe avec traçabilité source ; pas un benchmark ASTRA fondé sur la lecture des articles |
| Pertinence scientifique, inférence sur abstracts, évaluation clinique | **UNVERIFIED** |

## Exigences avant utilisation réelle

1. Réussir l'exécution `--allow-network` dans un environnement autorisé sans secret, avec logs de destination, empreintes XML et cohérence DOI + titre.
2. Réutiliser un modèle de reconnaissance d'implications scientifiques **réel**, validé séparément sur des paires claim–abstract avec split indépendant et abstention.
3. Mesurer les FP/FN **du moteur ASTRA** sur le **corpus pertinent** (en conservant les `NEI`, abstentions, intervalles d'incertitude), et non les confondre avec ceux du modèle tiers.
4. Faire examiner le protocole par des professionnels de santé et spécialistes de la conformité avant toute discussion sur une aide médicale.
5. Obtenir les droits de licence nécessaires avant tout usage commercial. SciFact est sous licence **CC BY-NC 2.0**.

Références :
- SciFact officiel : https://github.com/allenai/scifact ; DOI 10.18653/v1/2020.emnlp-main.609
- SciFact données : https://github.com/allenai/scifact/blob/master/doc/data.md
- Prédictions externes : https://github.com/Karthikvenugopal/Claim-Level-Halluciantion-Detection/blob/main/results/benchmark_results.json
- PubMed 22911011 : https://pubmed.ncbi.nlm.nih.gov/22911011/ ; DOI `10.1371/journal.pmed.1001270`
- NCBI E-utilities : https://www.ncbi.nlm.nih.gov/books/NBK25499/

**Sécurité :** si aucune publication ne peut être récupérée, c'est `UNVERIFIED`, jamais `PASS`. Toute instruction à risque repérée par v0.1 reste `FAIL`, indépendamment de l'identité d'une publication.