# ASTRA DINO Ω v0.8 — pre-registration, frozen before seeing Xi 2024 matrix

Timestamp: 2026-11-15 (Europe/Paris). Scope: independent *test of a fixed published matrix*, **not** an autonomous dinosaur ancestral DNA recovery claim.

## Holdout
- Dataset: Xi Yao et al. (2024), **New evidence for the earliest ornithischian dinosaurs from Asia**, Dryad DOI `10.5061/dryad.08kprr5d0`, file `Dataset_S1.tnt` (73 taxa, ~383 characters per publisher). The matrix **must not** be used to alter parameters or select features after discovery of performance.
- Source is an extension of Han et al. morphological character lineage, not necessarily statistically independent of the Baron and Hendrickx character genealogies. Verify overlap BEFORE interpreting replication.
- Archive raw original bytes; SHA-256; number of taxa, characters and ambiguities. Keep the untouched file distinct from any parser-normalized representation.

## Fixed evaluation protocol (not optimized on test)
1. Preserve v0.7 model definitions: equal-branch Mk rate **0.25**, 4-state/5-state support mapped strictly to observed valid codes; equal branch lengths clearly a limitation. Variation rates 0.08 and 0.60 only as **sensitivity**. Do not select rate based on results.
2. Hide anatomical character `j` for a target taxon and retain pre-specified other observed target characters `j%5 == 0` as explicit privileged fossil side information (test only characters not in anchors); score only unambiguous observed singleton entries, report coverage, abstentions and missingness.
3. Joint mixture coefficient `lambda=0.35`, at most 12 neighbors, >=3 co-observed anchors. No fitting of parameters to Xi data.
4. Compare equal-branch Mk, train-only character majority, joint anchors and target-anchor permutation negative control. Score **accuracy, log loss, Brier**. Report bootstrap uncertainty clustered by taxon (>=500 replicates), including negative results and raw denominators.
5. A true *taxon completely blinded* task must be reported separately; a method consulting side-information from the target is **not** evidence for recovering ancestrally unknowable information.
6. External tree gate: a taxon-labelled, independently published and inspectable Newick tree must have documented source, names, and outgroups; a taxonomy/clade backbone or an unresolved star is **not** a fully resolved independent evolutionary tree; it must not be reported as such.
7. Scientific victory **only if** joint model wins against the **best of Mk and majority** on every truly independent dataset, robust across the three rates and independent topologies with 95% cluster interval excluding zero; negative controls must degrade. No genome reconstruction claim without independent genetic truth.

## Pre-registered restrictions
- Do not mask anatomical states after looking at which ones fail.
- Do not silently treat `-` (inapplicable), `?` (unknown), polymorphic character codings or `0` (actual zero) as interchangeable.
- Refuse to treat Xi 2024 as independent without auditing provenance and shared character definitions inherited from Han.
- The published article describes "382 characters" in a methods passage and Dryad README describes 383; verify **the original file** rather than choosing either figure by fiat.
- GitHub default branch/main and published websites are out of scope.

References: https://datadryad.org/dataset/doi:10.5061/dryad.08kprr5d0 and https://pmc.ncbi.nlm.nih.gov/articles/PMC11761276/ .
