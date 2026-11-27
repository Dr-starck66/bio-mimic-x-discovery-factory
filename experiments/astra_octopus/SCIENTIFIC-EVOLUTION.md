# SCIENTIFIC EVOLUTION v0.14 — first-generation verdict

Decision: **REJECT** challenger; retain METASCIENCE v0.13. No merge or deployment.

Local validation: 16 policies (15 mutations), four development tasks and four reserved tasks. Development improvement 8.0961% in mean per-task RMSE ratio; development is not confirmatory. Frozen policy rolling=true, conservative=false, refit=false, expanded=false. Lock SHA-256 f378326ec8acbb3d8618d2fa21a5e6326c3c975f1788b3bf1c8f38e40651b13c.

| Reserved task | N | Test N | Parent RMSE | Candidate RMSE | Reference RMSE |
|---|---:|---:|---:|---:|---:|
| Nile | 98 | 20 | 127.076919 | 134.530002 | 126.197874 |
| El Niño | 730 | 146 | 0.513314 | 0.513314 | 0.526733 |
| US unemployment | 201 | 41 | 0.230865 | 0.237999 | 0.236704 |
| Credit expenditure | 72 | 15 | 448.006963 | 456.274710 | 458.083723 |

Regression in Nile, unemployment and credit expenditure. Zero confirmed gain tasks. 13 unit tests passed locally; full evaluation replay byte-identical. Parent equivalence verified on all four development tasks. Three new Python blob hashes match tested local files. Parent file unchanged.

Reproduce in an isolated directory with all v0.13 dependencies and the recorded Python environment:
```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python benchmark_evolution.py dev
python -m unittest -v test_scientific_evolution
python benchmark_evolution.py gate > gate_results.json
```

The original four reserved task datasets have now been exposed; do not reuse them for independent promotion of another challenger. The local archive retains the exact original lock, predictions, results and replay. No third-party blind evaluation or tamper-resistant execution environment; the lock checks use Python assertions (do not use -O). Block-bootstrap intervals are approximate. The search space changes policy configuration only; it cannot establish arbitrary self-modification or general scientific superiority. The reference portfolio is finite and chosen on validation. No real-world causal, clinical, autonomous-deployment or physical claims.

Next: independent evaluator and fresh hidden task bank before any new generation.
