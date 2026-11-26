# SENSOR GUARD v0.2 — 2026-11-26

Run from this directory: `python -m unittest -v test_sensor_guard`, then `python benchmark_guard.py --seeds 10 > results.json`. Python stdlib only. Reuses v0.1 plant and gains.

Initial run: 220 simulations, 11 scenarios, 10 seeds, two modes. Final run: 420 simulations, 14 scenarios, 10 seeds, three modes. Five unit tests and ten aggregate benchmark checks passed. Results JSON SHA256: 8a195fef300659f30af1e5eee5a57be9ab03fa02cb00c945147a95c572850330.

Affected-actuator RMSE during fault, dimensionless:

| Scenario | Raw | Guard | Anchored |
|---|---:|---:|---:|
| nominal | .2608 | .2608 | .2608 |
| freeze | 1.7544 | .2652 | .2619 |
| drift | .5430 | .2659 | .2622 |
| velocity bias | .7111 | .2608 | .2608 |
| dual position | .8608 | .5278 | .3531 |
| coherent fault | .7487 | .7486 | .3033 |
| all coherent, anchor included | .7487 | .7486 | .7486 |
| anchor fault | .2608 | .2608 | .3531 |
| anchor missing | .2608 | .2608 | .3464 |

Coherent fault detected on 92.3% of fault samples with independent absolute position anchor vs 0% without; 0% when anchor is coherently corrupted too. Anchor loss detected on 98% of fault samples, false anchor on 100%. Zero nominal false alerts after startup, zero nonfinite/out-of-limit commands across both baseline and guards (all modes clamp).

Assumptions: three position and three velocity channels, trusted initial position, anchor 10 Hz with deterministic small noise, control 100 Hz, 150 ms anchor freshness threshold, five valid steps before reopening. Fault applied to one actuator, not all eight. Physical independence assumed, not tested. No timestamp/replay validation, sensor dynamics, safety-certified stop, or long-term recalibration. Predictor tolerance grows with age; after velocity quorum loss, guard remains latched until trusted reinitialization (not yet implemented as a recovery API). Zero command may not be safe in real hardware. Anchor-only faults degrade availability; undetectable common-mode errors remain a negative result. Do not equate aggregate checks with proof of all-fault safety.
