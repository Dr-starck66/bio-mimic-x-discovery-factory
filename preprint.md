# Oracle-Free Retrieval and Selective Scientific-Claim Verification: A Reproducible SciFact Development-Set Audit

**Research programme:** ASTRA Ω Research  
**Author:** Dr Starck    
**Version:** v0.5 — 15 November 2026 (author-authorized open preprint)  
**Document status:** **PUBLIC PREPRINT — NOT PEER REVIEWED — NO DOI ASSIGNED AS OF 15 NOVEMBER 2026**  
**Scope:** Scientific-claim verification benchmarking, not clinical decision-making.

**Publication scope and rights:** This report describes existing non-clinical, exploratory results; it excludes ASTRA Ω inventions not already disclosed. **Licence for original manuscript text only:** Creative Commons Attribution 4.0 International (CC BY 4.0), authorized for public release by the author on 15 November 2026. Third-party data, code and model weights retain their own terms and are not included in the release package. No affiliation, ORCID or given name is fabricated. **Public release authorized by Dr Starck on 15 November 2026; no DOI has been issued as of this date.**

## Abstract

Scientific-claim verification systems may achieve plausible aggregate accuracy while exposing substantial error on individual decisions. We document an exploratory, oracle-free retrieval and verification pipeline applied to the 300-claim SciFact development split and a corpus of 5,183 scientific abstracts. A BM25 retriever using the claim alone returned at least one annotated evidence document in the first rank for 133/188 evidence-bearing claims (70.74%) and within the first ten ranks for 176/188 (93.62%). A separately pinned, pretrained scientific claim-verification model received the first retrieved abstract, restricted to three lexically selected sentences, in the upstream-prescribed claim-first input order. Without abstention, its three-class accuracy was 195/300 (65.00%). A predetermined filter requiring BM25 >= 8, maximum class probability >= 0.90, a top-two probability margin >= 0.20, and a decisive (SUPPORT or CONTRADICT) label accepted 122/300 claims (40.67% coverage). Of those accepted, 94/122 were correct (77.05% selective accuracy), leaving 28 incorrect decisions; contradiction recall declined from 33/64 (51.56%) to 17/64 (26.56%), while contradiction false positives decreased from 26 to 9. We retain a failed earlier input-order experiment as an invalid-protocol negative control rather than representing it as model performance. We document the methodology and reference a per-decision ledger but do not claim external generalization, clinical safety, or superiority over existing approaches. An independent blind test, additional baselines, and evaluation of uncertainty calibration remain necessary.

**Keywords:** scientific claim verification; SciFact; BM25; selective classification; abstention; negative results; reproducibility; evidence provenance.

## 1. Introduction

Automated systems can retrieve relevant scientific literature and classify claims as supported, contradicted or lacking evidence. However, deployment-oriented claims of trustworthiness require careful distinction among retrieval success, end-to-end verdict accuracy, confidence-based selection, and external validity. SciFact [1] provides annotated scientific claims and supporting or refuting abstracts. Prior work on selective classification [2,3] shows that prediction quality must be considered jointly with the proportion of examples on which the model is willing to decide. Reproducibility recommendations in machine-learning-based science further emphasize locked protocols, preserved artifacts, and transparent unfavorable outcomes [4,5].

The present report is an **audit of one configured pipeline on one known development split**, not a newly trained state-of-the-art model and not an independent generalization test. Its value is the accountable record of methods, decisions, abstentions and failure modes. The research programme is ASTRA Ω; the underlying research code and evidence are retained in a public BIO-MIMIC X repository, currently in a draft pull request.

## 2. Materials and methods

### 2.1 Source data and licensing

We used the official SciFact dataset [1]: 300 development claims and a corpus of 5,183 abstracts, as recorded in the source audit. Among these claims, 188 had at least one annotated evidence document and 112 had no such positive annotation in the development gold data. The upstream SciFact project explicitly separates licences: claims and evidence annotations (`claims_*.jsonl`) are **CC BY 4.0**; abstracts (`corpus.jsonl`) are **ODC-By 1.0**; and original SciFact repository code is **Apache 2.0** [7]. An earlier ASTRA research log inaccurately reported the whole dataset as CC BY-NC 2.0; that summary has been corrected here using the primary licence file. This manuscript does not repackage the SciFact corpus or redistribute third-party model weights; the independent model checkpoint's reuse and redistribution permissions still require review.

### 2.2 Oracle-free document retrieval

The claim text alone was used as the retrieval query. A BM25 retriever (k1 = 1.2; b = 0.75) indexed titles and abstracts with lower-case tokenization. No gold evidence IDs, cited-document IDs, evidence snippets or ground-truth labels entered the retrieval ranking. Gold evidence IDs were consulted only after ranking to compute hits among the top k documents. The denominator for hit@k was the **188 evidence-bearing claims**, not all 300 claims. This metric measures evidence retrieval and is not verdict precision.

### 2.3 Verification model and input protocol

