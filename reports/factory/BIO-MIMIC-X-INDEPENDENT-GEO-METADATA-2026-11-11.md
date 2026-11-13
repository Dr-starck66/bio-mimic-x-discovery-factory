# BIO-MIMIC X — independent GEO metadata acquisition (2026-11-11)

Actual NCBI FTP fetch using authorized Floot VM, HTTP 200 on both GEO series matrices.

- GSE179847 DNAm series matrix: 63,907 compressed bytes, 479 sample titles, 479 unique.
- GSE179848 RNA series matrix: 53,506 compressed bytes, 345 sample titles, 345 unique.
- After removing literal prefix `Methylation_` from DNAm titles, 109 **exact metadata-title matches**; parsed groups HC1 21, HC2 29, HC4 18, other/unparsed 41.
- GEO metadata fields inspected: sample GEO accession, title, source name and characteristics.
- Existing `geo_pairing_audit.py` local unit suite: 5/5 PASS (duplicate, metadata, passage-negative, parsing and matrix fixtures).

These are condition-level title matches, NOT proof of same aliquot, same sample or 109 independent donors. Independent cohort contains human fibroblast HC/SURF1 conditions; eligibility for a partial-reprogramming intervention replication is NOT established. No raw DNAm beta matrix, RNA values, age-clock estimates, function or safety outcomes were evaluated in this run.

**PASS:** actual public metadata retrieval, counts and overlap, local tests.
**PARTIAL:** independent cohort metadata mapping.
**UNVERIFIED:** biological sample pairing, therapeutic replication, functional rejuvenation and clinical safety.

Keep original GSE165179/GSE165177 discordant O3 and original preregistered FAIL unchanged. No new automation or cost.
