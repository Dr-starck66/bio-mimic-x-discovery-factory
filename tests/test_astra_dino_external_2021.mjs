import test from 'node:test';
import assert from 'node:assert/strict';
import {gitBlobSha1,assertExternalSource,subsetMetrics,evaluateExternalMatrix,EXTERNAL_SOURCE} from '../validation/astra_dino_external_2021.mjs';

function mockMatrix({n=80,removeBird=false,mutate=false}={}){
  const names=['Dromaeosauridae','Anas','Gallus',...Array.from({length:n-3},(_,i)=>'Fossil_'+(i+1))];
  if(removeBird)names[2]='NotGallus';
  const rows=names.map((name,i)=>name+' '+Array.from({length:280},(_,j)=>(i+j)%7===0?'?':String((i+Math.floor(j/20))%3)).join('')).join('\n');
  return '#NEXUS\nBEGIN DATA;\nDIMENSIONS NTAX='+n+' NCHAR=280;\nFORMAT SYMBOLS="0123456" MISSING=? GAP=-;\nMATRIX\n'+rows+'\n;\nEND;'+(mutate?' CHANGED':'')+'\n';
}
test('pinned source version and git blob SHA1 match standard',()=>{
  assert.equal(gitBlobSha1('test\n'),'9daeafb9864cf43055ae93beb0afd6c7d144bfa4');
  assert.equal(EXTERNAL_SOURCE.commit.length,40);
  assert.equal(EXTERNAL_SOURCE.blobSha1.length,40);
});
test('canonical matrix dimensions and extant birds are required',()=>{
  assert.equal(assertExternalSource(mockMatrix(),{checkHash:false}).rows.length,80);
  assert.throws(()=>assertExternalSource(mockMatrix({n:79}),{checkHash:false}),/Unexpected 2021/);
  assert.throws(()=>assertExternalSource(mockMatrix({removeBird:true}),{checkHash:false}),/Extant bird/);
});
test('any unpinned source fails closed',()=>{
  assert.throws(()=>assertExternalSource(mockMatrix()),/blob mismatch/);
  assert.throws(()=>assertExternalSource(mockMatrix({mutate:true})),/blob mismatch/);
});
test('modern and fossil denominators share the same evaluated cells',()=>{
  const p=[{taxon:'Anas',n:4,modelCorrect:3,baselineCorrect:2},
    {taxon:'Gallus',n:6,modelCorrect:5,baselineCorrect:4},
    {taxon:'Fossil',n:10,modelCorrect:8,baselineCorrect:6}];
  const live=subsetMetrics(p,r=>r.taxon==='Anas'||r.taxon==='Gallus');
  assert.equal(live.tests,10);assert.equal(live.modelCorrect,8);
  assert.equal(live.deltaPoints,20);
  assert.equal(subsetMetrics(p,r=>r.taxon==='None').status,'UNVERIFIED');
});
test('isolated-taxon evaluation and controls run without network on synthetic dataset',()=>{
  const r=evaluateExternalMatrix(mockMatrix(),{checkHash:false,nullReplicates:4,bootstrapIterations:30});
  assert.equal(r.overall.taxa,79);assert.equal(r.modern.taxa,2);assert.equal(r.fossil.taxa,77);
  assert.equal(r.overall.tests,r.modern.tests+r.fossil.tests);
  assert.ok(r.overall.tests>0);
  assert.equal(r.status,'EXPLORATORY_NOT_GENOME_TO_TRAIT');
});
test('biological evidence is not claimed by code',()=>{
  const r=evaluateExternalMatrix(mockMatrix(),{checkHash:false,nullReplicates:2,bootstrapIterations:10});
  assert.ok(r.limitations.some(x=>x.includes('truly unknown')));
  assert.equal(r.parameters.targetFeatureExcluded,true);
});
