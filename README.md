# BIO-MIMIC X V4

**Démonstration commerciale publique et gratuite (mise en ligne vérifiée le 2 novembre 2026) :** https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/  
[Rapport d'audit du déploiement, HTTPS et contrôles](reports/factory/BIO-MIMIC-X-PUBLIC-BUYER-DEMO-DEPLOY-2026-11-02.md) · [Fiche industrielle non confidentielle](docs/BIO-MIMIC-X-NONCONFIDENTIAL-BUYER-FACT-SHEET-2026-11-01.md). Cette démo n'est pas une preuve d'efficacité biologique, de gain industriel validé ou de vente de 1 M€ ; le lien GitHub/AppDeploy n'est pas synchronisé automatiquement.

## Novel Species Hunter + Sovereign Research Stack

V4 conserve l'atlas et le moteur de convergence de V3 et ajoute un système de découverte de nouvelles espèces dans la littérature.

### Briques intégrées
- AION-NEXUS Mission Graph
- Evidence Network / Claim Ledger
- DUALITY-X + Arbiter
- Morpheus adversarial audit
- Negative Knowledge Graph
- AgentShield Trust Gateway
- Ω-EXPERIMENT replay SHA-256
- BENCHMARK-X10 lens
- DEVOPS-X + Data Fusion Engine
- ASTRA TARDIGRADE Ω — TARDI-SHIELD / TARDI-DORMANCY / TARDI-RECOVERY, avec checkpoints SHA-256 et reprise fail-closed
- MILLION-EURO EVIDENCE PACKAGE — nettoyage du portefeuille, sélection d’un flagship, dossier de due diligence, registre IP/risques et gate anti-faux-PASS sur la valorisation

### Sources live
- Europe PMC REST + Annotations
- Ensembl REST
- Open Targets GraphQL

Aucune clé API n'est obligatoire.

### Fonctionnement important
Le Hunter détecte d'abord des noms binomiaux dans les titres/résumés. Cette étape peut produire des faux positifs. Le bouton d'enrichissement interroge ensuite les annotations Europe PMC et renforce seulement les correspondances retrouvées. Les résultats non vérifiés restent explicitement marqués comme tels.

Le paquet de due diligence filtre désormais les fragments textuels et entités non taxonomiques hors de la surface investisseur. Le flagship actuel est sélectionné par une combinaison de qualité du portefeuille et de preuves externes curées; une preuve de littérature n'est jamais présentée comme une validation indépendante de BIO-MIMIC X.

### Utilisation
Ouvrir `index.html`. Une connexion Internet est nécessaire pour les fonctions live. L'atlas et les briques locales continuent à fonctionner sans réseau.

Construire le dossier de due diligence :

```bash
python factory/million_euro_evidence.py
python -m unittest tests.test_million_euro_evidence -v
```

### Limites
- Les scores sont des heuristiques de recherche.
- Une association animale ne démontre pas une causalité.
- Une orthologie ne démontre pas une identité fonctionnelle.
- Open Targets apporte du contexte humain, pas une validation thérapeutique.
- Une valorisation de société n'est pas une preuve de prix de cession cash.
- Tant qu'une validation externe, une revue IP/FTO et une traction commerciale ne sont pas établies, le dossier de valorisation reste PARTIAL.
