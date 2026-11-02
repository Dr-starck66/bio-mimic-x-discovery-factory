# BIO-MIMIC X

**Sequence-supported review of ambiguous gene annotations.**  
*Research-stage computational software · Non-confidential technical overview*

BIO-MIMIC X is a research workflow for examining the uncertainty behind historical gene labels, modern reference assemblies and candidate cross-assembly matches. It records the underlying sequence provenance, compares candidate genomic windows and keeps unsupported or unresolved mappings visible for review.

**[Visit the BIO-MIMIC X technical overview](https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/)** · [Read the technical fact sheet](docs/BIO-MIMIC-X-NONCONFIDENTIAL-BUYER-FACT-SHEET-2026-11-01.md) · [Discuss an independent evaluation](docs/BIO-MIMIC-X-INDUSTRIAL-PAID-PILOT-SCOPE-2026-11-02.md)

## Documented research example

A historical axolotl annotation, `AMEX60DD030069`, contains both HAND1 and HAND2 homology tags. A source-pinned nucleotide comparison found **28,830 matching bases across 28,853 local alignment columns** when the historical locus was aligned with a modern NCBI HAND1 candidate window.

- [Exact NCBI accession windows, sequence fingerprints and edit distances](reports/factory/HAND1-HAND2-ALIGNMENT-LATEST.json)
- [Methods and complete interpretation](reports/factory/HAND1-HAND2-ALIGNMENT-EVIDENCE-2026-11-01.md)
- [Reproducible implementation](validation/hand1_hand2_global_alignment.py) · [unit tests](tests/test_hand1_hand2_global_alignment.py)
- [Actual scientific acceptance run](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/actions/runs/41359105768)

This is a **candidate-window comparison**, not a confirmed unique genome-wide gene mapping. A separate predeclared four-family screen documents exclusions and unresolved references; it is not yet a representative industrial validation. [Read its full results](reports/factory/AXOLOTL-PARALOG-PANEL-EVIDENCE-2026-11-02.md).

## Assessment and use

An independent evaluation would require a partner-selected reference dataset, a conventional comparison method, verified ground-truth mappings and pre-agreed technical measures. No broad mapping-accuracy result, clinical effect or economic improvement is claimed here.

The repository also retains earlier experimental modules for computational discovery, data-source integration and scientific audit. These are described below for development continuity; their existence does not establish industrial readiness.

<details>
<summary>Earlier experimental modules and development notes</summary>

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
- Commercial evidence integrity checks — provenance, due diligence, intellectual-property caveats and rejection of unverified valuation claims

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


</details>
