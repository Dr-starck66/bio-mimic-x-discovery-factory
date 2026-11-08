# ASTRA BIORESEARCH Ω — occupational research mesh (research prototype)

**Purpose:** coordinate BIO-MIMIC X scientific and supporting functions in a traceable, zero-additional-cost DAG. **Not affiliated with Inserm.** Florence Apparailly is an external scientific contact, not an agent, sponsor, approver or coauthor. Collaboration and funding remain UNVERIFIED.

## Existing BIO-MIMIC X engines reused

- `factory/hypothesis_engine.py::generate_hypotheses` for falsifiable hypotheses.
- `factory/debate_engine.py::debate_hypotheses` (Morpheus adversarial review).
- `factory/experiment_planner.py::plan_experiments` (conceptual plans only).
- Scientific outcomes are kept separate from computational test PASS. No clinical benefit or biological validation is implied.

## Roles and interoperability

23 executable roles in `factory/inserm_mesh.py` cover scientific direction, primary-source documentation, cohort integrity, genomics, RNA, proteomics, immunology, extracellular matrix, Acomys/Mus comparisons, bioinformatics, statistics, epidemiology, hypotheses, adversarial review, conceptual experimental design, ethics, clinical safety, privacy, legal/IP, quality, finance and partnerships. All depend on earlier task outputs; one shared mission and a SHA-256-linked handoff record make missing evidence visible to downstream roles.

This is **not yet a network of 23 standalone LLMs**. Most roles run explicit, deterministic policies; three reuse computational reasoning engines. Do not claim that data presence implies scientific verification. The prototype does not access private patient data, perform wet-lab experiments, send messages or schedule jobs.

## Optional locally executed model (no remote API)

If Ollama and an already downloaded model are available on the user's computer, add the `--local-model MODEL` flag. This dispatches bounded prompts to `127.0.0.1:11434/api/generate` for each role, with earlier role findings passed to dependent agents. Responses are **unverified suggestions**, not evidence. There is no automatic model installation, remote provider, paid API, scheduler, e-mail or patient-data transmission. A local model inference run has **not** been demonstrated in this change.

Example: `python factory/inserm_mesh.py --mission examples/florence-apparailly-mission.json --out /tmp/astra-inserm-report.json --local-model llama3.2` (only if the model is already installed locally).


## Run locally (Python stdlib, free, no GitHub Actions)

```bash
python factory/inserm_mesh.py --mission examples/florence-apparailly-mission.json --out /tmp/astra-inserm-report.json
python -m unittest discover -s tests -p 'test_inserm_mesh.py' -v
```

**Demonstration:** 10 isolated local unit tests PASS. Sample evidence is empty *on purpose*. Expected scientific statuses are UNVERIFIED or PARTIAL; technical DAG execution can PASS. This avoids pretending to have verified macrophage/ECM experimental evidence.

## Safety and collaboration boundary

No external email, no expense, no new cron, no clinical intervention, no approvals fabricated. Actual biological validation requires publications and datasets with independently checked provenance, negative controls, biological replicates and authorized expert review.

## Registry entry proposed (central registry not yet updated)

`ASTRA-277 | ASTRA BIORESEARCH INSERM MESH Ω | 1.0.0 | research, code, BIO-MIMIC X | ASTRA-083, ASTRA-086, ASTRA-087, ASTRA-097, ASTRA-113, ASTRA-234, ASTRA-235, ASTRA-236 | bio-mimic-x-discovery-factory/factory/inserm_mesh.py | PARTIAL (local technical tests PASS, scientific verification UNVERIFIED)`

Do not treat this ID as canonically registered until the central `indexation/ASTRA_REGISTRY.md` is updated and checked for concurrent changes.
