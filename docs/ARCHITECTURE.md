# BIO-MIMIC X V4 — Architecture

## Pipeline
QUESTION
→ AION-NEXUS MISSION GRAPH
→ DATA FUSION (Europe PMC)
→ NOVEL SPECIES EXTRACTION
→ ANNOTATION VERIFY
→ ATLAS DIFFERENCE
→ EVIDENCE NETWORK / CLAIM LEDGER
→ DUALITY-X + ARBITER
→ MORPHEUS RED TEAM
→ ENSEMBL HUMAN ORTHOLOGY
→ OPEN TARGETS HUMAN CONTEXT
→ EXPERIMENT FORGE
→ NEGATIVE KNOWLEDGE GRAPH
→ Ω-EXPERIMENT REPLAY
→ BENCHMARK / DEVOPS-X HEALTH

## Important scientific distinction
A repeated phenotype across species does not prove a repeated molecular mechanism.
A molecular mechanism in an animal does not prove that manipulating its human orthologue is safe or useful.

## Data model
- Paper: immutable publication metadata + source ID
- CandidateSpecies: extracted taxon mention + evidence bundle
- Claim: statement + status + source IDs
- NegativeKnowledge: rejected subject + reason + query + timestamp
- HumanBridge: animal gene + human Ensembl target + Open Targets context
- Replay: whole run + SHA-256

## Provider policy
Allowlisted:
- Europe PMC
- Ensembl REST
- Open Targets GraphQL

All live network failures degrade to PARTIAL/FAIL. No fabricated fallback claims.
