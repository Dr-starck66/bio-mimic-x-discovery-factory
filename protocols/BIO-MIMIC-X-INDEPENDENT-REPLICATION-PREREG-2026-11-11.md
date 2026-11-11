# BIO-MIMIC X — preregistration for independent rejuvenation replication
Date: 2026-11-11. Status: protocol locked in Git before outcome inspection. No independent replication has been executed.

## Discovery data (NOT validation)
GSE165179 DNAm / GSE165177 RNA: 13 post-recovery treated/control contrasts across donors O1 (2), O2 (4), O3 (7). S&B 2018 fully measured (391/391 CpGs): O1 -11.9713y, O2 -14.9877y, O3 +3.5811y; only 7/13 treated comparisons decline. Horvath 2013 uses 334/353 observed, 19 imputed: O1 -6.0039y, O2 -12.6222y, O3 -10.4340y. Original concordance criterion FAIL. RNA lineages resemble fibroblast centroid more than iPSC but treated cells are more distant from fibroblast centroid than their controls. Do not call therapy validated.

## Eligibility before opening outcomes
An independent dataset must be from a different biological cohort/laboratory, with baseline and treated/control groups, chronological age, intervention, recovery duration and passages documented, and accessible sample-level DNAm plus RNA or a documented same-donor linkage. Record biological donor, culture batch, sample IDs and aliquot identity explicitly. Exclude reuses of GSE165179/GSE165177 and derivative datasets, unpaired aggregates, and datasets lacking control conditions. If no qualifying dataset is found, record NO_ELIGIBLE_DATASET; do not substitute discovery cohort.

## Fixed endpoints
Primary: donor-level paired treatment-minus-control Skin & Blood 2018 clock change (391 CpGs with measured beta required, no imputation) after recovery. Report sample and donor distributions and 95% uncertainty interval; require negative donor-level mean and at least 80% donors with negative paired effect, with uncertainty interval excluding zero, for a positive replication decision. A sample-level p-value alone does not count as donor replication.
Secondary: independently computable Horvath 2013 clock with CpG coverage and imputation explicitly reported, fibroblast-vs-iPSC RNA centroid correlations and distance, fibroblast marker panel, pluripotency and cell-cycle markers. Concordance and loss of identity reported separately. No cherry-picking of recovery days.
Safety/function: independent experimental evidence required for cell function, genomic stability, transformation/tumorigenicity and long-term effects. Public omics alone cannot satisfy these criteria.

## Analysis safeguards
Freeze sample inclusion before computing clock outcomes; preserve failed and missing pairs. Separate donors, culture passages, batches, and technical replicates; no pseudoreplication. Controls: untreated controls, iPSC identity contrast, known non-reprogrammed/failed controls when available, negative-control signatures and batch covariates. Evaluate each donor and leave-one-donor-out sensitivity. Report contradictory results and any QC probe exclusions with original and sensitivity results. Independent verification of matrix extraction, CpG mapping, SHA256, software versions and arithmetic.

## Decision states
PASS_REPLICATION only if independent cohort eligible and preregistered primary criteria met, with all limitations. FAIL_REPLICATION if eligible dataset analyzed and criterion fails. UNVERIFIED if no eligible dataset or incomplete inputs. Even PASS_REPLICATION is NOT clinical validation or a safe therapy.

## Execution log
2026-11-11: protocol authored and committed before any new cohort outcome calculation. No independent cohort has yet been identified, downloaded, or analyzed in this action. No cost, no new automation.
