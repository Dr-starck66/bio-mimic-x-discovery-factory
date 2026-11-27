# BIO-MIMIC X Ω — Parkinson / thrombine / alpha-synucléine

**Date:** 2026-11-12 · **Scope:** independent reproducibility gate; **not** a therapeutic trial.

## Sources (public, verified)

- Article: Trolese et al. *Thrombin reshapes α-synuclein biochemical properties by N-terminal truncation*. Nature Communications, 2026-10-28. https://doi.org/10.1038/s41467-026-78990-z
- Proteomics archive: PRIDE `PXD083225`, including native MS and HDX-MS experiments (metadata located, no raw spectra yet): https://www.omicsdi.org/dataset/pride/PXD083225
- Human protein sequence: UniProt P37840 (140 residues): https://www.uniprot.org/uniprotkb/P37840/entry
- University author announcement: https://www.unipd.it/en/news/parkinson-uno-studio-di-unipd-svela-un-possibile-ruolo-della-trombina

## Evidence ledger

| Claim | Status | Evidence / limitation |
| --- | --- | --- |
| Thrombin Lys6–Gly7 cleavage, fragment 7–140 | PASS (published observation) | Peer-reviewed paper, **not** independently reproduced |
| Human reference 140 residues, first six `MDVFMK` removed | PASS (sequence-only) | Deterministic source-identified gate |
| Theoretical mass of unmodified free-termini molecules | PASS (calculation only) | Full 14451.219062 Da, fragment 13699.879359 Da, delta 751.339703 Da |
| Publisher Source Data XLSX downloaded and measured | UNVERIFIED | Publisher metadata lists it, inaccessible from execution sandbox |
| Original PRIDE native MS / HDX-MS spectra downloaded | UNVERIFIED | PXD083225 metadata available, raw acquisition files not retrieved |
| Published aggregation and toxicity effect independently recomputed | UNVERIFIED | No full measurements or sample design |
| Patient tissue fragment and therapeutic benefit | UNVERIFIED | Not established by this research |

## Reproducibility and negative controls

Use the existing BIO-MIMIC X `validation/`, `tests/`, `reports/factory/` conventions.

```sh
python -m unittest tests.test_parkinson_thrombin_sequence_gate -v
python validation/parkinson_thrombin_sequence_gate.py --output reports/factory/PARKINSON-THROMBIN-RECEIPT-LATEST.json
# Deliberately nonzero until real evidence is scientifically interpreted:
python validation/parkinson_thrombin_sequence_gate.py --require-experimental-data
```

The tested local reference package also includes a more extensive source receipt and local test logs. It is distinct from CI; do not infer a GitHub Actions PASS from the branch's existence.

The experimental CSV parser requires columns `experiment_id,assay,sample_id,condition,value,unit`; conditions are exactly `intact_1_140` and `truncated_7_140`. Reject duplicate or unmatched pairs, non-finite numbers, unapproved conditions, n<3 and n>16. Compute an exploratory two-sided exact sign-flip p-value only for *biologically justified* paired replicates. Never infer pairing, power, multiplicity correction, disease relevance, or scientific replication from software computation alone. Unit tests contain only explicitly **synthetic fixtures**, never presented as research observations.

## Next scientific gate

1. Retrieve publisher Source Data XLSX, record exact link, access date, file SHA-256, size and worksheet mapping.
2. Retrieve PRIDE files for PXD083225 and record file-level SHA-256, instrument and buffer conditions, sample-to-condition mapping and technical-vs-biological replicate structure.
3. Pre-register primary MS/HDX endpoint and null hypothesis; compare 1–140 with 7–140 while controlling solution ionic strength and protein modifications.
4. Reproduce an author's plotted effect with uncertainty and controls; report negative and adverse effects (altered physiological membrane function, potential soluble-oligomer persistence), not only reduced aggregate toxicity.
5. Seek independent analysis with the Padova team; confirm whether 7–140 is measurable in verified Parkinson patient samples before discussing clinical implications.

Corresponding author: **Patrizia Polverino de Laureto** <patrizia.polverinodelaureto@unipd.it> (published contact). Data submitter: **Philipp Trolese** <philipp.trolese@univr.it> (PRIDE metadata). No email sent by this technical PR.

**Current verdict: PARTIAL.** PASS covers only sequence identity, arithmetic and tested invalid-input behavior; no biological validation, cure or treatment is claimed. No paywall bypass, paid infrastructure or secrets used.
