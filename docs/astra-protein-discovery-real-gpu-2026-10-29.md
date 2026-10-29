# ASTRA PROTEIN DISCOVERY Ω — genuine generative engine, zero extra cost (2026-10-29)

## Live deployed console

https://astra-protein-discovery-evpr93.v2.appdeploy.ai/

Deployment confirmation: AppDeploy `ready`, QA `frontend_errors=[]`, `backend_errors=[]`, `network_errors=[]`.

## Genuine protein generation (not hypothesis generation)

- NVIDIA / Institute for Protein Design RFD4-Proteina: actual sequence + 3D structure co-generation. Official hosted Studio is embedded in the deployed ASTRA console: https://huggingface.co/spaces/nvidia/rfd4-proteina-space
- NVIDIA sponsors the dedicated GPU Space from 2026-10-21 through 2026-11-04; afterward no free dedicated GPU is promised.
- ZeroGPU fallback: https://huggingface.co/spaces/nvidia/rfd4-proteina-zerogpu (Hugging Face Free account daily quota applies, not unlimited).
- Experimental validation opportunity: https://proteinbase.com/competitions/anthropic-adaptyv-2026 (Track 3, free entry, no guaranteed selected designs).

## Verification / hard evidence

- **PASS:** AppDeploy deploy and frontend/backend QA had no reported errors.
- **PASS:** real RFD4 model, real hosted GPU and sponsor period evidenced by NVIDIA official article (2026-10-21): https://huggingface.co/blog/nvidia/rfd4-proteina-protein-design
- **UNVERIFIED:** whether the Studio iframe successfully runs inside the third-party ASTRA origin, beyond host deployment and zero network errors.
- **UNVERIFIED:** RFD4 generation from ASTRA; zero output designs verified; no CIF/FASTA or GPU inference receipt exists.
- **UNVERIFIED:** biological activity, affinity, specificity, and independent wet lab replication.
- **PARTIAL:** end-to-end automated campaign; generation is interactive in the embedded official Studio, not an automated connected API pipeline.

## Financial guard

AppDeploy connected account was confirmed on `plan=free`, `funding_plan=free`, no subscription and no top-up balance. No paid model API, compute job, or recurring task was launched. Do not attempt any metered GPU job, credit purchase or backend upgrade without explicit separate user approval.

## Next milestone

Generate **one** real design in NVIDIA sponsored RFD4 Studio and retain original CIF, sequence, model/checkpoint, seed, and inference receipt; then reproduce with an independent evaluator, and compare against negative controls. Until then, do not promote the local hypothetical-science pilot as a molecular-design result.
