import test from 'node:test';
import assert from 'node:assert/strict';
import {tokenizeNexus,parseNexus,individualTaxa,majority,evaluateMorph,
  bootstrapDelta,permutedLabelNull,parseFasta,genomicComparison} from '../validation/astra_dino_ancestry.mjs';

const fixture='#NEXUS\nBEGIN DATA;\nDIMENSIONS NTAX=6 NCHAR=6;\nFORMAT MISSING=? GAP=-;\nMATRIX\nallzero 000000\nA 010101\nB 010100\nC 000101\nD 001100\nE 011101\n;\nEND;';
test('NEXUS source shape and distinct taxa are strict',()=>{
  const d=parseNexus(fixture);
  assert.equal(d.nTax,6);assert.equal(d.nChar,6);assert.equal(d.rows[2].taxon,'B');
  assert.throws(()=>parseNexus(fixture,true),/Unexpected source dimensions/);
  assert.throws(()=>parseNexus(fixture.replace('010101','01010')),/Invalid character count/);
  assert.throws(()=>parseNexus(fixture.replace('E 011101','A 011101')),/unique taxon count/);
});
test('polymorphism and missing scores never become false labels',()=>{
  assert.deepEqual(tokenizeNexus('01?(01){12}-2'),['0','1',null,null,null,null,'2']);
  assert.throws(()=>tokenizeNexus('1(01'),/Unclosed/);
});
test('artificial row and aggregate taxa excluded',()=>{
  const rows=[{taxon:'allzero'},{taxon:'Abelisauridae'},{taxon:'Archaeopteryx'},{taxon:'Prosauropoda'}];
  assert.deepEqual(individualTaxa(rows).map(x=>x.taxon),['Archaeopteryx']);
});
test('held-out taxon and baseline share eligible cells',()=>{
  const r=evaluateMorph(parseNexus(fixture),2,2);
  assert.equal(r.taxa,5);assert.ok(r.tests>0);
  assert.equal(r.perTaxon.reduce((a,x)=>a+x.n,0),r.tests);
  const perm=permutedLabelNull(r.cells,5,2,4);
  assert.ok(perm.mean>=0&&perm.mean<=1);
  const ci=bootstrapDelta(r.perTaxon,100,5);
  assert.ok(ci.lower95<=ci.upper95);
});
test('held out target observations do not affect eligible row counts',()=>{
  const a=evaluateMorph(parseNexus(fixture),2,2);
  const b=evaluateMorph(parseNexus(fixture.replace('A 010101','A 110101')),2,2);
  assert.equal(a.perTaxon.find(x=>x.taxon==='A').n,
    b.perTaxon.find(x=>x.taxon==='A').n);
});
test('mitochondrial FASTA accession and nucleotide length fail closed',()=>{
  const fake='>NC_001323.1 Gallus gallus\n'+'ACGT'.repeat(4000);
  assert.equal(parseFasta(fake,'NC_001323.1').length,16000);
  assert.throws(()=>parseFasta(fake,'NC_010195.2'),/Unmatched/);
  assert.throws(()=>parseFasta('>NC_001323.1\nACGT','NC_001323.1'),/Invalid mitochondrial/);
  assert.throws(()=>parseFasta(fake.replace(/A/,'Z'),'NC_001323.1'),/Invalid mitochondrial/);
});
test('genomic k-mer similarity extreme controls',()=>{
  const d=genomicComparison({bird1:'ACGTACGTACGT',bird2:'ACGTACGTACGT',bird3:'TTTTTTTTTTTT'},3);
  assert.equal(d.pairs[0].jaccard,1);
  assert.equal(d.pairs[1].jaccard,0);
});
test('missing evidence and empty classifications fail closed',()=>{
  assert.equal(majority([null,null]),null);assert.equal(majority(['1','0']),'0');
  assert.throws(()=>evaluateMorph(parseNexus(fixture),20,2),/No evaluable/);
});
