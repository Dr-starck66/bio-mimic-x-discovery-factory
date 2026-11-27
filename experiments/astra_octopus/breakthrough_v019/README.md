# ASTRA BREAKTHROUGH v0.19
Exploratory scale-law discovery, not a new mathematical law.
Run from this directory with the existing parent modules on the path:
```sh
python -m pip install -r requirements.txt
PYTHONPATH=.. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark.py
PYTHONPATH=.. OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python benchmark_mixed.py
```
Six public real datasets, 84 simulated systems. Both result JSON files reproduced byte-identically locally. The initial shared-power model beats validation-selected references on Gapminder (35.34%) and copper (39.70%), loses on Linnerud and stackloss. Gapminder matches standard log-input ridge exactly. The mixed-power model recovers the simulated off-grid exponents, with 93.26% lower mean RMSE than the selected reference, but loses to the reference on all 12 linear and all 12 regime-shift cases. No universal superiority or promotion. Full test suite and detailed results are in the separate local reproducibility archive. Public data are not an independent blind test. Reference portfolios are finite, not a claim against all state-of-the-art approaches.
