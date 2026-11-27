/** BIO-MIMIC X: two published cohorts, no claim of clinical prediction.
 * Original: https://ars.els-cdn.com/content/image/1-s2.0-S1550413126004535-mmc2.xlsx
 * External: https://journals.asm.org/doi/suppl/10.1128/msystems.00325-19/suppl_file/msystems.00325-19-sd001.xlsx
 */
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
export function readCsv(file){
 const lines=fs.readFileSync(file,'utf8').trim().split(/\r?\n/);
 if(lines.length<2)throw Error('Empty input: '+file);
 const header=lines[0].split(',');
 return lines.slice(1).map((line,i)=>{
  const c=line.split(',');
  if(c.length!==header.length)throw Error('Column mismatch '+file+':'+(i+2));
  return Object.fromEntries(header.map((k,j)=>[k,c[j]]));
 });
}
export function auc(pos,neg){
 if(!pos.length||!neg.length||[...pos,...neg].some(x=>!Number.isFinite(x)))throw Error('Both nonempty finite groups required');
 let wins=0;for(const p of pos)for(const n of neg)wins+=p>n?1:p===n?.5:0;
 return wins/pos.length/neg.length;
}
export function median(a){
 const v=[...a].sort((x,y)=>x-y);return (v[Math.floor((v.length-1)/2)]+v[Math.ceil((v.length-1)/2)])/2;
}
export function rng(start){let seed=start>>>0;return()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};}
export function permutationP(pos,neg,n=2000,seed=983192){
 const random=rng(seed),pool=[...neg,...pos],obs=Math.abs(auc(pos,neg)-.5);
 let exceed=0;
 for(let t=0;t<n;t++){
  const p=[...pool];
  for(let i=p.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[p[i],p[j]]=[p[j],p[i]];}
  const test=auc(p.slice(neg.length),p.slice(0,neg.length));
  if(Math.abs(test-.5)>=obs-1e-12)exceed++;
 }
 return (exceed+1)/(n+1);
}
export function bootstrapAuc(pos,neg,n=1500,seed=983192){
 const random=rng(seed),values=[];
 for(let t=0;t<n;t++){
  const a=Array.from({length:pos.length},()=>pos[Math.floor(random()*pos.length)]);
  const b=Array.from({length:neg.length},()=>neg[Math.floor(random()*neg.length)]);
  values.push(auc(a,b));
 }
 values.sort((a,b)=>a-b);
 return [values[Math.floor((n-1)*.025)],values[Math.floor((n-1)*.975)]];
}
function group(rows,label,feature){
 return rows.filter(r=>r.group===label).map(r=>{
  const v=Number(r[feature]);
  if(r[feature]===undefined||r[feature]===''||!Number.isFinite(v))throw Error('Invalid '+feature);
  return v;
 });
}
function check(rows,expected){
 for(const [key,n]of Object.entries(expected))if(rows.filter(r=>r.group===key).length!==n)throw Error('Unexpected '+key+' count');
 if(rows.length!==Object.values(expected).reduce((a,b)=>a+b,0))throw Error('Unexpected groups');
}
export function analyse(main,other,sardinia){
 check(main,{Young:44,Elderly:110,Centenarian:154});
 const y=group(main,'Young','ln_cbh_over_recA'),e=group(main,'Elderly','ln_cbh_over_recA'),c=group(main,'Centenarian','ln_cbh_over_recA');
 const featureAucs={cbh:auc(c,e)};
 for(const gene of ['hdhA','baiA','baiB','baiH']){
  const rows=other.filter(x=>x.gene===gene);check(rows,{Young:44,Elderly:110,Centenarian:154});
  featureAucs[gene]=auc(group(rows,'Centenarian','ln_gene_over_recA'),group(rows,'Elderly','ln_gene_over_recA'));
 }
 check(sardinia,{Young:17,Elderly:23,Centenarian:19});
 const sC=group(sardinia,'Centenarian','7ALPHADEHYDROX_PWY'),sE=group(sardinia,'Elderly','7ALPHADEHYDROX_PWY');
 return {
  status:'PARTIAL_ASSOCIATION_REPRODUCED_NOT_PREDICTION',
  original:{n:main.length,groups:{Young:44,Elderly:110,Centenarian:154},
   medians:{Young:median(y),Elderly:median(e),Centenarian:median(c)},
   auc_centenarian_vs_elderly:featureAucs.cbh,exploratory_auc_ci95:bootstrapAuc(c,e),
   unstratified_permutation_p:permutationP(c,e),candidate_gene_aucs:featureAucs},
  independent_sardinia:{n:sardinia.length,groups:{Young:17,Elderly:23,Centenarian:19},
   feature:'7ALPHADEHYDROX-PWY cholate degradation (NOT K01442/BSH)',
   nonzero:{Centenarian:sC.filter(v=>v>0).length,Elderly:sE.filter(v=>v>0).length},
   auc_centenarian_vs_elderly:auc(sC,sE),unstratified_permutation_p:permutationP(sC,sE,4999,2461)},
  biological_negative_control_gene:'NOT_AVAILABLE',separate_K01442_and_recA_counts:'NOT_AVAILABLE',
  matched_individual_IDs:'NOT_AVAILABLE',independent_K01442_recA_validation:'UNVERIFIED',
  interpretation:'Unadjusted cross-sectional published log ratios; external pathway proxy is NOT direct BSH replication'
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=process.argv[2]||'.';
 const res=analyse(readCsv(path.join(root,'data/centenarian_2026_Fig2D_ln_cbh_recA.csv')),
  readCsv(path.join(root,'data/centenarian_2026_FigS2D_other_bile_genes.csv')),
  readCsv(path.join(root,'data/sardinia_2019_7ALPHADEHYDROX_59.csv')));
 process.stdout.write(JSON.stringify(res,null,2)+'\n');
}
