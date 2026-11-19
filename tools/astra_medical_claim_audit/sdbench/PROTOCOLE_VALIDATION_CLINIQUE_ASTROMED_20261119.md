# ASTRA MEDICAL Ω — Protocole de preuves diagnostiques et cliniques (v0.1)

**Date** : 19 novembre 2026. **Usage prévu à évaluer** : soutien au diagnostic séquentiel dans un contexte d'urgences hospitalières, **pour recherche sous supervision clinique, sans décision autonome**. Toute autre spécialité, population ou usage exige sa propre validation. **Statut actuel** : algorithme de garde et intégration synthétique testés; efficacité diagnostique clinique **NON DÉMONTRÉE**.

## 1. Source de données cliniquement pertinente — accès strictement autorisé

- **MIMIC-IV-Ext-SDBench v1.0.0**, doi **10.13026/xdmx-ty42**, 488 séjours hospitaliers désidentifiés : **163 entraînement, 254 validation, 71 test**; les 71 diagnostics de référence ont été revus par des cliniciens (13 diagnostics corrigés durant la revue du jeu). Source : https://physionet.org/content/mimic-iv-ext-sdbench/1.0.0/ .
- **Les cinq cas synthétiques SDBench** sont exclusivement des tests d'intégration/développement. Ils ne permettent pas de calculer une exactitude clinique. Source : https://github.com/microsoft/sdbench/blob/main/data/synthetic_case_data/README.md .
- Accès aux dossiers MIMIC : compte PhysioNet **personnel**, accréditation, formation **CITI Data or Specimens Only Research** et signature du **Data Use Agreement (DUA)**. Aucune récupération sans ces droits. Aucune redistribution des cas ou notes.
- Les cas médicaux protégés restent dans l'environnement autorisé de l'investigateur. **Ne pas les mettre dans GitHub, cette conversation, un service IA ou une sandbox cloud non évalué(e) contractuellement.** Si service externe : vérifier les exigences PhysioNet de *zero data retention*, interdiction d'entraînement et de revue humaine par le prestataire, ainsi que le DUA : https://physionet.org/news/post/llm-responsible-use/ . Préférer inférence locale privée autorisée.

## 2. Protocole d'évaluation rétrospective (première preuve)

**Phase A — pré-enregistrement, avant d'ouvrir le test :** figer commit Git, empreintes du modèle, prompts, température, taille de contexte, limites de tours, schéma de coûts, plan statistique, critères d'exclusion et de sécurité. Définir exactement l'usage ciblé, la population, le comparateur et le diagnostic final de référence. Éviter l'accès au libellé de référence côté agent; toute inspection ou tuning du test invalide ce lot comme test final. Les **163 train** servent aux travaux, **254 validation** aux réglages; **71 test** à une seule analyse de performance préspécifiée.

**Phase B — exécution appariée :** faire traiter les mêmes cas, dans les mêmes conditions, à ASTRA et à un agent comparateur (par exemple le `baseline` officiel) avec l'interface `sdbench.harness.harness.run_case`; noter les changements apportés aux modèles gatekeeper et juge. **Aucun faux score déterministe** ou diagnostic simulé ne peut servir de preuve d'exactitude. Journaliser chaque abstention, crash, test demandé, coût imputé, réponse synthétisée par le gatekeeper, latence, erreur et sortie brute; conserver ces journaux confidentiels.

**Phase C — adjudication indépendante :** deux médecins compétents dans le contexte clinique examinent à l'aveugle les réponses de chaque système et la référence, selon une grille écrite, avec troisième arbitrage des désaccords. Les jugements IA officiels SDBench (score 4/5) sont utiles **en tant qu'approximation**, mais ne remplacent pas la revue humaine. Présenter séparément les deux résultats. Contrôles : agent ne demandant aucun examen, prédictions aléatoires, comparaison « sans nouvelles informations », réponses gatekeeper non informatives, références mélangées après scellement (contrôle négatif), absence de fuite de diagnostic.

**Critères principaux avant collecte** : proportion correcte / **ensemble des cas** (abstention et crash comptés séparément et **non** considérés comme réussites); intervalles de confiance à 95 %; différence appariée ASTRA–comparateur et test exact de McNemar descriptif; proportion d'erreurs cliniquement graves; taux d'abstention, pertinence et nombre d'examens, coût, latence; analyse par sous-groupes avec effectifs et incertitude. Ne jamais masquer les pires dossiers. Aucun seuil arbitraire n'est une preuve : un objectif de non-infériorité/supériorité, sa marge et la taille d'échantillon doivent être définis **avec un biostatisticien** avant la cohorte d'étude. **71 cas sont insuffisants à eux seuls pour prouver toute sécurité ou supériorité en population.**

