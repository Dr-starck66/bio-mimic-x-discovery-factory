# ASTRA CROSS-SENSE Ω v0.3 — 2026-11-26

Run from this directory: python -m unittest -v test_cross_sense; python benchmark_cross.py --seeds 10 > results.json

390 final simulations (13 scenarios × 10 paired seeds × 3 controllers), 117 pilot simulations, seven unit tests OK and six benchmark predicates true. Negative control success means the blind spot is reproduced, NOT that the fault is prevented.

Eight-actuator dimensionless ring, actuator 0 protected and fault-injected only. Other actuators ideal feedback. v0.2 baseline uses three correlated copies of encoder position/velocity plus the same vision source. IMU and net-force channels observe the same simulated acceleration with distinct noise/fault injection, not physically validated sensors. Unit mass. 100 Hz controller, 10 Hz vision, 150 ms freshness, five good ticks to resume. Trusted initialization, growing integration uncertainty, no recalibration. Zero command is not certified safe braking. Exact-tick frame acceptance is a simulation convention.

| Scenario | v0.2 RMSE | Cross RMSE | Cross accepted-error fraction | Cross fallback fraction |
|---|---:|---:|---:|---:|
| nominal | .2624 | .2622 | 0 | 0 |
| encoder bias | .3630 | .2623 | 0 | 0 |
| vision bias | .3630 | .2627 | 0 | 0 |
| encoder + vision coherent | 1.1977 | .3373 | 0 | .8237 |
| encoder + IMU coherent | .3479 | .3438 | .0047 | .8370 |
| missing vision | .3558 | .2629 | 0 | 0 |
| replay vision | .3630 | .2629 | 0 | 0 |
| missing IMU + force | .2624 | .3627 | 0 | 1 |
| all coherent | 1.1977 | 1.1976 | .8333 | 0 |
| high noise ×5 | .2624 | .3537 | 0 | .6523 |

Metrics over 300 ticks from t=4 to 7 seconds. Accepted error means non-fallback command differs by >2 from ideal clipped PD computed using ground truth only for scoring. Encoder+vision coherent: v0.2 accepted-error fraction .8323, CROSS 0; first alert mean 193 ms. No nominal alerts in main evaluation window, but five nominal alert ticks over 11,800 total post-startup ticks across ten seeds (0.0424%). High noise causes 65.23% fallback. All-modal coherent corruption not detected. Thresholds hand-selected, no external calibration or generalization test.

Five local Python file blob hashes match remote files. Local results SHA-256: 28b57ab7ed06b95c7086dc3ebbd3d2756806a89dbf4d7ff2a5ec9f512202d321. Next: separate calibration/holdout protocol with varying dynamics, sensor noise and mechanically safe fallback. No hardware validation, universal safety, or novelty claim.
