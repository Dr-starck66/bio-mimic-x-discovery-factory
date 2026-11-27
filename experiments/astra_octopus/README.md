# ASTRA OCTOPUS Ω v0.1

Research prototype: dimensionless ring of eight coupled actuators, 100 Hz, 15 seconds, 30 paired deterministic seeds, five scenarios and three control modes (450 runs). Standard Python only. No robot, deployment, learned policy or energy measurement.

Run: `python benchmark.py --seeds 30 > results.json`

| Scenario | Central RMSE | Local RMSE | Guarded local RMSE |
|---|---:|---:|---:|
| Ideal | 0.278023 | 0.278023 | 0.278023 |
| 100 ms delay | 0.277368 | 0.278023 | 0.278023 |
| 30% packet loss | 0.278013 | 0.278023 | 0.278023 |
| 2 s outage | 0.316298 | 0.278023 | 0.278023 |
| Asymmetric local sensor bias | 0.278023 | 0.341422 | 0.277950 |

Six assertions passed. Outage: local RMSE 12.1% lower (30/30 paired wins); mean peak error 58.0% lower; integral squared effort 60.2% lower (not electrical energy). No gain demonstrated for delay or random losses. Bias test deliberately only corrupts local position; guard uses simulated independent velocity (not proof of resilience to common-mode failure). Central holds last command during outage; local tracks a preloaded reference, so new mission delivery and safety under outdated commands are untested. Communication counts omit mission distribution and health telemetry. No claims of universal superiority or novelty. Next: compare stronger central and hybrid fail-safe baselines with equal sensor faults, adaptive references and physical robot simulator.

Scientific context: https://doi.org/10.3389/frobt.2022.862391 ; https://pubmed.ncbi.nlm.nih.gov/40924275/ ; https://www.nature.com/articles/s42256-026-01230-y ; https://zenodo.org/records/18969202 .

Code SHA-256: b5fac7115c4b61467b81afc967468e81bef2ca5a1cf98762e3a72dfce2c74816
Local results SHA-256: 11ef09ee047b204bb34e982165678ae182558b49075e61771a825dfba41d4529
