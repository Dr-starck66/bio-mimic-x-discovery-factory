/**
 * ASTRA DINO Ω — real bird mtDNA to AVONET morphology baseline.
 * 17 independent species measurements; whole-families held out.
 * Not nuclear genetics, not fossil DNA, not reconstruction of extinct animals.
 * Node.js >=20, no dependencies.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

export const TRAITS=['Mass','Beak.Length_Culmen','Beak.Depth','Tarsus.Length','Wing.Length'];
export function validate(dataset){
  if(dataset?.schema!=='astra.dino.mtDNA_avonet_paired.v1')throw Error('FAIL_CLOSED: wrong schema');
  const s=dataset.taxa, d=dataset.distance, n=s?.length;
  if(!Array.isArray(s)||n<5||!Array.isArray(d)||d.length!==n)
    throw Error('FAIL_CLOSED: incomplete matched data');
  if(new Set(s.map(t=>t.species)).size!==n||new Set(s.map(t=>t.accession)).size!==n)
    throw Error('FAIL_CLOSED: duplicate species or accession');
  for(let i=0;i<n;i++){
    const t=s[i];
    if(!t.species||!t.family||!t.order||!t.accession||t.sequenceLength<14000||
       !TRAITS.every(k=>Number.isFinite(t.traits?.[k])&&t.traits[k]>0))
      throw Error('FAIL_CLOSED: invalid taxon or anatomy');
    if(!Array.isArray(d[i])||d[i].length!==n||d[i][i]!==0)
      throw Error('FAIL_CLOSED: invalid distance matrix');
    for(let j=0;j<n;j++)if(!Number.isFinite(d[i][j])||d[i][j]<0||
       d[i][j]>1||Math.abs(d[i][j]-d[j]?.[i])>1e-8)
      throw Error('FAIL_CLOSED: nonsymmetric or invalid genome distance');
  }
  return n;
}
export function kmers(sequence,k=11){
  const out=new Set();
  for(let i=0;i<=sequence.length-k;i++){
    const x=sequence.slice(i,i+k);
    if(/^[ACGT]+$/.test(x))out.add(x);
  }
  return out;
}
export function rebuildDistances(dataset,sources){
  validate(dataset);
  const entries=sources.flatMap(p=>p.entries||[]);
  const map=new Map(entries.map(e=>[e.species,e]));
  if(entries.length!==map.size)throw Error('FAIL_CLOSED: duplicate primary sequence');
  const k=dataset.kmer??11;
  const seqSets=dataset.taxa.map(t=>{
    const e=map.get(t.species);
    if(!e||e.accession!==t.accession||e.sequence.length!==t.sequenceLength||
       /[^ACGTN]/.test(e.sequence))throw Error('FAIL_CLOSED: source FASTA mismatch for '+t.species);
    return kmers(e.sequence,k);
  });
  const tolerance=1e-7;
  for(let i=0;i<seqSets.length;i++)for(let j=i+1;j<seqSets.length;j++){
    let common=0;for(const word of seqSets[i])if(seqSets[j].has(word))common++;
    const d=1-common/(seqSets[i].size+seqSets[j].size-common);
    if(Math.abs(d-dataset.distance[i][j])>tolerance)
      throw Error('FAIL_CLOSED: genomic distance mismatch '+i+':'+j);
  }
  return {status:'PASS',checkedSequences:seqSets.length,checkedDistances:seqSets.length*(seqSets.length-1)/2};
}
export function seeded(seed=20261114){
  let state=seed>>>0;
  return ()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;
    return state/4294967296;};
}
export function holdout(dataset,permutation=null,k=3){
  const n=validate(dataset),s=dataset.taxa,d=dataset.distance;
  if(!Number.isInteger(k)||k<1||k>=n)throw Error('FAIL_CLOSED: invalid number of neighbors');
  if(permutation&&
     (permutation.length!==n||new Set(permutation).size!==n||
      permutation.some(i=>!Number.isInteger(i)||i<0||i>=n)))
    throw Error('FAIL_CLOSED: invalid sequence shuffle');
  const errors=Object.fromEntries(TRAITS.map(t=>[t,{model:0,baseline:0,perTaxon:[]}]));
  let count=0;
  for(let i=0;i<n;i++){
    const train=s.map((_,j)=>j).filter(j=>s[j].family!==s[i].family);
    if(train.length<k)throw Error('FAIL_CLOSED: insufficient outside-family training birds');
    const index=permutation?permutation[i]:i;
    const nearby=train.slice().sort((a,b)=>d[index][permutation?permutation[a]:a]-
      d[index][permutation?permutation[b]:b]||a-b).slice(0,k);
    for(const trait of TRAITS){
      const y=Math.log(s[i].traits[trait]);
      const pred=nearby.reduce((v,j)=>v+Math.log(s[j].traits[trait]),0)/k;
      const ref=train.reduce((v,j)=>v+Math.log(s[j].traits[trait]),0)/train.length;
      const err=Math.abs(pred-y),errRef=Math.abs(ref-y);
      errors[trait].model+=err/n;errors[trait].baseline+=errRef/n;
      errors[trait].perTaxon.push({species:s[i].species,family:s[i].family,errorModel:err,errorBaseline:errRef});
      count++;
    }
  }
  const model=TRAITS.reduce((v,t)=>v+errors[t].model,0)/TRAITS.length;
  const baseline=TRAITS.reduce((v,t)=>v+errors[t].baseline,0)/TRAITS.length;
  return {species:n,families:new Set(s.map(t=>t.family)).size,count,model,baseline,
    relativeImprovement:(baseline-model)/baseline,byTrait:errors};
}
export function negativeControl(dataset,replicates=200,seed=20261114){
  if(!Number.isInteger(replicates)||replicates<1)throw Error('FAIL_CLOSED: bad replicate count');
  const random=seeded(seed),n=validate(dataset),original=holdout(dataset);
  const nullScores=[];
  for(let p=0;p<replicates;p++){
    const perm=Array.from({length:n},(_,i)=>i);
    for(let j=n-1;j>0;j--){const k=Math.floor(random()*(j+1));
      [perm[j],perm[k]]=[perm[k],perm[j]];}
    nullScores.push(holdout(dataset,perm).model);
  }
  const rank=nullScores.filter(x=>x<=original.model).length;
  return {replicates,seed,mean:nullScores.reduce((a,b)=>a+b,0)/replicates,
    countAtLeastAsGood:rank,empiricalP:(rank+1)/(replicates+1)};
}
export function fossilBridgeGate(fossilTaxa, modernTaxa){
  const overlap=['Anas','Gallus'].filter(genus=>
    fossilTaxa.includes(genus)&&modernTaxa.some(t=>t.species.startsWith(genus+' ')));
  return {overlap,intersectingGenera:overlap.length,status:'PARTIAL',
    testableHypothesis:'Orthologous anatomy requires independently defined character correspondence',
    transferAllowed:false,
    reason:'AVONET continuous external measurements cannot be treated as homologous to the Wang 2021 NEXUS discrete characters merely because genus names match'};
}
async function main(){
  const args=process.argv.slice(2),at=args.indexOf('--data');
  if(at<0||!args[at+1])throw Error('Usage: node validation/astra_dino_genome_trait_v1.mjs --data <paired.json> [--raw-prefix <path>]');
  const dataset=JSON.parse(fs.readFileSync(args[at+1],'utf8'));validate(dataset);
  const result={project:'ASTRA DINO OMEGA',stage:'REAL_EXTANT_BIRD_MTDNA_TO_AVONET',
    source:dataset.source,studyLimitations:['Mitochondrial sequences only','Small hand-picked cohort',
      'No nuclear gene architecture','Phylogenetic structure not modeled',
      'No extinct animal genome, no fossil reconstruction'],
    metrics:holdout(dataset),shuffledGenotypeControl:negativeControl(dataset),
    fossilBridge:fossilBridgeGate(['Anas','Gallus'],dataset.taxa)};
  const rawAt=args.indexOf('--raw-prefix');
  if(rawAt>=0){
    const dir=args[rawAt+1];if(!dir)throw Error('Missing raw prefix');
    const sources=[1,2,3,4].map(i=>JSON.parse(fs.readFileSync(`${dir}/astra_dino_mtDNA_source_part${i}.json`,'utf8')));
    result.sequenceAudit=rebuildDistances(dataset,sources);
  }
  console.log(JSON.stringify(result,null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)
  main().catch(e=>{console.error(e.message);process.exitCode=1;});
