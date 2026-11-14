import test from 'node:test';
import assert from 'node:assert/strict';
import {evaluateSparsity,stableRandom} from '../validation/astra_dino_sparsity_stress.mjs';
const matrix={nChar:40,rows:Array.from({length:8},(_,i)=>({taxon:'Fossil_'+i,states:Array.from({length:40},(_,j)=>j%11===0?null:String((i+j%3)%2))}))};
test('fixed seed reproducibility and bounded scores',()=>{
 const a=evaluateSparsity(matrix,{fractions:[0.4],repeats:2,minOverlap:2,k:2});
 const b=evaluateSparsity(matrix,{fractions:[0.4],repeats:2,minOverlap:2,k:2});
 assert.deepEqual(a,b);
 assert.ok(a.results[0].coverage>=0&&a.results[0].coverage<=1);
 assert.equal(a.results[0].eligibleHidden,a.results[0].scored+a.results[0].abstained);
});
test('randomness uses taxon, character, replicate',()=>{
 assert.equal(stableRandom(3,4,1),stableRandom(3,4,1));
 assert.notEqual(stableRandom(3,4,1),stableRandom(4,4,1));
});
test('unknown character never in truth denominator',()=>{
 const data=evaluateSparsity(matrix,{fractions:[0.5],repeats:1,minOverlap:1,k:2});
 assert.ok(data.results[0].eligibleHidden<=8*36);
});
test('abstention is explicit when no reliable overlaps',()=>{
 const data=evaluateSparsity(matrix,{fractions:[0.2],repeats:1,minOverlap:39,k:2});
 assert.equal(data.results[0].scored,0);
 assert.ok(data.results[0].abstained>0);
 assert.equal(data.results[0].accuracy,null);
});
test('bad source parameter and nonexistent source fail closed',()=>{
 assert.throws(()=>evaluateSparsity(matrix,{fractions:[1]}),/Fractions/);
 assert.throws(()=>evaluateSparsity(matrix,{repeats:0}),/Invalid test/);
 assert.throws(()=>evaluateSparsity({rows:[],nChar:40}),/Invalid parsed/);
});
