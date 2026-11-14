import test from 'node:test';
import assert from 'node:assert/strict';
import {audit,samePosition,validate,phenotypeGenotypeCrosswalk} from '../validation/astra_dino_nuclear_audit.mjs';
function valid(){const proteins=[];for(const [gene,species,accession] of [
  ['ALX1','Geospiza fortis','XP_005421635.1'],['HMGA2','Geospiza fortis','XP_030911403.1'],
  ['ALX1','Taeniopygia guttata','XP_002196043.1'],['HMGA2','Taeniopygia guttata','XP_004176139.1'],
  ['ALX1','Gallus gallus','XP_040516271.1'],['HMGA2','Gallus gallus','NP_990332.1']]){
    const n=gene==='ALX1'?328:109;proteins.push({gene,species,accession,length:n,sequence:'A'.repeat(n),header:accession+' '+gene+' ['+species+']'});
  }return {schema:'astra.dino.nuclear_proteins.v1',proteins};}
test('6 pinned protein refs, pairwise deterministic comparisons',()=>{
 const result=audit(valid());assert.equal(result.proteins,6);assert.equal(result.comparisons.length,6);
 assert.ok(result.comparisons.every(x=>x.identityPercent===100));
});
test('correct mismatch position for equal-length sequences',()=>{
 assert.deepEqual(samePosition('ACAC','ACCC').mismatches,[3]);
 assert.throws(()=>samePosition('ABC','A'),/not positionally comparable/);
});
test('refusal wrong accessions, missing proteins and duplicate',()=>{
 const data=valid();data.proteins[0].accession='BAD';assert.throws(()=>validate(data),/FAIL_CLOSED/);
 const copy=valid();copy.proteins.pop();assert.throws(()=>validate(copy),/FAIL_CLOSED/);
 const dupe=valid();dupe.proteins[1]=dupe.proteins[0];assert.throws(()=>validate(dupe),/FAIL_CLOSED/);
});
test('fail closed malformed amino acids and wrong organism',()=>{
 let x=valid();x.proteins[0].sequence='Z'+'A'.repeat(327);assert.throws(()=>validate(x),/FAIL_CLOSED/);
 x=valid();x.proteins[0].header='>XP_005421635.1 [wrong]';assert.throws(()=>validate(x),/FAIL_CLOSED/);
});
test('no automatic join without mapping or with mismatched identifiers',()=>{
 const phen=[{AccNo:'123456',Beak_length:11,Beak_height:6,Beak_width:5}];
 assert.throws(()=>phenotypeGenotypeCrosswalk(phen,['foo'],null),/mapping required/);
 assert.deepEqual(phenotypeGenotypeCrosswalk(phen,['foo'],{}).matched,0);
 assert.throws(()=>phenotypeGenotypeCrosswalk(phen,['foo'],{foo:'987654'}),/absent/);
 const ok=phenotypeGenotypeCrosswalk(phen,['foo','bar'],{foo:'123456'});
 assert.equal(ok.matched,1);assert.equal(ok.unmatched,1);
});
test('reject two genetically distinct samples assigned to one bird',()=>{
 const phen=[{AccNo:'123456',Beak_length:11,Beak_height:6,Beak_width:5}];
 assert.throws(()=>phenotypeGenotypeCrosswalk(phen,['foo','bar'],{foo:'123456',bar:'123456'}),/two genotypes/);
 assert.throws(()=>phenotypeGenotypeCrosswalk(phen,['foo','foo'],{foo:'123456'}),/duplicate VCF sample/);
});
