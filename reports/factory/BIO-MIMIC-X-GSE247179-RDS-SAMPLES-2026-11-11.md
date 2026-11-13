# BIO-MIMIC X — RDS metadata extraction proof — 2026-11-11

Source: NCBI GEO GSE247179, supplemental `GSE247179_samples.RDS.gz` (HTTP 200, 1,593 bytes compressed). Two nested gzip streams were decompressed and the serialized R object was parsed by Python `rdata` into a `pandas.DataFrame`, 36 rows × 27 columns. Verified columns include `SID`, `ExternalSampleName`, `Sample_Group`, `AgeMonths`, `Treatment`, `Tissue`, `Sex`, `Genotype`, `Sample_Well`, `Sentrix_Position`, `Basename`, `Project`.

The 30 fibroblast rows represent 4/20 month C57BL/6 male fibroblasts, control/2c/7c; six remaining rows are OSKM iPSC controls. For example `ET030841A` = external `4_1A`, 4mo, control; `ET030841B` = `4_1B`, 4mo, 2c; `ET030841C` = `4_1C`, 4mo, 7c. The external sample name and internal SID are now directly verified. Do not assume replicate indices are identical donors across RNA and DNAm assays.

Prior full DNAm RDS download: `GSE247179_data_sesame.RDS.gz` 157,071,853 compressed bytes, SHA256 `c80dde2ac34e21f5f140612f48102319072ca1b8be1056e013dd7ab49d4caed0`. Two gzip layers validate and yield 471,394,725 RDS bytes; whole-object `rdata` parsing exceeded execution limit (SIGTERM), so no beta values or epigenetic ages were calculated. The smaller `GSE247179_data_sesame_40k.RDS.gz` is publicly available (HEAD 200, 77,504,081 bytes) and is a possible reduced assay path but not yet parsed.

Statuses: PASS 36×27 sample metadata extraction, PASS binary integrity; PARTIAL experimental matching; UNVERIFIED same-animal pairing, beta values, clocks, biological rejuvenation. No costs or new schedules.
