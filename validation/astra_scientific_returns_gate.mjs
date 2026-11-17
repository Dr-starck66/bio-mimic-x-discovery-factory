#!/usr/bin/env node
import fs from 'node:fs';
import assert from 'node:assert/strict';
const path=process.argv[2] || 'reports/factory/astra_scientific_returns_20261116.json';
function audit(x){
 const e=[]; const a=x.axolotl,d=x.dino;
 if(x.schema!=='astra.science.replies.v1')e.push('schema');
 if(a.old_model!=='AMEX60DD030069'||a.working_gene!=='HAND1'||a.old_hand2_model!=='AMEX60DD045298')e.push('paralog');
 if(a.kmer_size!==31||a.old_distinct_kmers!==27332||a.hand1_shared_kmers!==26858||a.hand2_shared_kmers!==8)e.push('previous_kmer_evidence');
 if(a.reciprocal_assembly_liftover!=='UNVERIFIED'||a.genome_wide_uniqueness!=='UNVERIFIED')e.push('unearned_exact_mapping');
 if(a.old_expression_is_hand2!==false||a.human_hand2_comparison_allowed!==false||a.regeneration_claim!==false)e.push('invalid_expression_inference');
 if(d.existing_pr!==52||d.oslo_birds_paired!==50||d.oslo_populations!==11||d.hmga2_block_snps!==394||d.alx1_block_snps!==238)e.push('oslo_provenance');
 if(d.global_p_original_model_beak_size!==0.0847||d.initial_model_significant!==false)e.push('incorrect_significance');
 if(d.right_flank_causal!==false||d.independent_cohort!=='UNVERIFIED'||d.new_genotype_phenotype_crosswalk!=='UNVERIFIED')e.push('unproven_causality');
 if(x.privacy.scientist_citation_permission!=='PENDING'||x.privacy.private_mail_reproduced!==false)e.push('consent');
 if(x.phyto.dataset_received!==false||x.phyto.selenium_phenotype_validated!==false)e.push('missing_biological_data');
 return e;
}
const x=JSON.parse(fs.readFileSync(path,'utf8'));
assert.deepEqual(audit(x),[]);
const clone=()=>JSON.parse(JSON.stringify(x));
const cases=[
 ['paralog',y=>{y.axolotl.working_gene='HAND2'}],
 ['unearned_exact_mapping',y=>{y.axolotl.reciprocal_assembly_liftover='PASS'}],
 ['invalid_expression_inference',y=>{y.axolotl.human_hand2_comparison_allowed=true}],
 ['incorrect_significance',y=>{y.dino.initial_model_significant=true}],
 ['unproven_causality',y=>{y.dino.independent_cohort='PASS'}],
 ['consent',y=>{y.privacy.scientist_citation_permission='GRANTED'}],
 ['missing_biological_data',y=>{y.phyto.selenium_phenotype_validated=true}]
];
for(const [reason,mutate] of cases){const y=clone();mutate(y);assert(audit(y).includes(reason),reason)}
console.log('PASS 8/8: 1 evidence baseline + 7 adversarial negative controls; NOT genomic validation');
