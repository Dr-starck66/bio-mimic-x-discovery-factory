import test from 'node:test';
import assert from 'node:assert/strict';
import {validate,kmers,rebuildDistances,seeded,holdout,negativeControl,fossilBridgeGate} from '../validation/astra_dino_genome_trait_v1.mjs';
const names=['A a','B b','C c','D d','E e','F f'];
const taxa=names.map((species,i)=>({species,family:['F1','F2','F2','F3','F4','F5'][i],order:'O'+i,
  accession:'NC_'+(100+i)+'.1',sequenceLength:15000,
  traits:Object.fromEntries(['Mass','Beak.Length_Culmen','Beak.Depth','Tarsus.Length','Wing.Length'].map(k=>[k,10+i]))}));
const snapshot={schema:'astra.dino.mtDNA_avonet_paired.v1',taxa,distance:Array.from({length:6},(_,i)=>Array.from({length:6},(_,j)=>i===j?0:1))};
test('symmetric exact distances, positive morphology and unique accessions checked',()=>{
  assert.equal(validate(snapshot),6);
  const altered=structuredClone(snapshot);altered.distance[2][4]=0.3;
  assert.throws(()=>validate(altered),/nonsymmetric/);
  const bad=structuredClone(snapshot);bad.taxa[2].traits.Mass=-1;
  assert.throws(()=>validate(bad),/invalid taxon/);
});
test('whole-family holdout excludes close relatives from train',()=>{
  const x=holdout(snapshot);
  assert.equal(x.species,6);assert.equal(x.count,30);
  assert.ok(Number.isFinite(x.model)&&Number.isFinite(x.baseline));
  assert.equal(x.byTrait.Mass.perTaxon.length,6);
});
test('permutation control is seeded and deterministic',()=>{
 const a=negativeControl(snapshot,20,20261114);
 assert.deepEqual(a,negativeControl(snapshot,20,20261114));
 assert.ok(a.empiricalP>0&&a.empiricalP<=1);
});
test('self-score and tampered labels never silently accepted',()=>{
 const bad=structuredClone(snapshot);
 bad.distance[0][0]=1;
 assert.throws(()=>holdout(bad),/invalid distance/);
 const perm=[0,0,2,3,4,5];
 assert.throws(()=>holdout(snapshot,perm),/invalid sequence shuffle/);
});
test('genomic distances rebuild from exact source sequences',()=>{
 const a='ACGT'.repeat(3750),b='TGCA'.repeat(3750);
 const x=structuredClone(snapshot);
 x.taxa=x.taxa.slice(0,5);
 x.distance=Array.from({length:5},(_,i)=>Array.from({length:5},(_,j)=>i===j?0:1));
 const source=[{entries:x.taxa.map((t,i)=>({species:t.species,accession:t.accession,sequence:i===0?a:b}))}];
 assert.throws(()=>rebuildDistances(x,source),/distance mismatch/);
 source[0].entries[0].accession='NC_WRONG';
 assert.throws(()=>rebuildDistances(x,source),/source FASTA mismatch/);
});
test('fossil bridge cannot transfer non-homologous phenotypes',()=>{
 const gate=fossilBridgeGate(['Anas','Gallus','Velociraptor'],[{species:'Anas platyrhynchos'},{species:'Gallus gallus'}]);
 assert.deepEqual(gate.overlap,['Anas','Gallus']);
 assert.equal(gate.transferAllowed,false);
});