**Reproductibilité** : version SHA du modèle et du code, liste et ordre des cas scellés, journal d'inférence, versions de prompts, métriques agrégées et scripts d'analyse; un investigateur indépendant réexécute, sans reproduire ou publier les informations patient. Rapporter les résultats défavorables et contrôler les essais multiples.

## 3. Étude externe + démonstration d'utilité réelle (deuxième et troisième preuves)

- **Validation hors développement** dans un autre hôpital, sur une cohorte consécutive représentative, avec étiquettes et décision de référence indépendantes. Prévoir revue par DPO/éthique/établissement, base juridique et sécurité des données; ne jamais inférer que la désidentification suffit à autoriser tous les usages.
- **Étude prospective en mode silencieux** : ASTRA enregistre ses suggestions sans que les soignants les voient ou que les décisions thérapeutiques changent. Évaluer les erreurs, les sous-groupes, les alertes et les comportements d'abstention.
- Si la sécurité et l'acceptabilité sont établies, **étude comparative contrôlée** (randomisée quand approprié, avec médecin responsable) pour mesurer l'effet du support ASTRA sur la qualité des décisions, les délais, les examens inutiles, les erreurs potentiellement graves et les résultats patients. Suivre **DECIDE-AI** et les recommandations applicables; l'évaluation d'un dispositif médical et la conformité réglementaire sont des procédures supplémentaires.
- Ne jamais déclarer « sûr en clinique », « équivalent/supérieur au médecin » ou « améliore les patients » sans les données et l'analyse correspondantes. La publication d'un protocole sur Zenodo n'en serait pas la démonstration.

## 4. Commandes et outils déjà livrés

Dans un **environnement où la licence et la sécurité autorisent le traitement local** :

```bash
# Après l'accès PhysioNet, stocker data/processed_case_data/mimic/dataset.json
# localement, et vérifier la disponibilité des splits.
uv run python -m sdbench.cli.case_data mimic

# Le moteur SDBench comporte : --dataset mimic --case-set test
# --agent baseline --sdbench-config science --model <modèle>
# ATTENTION : la configuration science implique des modèles gatekeeper/juge
# officiels dont les appels peuvent être PAYANTS. Une substitution locale
# est un protocole MODIFIÉ, à déclarer distinct du résultat publié Microsoft.

# Sur les fichiers JSON résultats SDBench *officiels*, un audit agrégé :
python clinical_validation_audit.py \
  --baseline /chemin_prive/sdbench_baseline \
  --astra /chemin_prive/sdbench_astra \
  --provenance /chemin_prive/evaluation_manifest.json \
  --expected-cases 71 \
  --out /chemin_prive/rapport_agrege.json

python -m unittest -v test_clinical_validation_audit.py
```

L'auditeur refuse jeux synthétiques, split entraînement, juges/gatekeepers substitutifs déclarés, fichiers manquants ou erronés, doublons, notes incohérentes, comparaison non appariée et déclaration d'accès non autorisé. **Un manifeste auto-déclaré ne prouve pas en soi l'existence d'une accréditation ou d'un comité indépendant** : les originaux et signatures restent à auditer par un tiers.

## 5. Situation réelle et verrou externe

- **PASS local** : programme d'audit statistique, contrôle de provenance et tests unitaires (voir journaux), utilisant des cas factices uniquement.
- **UNVERIFIED** : accès utilisateur aux 488 cas restreints PhysioNet, exécution des 71 cas de test, jugement clinique indépendant, validation externe, bénéfice patient.
- **Action externe nécessaire** : accréditation PhysioNet/CITI/DUA, puis investigateur clinique et biostatisticien indépendants. Impossible de remplacer ces autorisations par davantage de simulations ou de scripts.

**Références** : TRIPOD+AI, BMJ 2024, doi 10.1136/bmj-2023-078378 ; TRIPOD-LLM, Nature Medicine 2025, doi 10.1038/s41591-024-03425-5 ; DECIDE-AI, Nature Medicine 2022, doi 10.1038/s41591-022-01772-9 ; PhysioNet MIMIC-IV-Ext-SDBench v1.0.0, doi 10.13026/xdmx-ty42 ; Microsoft SDBench, https://github.com/microsoft/sdbench .