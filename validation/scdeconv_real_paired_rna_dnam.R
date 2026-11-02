#!/usr/bin/env Rscript
# BIO-MIMIC X scDeconv PUBLIC real paired RNA and DNAm negative/method-control.
# Primary references:
# Yu Liu, Brief Bioinform 2022, doi:10.1093/bib/bbac150
# https://github.com/yuabrahamliu/scDeconv/inst/extdata/
# 48 human placenta GEO GSM IDs matched exactly across two public assay matrices.
# Clinical covariate = GESTATIONAL WEEK, NEVER adult epigenetic age.
# No protected data and no human rejuvenation claims.
args <- commandArgs(trailingOnly=TRUE)
if(length(args)!=2) stop("usage: script.R <scDeconv-repo-path> <output-dir>")
path <- args[1]; out <- args[2]
dir.create(out, recursive=TRUE, showWarnings=FALSE)
rna_path <- file.path(path,"inst","extdata","pairedRNAdat.rds")
meth_path <- file.path(path,"inst","extdata","pairedDNAmdat.rds")
meta_path <- file.path(path,"inst","extdata","DNAmpd.rds")
for(f in c(rna_path,meth_path,meta_path)) if(!file.exists(f))stop(paste("public RDS unavailable",f))
rna <- readRDS(rna_path)
meth <- readRDS(meth_path)
meta <- readRDS(meta_path)
if(!is.matrix(rna) && !is.data.frame(rna))stop("RNA should be a tabular matrix")
if(!is.matrix(meth) && !is.data.frame(meth))stop("methylation should be a tabular matrix")
if(ncol(rna)!=48L || ncol(meth)!=48L)stop("the independently paired public assay matrices must have 48 samples each")
if(nrow(rna)<21000L || nrow(meth)<18000L)stop("public molecular feature coverage unexpectedly low")
if(anyDuplicated(colnames(rna)) || anyDuplicated(colnames(meth)))stop("GSM samples not unique")
if(!identical(colnames(rna),colnames(meth)))stop("FAIL CLOSED: RNA and DNAm are NOT exactly aligned by GSM")
if(!all(grepl("^GSM[0-9]+$",colnames(rna))))stop("RNA and DNAm sample IDs not GEO GSM")
ids<-colnames(rna)
meta_pairs<-meta[meta$type=="paired",,drop=FALSE]
if(nrow(meta_pairs)!=48L || !setequal(ids,meta_pairs$sampleid))stop("metadata does not map one-to-one to paired GSM samples")
meta_pairs<-meta_pairs[match(ids,meta_pairs$sampleid),,drop=FALSE]
gest<-as.numeric(as.character(meta_pairs$Gestwk))
group<-factor(meta_pairs$Samplegroup)
if(any(!is.finite(gest)) || length(unique(gest))<4L)stop("clinical gestational-week covariate malformed")
if(length(levels(group))!=2L)stop("predeclared preeclampsia negative control unavailable")

# Genes selected from cell-type marker knowledge BEFORE examining DNAm beta.
fibro<-intersect(c("COL1A1","DCN","LUM","COL1A2","FN1"),rownames(rna))
troph<-intersect(c("KRT7","EPCAM","GATA3","KRT8","KRT18"),rownames(rna))
if(length(fibro)<2 || length(troph)<2)stop("insufficient observed independent RNA lineage marker genes")
normalized_score<-function(g){
  x<-as.numeric(rna[g,ids])
  if(any(!is.finite(x)))stop(paste("nonfinite marker gene",g))
  sigma<-sd(x)
  if(!is.finite(sigma)||sigma<1e-5)stop(paste("constant RNA marker",g))
  as.numeric((x-mean(x))/sigma)
}
fibro_score<-rowMeans(sapply(fibro,normalized_score))
troph_score<-rowMeans(sapply(troph,normalized_score))
if(!is.numeric(fibro_score)||!is.numeric(troph_score))stop("invalid measured RNA lineage scores")

# Fixed methylation loci from published tutorial, NOT selected by outcomes.
candidate_cpg<-c("cg00000292","cg00002426","cg00003994",
                 "cg00007981","cg00008493","cg00008713")
cpg<-intersect(candidate_cpg,rownames(meth))
if(length(cpg)<4)stop("independent DNA methylation CpGs unavailable")
beta<-as.numeric(meth[cpg[1],ids])
if(any(!is.finite(beta)) || any(beta<0|beta>1))stop("methylation beta impossible/out-of-range")
dt<-data.frame(gsm=ids,Gestwk=gest,Samplegroup=group,
               transcriptome_fibroblast_score=fibro_score,
               transcriptome_trophoblast_score=troph_score,
               DNAm_beta_cg00000292=beta)
# These are orthogonal *observational associations*, not an ageing clock.
m_base<-lm(DNAm_beta_cg00000292 ~ Gestwk + Samplegroup,data=dt)
m_adjusted<-lm(DNAm_beta_cg00000292 ~ Gestwk + Samplegroup +
               transcriptome_fibroblast_score + transcriptome_trophoblast_score,data=dt)
if(length(coef(m_adjusted))!=5L || any(!is.finite(coef(m_adjusted))))stop("adjusted model unidentifiable")
if(is.null(coef(m_base)[["Gestwk"]]))stop("gestational-week regression coefficient missing")
model<-data.frame(
  benchmark="real human placenta RNA/DNAm paired GSM",
  dataset="scDeconv public paired multi-omics (source GEO GSE98224)",
  n_samples=nrow(dt),
  n_RNA_genes=nrow(rna),
  n_DNAm_CpGs=nrow(meth),
  exact_GSM_match=TRUE,
  n_fibro_marker_genes=length(fibro),
  n_troph_marker_genes=length(troph),
  n_clinical_control=sum(group=="Control"),
  n_clinical_preeclampsia=sum(group=="Preeclampsia"),
  measured_DNAm_probe=cpg[1],
  gestational_week_coefficient_before=unname(coef(m_base)["Gestwk"]),
  gestational_week_coefficient_after_RNA_adjustment=unname(coef(m_adjusted)["Gestwk"]),
  residual_sd_before=sigma(m_base),
  residual_sd_after=sigma(m_adjusted),
  status="PASS_REAL_PUBLIC_PAIRED_RNA_DNAM_ASSOCIATION_ONLY",
  chronological_human_aging_effect="UNVERIFIED_NOT_AN_AGING_STUDY",
  epigenetic_rejuvenation_mechanism="UNVERIFIED",
  same_biological_aliquot_verified=FALSE
)
write.csv(model,file.path(out,"gse98224-scdeconv-real-assay-adjustment-summary.csv"),row.names=FALSE,quote=TRUE)
write.csv(dt,file.path(out,"gse98224-scdeconv-48-real-paired-sample-scores.csv"),row.names=FALSE,quote=TRUE)
cat("BIO_MIMIC_PUBLIC_RNA_DNAM_PAIRS",
    "n=",nrow(dt),"rna_genes=",nrow(rna),"methyl_CpGs=",nrow(meth),
    "fibro_genes=",paste(fibro,collapse=","),"troph_genes=",paste(troph,collapse=","),
    "gest_beta_before=",unname(coef(m_base)["Gestwk"]),
    "gest_beta_after=",unname(coef(m_adjusted)["Gestwk"]),
    "RNA_and_DNAm_same_GSM=",identical(colnames(rna),colnames(meth)),
    "aging_mechanism=UNVERIFIED",
    "\n")
