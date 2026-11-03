# BIO-MIMIC X — on-site analysis request for an authorized research partner
**Version:** 2026-11-03 · **Status:** SOFTWARE READY FOR VALIDATION; INSTITUTIONAL ACCESS AND RELEASE NOT GRANTED · **Budget:** €0 additional

## Research question
In Berg et al., *Aging Cell* (2026), DOI [10.1111/acel.70751](https://doi.org/10.1111/acel.70751), does the within-donor decrease in Horvath Skin&Blood clock age between induced neural stem cell (iNSC) day 14 and late passage persist once independently measured RNA cell-fate identity is accounted for?

**Important:** This is an observational covariate association test, **not** evidence of causal rejuvenation. RNA and DNA methylation are linked by **public donor/stage pseudonyms**, without verified same-aliquot identity or batch/treatment correspondence.

## Why an authorized institution must process the data
- Human RNA-seq and processed expression are **controlled-access**: NCBI dbGaP **phs004047.v1.p1**, 48 RNA experiments; 47 processed expression records catalogued. GEO **GSE295849** methylation is public.
- Access is governed by the relevant **institutional/DAC Data Access Request**, consent and Data Use Certification. Neither public SRA metadata nor a publisher's open-access paper grants raw/derived individual expression access.
- **Preferred request:** Bonn authors or an institutionally approved collaborator should run the script locally in their already-approved computational environment, and send only a **disclosure-reviewed high-level aggregate** (or tell us that even aggregates cannot be shared). This avoids any transfer of samplewise protected RNA.

## Exact target pairs from public study metadata
| Pseudonym | D14 SRR | LP SRR |
|:---|:---|:---|
| 190 | SRR34149245 | SRR34149253 |
| 216 | SRR34149282 | SRR34149276 |
| 218 | SRR34149268 | SRR34149289 |
| 286 | SRR34149280 | SRR34149287 |
| 287 | SRR34149266 | SRR34149274 |
| 288 | SRR34149251 | SRR34149261 |

See [independent public provenance register](./GSE295849-RNA-LAWFUL-ACCESS-REQUEST-2026-11-02.json) for full SRX, BioSample, and GEO source condition identifiers. **These are candidate condition-level pairs, not proof of the same physical cell aliquot.**

## Minimal data requirements inside the authorized environment
A locally created TSV, **not committed or emailed**, with first column `gene_symbol`, the **12 listed SRR run IDs** as separate columns, and at least 1,000 complete gene rows of **raw integer counts**, with verified unique gene symbols and complete library sizes. No fabricated, imputed, TPM, VST or normalized values substituted for raw counts.

Use the existing preregistered marker panel (six neural and six erythroid genes). Exact symbol mapping and ambiguous Ensembl loci must be examined and documented by the approved analyst. Ambiguity or insufficient marker coverage fails closed; do not silently select gene IDs.

## Authorized execution (on the **institution's private computer only**)

The analyst must first verify that the institutional/dbGaP agreement covers use of the restricted study data and that the intended **six-donor summary** is permitted for release. This script does not and cannot grant permission or certify its validity.

```bash
cd /path/to/bio-mimic-x-discovery-factory
python -m unittest tests.test_gse295849_authorized_aggregate_export -v

# NEVER EXECUTE ON GITHUB ACTIONS OR A SHARED CLOUD RUNNER.
# This example assumes a researcher has verified BOTH distinct approvals.
python -m validation.gse295849_authorized_aggregate_export \
  --institutionally-authorized \
  --aggregate-release-approved \
  --authorization-reference 'REFERENCE_PROVIDED_BY_INSTITUTION' \
  --release-reference 'APPROVED_DISCLOSURE_REFERENCE' \
  --rna-counts /secure/phs004047/authorized_gene_counts.tsv \
  --out /secure/approved-output/aggregate-only.json
```

### Hard safeguards
1. Both separate authorization/release attestations and references are required. Mere command-line flags are **not proof**; the approved scientist must check actual authorizations independently.
2. GitHub Actions and CI are rejected **before opening any restricted RNA**.
3. Restricted input and released output are rejected if they reside inside the repository. The aggregate JSON is created without overwriting any prior report, with OS mode 0600.
4. Output includes **only a short whitelist of cohort-level scalar statistics**, not SRR IDs, donor pseudonyms, read counts, expression vectors, or individual-donor score deltas.
5. Report automatically removes the extrapolated zero-identity-change intercept when there is no observed near-zero support. No causal rejuvenation or same-aliquot claim.
6. The six-donor summary remains small-N and possibly disclosive; **approval to disclose must be confirmed by the institution first**. If the institution declines, send no data.

### What to send us after explicit release approval
The resulting `aggregate-only.json` if authorized for this recipient, **plus written confirmation of what type of aggregate release is permitted**, treatment/batch/sex matching status, and whether follow-up independent validation is possible. If not approved, reply with “Unable to release aggregate results under applicable consent/data use rules” (no individual metadata required).

## Verified official contact and outstanding submission
- University of Bonn Institute of Reconstructive Neurobiology: https://www.meb.uni-bonn.de/rnb/reconstructive-neurobiology/contact-staff/
- University Bonn news item for the 2026 paper: https://www.uni-bonn.de/en/news/211-2026
- Corresponding author published by journal: Prof. Oliver Brüstle, `brustle@uni-bonn.de`
- Institute official contact: `r.neuro@uni-bonn.de`

**Mailing status: NOT SENT**, because ASTRA MAILGUARD Ω v2026-11-01.2 requires independently verified mailbox control in addition to an official publication of an address. No reply or verification has yet been received. Existing Gmail draft may be used once this gate is satisfied.

**Access and approval:** UNVERIFIED / no positive authorization recorded. **Software:** tests required before PASS.
