# HAND2 — independent remote BLAST and curator audit (2026-11-18)

## Scope and provenance
Read-only independent compute on existing Floot VM (Node.js with network, no GitHub Actions). The historical query was retrieved from NCBI EFetch: CM010938.2, 1-based inclusive 884794726–884799066, 4,341 nt. NCBI BLAST remote requests used taxid 8296 and megablast, with a maximum of 100 reported hits and E-value threshold 1e-10.

## Executed evidence
- `core_nt` remote BLAST RID **FTSRZ49P014**: **READY**, `ThereAreHits=yes`. XML reports:
  - `XM_069631422` HAND2 mRNA, 1181/1181 identities in aligned HSP, bit score 2182.01.
  - `KU882016` HAND2 partial cds, 531/532 identities, bit score 977.998.
  - `XM_069653976` HAND1 mRNA negative control, 173/206 identities, bit score 193.172.
  - These are **transcripts**, not an exhaustive genomic-locus scan. Identity numerators are HSP-specific, not 4341-nt full-query identity.
- `refseq_genomic` remote BLAST RID **FTSU75ND016**: accepted, RTOE 23 seconds, but repeatedly reported **WAITING** through the last 2026-11-18 poll. **NO genome-wide result yet**. Do not report any genomic hit ranking or uniqueness.
- NCBI FTP directories confirmed for `GCA_002915635.3_AmbMex60DD` and `GCF_040938575.1_UKY_AmexF1_1`. Each compressed genomic FASTA is listed at ~8.3 GB. Floot VM has ~4.6 GB free; `minimap2` and `blastn` are not installed there. Whole-genome local alignment NOT executed.

## Independent human curator correspondence
Human email dated **2026-11-16**, Dr Francisco Falcon Chavez (Gmail message `1a1e42207f38914f`), explicitly confirms `AMEX60DD030069 = HAND1` and `AMEX60DD045298 = HAND2`. The email says the team is not planning corrections to AmexT47 and is working on a new assembly with lift-over annotations between UKY_AmexF1_1 and AmexT47, **not yet public**.
Dr Sergej Nowoshilow (message `1a1e3e2fd388280f`) explains that `HAND1 [nr]|HAND2 [hs]` denotes divergent closest BLAST database hits; a distinct historical HAND2 transcript `AMEX60DD201045298.1` was supported by his targeted searches and internal curated cDNA. His evidence is informative, but is not a published genome-wide reciprocal benchmark. **Do not confuse `AMEX60DD201045298.1` with `AMEX60DD045298`.**
The emails are not reproduced verbatim in this public report, to avoid disclosing private correspondence.

## Historical local flank evidence (not rerun)
Versioned local flank report `HAND2-LOCAL-FLANK-SYNTENY-2026-11-05.json` states 3888 and 4268 shared distinct 31-mers in the correct reverse-complement flank pairs, and zero in six orientation/side controls. Historical result PARTIAL; no claim of genomic uniqueness.

## Status and falsifiable closure
- **PASS**: NCBI sequence retrieval, completed transcript BLAST with HAND1 negative control, and direct reading of human curator replies.
- **PARTIAL**: historical local flanks and targeted genomic/transcript support.
- **UNVERIFIED**: exhaustive whole-genome best-hit/runner-up margin, annotated reciprocal flanking genes, published cross-assembly lift-over, independent functional efficacy.
- **BLOCKED**: remote `refseq_genomic` BLAST pending; local assembly larger than available disk.
- To claim a genome-wide PASS: search the complete versioned modern assembly with the full historical 4341 nt, report every competing locus above a prespecified score/coverage threshold, orientation, coordinates, percent identity, aligned coverage, secondary-best margin and HAND1 negative control; then reverse query the best candidate against the complete historical assembly. Preserve unfavorable alignments and source FASTA SHA256 checksums.

## Commercial boundaries
A reproducible **non-clinical annotation/orthology audit** may be offered as a paid scoped pilot, with clear deliverables and acceptance tests. This report does not prove industrial chemical performance, therapeutic benefit, military efficacy, a buyer, an agreed €2900 fee, or revenue.
