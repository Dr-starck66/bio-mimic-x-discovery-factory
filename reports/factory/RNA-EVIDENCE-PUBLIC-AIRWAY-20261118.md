# BIO-MIMIC X — Public Airway RNA-seq stress test, 2026-11-18

Status: **PASS for data loading and exploratory computation; NOT a biological validation**.

## Scope / independence
This exercise uses independent **public human** RNA-seq raw gene counts from Himes et al. 2014, supplied in the Bioconductor `airway` example and mirrored publicly by bioconnector. **No private E-MTAB-16643 Zollo data was used**.

Primary public dataset:
https://raw.githubusercontent.com/bioconnector/workshops/master/data/airway_rawcounts.csv

Biological interpretation reference:
https://bioconductor.org/packages/release/data/experiment/html/airway.html

Source table contains **64,102 gene rows × 8 sample columns**. Download HTTP 200 confirmed; all 64,102 rows parsed as nonnegative integer counts.

To stress-test the product's 3 control / 3 case input limit, selected:
- whole/control: SRR1039508, SRR1039512, SRR1039516
- case/treated: SRR1039509, SRR1039513, SRR1039517

The original study design is donor-matched: this six-sample *unpaired* slice is technically valid as an input/algorithm smoke test but **incorrect for rigorous biological differential-expression inference**. Two further samples were excluded solely because the present prototype only accepts six. This is a limitations finding, not an improvement claim.

## Executed results on actual public rows
- Input rows processed: **64,102**, malformed rows: **0**
- DESeq-style median ratio size factors (not a full DESeq2 fit), in the above six-sample order:
  `[0.99726258, 1.14879473, 1.14742059, 0.87462055, 0.65426688, 1.36446972]`
- Candidate gapped-effect screen (`mean normalized counts>=10`, `|log2((case+1)/(control+1))|>=1`, strict between-group replicate separation): **384 enriched and 333 depleted**
- Exhaustive assignment of 3 of 6 samples to each group: **20 splits**; observed total **717**, maximum among the 18 nontrivial alternative assignments **292**; exact two-sided global permutation score **p=0.10**.
- Top enriched ENSG00000109906: **log2FC≈7.3010** under the *exploratory* effect calculation.

## Important interpretation limits
1. Donor pairing ignored; unpaired permutations do not respect the actual experimental randomization. **p=0.10 is a program output and must not be reported as a valid inferential p-value for the Airway biological hypothesis.**
2. No gene-wise negative-binomial generalized linear model, covariate adjustment, BH FDR correction, or held-out biological accuracy benchmark has been performed.
3. The screen intentionally does not reproduce the published Airway differential-gene list or therapeutic findings.
4. No Zollo private matrices, access tokens or results were included. Use of embargoed datasets commercially requires explicit permission.
5. A paid customer pilot needs partner-selected inputs, independent ground truth/reference method, approved study design, and an agreed acceptance protocol.

## Reproduction
Script `validation/benchmark_airway_public.py` in this repository is self-contained (Python stdlib only). It downloads **nothing automatically**; obtain the public CSV directly and run:

```bash
python validation/benchmark_airway_public.py --self-test
python validation/benchmark_airway_public.py --input airway_rawcounts.csv --output public_airway_audit.json
```

The self-test was executed locally with synthetic positive and negative controls: **PASS**. The full 64,102-row public-data execution above was performed against the production browser JavaScript engine by an independent tool runtime, not yet by this Python reproduction script. Exact independent Python-vs-JS output equivalence on full public data is therefore **UNVERIFIED**, pending local execution of the Python script with the same publicly downloadable input.

Deployed product: https://bio-mimic-x-industrial-evidence-if9m9p.v2.appdeploy.ai/rna-evidence/

Commercial purpose: a transparently bounded **research-software pilot**, not an IVF treatment, diagnostic test, fully validated transcriptomic solution, or guaranteed revenue.
