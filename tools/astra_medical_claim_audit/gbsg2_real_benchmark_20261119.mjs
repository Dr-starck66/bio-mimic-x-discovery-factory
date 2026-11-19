/** ASTRA MEDICAL Ω — Public GBSG2 methodological benchmark, no individual medical advice.
 * Source: sebp/scikit-survival/sksurv/datasets/data/GBSG2.arff
 * Runs with Node 22+, only local input ARFF. Does NOT use NATALEE IPD.
 * Run: node gbsg2_real_benchmark_20261119.mjs /path/to/GBSG2.arff
 */

function parseARFF(input){
  const split=input.split(/@data/i);if(split.length!==2)throw Error("ARFF missing data marker");
  const lines=split[1].trim().split(/\r?\n/).filter(s=>s.trim()&&!s.trim().startsWith("%"));
  return lines.map((s,i)=>{const p=s.replaceAll("'","").split(",").map(x=>x.trim());
    if(p.length!==10||!["yes","no"].includes(p[0])||!["0","1"].includes(p[9]))throw Error("Invalid row "+i);
    const v={hormone:p[0]==="yes",age:+p[1],menopause:p[2],tumourSize:+p[3],grade:p[4],nodes:+p[5],progesterone:+p[6],estrogen:+p[7],time:+p[8],event:p[9]==="1"};
    if(![v.age,v.tumourSize,v.nodes,v.progesterone,v.estrogen,v.time].every(Number.isFinite)||v.time<=0||v.nodes<0)throw Error("Bad numeric row "+i);
    return v;
  });
}

function cIndex(rows,score){
  if(rows.length!==score.length)throw Error("Score mismatch");
  let concordant=0,discordant=0,ties=0;
  for(let i=0;i<rows.length;i++)for(let j=i+1;j<rows.length;j++){
    let k=-1;
    if(rows[i].time<rows[j].time&&rows[i].event)k=i;
    else if(rows[j].time<rows[i].time&&rows[j].event)k=j;
    else continue;
    const delta=score[i]-score[j];
    if(delta===0)ties++;
    else if((k===i&&delta>0)||(k===j&&delta<0))concordant++;
    else discordant++;
  }
  const total=concordant+discordant+ties;
  return {value:total?(concordant+0.5*ties)/total:null,comparable_pairs:total,concordant,discordant,ties};
}

function kmSurvival(rows,horizonDays){
  if(!rows.length||!rows.some(x=>x.time>=horizonDays))return null;
  const eventTimes=[...new Set(rows.filter(x=>x.event&&x.time<=horizonDays).map(x=>x.time))].sort((a,b)=>a-b);
  let s=1;
  for(const time of eventTimes){
    let atRisk=0,events=0;
    for(const x of rows){if(x.time>=time)atRisk++;if(x.event&&x.time===time)events++;}
    if(!atRisk||events>atRisk)throw Error("Invalid survival risk set");
    s*=1-events/atRisk;
  }
  return s;
}

function seededRandom(seed){let x=seed>>>0;return ()=>((x=(Math.imul(1664525,x)+1013904223)>>>0)/4294967296);}

function shuffleInPlace(a,rand){for(let i=a.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}

function interactionEstimate(rows,horizonDays=1095){
  const groups={};
  for(const cat of [true,false]){
    const yy=rows.filter(r=>(r.nodes<=3)===cat&&r.hormone),nn=rows.filter(r=>(r.nodes<=3)===cat&&!r.hormone);
    const a=kmSurvival(yy,horizonDays),b=kmSurvival(nn,horizonDays);
    groups[cat?"nodes_le3":"nodes_gt3"]={treated_n:yy.length,control_n:nn.length,treated_survival:a,control_survival:b,difference:a===null||b===null?null:a-b};
  }
  const x=groups.nodes_le3.difference,y=groups.nodes_gt3.difference;
  return {groups,interaction:x===null||y===null?null:x-y};
}

function analyzeGBSG2(input,seed=20261119){
 const rows=parseARFF(input), n=rows.length,events=rows.filter(x=>x.event).length;
 if(n!==686||events!==299)throw Error("Source dataset shape mismatch");
 const rand=seededRandom(seed),scores=rows.map(x=>Math.log1p(x.nodes)),index=cIndex(rows,scores);
 const permScores=[];
 for(let k=0;k<100;k++)permScores.push(cIndex(rows,shuffleInPlace(scores.slice(),rand)).value);
 const bootScores=[];
 for(let k=0;k<200;k++){const b=[],s=[];for(let i=0;i<n;i++){const id=Math.floor(rand()*n);b.push(rows[id]);s.push(scores[id]);}bootScores.push(cIndex(b,s).value);}
 bootScores.sort((a,b)=>a-b);
 const est=interactionEstimate(rows),perms=[];
 for(let k=0;k<300;k++){
   const b=rows.map(x=>({...x}));
   for(const cat of [true,false]){
     const indices=b.map((x,i)=>(x.nodes<=3)===cat?i:-1).filter(i=>i>=0);
     const shuffle=shuffleInPlace(indices.map(i=>b[i].hormone),rand);
     indices.forEach((id,i)=>b[id].hormone=shuffle[i]);
   }
   perms.push(interactionEstimate(b).interaction);
 }
 const boot=[];
 for(let k=0;k<300;k++){
   const b=[];
   for(const cat of [true,false])for(const tx of [true,false]){
     const cell=rows.filter(x=>(x.nodes<=3)===cat&&x.hormone===tx);
     for(let i=0;i<cell.length;i++)b.push(cell[Math.floor(rand()*cell.length)]);
   }
   boot.push(interactionEstimate(b).interaction);
 }
 boot.sort((a,b)=>a-b);
 const extreme=perms.filter(x=>Math.abs(x)>=Math.abs(est.interaction)).length;
 return {
  patients:n,event_count:events,
  no_hormonal_therapy_n:rows.filter(x=>!x.hormone).length,
  hormonal_therapy_n:rows.filter(x=>x.hormone).length,
  nodes_prognostic_c_index:index.value,comparable_pairs:index.comparable_pairs,
  c_index_bootstrap_95:[bootScores[4],bootScores[194]],
  negative_permutations:100,permutation_c_index_average:permScores.reduce((a,b)=>a+b,0)/100,
  negative_permutations_at_least_observed:permScores.filter(x=>x>=index.value).length,
  hormone_3yr_rec_free:est,
  interaction_exploratory_bootstrap_95:[boot[7],boot[292]],
  interaction_permutation_p_plus_one:(1+extreme)/301,interaction_permutations:300,interaction_extreme_count:extreme,
  seed,limitations:["GBSG2 is historical randomized adjuvant hormonal treatment, not ribociclib or NATALEE","Prognostic C-index is not treatment-effect prediction","Subgroup cutpoint <=3 nodes explored with no independent holdout; not a clinical rule","Causal effect per individual unidentifiable; interaction confidence interval includes zero","Only aggregate output, no clinical use"]
 };
}
import {readFileSync} from "node:fs";
import {pathToFileURL} from "node:url";
export {parseARFF,cIndex,kmSurvival,interactionEstimate,analyzeGBSG2};
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href){
 if(!process.argv[2]){console.error("Usage: node gbsg2_real_benchmark_20261119.mjs GBSG2.arff");process.exit(2);}
 const result=analyzeGBSG2(readFileSync(process.argv[2],"utf8"));
 console.log(JSON.stringify(result,null,2));
}
