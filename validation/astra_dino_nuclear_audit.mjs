/** ASTRA DINO Ω: audit of pinned public avian nuclear ALX1/HMGA2 proteins.
 * No genome->phenotype claim; no ancient DNA; source data JSON kept separately.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
const EXPECTED = new Map([
  ['ALX1|Geospiza fortis','XP_005421635.1'],
  ['HMGA2|Geospiza fortis','XP_030911403.1'],
  ['ALX1|Taeniopygia guttata','XP_002196043.1'],
  ['HMGA2|Taeniopygia guttata','XP_004176139.1'],
  ['ALX1|Gallus gallus','XP_040516271.1'],
  ['HMGA2|Gallus gallus','NP_990332.1']
]);
export function validate(data) {
  if (data?.schema!=='astra.dino.nuclear_proteins.v1'||data.proteins?.length!==6)
    throw Error('FAIL_CLOSED: schema or number of references');
  const by = new Map();
  for(const p of data.proteins) {
    const key=p.gene+'|'+p.species;
    if(!EXPECTED.has(key)||EXPECTED.get(key)!==p.accession||by.has(key)||
       p.length!==(p.gene==='ALX1'?328:109)||p.sequence?.length!==p.length||
       /[^ACDEFGHIKLMNPQRSTVWY]/.test(p.sequence))
      throw Error('FAIL_CLOSED: wrong accession, length, species or amino acid alphabet');
    if(!p.header?.includes('['+p.species+']'))throw Error('FAIL_CLOSED: wrong FASTA species');
    by.set(key,p);
  }
  if(by.size!==EXPECTED.size)throw Error('FAIL_CLOSED: incomplete reference set');
  return by;
}
export function samePosition(a,b) {
  if(a.length!==b.length)throw Error('FAIL_CLOSED: sequences are not positionally comparable');
  let matches=0; const mismatches=[];
  for(let i=0;i<a.length;i++) {
    if(a[i]===b[i])matches++;else mismatches.push(i+1);
  }
  return {matches,total:a.length,identityPercent:100*matches/a.length,mismatches};
}
export function audit(data) {
  const by=validate(data), comparisons=[];
  const birds=['Geospiza fortis','Taeniopygia guttata','Gallus gallus'];
  for (const gene of ['ALX1','HMGA2'])for(let i=0;i<birds.length;i++)for(let j=i+1;j<birds.length;j++) {
    const one=by.get(gene+'|'+birds[i]).sequence;
    const two=by.get(gene+'|'+birds[j]).sequence;
    comparisons.push({gene,one:birds[i],two:birds[j],...samePosition(one,two)});
  }
  return {source:'NCBI RefSeq protein FASTA, accession version + species verified',
    status:'SEQUENCE_COMPARISON_PASS', proteins:by.size, comparisons,
    interpretation:'Conservation of reference proteins; not locus haplotypes, regulation, causal alleles, genotype-phenotype association or dinosaur DNA'};
}
// Explicit provenance gate for public individual paired data, no automatic unproven matching.
export function phenotypeGenotypeCrosswalk(phenotypes, genotypes, mapping) {
  if(!Array.isArray(phenotypes)||!Array.isArray(genotypes)||!mapping||typeof mapping!=='object')
    throw Error('FAIL_CLOSED: independent sample mapping required');
  const ph=new Map();
  for(const row of phenotypes) {
    if(!row.AccNo||!Number.isFinite(row.Beak_length)||!Number.isFinite(row.Beak_height)||
       !Number.isFinite(row.Beak_width)||ph.has(row.AccNo))throw Error('FAIL_CLOSED: invalid or duplicated phenotypes');
    ph.set(row.AccNo,row);
  }
  const used=new Set(),out=[];
  for(const sample of genotypes) {
    if(used.has(sample))throw Error('FAIL_CLOSED: duplicate VCF sample');
    used.add(sample);
    const id=mapping[sample];
    if(!id)continue;
    if(!ph.has(id))throw Error('FAIL_CLOSED: mapped phenotype is absent');
    out.push({sample,AccNo:id,phenotype:ph.get(id)});
  }
  if(new Set(out.map(x=>x.AccNo)).size!==out.length)throw Error('FAIL_CLOSED: two genotypes map to one individual');
  return {status:out.length?'PAIRED':'NO_VALIDATED_PAIRS',matched:out.length,unmatched:genotypes.length-out.length,pairs:out};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  try {const path=process.argv[2];if(!path)throw Error('Usage: node astra_dino_nuclear_audit.mjs proteins.json');
    console.log(JSON.stringify(audit(JSON.parse(fs.readFileSync(path,'utf8'))),null,2));
  }catch(e){console.error(e.message);process.exitCode=1;}
}
