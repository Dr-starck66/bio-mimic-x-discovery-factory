// Sequential dual evidence: two-sided CUSUM of absolute and relative standardized signals.
// Development on synthetic data only. Fixed parameters before fresh synthetic seeds.
function sequentialAudit(){
 const n=200,start=202,onset=250,N=400,alpha=.05,drift=.25;
 const seeds={cal:1829001,test:1929001};
 const median=a=>{let b=[...a].sort((a,b)=>a-b),k=b.length>>1;return b.length%2?b[k]:(b[k-1]+b[k])/2};
 function make(seed){let state=seed>>>0;const u=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};const g=()=>Math.sqrt(-2*Math.log(Math.max(u(),1e-12)))*Math.cos(2*Math.PI*u());return Array.from({length:N},()=>Array.from({length:4},g))}
 const time=Array.from({length:N},(_,i)=>i);
 function series(X){let a=fitScore(X,time).dual;if(!(a.threshold>0))throw Error('threshold');return a.score.slice(start).map(v=>v/a.threshold)}
 function cusum(X){
   const fit=X.slice(0,100),c=Array.from({length:4},(_,j)=>median(fit.map(r=>r[j]))),s=c.map((m,j)=>Math.max(.05,1.4826*median(fit.map(r=>Math.abs(r[j]-m)))));
   const z=X.map(r=>r.map((v,j)=>(v-c[j])/s[j]));
   const features=z.map(r=>{const m=median(r);return [...r,...r.map(v=>v-m),m]});
   const offset=Array.from({length:9},(_,j)=>median(features.slice(0,100).map(r=>r[j])));
   const pos=Array(9).fill(0),neg=Array(9).fill(0);
   return features.slice(start).map(r=>{r.forEach((v,j)=>{let x=v-offset[j];pos[j]=Math.max(0,pos[j]+x-drift);neg[j]=Math.max(0,neg[j]-x-drift)});return Math.max(...pos,...neg)});
 }
 const rank=Math.ceil((n+1)*(1-alpha));
 const normal=Array.from({length:n},(_,i)=>make(seeds.cal+i));
 const cal=fn=>normal.map(X=>Math.max(...fn(X))).sort((a,b)=>a-b)[rank-1];
 const limits={dual:1,calibrated_dual:cal(series),sequential:cal(cusum)};
 const out={};
 for(const [name,shift,local] of [['healthy',0,false],['local_strong',6,true],['common_strong',6,false],['local_weak',1.5,true],['common_weak',1.5,false]]){
  const a=Object.fromEntries(Object.keys(limits).map(k=>[k,{any:0,early:0,detected:0,delays:[]}]));
  for(let i=0;i<n;i++){const X=make(seeds.test+i).map((r,t)=>r.map((v,j)=>v+(t>=onset&&(!local||j===0)?shift:0))),d=series(X),c=cusum(X);for(const [k,v] of Object.entries({dual:d,calibrated_dual:d,sequential:c})){const j=v.findIndex(x=>x>limits[k]);if(j<0)continue;const t=start+j,q=a[k];q.any++;if(t<onset)q.early++;else{q.detected++;q.delays.push(t-onset)}}}
  out[name]=Object.fromEntries(Object.entries(a).map(([k,v])=>[k,{any:v.any,early:v.early,detected:v.detected,medianDelay:v.delays.length?median(v.delays):null}]));
 }
 return {n,seeds,start,onset,horizon:N-start,alpha,drift,limits,results:out,scope:'simulated iid Gaussian noise; first alarm before onset disqualifies a fault detection'};
}
