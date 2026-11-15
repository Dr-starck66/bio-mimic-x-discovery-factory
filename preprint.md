# Stress-testing idealized QAOA against classical heuristics on 70 seeded weighted MaxCut graphs: a reproducibility and cost-accounting audit

**Author:** Dr Starck  
**Research program:** ASTRA Ω Research  
**Document:** Open scientific preprint, v0.1 — 15 November 2026  
**Status:** AUTHOR-AUTHORIZED OPEN PREPRINT — NOT PEER REVIEWED — DOI PENDING AT RELEASE  
**Rights:** Author-owned original text is released under Creative Commons Attribution 4.0 International (CC BY 4.0). Third-party materials retain their original rights.  
**Interpretation:** Fully classical simulation; no quantum processor and no quantum advantage claim.

## Abstract

Quantum Approximate Optimization Algorithm (QAOA) benchmarks can be hard to interpret when the expense of optimizing circuit parameters is excluded from cost comparisons or when favorable shots are selected after evaluation. We report a deliberately small, reproducible stress test of ideal state-vector QAOA at depths `p=1` and `p=2` against four classical candidate-generating baselines on 70 **unique**, seeded, weighted MaxCut instances with 8–16 vertices. Reference optima agreed between brute-force enumeration and an independently formulated mixed-integer program solved with HiGHS for all 70 instances. With 256 terminal candidate samples per heuristic or QAOA depth, the numbers of instances at the exact optimum were 37/70 (uniform), 63/70 (greedy), 65/70 (simulated annealing), 65/70 (tabu search), 64/70 (QAOA `p=1`), and 61/70 (QAOA `p=2`). In a paired comparison `p=2` versus annealing, QAOA won on 5, tied on 56, and lost on 9 instances. Angle optimization used **7,980 exact state-vector expectation evaluations** across the two depths, a non-equivalent training expense excluded from the terminal 256-shot count. Two end-to-end runs matched on deterministic fields, and four injected data-integrity mutations were rejected. These findings are **negative and descriptive**, without general claims about quantum versus classical optimization.

**Keywords:** QAOA, MaxCut, reproducible computational experiments, simulation, negative results, experimental design, cost accounting.

## 1. Research question and scope

A practical benchmarking question is not merely whether a candidate returned by a quantum-inspired or quantum algorithm is good, but whether comparisons share an honest accounting unit and guard against silent data corruption or post-selection. We ask: on a disclosed small suite of unique seeded graphs, how often does a limited-depth, idealized QAOA simulator sample an exact optimum compared with conventional heuristics, and what hidden cost is incurred in selecting angles?

This is a technical audit of one *exploratory simulator* with fixed parameter search, not a claim of a representative MaxCut problem distribution, quantum hardware execution, statistical significance, general superiority, or operational speedup.

## 2. Materials and methods

### 2.1 Graph generation and exact reference

The locked corpus consists of **7 families × 5 sizes × 2 variants**, yielding 70 unique weighted MaxCut instances. The five vertex counts are 8, 10, 12, 14 and 16. The seven families are cycle/chords, Erdős–Rényi, dense, planted frustrated bipartite, disconnected cliques, lollipop and a heavy-edge family. The master seed is `20261110`; per-instance and per-method seeds are SHA-256 derived. Full graphs and method outputs are preserved in `results/benchmark_raw.json`.

An earlier generation produced **15 pairs of duplicated instances**. This invalid preliminary corpus was corrected **before** the definitive results were frozen. Every final optimum was independently checked by exhaustive search over all binary configurations and by a HiGHS mixed-integer formulation: **70/70 agreements**.

### 2.2 Candidate generation

Six methods were evaluated: uniform random candidates, multi-start greedy construction, simulated annealing, tabu search, and ideal state-vector QAOA at `p=1` and `p=2`. Every final method generated or evaluated **256 terminal candidate solutions per graph**. QAOA `p=1` used a 7×7 parameter grid (49 exact expectation evaluations per graph). QAOA `p=2` tested 64 fixed angle combinations plus one initialization from the best `p=1` setting (65 expectation evaluations per graph). These angle-search efforts were **not cost-matched** to classical search and are not equivalent to hardware shot costs.

The QAOA simulator computes exact expectations from the complete ideal state vector. Neither noise nor physical gate execution was modeled, and no QPU was accessed.

### 2.3 Safeguards

