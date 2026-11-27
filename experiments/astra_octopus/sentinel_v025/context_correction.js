// Exploratory post-audit correction; NOT an unseen holdout.
// Same test cycles. Training/calibration labels used only for pump-no-leak selection.
function corrected(rows,seed=0,rate=0){
 const train=rows.slice(0,735).filter(r=>r.pump===0);
 const cal=rows.slice(735,1470);
 const test=rows.slice(1470);
 const idx=[0,1,2,4,5,8,9]; // omit degenerate PS4; TS1 context, TS2 not independent.
 const q=(a,p)=>quant(a,p);
 const fitModels=idx.map(j=>{
   const pairs=train.map(r=>[r.x[6],r.x[j]]).filter(v=>v.every(Number.isFinite));
   const slopes=[];
   for(let i=0;i<pairs.length;i++)for(let k=i+1;k<pairs.length;k++){
     const dt=pairs[k][0]-pairs[i][0];if(Math.abs(dt)>=1)slopes.push((pairs[k][1]-pairs[i][1])/dt);
   }
   const slope=med(slopes),intercept=med(pairs.map(([t,x])=>x-slope*t)),res=pairs.map(([t,x])=>x-slope*t-intercept);
   const scale=Math.max(1e-6,1.4826*med(res.map(Math.abs)),.05*(q(pairs.map(p=>p[1]),.95)-q(pairs.map(p=>p[1]),.05)),.001*Math.abs(med(pairs.map(p=>p[1]))));
   return {j,slope,intercept,scale};
 });
 const groups=[[0,1,2],[3,4],[5,6]];
 const norm=r=>fitModels.map(m=>Number.isFinite(r.x[6])&&Number.isFinite(r.x[m.j])?(r.x[m.j]-m.intercept-m.slope*r.x[6])/m.scale:NaN);
 const contrasts=z=>groups.flatMap(g=>{const a=g.map(i=>z[i]).filter(Number.isFinite);const m=a.length>=2?med(a):NaN;return g.map(i=>z[i]-m)});
 const relativeOffset=idx.map((_,j)=>med(train.map(r=>contrasts(norm(r))[j])));
 const relativeScale=relativeOffset.map((m,j)=>Math.max(.05,1.4826*med(train.map(r=>Math.abs(contrasts(norm(r))[j]-m)))));
 function scores(rs){
  let p=Array(14).fill(0),n=Array(14).fill(0),last=null;
  return rs.map(r=>{
   if(last===null||r.id!==last+1||(r.id-1)%15===0){p.fill(0);n.fill(0)}last=r.id;
   const z=norm(r),rel=contrasts(z).map((v,j)=>(v-relativeOffset[j])/relativeScale[j]),a=[...z,...rel];
   for(let j=0;j<a.length;j++){let v=a[j];if(!Number.isFinite(v)){p[j]=n[j]=0;continue}p[j]=Math.max(0,p[j]+v-.25);n[j]=Math.max(0,n[j]-v-.25)}
   const available=z.filter(Number.isFinite).length;
   if(available<5){p.fill(0);n.fill(0);return {r,s:null}}
   const v=a.map((x,j)=>Number.isFinite(x)?Math.max(p[j],n[j]):NaN);
   const max=a=>Math.max(...a.filter(Number.isFinite)),A=max(v.slice(0,7)),R=max(v.slice(7));
   const gs=groups.map(g=>max(g.map(i=>v[i]))).filter(Number.isFinite).sort((a,b)=>b-a);
   const P=max(z.map(Math.abs));
   // Need corroboration across two families; no causal independence claimed.
   return {r,s:{absolute_cusum:A,relative_cusum:Number.isFinite(R)?R:null,sequential_dual:Math.max(A,R),sentinel:gs.length>=2?gs[1]:null,pointwise:P}};
  });
 }
 const blocks=[];for(let i=0;i<cal.length;i+=15){const b=cal.slice(i,i+15);if(b.length===15&&b.every(r=>r.pump===0))blocks.push(scores(b))}
 const names=['absolute_cusum','relative_cusum','sequential_dual','sentinel','pointwise'];
 const thresholds=Object.fromEntries(names.map(k=>[k,q(blocks.map(b=>Math.max(...b.map(o=>o.s?.[k]).filter(Number.isFinite))),.95)]));
 let state=seed>>>0;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
 const observed=test.map(r=>({...r,x:r.x.map(v=>rate&&rand()<rate?NaN:v)}));
 const pred=scores(observed);
 const out={};
 for(const k of names){
   let a={tp:0,fp:0,tn:0,fn:0,unknownNormal:0,unknownFault:0,weak:0,severe:0,healthyAlarms:0,healthyUnknown:0};
   for(const {r,s} of pred){const v=s?.[k],unknown=typeof v!=='number'||!Number.isFinite(v),alarm=!unknown&&v>thresholds[k];if(r.pump){if(alarm){a.tp++;a[r.pump===1?'weak':'severe']++}else a.fn++;if(unknown)a.unknownFault++}else{if(unknown)a.unknownNormal++;else if(alarm)a.fp++;else a.tn++;if(r.cooler===100&&r.valve===100&&r.acc===130){a.healthyAlarms+=Number(alarm);a.healthyUnknown+=Number(unknown)}}}
   a.fpr=a.fp/(a.fp+a.tn);a.recall=a.tp/(a.tp+a.fn);a.coverage=(test.length-a.unknownFault-a.unknownNormal)/test.length;out[k]=a;
 }
 return {seed,rate,fitModels,relativeOffset,relativeScale,thresholds,out};
}
