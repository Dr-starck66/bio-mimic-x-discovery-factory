// Calibrate a trajectory-level alarm budget, not a per-window percentile.
// Uses unchanged v0.23 fitScore and fixed 150-sample monitoring horizon.
function trajectoryAudit(){
 const seeds={cal:572001,test:983001},n=200,horizon=150,onset=250;
 function make(seed){let state=seed>>>0;const u=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};const g=()=>Math.sqrt(-2*Math.log(Math.max(u(),1e-12)))*Math.cos(2*Math.PI*u());return Array.from({length:400},()=>Array.from({length:4},g))}
 const time=Array.from({length:400},(_,i)=>i);
 function series(X){const a=fitScore(X,time).dual;if(!(a.threshold>0))throw Error('nonpositive threshold');return a.score.slice(onset).map(v=>v/a.threshold)}
 // Split conformal rank: ceil((n+1)*(1-alpha)); exchangeable trajectory maxima only.
 const alpha=.05,peaks=Array.from({length:n},(_,i)=>Math.max(...series(make(seeds.cal+i)))).sort((a,b)=>a-b);
 const rank=Math.ceil((n+1)*(1-alpha)),factor=peaks[rank-1];if(!(factor>=1))throw Error('unexpected factor');
 const results={};
 for(const [name,shift,local] of [['healthy',0,false],['local_strong',6,true],['common_strong',6,false],['local_weak',1.5,true],['common_weak',1.5,false]]){
  let old=0,corrected=0,oldDelay=[],newDelay=[];
  for(let i=0;i<n;i++){const X=make(seeds.test+i).map((r,t)=>r.map((v,j)=>v+(t>=onset&&(!local||j===0)?shift:0))),s=series(X),a=s.findIndex(v=>v>1),b=s.findIndex(v=>v>factor);old+=Number(a>=0);corrected+=Number(b>=0);if(a>=0)oldDelay.push(a);if(b>=0)newDelay.push(b)}
  const median=a=>{a.sort((x,y)=>x-y);return a.length?a[Math.floor(a.length/2)]:null};
  results[name]={old,corrected,n,oldMedianDetectedDelay:median(oldDelay),newMedianDetectedDelay:median(newDelay)};
 }
 return {seeds,n,horizon,alpha,rank,factor,results,scope:'independent simulated Gaussian trajectories, exchangeability assumed; not validated on industrial data'};
}
