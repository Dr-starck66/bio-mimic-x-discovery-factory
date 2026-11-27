# ASTRA DINO Ω — Hendrickx fossil benchmark v0.6 (2026-11-14)

This isolated research branch archives **three authentic January 2022 NEXUS files** from Christophe Hendrickx et al. (DOI [10.5061/dryad.zcrjdfnck](https://doi.org/10.5061/dryad.zcrjdfnck)), recovered through the official [Zenodo mirror](https://zenodo.org/records/5259937) after direct Dryad HTTP 403 errors.

The archived files are losslessly gzip-compressed. Verification was performed on the original, uncompressed bytes using the Zenodo MD5 identifiers.

| Original file | MD5 verified | SHA-256 (original bytes) |
|---|---|---|
| Ancestral_state_reconstruction_analysis_Jan_2022.nex | `3abc358b7e4402d42278e49f1c420edf` | `70edf9e9ceb5959f0070911e9cf78e44ff44027043f91c89dc088353ef821c82` |
| Mapping_Integument_characters_Jan_2022.nex | `6f2701d205b900a9498483348447afe5` | `ae84112b09d2983827bc569e66026b2c1614ace6e8ba230c315f8601cfd721e9` |
| Mapping_Integument_characters_Jan_2022_no_DIP.nex | `381ee714805a096a6e8e0e8383868c8f` | `c2431187796edbee98920d6a7a6ea3b64fc610bb7b3e230718a23273e8748bf0` |

The independent Excel original was also fetched and MD5-verified against Zenodo (`b4500bc034f125bc86f19a96936ce09c`); it remains available from the original Zenodo record and is not committed here.

## Blind whole-taxon holdout

Analysis uses **Ancestral_state_reconstruction_analysis_Jan_2022.nex**: 61 taxa, 71 characters, six published topologies; 1121 unambiguous character states (0=537, 1=433, 2=147, 3=4). This is distinct from the 66-taxon **Mapping** NEXUS and the broader 67-taxon count stated in the article.

Taxa with at least ten known states were fixed as holdout targets before scoring: **50 complete-taxon exclusions / 1063 hidden states**. Target-character values are excluded from all training inputs. Unknown `?`, inapplicable `-`, polymorphic and uncertain states are distinct.

| Comparator | Correct / 1063 | Abstentions |
|---|---:|---:|
| Per-character train-only majority | 711 | 1 |
| Classical Fitch/Sankoff parsimony, published Tree1 | 713 | 178 |
| Agreement of all six published trees | 694 | 205 |
| Tree1 with permuted training-only labels (negative control) | 605 | 194 |

Paired gain Fitch minus majority: **+0.19 percentage points**, with 1000-replicate taxon-cluster bootstrap 95% interval **[-2.24, +2.35] percentage points**, including zero.

**Verdict: acquisition PASS; blind execution PASS; claimed superior ancestral inference FAIL.** No ancestral genotype has been demonstrated, no causal fossil-phenotype/nucleotide map established, and no autonomous dinosaur revival is implied.

The standard-library Python reproducer, local unit tests and full scientific report are delivered separately as the ChatGPT artifact `ASTRA_DINO_HENDRICKX_BLIND_V06_20261114.zip` from the same 2026-11-14 execution. Production branches and websites remain untouched.
