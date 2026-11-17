# ASTRA DINO Ω — GENOME × MORPHOLOGY v1 — Audited negative result
Date: 2026-11-14 · BIO-MIMIC X · research only · 0 € additional cost.

## Scientific objective
Test whether public mitochondrial sequences of living birds can predict measured external anatomy of **previously unseen families**, then check whether the available fossil character matrices permit a defensible bridge to extinct animals. This is a software and evidence benchmark, not a nuclear genotype-to-phenotype model and not resurrection.

## Authentic paired dataset (PASS)
- AVONET BirdTree form, Tobias et al. 2022, *Ecology Letters*, DOI **10.1111/ele.13898**, originally 9,993 species in this source export. Source code repository `stephchia/bird-morphology-tda/data/raw/AVONET_birdtree.csv`; Git blob SHA-1 `ee00cd347179844041f490e6eb3e3f902cd0ed94`. AVONET license CC BY 4.0. No inferred-trait rows admitted.
- NCBI nuccore versioned mitochondrial FASTA, exact species-binomial match, 17 successful species-level pairs, 14 families, 12 orders, **291,240 nt**. Raw sequences preserved in four parts (`data/astra_dino_mtDNA_source_part{1..4}.json`).
- Derived traits are species-level AVONET measurements, **not** paired DNA and anatomy from the same biological individual. AVONET measurements can have low sampling per species.
- Snapshot `data/astra_dino_genome_trait_paired_v1.json`: length-checking accession records; independent full-sequence **11-mer Jaccard** distance (136 pairwise distances), each distance frozen with 8-digit precision.
- Full source audit independently re-ran on the four NCBI batches: **17/17** accession/length pairs, **136/136** pairwise distances PASS; largest absolute roundoff discrepancy **4.98 × 10⁻⁹** (threshold 10⁻⁷). Genome-trait analysis independently recalculated on the saved snapshot: exact match to original result.

### Access failures (not imputed)
Three originally identified FASTA species (`Falco peregrinus`, `Pygoscelis adeliae`, `Passer domesticus`) could not be successfully re-fetched from the permitted NCBI read endpoint at the time of freezing. Their sequences/traits were **excluded**, not invented. Independent ENA attempt returned HTTP 400; no paid service was used.

## Predeclared baseline / data leakage controls
Leave-one-family-out (LOFO), 17 species × five traits = **85 held-out observations**. For each bird, all members of its family are removed from the training pool. Choose k=3 nearest **other-family** birds by mitochondrial 11-mer Jaccard distance. Predict `log(trait)` by arithmetic mean `log(trait)` of the k=3. Reference is mean `log(trait)` of all remaining families. Compare mean absolute error on exactly the same cells, lower is better.

| AVONET trait | Genomic-neighbor mean absolute log error | Reference mean absolute log error | Winner |
|---|---:|---:|---|
| Body mass | **1.767369** | 1.970340 | Genomic |
| Beak length (culmen) | 0.619521 | **0.578334** | Reference |
| Beak depth | 0.547501 | **0.453093** | Reference |
| Tarsus length | 0.857779 | **0.846505** | Reference |
| Wing length | 0.596682 | **0.590316** | Reference |
| **Mean across five outcomes** | **0.877770** | 0.887718 | +**1.12 %** in relative error reduction |

A weak +1.12% overall apparent gain is **not** a demonstrated credible genetics-to-trait predictor. Four of five morphology outcomes are worse than the reference. Sample size = 17, high phylogenetic dependence, no external individual-level test, no confidence bounds for biological generalization.

Negative control: 200 deterministic Fisher–Yates permutations (seed 20261114) of genomic sequence identity, preserving morphology and family-based train partitions. Null mean absolute log error **1.012493**; null permutations with loss <= observed: **15/200**, empirical one-sided p = **16/201 ≈ 0.07960**. This does not cross a usual 0.05 threshold, and the exploratory null should not be treated as a pre-registered discovery.

## Fossils crosswalk — explicit refusal to overclaim
Previously validated independent fossil source (Wang et al. 2021, DOI 10.1098/rspb.2020.3105; repository `graemetlloyd/ProjectAncientBeak`) contains both modern-bird **Anas** and **Gallus** genus-level terminals among 80 taxon × 280 discrete characters. Our AVONET+NCBI pairing covers **Anas platyrhynchos** and **Gallus gallus**. This yields **two shared genera**, not 17 paired fossil samples.

**Gate: PARTIAL / GENOME_TO_FOSSIL_TRANSFER_DISABLED**. AVONET beak dimensions, wing/tarsus lengths and mass are continuous individual-external morphometrics; fossil Wang matrix records different, predominantly discrete osteological characters. They are NOT automatically homologous variables. No mapping with verified trait definitions or independent phylogeny, thus no valid fossil target inference or ancestral nucleotide reconstruction. Hypothesis about evolutionary origin remains untested by genome-trait data.

## Code, testing, scientific next step
- `validation/astra_dino_genome_trait_v1.mjs`: strict validation, source-distance recomputation, LOFO no-family-leakage, randomized null, fossil transfer abstention.
- `tests/test_astra_dino_genome_trait_v1.mjs`: 6 deterministic synthetic offline unit tests including negative cases; **6/6 PASS** in local Node.js v22.16.0.
- On frozen GitHub snapshot, independent calculation of the actual 85 scored observations: **PASS**. The exact published validation module's end-to-end execution on that snapshot from GitHub runner/environment is **UNVERIFIED**; GitHub Actions not assumed working.
- Research priorities: swap mitochondrial similarity (mostly ancestry signal) for independently verified **nuclear** variants / genomic loci. Published beak-shape candidate ALX1 (Lamichhaney et al. 2015, *Nature*, DOI 10.1038/nature14181); beak-size locus HMGA2 (Lamichhaney et al. 2016, *Science*, PMID 27102486); genome sequencing data B10K (BioProject PRJNA545868). Before scoring fossils, build a phylogenetically justified homologous trait dictionary, including missingness audits and a larger held-out set.

## Status ledger
- Authentic matched data: **PASS**, 17 species, 14 families, 291,240 nt.
- 136 original distances reproduced from frozen FASTAs: **PASS**.
- Saved snapshot prediction independently reproduced: **PASS**, 85 observations.
- Local 6/6 software unit tests: **PASS**.
- Published exact script end-to-end on real snapshot/CI: **UNVERIFIED**.
- Useful predictive genomic model: **PARTIAL / insufficient evidence**.
- Verified trait homology, reliable fossil prediction, extinct genome and dinosaur revival: **UNVERIFIED**.
- Git main: unchanged. No deployment, new scheduled task, wetlab intervention, or paid resource.
