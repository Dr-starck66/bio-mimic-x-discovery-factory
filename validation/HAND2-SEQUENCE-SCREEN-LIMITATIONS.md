# HAND2 sequence-only independent screen — limitations

This module accepts a query FASTA and **complete local assembly FASTA** files, searches exact seeds on both strands and records candidate coordinates and input SHA-256. It does not use gene-neighborhood annotations or NCBI Datasets gene endpoints.

Run: `python -m unittest discover -s validation -p 'test_hand2_sequence_uniqueness.py' -v`

Run against real assemblies ONLY after downloading and verifying the complete historical and modern reference FASTA (with accession/version and checksum receipts): `python validation/hand2_sequence_uniqueness.py --query hand2_query.fa --assembly old_complete.fa modern_complete.fa --out reports/factory/HAND2-SEQUENCE-SCREEN.json`.

**Fail-closed:** this exact-seed screen is NOT an exhaustive sensitive alignment; insertions/deletions, repeats and missed seeds may hide alternative loci. A single candidate is not evidence of whole-genome uniqueness, official HAND2 annotation, function, or therapy. No real complete assemblies were supplied in this commit. Do not promote results to biological PASS. Preserve HAND1 as a negative control in a subsequent independent full-genome alignment.
