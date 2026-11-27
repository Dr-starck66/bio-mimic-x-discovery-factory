// Exploratory physics-guided pump diagnosis. UCI previously exposed, no blind validation.
// Reuse sentinel_v025 parse(), med(), quant(). Cycle means, NOT exact energy integral.
const PHYS_RULE=Object.freeze({lambda:.03,iterations:350,step:.15,q:.95,minPositiveRecall:.95,maskSeeds:10});
const methods=['raw_logistic','physical_logistic','raw_plus_physics','efficiency_proxy','published_SE','flow_only'];
function features(r){
 const [p1,p2,p3,p4,q1,q2,t1,t2,e,se]=r.x;
 const pos=(...a)=>a.every(v=>Number.isFinite(v)&&v>0);
 const log=v=>pos(v)?Math.log(v):NaN;
 const ratio=(a,b)=>pos(a,b)?Math.log(a/b):NaN;
 // p1*q1/0.6 gives watts: use explicit SI conversion.
 const hydraulic=pos(p1,q1,e)?p1*q1*(5/3)/e:NaN;
 const phys=[log(hydraulic),ratio(p2,p1),ratio(q1,q2),ratio(e,p1),ratio(p3,p1)];
 return {raw_logistic:[p1,p2,p3,p4,q1,q2,t1,t2,e],physical_logistic:phys,raw_plus_physics:[p1,p2,p3,p4,q1,q2,t1,t2,e,...phys],efficiency_proxy:[-log(hydraulic)],published_SE:[-se],flow_only:[-q1]};
}
function trainLogistic(rows,name){
 const v=rows.map(r=>({x:features(r)[name],y:Number(r.pump>0)})).filter(r=>r.x.every(Number.isFinite));
 if(!v.length||!v.some(r=>r.y)||!v.some(r=>!r.y))throw Error('class coverage');
 const d=v[0].x.length,center=Array.from({length:d},(_,j)=>med(v.map(r=>r.x[j]))),scale=center.map((m,j)=>Math.max(1e-8,1.4826*med(v.map(r=>Math.abs(r.x[j]-m))),.01*(quant(v.map(r=>r.x[j]),.95)-quant(v.map(r=>r.x[j]),.05))));
 const standard=x=>x.map((a,j)=>Math.max(-20,Math.min(20,(a-center[j])/scale[j])));
 const data=v.map(r=>({...r,x:standard(r.x)}));let w=Array(d).fill(0),b=0;
 const n1=data.filter(r=>r.y).length,n0=data.length-n1;
 for(let k=0;k<PHYS_RULE.iterations;k++){
  const g=Array(d).fill(0);let gb=0;
  for(const r of data){const s=b+r.x.reduce((s,x,j)=>s+x*w[j],0),p=1/(1+Math.exp(-Math.max(-40,Math.min(40,s)))),e=(p-r.y)/(2*(r.y?n1:n0));gb+=e;for(let j=0;j<d;j++)g[j]+=e*r.x[j];}
  b-=PHYS_RULE.step*gb;for(let j=0;j<d;j++)w[j]-=PHYS_RULE.step*(g[j]+PHYS_RULE.lambda*w[j]);
 }
 return {center,scale,w,b,score:r=>{const x=features(r)[name];return x.every(Number.isFinite)?b+standard(x).reduce((s,a,j)=>s+a*w[j],0):NaN}};
}
function runPhysics(rows,rate=0,seed=0){
 const splits=[{name:'previous_order',tr:rows.slice(0,735),ca:rows.slice(735,1470),te:rows.slice(1470)},...[[3,20,100],[20,100,3],[100,3,20]].map(([a,b,c])=>({name:'cooler_'+c,tr:rows.filter(r=>r.cooler===a),ca:rows.filter(r=>r.cooler===b),te:rows.filter(r=>r.cooler===c)}))];
 let st=seed>>>0;const rand=()=>{st=(Math.imul(st,1664525)+1013904223)>>>0;return st/4294967296};
 const out={};
 for(const {name,tr,ca,te} of splits){
  const row={n:[tr.length,ca.length,te.length],methods:{}},test=te.map(r=>({...r,x:r.x.map(v=>rate&&rand()<rate?NaN:v)}));
  for(const k of methods){
    const model=k.endsWith('logistic')||k==='raw_plus_physics'?trainLogistic(tr,k):{score:r=>features(r)[k][0]};
    const cal=ca.map(r=>({s:model.score(r),y:r.pump})).filter(r=>Number.isFinite(r.s));
    const neg=cal.filter(r=>!r.y).map(r=>r.s),weak=cal.filter(r=>r.y===1).map(r=>r.s),strong=cal.filter(r=>r.y===2).map(r=>r.s);
    // '>= threshold' detection; calibration sensitivity per severity at least 95%.
    const recallThreshold=a=>[...a].sort((a,b)=>a-b)[Math.floor(a.length*(1-PHYS_RULE.minPositiveRecall))];
    const th={fpr5:quant(neg,PHYS_RULE.q),recall95:Math.min(recallThreshold(weak),recallThreshold(strong))};
    const evaluate=(rows,threshold,strict)=>{let tp=0,fp=0,tn=0,fn=0,un=0,uf=0,w=0,s=0,wn=0,sn=0;for(const r of rows){const v=model.score(r),known=Number.isFinite(v),alarm=known&&(strict?v>threshold:v>=threshold);if(r.pump){if(r.pump===1)wn++;else sn++;if(!known)uf++;if(alarm){tp++;if(r.pump===1)w++;else s++}else fn++}else if(!known)un++;else if(alarm)fp++;else tn++;}return {tp,fp,tn,fn,unknownNormal:un,unknownFault:uf,weak:[w,wn],severe:[s,sn],fpr:fp/(fp+tn),recall:tp/(tp+fn),coverage:(rows.length-un-uf)/rows.length};};
    row.methods[k]={thresholds:th,cal:{fpr5:evaluate(ca,th.fpr5,true),recall95:evaluate(ca,th.recall95,false)},test:{fpr5:evaluate(test,th.fpr5,true),recall95:evaluate(test,th.recall95,false)},...(model.w?{coefficients:model.w,center:model.center,scale:model.scale,intercept:model.b}:{})};
  }out[name]=row;
 }return out;
}