The top-ranked abstract was reduced to three sentences selected by lexical overlap with the claim. Inference was performed with the pinned checkpoint [VeriSci-Claim retrieval-adapted model](https://huggingface.co/rishhh/verisci-claim-verifier-retrieval-adapted-seed123) at revision `5bed61128b128f6f960aa80d1aa8ac3d1bdd9b0f`. The documented input order was **claim first, evidence second**, matching the upstream inference and training code. The source audit reports CPU inference using PyTorch and Transformers. This is a third-party model, not a model trained by ASTRA Ω.

Three raw classes were recorded: SUPPORT, CONTRADICT and NEI (not enough information). The development split may have been encountered during model development or evaluation; consequently, the experiment is **not an external blind evaluation**.

### 2.4 Predefined selective-decision filter

Before the corrected evaluation, the source audit reports that the following filter had been frozen: first retrieved document BM25 score >= 8.0; maximum softmax class probability >= 0.90; margin between the two largest probabilities >= 0.20; and predicted class SUPPORT or CONTRADICT. Other outputs were recorded as ABSTAIN. The softmax score is **not an empirically calibrated likelihood of scientific truth**.

We distinguish: (a) raw three-class accuracy over 300 claims; (b) coverage, the fraction receiving a decisive selected verdict; (c) selective accuracy, the fraction correct among accepted decisions; and (d) contradiction-detection counts against the gold CONTRADICT class. For contradiction detection, an abstention is counted as a missed positive when the gold label is CONTRADICT. These denominators must not be interchanged.

### 2.5 Audit and quality controls

The source records 300 per-decision outputs with unique IDs, raw and selective labels, rank-1 document ID, retrieval status, quantized score fields and abstention reasons. In the current preparation session, a separate recomputation from the GitHub ledger confirmed: 300 unique IDs, 195 raw correct predictions, 122 accepted decisions, 94 accepted correct decisions, 178 abstentions, raw contradiction TP/FP = 33/26, and selective contradiction TP/FP = 17/9. This recomputation does not re-run model inference or provide independent external replication.

The prior experimental attempt reversed the model's expected text order and supplied an entire abstract. The retained negative-control record reports 37.67% raw accuracy and zero detected contradictions, but is marked **FAIL_PROTOCOL**. It cannot be interpreted as a valid comparison against the corrected configuration because both input order and evidence selection changed.

## 3. Results

### 3.1 Evidence retrieval

| Metric | Count | Rate |
|---|---:|---:|
| Evidence hit@1 | 133/188 | 70.74% |
| Evidence hit@3 | 158/188 | 84.04% |
| Evidence hit@5 | 166/188 | 88.30% |
| Evidence hit@10 | 176/188 | 93.62% |

The retrieval report gives MRR@10 = 0.78447. A top-ten evidence hit does not imply that the rank-one document used for verification contains the gold evidence. The choice to verify only rank one is a potential source of avoidable errors.

### 3.2 Raw classification and abstention

| Outcome | Unfiltered pipeline | Predefined abstention filter |
|---|---:|---:|
| Three-class accuracy, with abstentions not credited as correct | 195/300 (65.00%) | 94/300 (31.33%) |
| Decisive labels issued | 185/300 (61.67%) | 122/300 (40.67%) |
| Accuracy among decisive labels | 120/185 (64.86%) | 94/122 (77.05%) |
| Abstentions | 0 in raw three-class output | 178/300 (59.33%) |
| CONTRADICT true positives | 33 | 17 |
| CONTRADICT false positives | 26 | 9 |
| CONTRADICT false negatives | 31 | 47 |
| CONTRADICT true negatives | 210 | 227 |

**Interpretation caveat:** The 31.33% figure is *not* an ordinary classification accuracy metric for abstaining systems; it is the fraction of all 300 claims receiving a correct accepted decisive verdict. Comparisons should primarily report coverage alongside selective accuracy and class-specific error. The filter rejects many difficult cases, but 28 of the 122 accepted verdicts remain incorrect.

The gold class distribution in the development split was SUPPORT 124, CONTRADICT 64 and NEI 112. Raw three-class correct predictions totaled 195. The rejection gate changed the error profile: contradiction false positives fell by 17, whereas missed contradictions increased by 16. Because filter decisions are not randomized and this is a single known development split, the findings do not demonstrate clinical benefit, population-level safety, calibrated confidence or prospective improvement.

## 4. Discussion and limitations

This experiment supports a narrow methodological point: **a higher accuracy among selected decisions does not establish reliable verification when coverage is limited, substantial accepted errors persist, and false-negative costs may increase**. A robust assessment requires risk-coverage curves across frozen thresholds, calibration analyses, multiple retrieval baselines, error taxonomy, uncertainty intervals, and tests on an independent dataset not exposed during system development.

The experiment inherits annotation incompleteness and domain restrictions of SciFact. Document retrieval uses lexical heuristics and only the first retrieved document for inference. The checkpoint's rights and upstream training/evaluation exposure are not independently resolved. The source audit reports 50 passing Python regression tests, but these are primarily software checks; the current preparation session performed a ledger arithmetic recomputation, not a new full inference run. No clinical patients, diagnostic workflow, treatment recommendations or prospective clinical outcomes were examined.

This exploratory report must not be interpreted as a published peer-reviewed clinical study, a registered clinical trial, a medical-device validation, or an evidence of commercial readiness. Independent validation is the key unresolved scientific task.

## 5. Reproducibility and data availability

**Code and reports:** `https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/pull/48` (draft pull request; reference branch `astra/medical-claim-audit-20261112`).

**Per-decision ledger:** [claim-level decision ledger](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/blob/astra/medical-claim-audit-20261112/tools/astra_medical_claim_audit/reports/scifact_bm25_verisci_300_case_ledger_v04_20261112.json) in the reference branch. The original audit reports SHA-256 `a22d380d587dda658f6b6adea23a1b90` + `bdf9d31849eec26cafe13ca431a52027` (concatenate) for this compressed ledger. The hash should be rechecked independently on the exact exported file before external deposit.

**Retrieval report:** [BM25 retrieval results](https://github.com/Dr-starck66/bio-mimic-x-discovery-factory/blob/astra/medical-claim-audit-20261112/tools/astra_medical_claim_audit/reports/bm25_scifact_open_dev300_v04_20261112.json).

**Recorded dataset archive:** its complete SHA-256 is given in the accompanying release metadata and the upstream retrieval report; verify against the downloaded official SciFact archive.

**Model revision:** `5bed61128b128f6f960aa80d1aa8ac3d1bdd9b0f` (pinning is not a guarantee of future access or permission to redistribute).

The manuscript's supplementary audit script recalculates summary statistics from the ledger without accessing patient data, SciFact text, a neural-model API or paid infrastructure. Full reproducibility additionally requires authorized access to the upstream dataset, model checkpoint and compatible runtime. A GitHub draft branch is not an archival DOI; **no DOI has been issued for this report**.

## 6. Declarations

**Ethics:** This analysis used an existing research benchmark without patient-level data. No human-subject intervention was conducted for this report.  
**Funding:** No dedicated external funding has been documented for this experiment.  
**Competing interests:** The author directs the ASTRA Ω Research programme, which may seek future commercial use of related scientific-audit tools. This potential interest is disclosed for transparency. No independent verification of additional financial interests or relationships has been performed.  
**Author attribution and responsibility:** Dr Starck is the confirmed publication signature for this document. No institutional affiliation, ORCID or unprovided given name is claimed. The author remains responsible for approving the original work and its publication.  
**Use of AI:** AI assistance was used in preparation of the manuscript and elements of the research workflow; the author must review and assume responsibility for the final content, data rights, methods and conclusions.  
**Status:** Public exploratory technical preprint; peer review, external blind validation, journal acceptance and DOI **not obtained as of 15 November 2026**. Original manuscript text is licensed CC BY 4.0 by author authorization; references to SciFact or VeriSci do not imply ownership of third-party assets.

## 7. Rights and publication note

The author-owned original text of this open preprint is **released under CC BY 4.0** following explicit author approval on 15 November 2026. This publication does **not** license any third-party text, scientific abstract, dataset, model checkpoint, or external code. The source repository states CC BY 4.0 for SciFact claims/annotations, ODC-By 1.0 for abstracts and Apache 2.0 for its code [7]. The separately developed pretrained VeriSci checkpoint does not provide sufficiently clear redistribution terms in the inspected model documentation, so **no weights are redistributed**. Readers must independently check the applicable permissions before reproducing that component. This report and its archived aggregate outputs do not convey medical, clinical or commercial validation.

## References

1. Wadden D, Lin S, Lo K, Wang LL, van Zuylen M, Cohan A, Hajishirzi H. (2020). *Fact or Fiction: Verifying Scientific Claims*. EMNLP, 7534–7550. doi:10.18653/v1/2020.emnlp-main.609. https://aclanthology.org/2020.emnlp-main.609/
2. Geifman Y, El-Yaniv R. (2017). *Selective Classification for Deep Neural Networks*. NeurIPS 30. https://proceedings.neurips.cc/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html
3. Geifman Y, El-Yaniv R. (2019). *SelectiveNet: A Deep Neural Network with an Integrated Reject Option*. ICML, PMLR 97:2151–2159. https://proceedings.mlr.press/v97/geifman19a.html
4. *REFORMS: Consensus-based Recommendations for Machine-learning-based Science*. (2024). Science Advances 10(18), eadk3452. doi:10.1126/sciadv.adk3452. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11092361/)
5. *Reproducibility standards for machine learning in the life sciences*. (2021). Nature Methods. https://www.nature.com/articles/s41592-021-01256-7
6. Wadden D et al. (2022). *SciFact-Open: Towards Open-domain Scientific Claim Verification*. Findings of EMNLP. https://aclanthology.org/2022.findings-emnlp.347/

7. Allen Institute for AI. *SciFact dataset and code licences* (repository source licence file). https://github.com/allenai/scifact/blob/master/LICENSE.md (accessed 15 November 2026).