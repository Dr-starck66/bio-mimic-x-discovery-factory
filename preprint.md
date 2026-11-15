# Limits of retrospective robot-task duration calibration and causal dispatch inference in open collective robotic construction logs

**Author:** Dr Starck  
**Research program:** ASTRA Ω Research / ANT Robotics Ω  
**Document:** Open scientific preprint, v0.1 — 15 November 2026  
**Status:** AUTHOR-AUTHORIZED OPEN PREPRINT — NOT PEER REVIEWED — DOI PENDING AT RELEASE  
**Rights:** Author-owned original text is released under Creative Commons Attribution 4.0 International (CC BY 4.0); Skoury and Leder's DaRUS dataset is not redistributed.  
**Scope:** Secondary retrospective observational analysis. **No robot control, physical performance gain or causal effect identified.**

## Abstract

Digital-twin event logs from collective robotic construction provide real observed execution records, but do not necessarily support causal claims about alternative task-dispatch policies. We report a secondary analysis of the public Stuttgart ROB|ARCH 2024 dataset (Skoury and Leder; [DaRUS DOI 10.18419/DARUS-5612](https://doi.org/10.18419/DARUS-5612)). An officially distributed 31,216,902-byte archive was retrieved with checksum verification; 12 logs contained 22,571 events and 9,314 robot `Move`/`Grip` commands, 9,162 with valid positive durations up to 600 s. We rejected a proposed direct transfer of calibration coefficients from heterogeneous synthetic ASTRA ANT V3 robot/task types to physically recorded RADr commands because units and entity schemas did not match. For a method-only secondary test, models were refit on 5,925 physical commands from runs 1–6 and scored on 3,237 commands from runs 7–12, a retrospective block already examined in prior research. Test mean absolute errors (seconds) were 3.449721 for a global median baseline, 3.481807 for a robot-and-command-type median, 3.491630 for refit fixed residual calibration (worse), and 3.365057 for a recent-observation adaptive estimator. A schema audit found no structured per-decision admissible-action sets, assignment propensities, or observed outcomes for unchosen actions. These data allow descriptive duration modeling but do **not** identify an improvement in causal dispatch quality, industrial throughput, safety, or energy use. We retain negative results and define a minimal future logging contract.

**Keywords:** collective robotic construction, digital twins, runtime prediction, causal identification, observational logs, reproducibility, negative results.

## 1. Research question and scope

A common analytic error is to evaluate an algorithm on a log of **actions already taken**, then label the resulting fit as evidence that its unexecuted alternative scheduling policy would have improved the process. The distinction is acute for multi-robot construction, where task dependencies, concurrent operations, material availability and operator choices influence both assignment and outcomes.

We ask two narrowly scoped questions: (1) can an independently developed synthetic forecast calibration be transferred numerically to real RADr robots; and (2) what predictive and causal claims are defensible from the published Stuttgart digital-twin event log?

## 2. Data provenance and preprocessing

The study used the public dataset *Digital Twin task logs for Collective Robotic Construction (CRC) — ROB|ARCH 2024*, deposited by Skoury and Leder at [DaRUS 5612](https://doi.org/10.18419/DARUS-5612), reported under CC BY 4.0. The official `CRC_DATA.zip` archive has **31,216,902 bytes**, MD5 `e18d73a23ee1c19e00e9daee797c73ab`, and independently calculated SHA-256 `d52c5e77d9ab7cb5bb425985699f6d6cb460f4a113466f8bf28d156150a8892f`. The original audit retrieved it through **40 HTTP partial-content responses**, parsed 12 `Data/Run-*.json` event files, and did not persist original sensor data in GitHub.

Of **22,571** event rows, 9,314 were `Move` (8,080) or `Grip` (1,234) robot commands; **9,162** had complete positive physical durations ≤600 seconds, leaving **152** outside the analysis criterion. The logs covered `RADr_0` to `RADr_7` along with separate sensor actors. This is secondary use of a public research dataset, not a laboratory intervention.

## 3. Design and models

### 3.1 Refusal of invalid synthetic-to-physical transfer

The original ANT V3 synthetic study involved robot families including Spot, ANYmal, MiR, Matrice, UR20 and Unitree and task categories such as survey, inspection, transport and assembly, with durations expressed in **simulation ticks**. Stuttgart records RADr robots and `Move`/`Grip` commands in **physical seconds**. No checked entity mapping or calibrated scale converted one into the other. Consequently, copying the numerical calibration weights would violate domain compatibility. It was explicitly rejected by the transfer audit.

### 3.2 Physical-only retrospective refit

To separate the algorithmic *method* from incompatible source coefficients, a fixed residual-calibration routine was refit using only physical runs **1–6** (**5,925** eligible commands). Its models were compared with a global-duration median, command-type median, robot/type median, and a `recent20` adaptive estimator on runs **7–12** (**3,237** valid commands). The test block had already been studied in an earlier November experiment and must not be represented as an untouched confirmatory holdout.

The metric is mean absolute prediction error (MAE) **in seconds**, on commands executed under the original system. No intervention, randomized dispatch or unexecuted action was observed.

### 3.3 Causal-identifiability audit

We searched the event schema for task-level candidate action sets available **before assignment**, eligibility and constraint rules, a known or estimated assignment probability (propensity), structured pre-choice state, and outcome information or an appropriate causal design for actions not chosen. This is a necessary-data audit rather than a proof of sufficiency: even presence of these fields would not alone establish exchangeability, positivity or an interference model for interacting robots.

## 4. Results

| Physical duration estimator | MAE on 3,237 commands (s) |
|---|---:|
| Global median | **3.449721** |
| Command-type median | 3.460328 |
| Robot/type median | 3.481807 |
| Fixed residual calibration, refit on physical runs | **3.491630** |
| Adaptive prior-observation `recent20` | **3.365057** |

Fixed residual calibration was worse than the robot/type median on **runs 7, 9, 10 and 12** and better on only 8 and 11. The refit fixed estimator was also worse than the global median in aggregate (approximately **1.21% higher MAE**, not a gain). The lower `recent20` MAE is an **exploratory retrospective prediction finding**; it is not evidence of successful intervention.

Among all **9,314** command rows, the executed actor was recorded for 9,314, while structured decision-level admissible action sets, action-assignment propensities and structured pre-choice states were observed in **zero** rows under the tested schema checks. No outcomes are available for actions not executed. Some event fields contain motor and sensor information; absence of the *specific* structured decision fields is not absence of all contextual information.

**Scientific verdict: FAIL to identify the causal effect of alternative dispatch.** No positive claim about production throughput, real-world robot safety, energy savings or operating cost is supported by this audit.

## 5. Negative controls and threats to validity

The preserved test suite contains **32** checks for module behavior, source integrity and negative cases. Authentication gates reject wrong archive checksums; transfer logic rejects mismatched domains; the causal evidence gate refuses to infer unobserved alternative-action outcomes.

Threats include retrospective reuse of runs 7–12, lack of independent untouched validation, short and highly variable task durations, possible interdependence between robots, incomplete known assignment policy, and reuse of methods motivated by earlier observations. These data represent a specific published robotic construction demonstration; external generalization is not established.

## 6. A logging contract for a confirmatory next study

To evaluate a real dispatch policy with causal credibility, an authorized future experiment must capture a versioned, timestamped predecision state; **all admissible robot–task actions** and eligibility constraints; policy choice and, if randomized, probability; prior events and worker availability; actual task start/end, resource consumption and quality checks; and planned controls for multi-robot interference. A prospective supervised shadow comparison followed by a suitable randomized policy trial, subject to operator consent and safety review, would then be possible. This recommendation **does not** constitute a current field test.

## 7. Provenance, acknowledgments and reproducibility

The public original dataset is **Skoury & Leder, DaRUS V1 (2026), DOI [10.18419/DARUS-5612](https://doi.org/10.18419/DARUS-5612)**. Credit, versioning and licence terms must be preserved. The independent research code and aggregate report are in the private [ANT Robotics Stuttgart PR #272](https://github.com/Dr-starck66/indexation/pull/272), at snapshot `f41fe77bf0f9709fc58ed64c6a4869146a4477ac`, under:

`ant-robotics/neon-standalone/benchmark/real-dispatch/stuttgart-calibration/`

The saved records include `PREREGISTRATION_20261115.md` (locked before the new analysis), `README_FR.md`, `STUTTGART_CALIBRATION_AUDIT_20261115.json`, the Node.js runner and 32-test module. The prior executable analysis ran in a connected Node.js VM against authenticated official bytes; **draft preparation is not a repeat of this physical-data computation**. Neither original log ZIP nor raw sensitive sensor streams are copied into this manuscript.

We acknowledge the dataset authors and original robotic construction research team. **ASTRA Ω Research** also develops commercial concepts; a final disclosure statement must represent relevant ownership and interests without misrepresenting institutional affiliation or declaring an absence of conflicts as fact.

## 8. Release controls

The text has been approved for public release by Dr Starck under CC BY 4.0. Numerical values and metadata were cross-checked against the original locked aggregate research JSON; the physical dataset analysis was not newly rerun for this preprint. A release should contain a readable PDF and only authorized aggregate information, with independent Zenodo DOI verification. **Author-approved public release applies to this manuscript only.** It is not journal-reviewed and does not authorize redistributing original sensor data or proprietary implementations. The Zenodo DOI, if issued, must be independently verified. No claim of causal dispatch benefit or physical deployment is asserted.
