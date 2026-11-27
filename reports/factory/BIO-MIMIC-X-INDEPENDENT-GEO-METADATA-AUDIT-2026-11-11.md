# BIO-MIMIC X — GEO independent murine metadata audit (2026-11-11)

## Source and verified transfers
- NCBI GEO GSE246954 series matrix: HTTP 200, 3,504 compressed bytes, SHA256 `6ad90841d523fc6d73eb569c33ee90eecf23e903ab4fd694428d7f538b5a62d4`, gzip PASS, 24 GSM.
- NCBI GEO GSE247179 series matrix: HTTP 200, 3,700 compressed bytes, SHA256 `7044c187e7dc50bdfa4f8e8f0c7d503a4ccdd42e5d2f1585cf0816f9b70b31c6`, gzip PASS, 36 GSM.
- GSE246954 raw genecounts xls.gz: HTTP 200, 1,876,936 compressed bytes, 9,321,984 uncompressed bytes, SHA256 `6c955a52bf1bdbd608079e337afd7f4d7ffefbd46fad05baf295320e7cc37642`, gzip PASS. Payload is binary XLS, not CSV.
- GSE179848 processed human RNA CSV.gz: HTTP 200, 60,622,846 compressed bytes, 167,337,990 uncompressed bytes, SHA256 `b5731fa1253a2bd32f0b64c3bd58770e833a3da59dc90c4f8c8d858944b30109`, gzip PASS.
- GSE247179 sesame DNAm RDS.gz: HEAD HTTP 200, Content-Length 157,071,853 bytes; full payload NOT DOWNLOADED.
- GSE179847 processed human DNAm CSV.gz: HEAD HTTP 200, Content-Length 2,157,881,029 bytes; full payload NOT DOWNLOADED.

## External murine matching: 24 candidate metadata correspondences
Matching key: mouse age (4/20 months) + treatment (control/2c/7c) + replicate index (1–4). Every RNA sample has exactly one DNAm metadata match. This is a match **by labels**, not proof of same donor, animal, aliquot or passage. Replicate labels may be assigned independently between assays. Biological pairs **UNVERIFIED**.

| Age | Treatment | RNA GSM rep 1–4 | DNAm GSM rep 1–4 |
|---|---|---|---|
| 20mo | control | 7881367,7881370,7881373,7881376 | 7884785,7884797,7884800,7884803 |
| 20mo | 7c | 7881368,7881371,7881374,7881377 | 7884787,7884799,7884802,7884810 |
| 20mo | 2c | 7881369,7881372,7881375,7881378 | 7884786,7884798,7884801,7884809 |
| 4mo | control | 7881379,7881382,7881385,7881388 | 7884788,7884791,7884794,7884804 |
| 4mo | 7c | 7881380,7881383,7881386,7881389 | 7884790,7884793,7884796,7884806 |
| 4mo | 2c | 7881381,7881384,7881387,7881390 | 7884789,7884792,7884795,7884805 |

All GSM numbers in table have GSM prefix. Six additional DNAm samples are iPSC reprogramming controls without matching RNA in the selected series.

## Evidence boundaries
- PASS: NCBI remote binary downloads and gzip integrity of RNA; 24/24 metadata key matches.
- PARTIAL: independent experimental conditions available.
- UNVERIFIED: same-animal pairing, same-aliquot pairing, passage equivalence, independent DNAm+RNA biological replication, rejuvenation effect.
- No methylation clock run, no new biological finding; no protected cohort access.
- This cohort is mouse chemical reprogramming, **not** a direct replication of Gill human transient reprogramming.

## Predefined negative controls
- Permute replicate indices between modalities: same condition matching persists but biological pairing must remain unverified.
- Compare 2c and 7c against same-age vehicle, stratify 4mo/20mo, do not pool mouse ages.
- Keep iPSC-only DNAm samples as unmatched, not fabricate RNA.
- Require assay metadata linking donor/animal or aliquot before paired cross-modal inference.
