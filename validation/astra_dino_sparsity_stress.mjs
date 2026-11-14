/** ASTRA DINO Omega: blind fossil morphology recovery under missing features.
 * Primary source must match pinned Wang et al. 2021 Git blob SHA.
 * Non-random fossil preservation and genome-to-phenotype transfer NOT tested.
 */
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import {assertExternalSource, EXTERNAL_SOURCE} from './astra_dino_external_2021.mjs';
import {majority, individualTaxa, downloadText} from './astra_dino_ancestry.mjs';

export const DEFAULT_FRACTIONS=[0.2,0.4,0.6,0.8];
export function stableRandom(taxonIndex, charIndex, repeat, seed=20261114){
  let s=(seed^Math.imul(taxonIndex+19,1013904223)^Math.imul(charIndex+3,1664525)^Math.imul(repeat+7,2246822519))>>>0;
  s^=s>>>16;s=Math.imul(s,0x7feb352d);s^=s>>>15;s=Math.imul(s,0x846ca68b);s^=s>>>16;
  return (s>>>0)/4294967296;
}
export function evaluateSparsity(parsed,{fractions=DEFAULT_FRACTIONS,repeats=5,minOverlap=20,k=3,seed=20261114}={}){
  if(!parsed?.rows?.length||!Number.isInteger(parsed.nChar)||parsed.nChar<=0)throw Error('Invalid parsed matrix');
  if(!Number.isInteger(repeats)||repeats<1||!Number.isInteger(k)||k<1||!Number.isInteger(minOverlap)||minOverlap<0)throw Error('Invalid test parameters');
  const taxa=individualTaxa(parsed.rows);
  if(taxa.length<=k)throw Error('Insufficient taxonomic diversity');
  if(taxa.some(x=>x.states.length!==parsed.nChar))throw Error('Row width mismatch');
  const out=[];
  for(const fraction of fractions){
    if(!(fraction>0&&fraction<1))throw Error('Fractions must be strictly between 0 and 1');
    let scored=0,correct=0,referenceCorrect=0,eligibleHidden=0,abstained=0;
    const perRepeat=[];
    for(let repeat=0;repeat<repeats;repeat++){
      let n=0,hits=0,refHits=0,hidden=0,blocked=0;
      for(let ti=0;ti<taxa.length;ti++){
        const target=taxa[ti],train=taxa.filter((_,j)=>j!==ti),observed=[];
        for(let c=0;c<parsed.nChar;c++)if(target.states[c]!==null&&stableRandom(ti,c,repeat,seed)<fraction)observed.push(c);
        const used=new Set(observed);
        const ranked=train.map(t=>{
          let overlap=0,agree=0;
          for(const c of observed){if(t.states[c]!==null){overlap++;if(t.states[c]===target.states[c])agree++;}}
          return {t,overlap,score:overlap>=minOverlap?agree/overlap:-1};
        }).filter(x=>x.score>=0).sort((a,b)=>b.score-a.score||b.overlap-a.overlap||a.t.taxon.localeCompare(b.t.taxon));
        for(let c=0;c<parsed.nChar;c++){
          if(target.states[c]===null||used.has(c))continue;
          const eligible=train.filter(t=>t.states[c]!==null);
          if(eligible.length<k)continue;
          hidden++;
          const neighbors=ranked.filter(t=>t.t.states[c]!==null).slice(0,k);
          if(neighbors.length!==k){blocked++;continue;}
          const guess=majority(neighbors.map(x=>x.t.states[c]));
          const baseline=majority(eligible.map(x=>x.states[c]));
          n++;hits+=Number(guess===target.states[c]);refHits+=Number(baseline===target.states[c]);
        }
      }
      scored+=n;correct+=hits;referenceCorrect+=refHits;eligibleHidden+=hidden;abstained+=blocked;
      perRepeat.push({tested:n,hidden,correct:hits,referenceCorrect:refHits,coverage:hidden?n/hidden:0,accuracy:n?hits/n:null});
    }
    out.push({fraction,repeats,scored,correct,referenceCorrect,eligibleHidden,abstained,
      accuracy:scored?correct/scored:null,referenceAccuracy:scored?referenceCorrect/scored:null,
      gainPoints:scored?100*(correct-referenceCorrect)/scored:null,
      coverage:eligibleHidden?scored/eligibleHidden:null,perRepeat});
  }
  return {taxa:taxa.length,characters:parsed.nChar,k,minOverlap,seed,results:out,
    interpretation:'Known fossil characters withheld at random; refitted morphological neighbor method, not genomic prediction; preserved fossils are not missing at random'};
}
async function main(){
  const a=process.argv.slice(2);const file=a.indexOf('--file');
  if(file>=0&&!a[file+1])throw Error('Missing file');
  if(file<0&&!a.includes('--online'))throw Error('Use --online or --file <pinned.nex>');
  const raw=file<0?await downloadText(EXTERNAL_SOURCE.url):fs.readFileSync(a[file+1],'utf8');
  const parsed=assertExternalSource(raw);
  console.log(JSON.stringify({source:EXTERNAL_SOURCE,benchmark:'ASTRA_DINO_SPARSE_FOSSIL_V1',...evaluateSparsity(parsed)},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)
  main().catch(e=>{console.error('FAIL_CLOSED:',e.message);process.exitCode=1;});