The saved study included independent matrix-state checks on three qubits for depths 1–3 (numerical differences < 10^-12), 35 normalization and symmetry checks, four deliberately falsified artefacts rejected by the verifier, historical ASTRA `solve_qubo` reuse checked on three weighted instances, a negative post-selection control, and a second complete run matching the first on deterministic output fields. These checks address implementation consistency, **not** external generalizability.

## 3. Results

| Method | Exact optima / 70 | Mean best score / exact optimum |
|---|---:|---:|
| Uniform sampling | 37 | 0.961432 |
| Multi-start greedy | 63 | 0.995012 |
| Simulated annealing | **65** | 0.995847 |
| Tabu search | **65** | 0.995866 |
| QAOA `p=1`, ideal simulation | 64 | 0.996505 |
| QAOA `p=2`, ideal simulation | 61 | 0.995800 |
| Exact enumeration and MILP | 70 | 1.000000 |

The paired `p=2` comparison against simulated annealing was **5 wins, 56 ties and 9 losses**; versus tabu search it was **4 wins, 58 ties and 8 losses**; versus greedy it was **6 wins, 58 ties and 6 losses**. The original 10,000-resample descriptive bootstrap interval for mean normalized `p=2` minus annealing was **[-0.00518, +0.00570]**, spanning zero and without adjustment for family clustering or multiple comparisons.

The QAOA optimization stage required **7,980 exact expectation evaluations**, accessing at least **139,324,416 state amplitudes**. The reported **35,840** simulated QAOA final measurements and **71,680** classical heuristic candidate evaluations represent terminal candidates only, not a common total computational budget. A post-selection negative control showed that restricting to the best quartile would artificially inflate mean cut scores by about **2.94** (`p=1`) and **2.41** (`p=2`) score units, respectively. The published table uses unfiltered values.

## 4. Interpretation

The experiment failed to demonstrate an advantage for `p=2` QAOA over the examined classical heuristics in this setting, despite optimistic idealized access to exact expectations. Differences between depths must not be interpreted as a monotonic physical QAOA failure: the `p=2` parameter search and shot realizations are separate from the `p=1` experiment. Exact expectation quality and sampled best-solution quality are different metrics.

Comparability remains limited by unequal training-versus-search budgets, small graphs, structured rather than representative instances, ideal noiseless simulation, fixed seeds and a non-exhaustive angle policy. The descriptive interval is not confirmatory. A more credible independent follow-up requires larger preregistered unseen graph cohorts, multiple seeds, realistic hardware cost/noise and an equal-resource accounting method.

## 5. Data/code provenance and reproducibility

Original research records were created **10 November 2026** on the private branch corresponding to [ASTRA QUANTUM GATE Ω PR #229](https://github.com/Dr-starck66/indexation/pull/229). The source, validation code, deterministic comparison, raw JSON, independent MILP records and SHA-256 manifest are under:

`tools/astra-quantum-gate/advanced-20261110/`

Audit snapshot: `4cfcdd49342859a9ca3a1305e82f992f31cffc98`. Instructions: `README.md` in that directory. The main Python runner is `astra_advanced_maxcut.py`; the independent validators are `verify_advanced.py`, `test_quantum_properties.py`, `verify_legacy_astra.py`, `statistics_summary.py`, and `verify_repetition.py`. The 70 graphs and outputs are in `results/benchmark_raw.json`; a second full deterministic run is in `results_repetition/benchmark_raw.json`.

The numerical evidence above is drawn from the version-locked research reports and result JSON. **This preprint preparation is not itself a fresh benchmark execution.** Original code and raw graph data currently reside in a **private** research branch and are not independently downloadable from this release, limiting external reproducibility. No source code, trained weights, proprietary experiments, or third-party files are included here.

## 6. Conflicts of interest, ethics and release gate

This is research carried out within **ASTRA Ω Research**, a broader program that also explores commercially oriented software. No third-party funding, commercial contract, institutional appointment, or absence of competing interests is asserted without supporting evidence. No human-subject data or physical experiments are included. Scientific review should focus on the original reproducible claims and on the adverse findings.

**Publication and peer-review status:** The author explicitly approved this original-text preprint for public distribution under CC BY 4.0 on 15 November 2026. Original research reports and numerical JSON sources were cross-checked during preparation; the benchmark was not re-executed for this version. Publication is **not peer review**, and any DOI must be independently verified after Zenodo archival. No quantum advantage, externally validated generalization, or new intellectual-property claim is asserted.
