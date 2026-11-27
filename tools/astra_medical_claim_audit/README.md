# ASTRA MEDICAL CLAIM AUDIT Ω — v0.1 (prototype de recherche)

**Périmètre strict :** contrôle hors ligne, déterministe, de la **forme** des références et signalement heuristique de certaines instructions risquées dans un texte généré par IA. **Ce n'est PAS** un outil médical, un dispositif de diagnostic, un validateur de traitement, une vérification automatique de littérature, ni une autorisation de modifier un traitement.

Réutilisation conceptuelle du **Claim Ledger / Evidence Network**, du **Negative Knowledge Graph** et des statuts de preuve **PASS / PARTIAL / FAIL / UNVERIFIED** de BIO-MIMIC X. Implémentation isolée, bibliothèque standard Python, **zéro appel réseau**, zéro API, aucune dépendance à un modèle ou abonnement.

## Exécution

Depuis ce dossier :

```bash
python -m unittest discover -s tests -v
python audit.py examples/synthetic_case.json --out evidence.json
```

`schema_validation=PASS` signifie seulement que le format d'entrée a été accepté. `citation_status=PARTIAL` signifie que le lien possède une forme HTTPS plausible **sans avoir été consulté**. `safety_screen=FAIL` signale **un possible ordre de modification de traitement**, pas un diagnostic de danger clinique. `scientific_validity=UNVERIFIED` est imposé à toutes les affirmations. Les empreintes SHA-256 permettent de vérifier l'intégrité des entrées et sorties sur un même protocole.

## Garde-fous et limites

- Entrées exclusivement **synthétiques**. Rejette les champs de patient et certaines coordonnées évidentes, mais **ne constitue pas un détecteur fiable de données de santé**. N'introduire aucune information concernant une vraie personne.
- Aucune extraction de preuves à partir de PubMed, d'articles ou de recommandations, aucun contrôle de fraîcheur, de qualité méthodologique, de conflit d'intérêt, d'applicabilité à un patient ou d'effets indésirables.
- Références et qualificatifs `supports` / `contradicts` fournis par l'utilisateur : ce ne sont **pas** des preuves indépendamment validées. Les contradictions restent déclaratives.
- Détection par expressions régulières **incomplète** : faux positifs / négatifs probables (paraphrases, négation complexe, multilinguisme, obfuscation). **PARTIAL ne signifie jamais « sûr »**.
- Le score agrégé n'est pas une note clinique. **Aucune décision de soin ne doit être prise sur cette base.** Toute décision thérapeutique relève de professionnels de santé compétents.
- Une future utilisation clinique nécessitera validation prospective sur un banc indépendant, supervision médicale, politique de confidentialité/RGPD et analyse de la réglementation selon le marché et l'usage déclaré.

## Correspondance des statuts

| Périmètre | PASS | PARTIAL | FAIL | UNVERIFIED |
|---|---|---|---|---|
| Schéma / empreintes | JSON conforme et hash recalculable | — | JSON rejeté | Pas exécuté |
| Citation | **Jamais attribué en v0.1** | HTTPS structurellement plausible, non lu | URL rejetée comme référence | Référence absente / invalide |
| Détection de consigne de soin | **Jamais attribué en v0.1** | Aucune des expressions recherchées trouvée | Expression pouvant suggérer un changement de traitement | Pas exécuté |
| Exactitude scientifique | **Jamais attribué en v0.1** | — | — | Toujours : pas de validation indépendante |

## Préconditions avant pilote médical réel

Avis clinique externe ; protocole et métriques de sensibilité/spécificité préenregistrés ; tests multilingues, négations et contrôles adversariaux ; audit protection des données ; vérification des sources primaires ; clarification du statut réglementaire. Livrer **uniquement** des rapports de recherche non nominatifs tant que ces jalons ne sont pas établis.

Sources générales pour cadrage (le programme ne les récupère pas) :
- OMS, 2024 : https://www.who.int/fr/news/item/18-01-2024-who-releases-ai-ethics-and-governance-guidance-for-large-multi-modal-models
- FDA, guidance de logiciel d'aide à la décision clinique de janvier 2026 : https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software