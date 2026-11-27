/** ASTRA DINO Ω — fossil morphology + extant avian mtDNA audit, no third-party npm deps.
 * Dataset is fetched from authors/NCBI at runtime, not redistributed.
 * NEVER interprets inferred characters as extinct DNA or a living dinosaur.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';

export const HOLTZ_URL='https://www.geol.umd.edu/~tholtz/Gaia2000';
export const BIRD_MTDNA=Object.freeze({
  'Gallus gallus':'NC_001323.1',
  'Meleagris gallopavo':'NC_010195.2',
  'Anas platyrhynchos':'NC_009684.1',
  'Struthio camelus':'NC_002785.1'
});
export function tokenizeNexus(seq) {
  const result=[];
  for(let i=0;i<seq.length;i++){
    const c=seq[i];
    if(c==='('||c==='{'){
      const j=seq.indexOf(c==='('?')':'}',i+1);
      if(j<0)throw new Error('Unclosed polymorphic state');
      result.push(null);i=j;
    }else if(/^[0-9]$/.test(c))result.push(c);
    else if(c==='?'||c==='-')result.push(null);
    else if(!/\s/.test(c))throw new Error('Unrecognized NEXUS state: '+c);
  }
  return result;
}
export function parseNexus(text,strictHoltz=false) {
  const dims=text.match(/NTAX\s*=\s*(\d+)\s+NCHAR\s*=\s*(\d+)/i);
  if(!dims)throw new Error('Missing NTAX/NCHAR');
  const nTax=Number(dims[1]),nChar=Number(dims[2]);
  if(strictHoltz&&(nTax!==50||nChar!==386))throw new Error('Unexpected source dimensions');
  const matrix=text.match(/\bMATRIX\s*\n([\s\S]*?)\n\s*;/i);
  if(!matrix)throw new Error('Missing MATRIX block');
  const rows=matrix[1].trim().split(/\r?\n/).map(line=>{
    const match=line.trim().match(/^(\S+)\s+(.+)$/);
    if(!match)throw new Error('Invalid matrix row');
    const states=tokenizeNexus(match[2]);
    if(states.length!==nChar)throw new Error('Invalid character count for '+match[1]);
    return {taxon:match[1],states};
  });
  if(rows.length!==nTax||new Set(rows.map(x=>x.taxon)).size!==nTax)throw new Error('Invalid unique taxon count');
  return {nTax,nChar,rows};
}
export function individualTaxa(rows){
  return rows.filter(({taxon})=>taxon!=='allzero'&&!/(idae|inae|oidea)$/i.test(taxon)&&!['Prosauropoda','Ornithothoraces'].includes(taxon));
}
export function majority(values){
  const counts=new Map();
  for(const v of values)if(v!==null)counts.set(v,(counts.get(v)||0)+1);
  return [...counts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))[0]?.[0]??null;
}
/** Entire fossil taxon excluded from training; all other known test-taxon
 * characters permitted at prediction time; target column excluded from metric.
 * Comparisons to majority baseline on exactly the same evaluable cells.
 */
