# ASTRA EXTERNAL CHALLENGE Ω v0.18

An external custodian retains test labels and signing key. Pilot for grouped tabular regression only. A single task never authorizes promotion. The holder must supply lawfully shareable nonsensitive data; do not share restricted records. Register the custodian key and preregistration digest via an independently authenticated channel before submissions.

Run in an isolated reviewed environment with Python 3 and pinned requirements:
```sh
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python demo_external_challenge.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -v test_external_challenge
```

Partner task.json: train, validation, test each contain X numeric rows and groups string per row; train and validation include y, test must omit y. Groups cannot overlap. Private labels.json contains ordered test targets.
```sh
python external_challenge.py prepare --task task.json --labels labels.json --private PRIVATE --public PUBLIC
python external_challenge.py submit --public PUBLIC --pin PIN --expected DIGEST
python external_challenge.py judge --public PUBLIC --private PRIVATE --pin PIN --expected DIGEST
python external_challenge.py verify --public PUBLIC --pin PIN --expected DIGEST
```
Keep PRIVATE on the custodian machine and transfer PUBLIC alone. Independently register returned pin and prereg_sha256 as PIN and DIGEST. The custodian replays predictions and computes scores. Public verification authenticates the signed receipt, not the undisclosed labels or scores. Separate machines and restricted execution are required for an actual independent trial; the local prototype is not a sandbox.

Demo: statsmodels Grunfeld, 220 firm-years, split 7/2/2 firms, 140/40/40 rows. All select linear ridge alpha=0.1. Parent and reference RMSE 36.6029522021, candidate refit RMSE 40.5036124610. REJECT. Twelve local tests passed. No external partner has yet performed the experiment. No new scientific law, statistical generalization or autonomous promotion is claimed. The public dataset is known, so this is not a genuinely secret test. No private keys are published.
