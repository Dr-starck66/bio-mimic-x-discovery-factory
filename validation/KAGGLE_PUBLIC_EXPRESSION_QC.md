# Kaggle — BIO-MIMIC X public gene-expression QC (research only)

Scope: quality control of legally public, non-identifiable sample-by-gene CSV files. **No private clinical records**, genomic patient identifiers, confidential partner files or source uploads by default.
Format: CSV header sample_id,GENE_1,GENE_2,...; at least two samples and two features; numeric nonnegative finite expression data.

Example run in an authorized Kaggle session (file already attached):
python validation/kaggle_public_expression_qc.py --matrix-csv /kaggle/input/PUBLIC-DATA/expression.csv --source-url https://www.kaggle.com/datasets/OWNER/PUBLIC-DATA --public-approved --output /kaggle/working/bio-mimic-x-expression-qc.json

The flag is a declaration and not independent license verification. Outputs sample count, gene count, zero library QC and SHA-256.
Local tests: python -m unittest discover -s validation -p test_kaggle_public_expression_qc.py -v
Scientific biological replication, orthology assignment, clinical/aging efficacy and Kaggle execution are UNVERIFIED until separately proven.
Existing axolotl global-alignment and other BIO-MIMIC X validators remain canonical and unchanged.