export function evaluateMorph(parsed,minOverlap=20,k=3){
  const taxa=individualTaxa(parsed.rows),nChar=parsed.nChar,perTaxon=[],cells=[];
  for(let i=0;i<taxa.length;i++){
    const target=taxa[i],train=taxa.filter((_,j)=>j!==i);
    let tested=0,model=0,baseline=0;
    for(let c=0;c<nChar;c++){
      const truth=target.states[c];
      if(truth===null)continue;
      const eligible=train.filter(t=>t.states[c]!==null);
      if(eligible.length<k)continue;
      const ranked=eligible.map(t=>{
        let agree=0,overlap=0;
        for(let j=0;j<nChar;j++){
          if(j===c||t.states[j]===null||target.states[j]===null)continue;
          overlap++;
          if(t.states[j]===target.states[j])agree++;
        }
        return {taxon:t.taxon,value:t.states[c],score:overlap>=minOverlap?agree/overlap:-1,overlap};
      }).filter(x=>x.score>=0).sort((a,b)=>b.score-a.score||b.overlap-a.overlap||a.taxon.localeCompare(b.taxon));
      const nearest=ranked.slice(0,k);
      if(nearest.length<k)continue;
      const prediction=majority(nearest.map(x=>x.value));
      const naive=majority(eligible.map(t=>t.states[c]));
      tested++;model+=Number(prediction===truth);baseline+=Number(naive===truth);
      cells.push({truth,eligible:eligible.map(t=>t.states[c])});
    }
    perTaxon.push({taxon:target.taxon,n:tested,modelCorrect:model,baselineCorrect:baseline});
  }
  const tests=cells.length;
  if(!tests)throw new Error('No evaluable withheld fossil characters');
  const modelCorrect=perTaxon.reduce((a,t)=>a+t.modelCorrect,0);
  const baselineCorrect=perTaxon.reduce((a,t)=>a+t.baselineCorrect,0);
  return {taxa:taxa.length,characters:nChar,tests,modelCorrect,baselineCorrect,
    accuracy:modelCorrect/tests,baselineAccuracy:baselineCorrect/tests,
    deltaPoints:100*(modelCorrect-baselineCorrect)/tests,
    betterTaxa:perTaxon.filter(x=>x.modelCorrect>x.baselineCorrect).length,
    worseTaxa:perTaxon.filter(x=>x.modelCorrect<x.baselineCorrect).length,
    tiedTaxa:perTaxon.filter(x=>x.modelCorrect===x.baselineCorrect).length,
    perTaxon,cells};
}
function rng(seed=20261114){
  let value=seed>>>0;
  return ()=>{value=(Math.imul(value,1664525)+1013904223)>>>0;return value/4294967296;};
}
/** Confidence interval samples taxa (not correlated cells). Exploratory only. */
export function bootstrapDelta(perTaxon,iterations=1000,seed=20261114){
  const random=rng(seed),deltas=[];
  for(let p=0;p<iterations;p++){
    let n=0,m=0,b=0;
    for(let j=0;j<perTaxon.length;j++){
      const t=perTaxon[Math.floor(random()*perTaxon.length)];
      n+=t.n;m+=t.modelCorrect;b+=t.baselineCorrect;
    }
    if(n)deltas.push(100*(m-b)/n);
  }
  deltas.sort((a,b)=>a-b);
  if(!deltas.length)throw new Error('Insufficient observations for bootstrap');
  return {lower95:deltas[Math.floor(0.025*(deltas.length-1))],
    upper95:deltas[Math.floor(0.975*(deltas.length-1))],iterations};
}
/** Random training labels sampled without replacement, prevalence maintained. */
export function permutedLabelNull(cells,replicates=30,k=3,seed=20261114){
  const random=rng(seed),accuracy=[];
  for(let p=0;p<replicates;p++){
    let hits=0;
    for(const cell of cells){
      const arr=cell.eligible,selected=new Set();
      while(selected.size<k)selected.add(Math.floor(random()*arr.length));
      hits+=Number(majority([...selected].map(i=>arr[i]))===cell.truth);
    }
    accuracy.push(hits/cells.length);
  }
  return {replicates,mean:accuracy.reduce((a,b)=>a+b,0)/replicates,
    min:Math.min(...accuracy),max:Math.max(...accuracy)};
}
export function parseFasta(text,accession){
  const lines=text.trim().replace(/\\_/g,'_').split(/\r?\n/);
  if(!lines[0]?.startsWith('>')||!lines[0].includes(accession))
    throw new Error('Unmatched FASTA accession: '+accession);
  const seq=lines.slice(1).join('').replace(/\s/g,'').toUpperCase();
  if(seq.length<14000||seq.length>19000||/[^ACGTN]/.test(seq))
    throw new Error('Invalid mitochondrial reference sequence');
  return seq;
}
export function genomicComparison(sequences,k=11){
  const sets=Object.entries(sequences).map(([name,seq])=>{
    const kmers=new Set();
    for(let i=0;i<=seq.length-k;i++){
      const word=seq.slice(i,i+k);
      if(/^[ACGT]+$/.test(word))kmers.add(word);
    }
    return {name,seq,kmers};
  });
  const pairs=[];
  for(let i=0;i<sets.length;i++)for(let j=i+1;j<sets.length;j++){
    const a=sets[i],b=sets[j];let shared=0;
    for(const word of a.kmers)if(b.kmers.has(word))shared++;
    pairs.push({a:a.name,b:b.name,shared,jaccard:shared/(a.kmers.size+b.kmers.size-shared)});
  }
  return {k,genomes:sets.map(x=>({name:x.name,length:x.seq.length,
    gc:(x.seq.match(/[GC]/g)||[]).length/x.seq.length})),pairs};
}
export async function downloadText(url){
  const response=await fetch(url,{signal:AbortSignal.timeout(25000),
    headers:{'User-Agent':'ASTRA-DINO-OMEGA-open-science/0.1'}});
  if(!response.ok)throw new Error('Upstream '+response.status+': '+url);
  return response.text();
}
async function main(){
  const args=process.argv.slice(2);
  if(!args.includes('--online')&&!args.includes('--file'))
    throw new Error('Usage: node astra_dino_ancestry.mjs --online | --file dataset.nex');
  const index=args.indexOf('--file');
  const text=index>=0?fs.readFileSync(args[index+1],'utf8'):await downloadText(HOLTZ_URL);
  const parsed=parseNexus(text,true);
  const {cells,...morph}=evaluateMorph(parsed);
  const report={project:'ASTRA DINO OMEGA',status:'EXPLORATORY',
    sources:{morphology:HOLTZ_URL},
    morphology:{...morph,bootstrap:bootstrapDelta(morph.perTaxon),
      negativeControl:permutedLabelNull(cells)}};
  if(args.includes('--online')){
    const seqs={};
    for(const [species,accession] of Object.entries(BIRD_MTDNA)){
      const url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id='+
        accession+'&rettype=fasta&retmode=text';
      seqs[species]=parseFasta(await downloadText(url),accession);
    }
    report.sources.avianMitochondria=BIRD_MTDNA;
    report.genomics=genomicComparison(seqs);
  }
  console.log(JSON.stringify(report,null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)
  main().catch(e=>{console.error('FAIL_CLOSED:',e.message);process.exitCode=1;});
