# ASTRA PREDICTIVE MAINTENANCE Ω v0.22 — IMS exploratory evaluation

## Data and provenance
NASA IMS Bearing Data, Lee/Qiu/Yu/Lin/Rexnord, University of Cincinnati IMS, distributed by NASA: https://data.nasa.gov/dataset/ims-bearings . Physical run-to-failure experiments. Third-party extracted time features: https://github.com/Ianmendonca/Bearing-fault-diagnosis-NASA-dataset . Original vibration samples not retrieved or independently recomputed. The code used RMS, excess kurtosis + 3, crest factor and timestamps from the source tables. Source blob IDs are in the result JSON; 37,856 bearing-snapshot rows, 37,840 retained, 12 bearing/run combinations. Removed one duplicated timestamp in run 1 (keep first, all four bearings), two trailing low-RMS snapshots in run 2 and one in run 3 (all four). Run 1 bearing 3/4, run 2 bearing 1 and run 3 bearing 3 are documented failed bearings. Shared shafts, not twelve independent trials; eight other bearings have no recorded terminal failure, not certified healthy.

## Protocol
Each channel's first 100 snapshots fit robust median/MAD normalization, next 100 calibrate thresholds, 99th percentile of three-snapshot persistence score; no test outcomes used to fit thresholds. Monitoring begins at index 202. Median smoothing uses five past/current samples. EWMA alpha 0.2. Same nominal calibration quantile, not a matching observed false-alarm rate. No random row split; each bearing uses its own commissioning prefix, not fully untouched machine-level holdout. Settings exploratory; no external timestamp. Run 3 added after runs 1/2; code differs only in run configuration (failure mapping and expected row count). Repeated execution on identical data produced identical results. Endpoint is last retained sample, not independently labeled defect onset. Estimated operating clock compresses gaps >15 minutes to 10 minutes, following a published repository's approach; not elapsed wall time. Alert episodes persist for 3 snapshots; sustained alarm onset is retrospectively identified from last active episode ending within final 6 retained snapshots. This is not a prospective RUL forecast. Gaps do not reset persistence in this version. All comparisons use the same endpoint. Shutdown trimming is retrospective.

## Results across all three runs
Four documented failures. Candidate peer_ratio: median-centered log RMS minus peer median, robust normalized, one-sided alert. A common multiplicative change across every RMS channel cancels exactly, so the candidate cannot detect common-mode degradation alone. The composite candidate adds kurtosis and crest-factor score; rejected for excessive alert burden.

| Detector | >=4h sustained lead | Proxy episodes | Proxy alarm occupancy | median sustained lead (h) |
|---|---:|---:|---:|---:|
| RMS | 4/4 | 104 | 20.94% | 92.85 |
| EWMA | 4/4 | 76 | 23.02% | 131.62 |
| Kurtosis | 1/4 | 72 | 1.23% | not comparable (1 missing, 2 late) |
| Multifeature | 4/4 | 178 | 60.00% | 75.43 |
| Peer ratio | 4/4 | 53 | 20.52% | 121.81 |
| ASTRA composite | 4/4 | 301 | 52.35% | 94.84 |

Proxy exposure: 4078.97 estimated bearing-hours; 24,609 monitored snapshots across nonfailed bearings. 53 vs 104 episodes, 49.04% reduction; 53 vs 76, 30.26% reduction. Occupancy is similar to RMS, so no claim of halved alarm time. Run 3 peer ratio 246.02h vs RMS 109.02h and EWMA 193.52h, but 35 proxy episodes vs 52 and 28, occupancy 24.27% vs 19.33% and 20.52%. Not consistently superior; one case on run 3, four failures total. This is an empirical comparator, not a newly proven physical invariant. No promotion or valuation claim. No motors or turbines evaluated; NASA C-MAPSS is simulated, not measured physical engine failures.

## Reproduce
Node 22 or newer, from this directory: node replay.mjs . The runner downloads the pinned source Git blobs via GitHub public API and verifies SHA-1 Git blob IDs before invoking the same benchmark function. Network access required, no packages. The runner was authored but not executed from the local network-restricted container. The underlying benchmark was executed twice on retrieved data through the authenticated connector. Results: bearing_results.json, bearing_test3.json, aggregate.json. No GitHub Actions required.
