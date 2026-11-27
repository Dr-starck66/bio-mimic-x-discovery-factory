// Exploratory missing-sensor fallback: fixed model priority; never impute a missing physical variable.
function maskedPhysics(rows){
 const tr=rows.slice(0,735),ca=rows.slice(735,1470),te=rows.slice(1470);
 const priority=['raw_plus_physics','efficiency_proxy','published_SE','flow_only'];
 const fits=Object.fromEntries(priority.map(k=>[k,k.endsWith('logistic')||k==='raw_plus_physics'?trainLogistic(tr,k):{score:r=>features(r)[k][0]}]));
 const thresholds=Object.fromEntries(priority.map(k=>{const a=ca.map(r=>({v:fits[k].score(r),y:r.pump}));return [k,Math.min(...[1,2].map(y=>{const v=a.filter(r=>r.y===y&&Number.isFinite(r.v)).map(r=>r.v).sort((a,b)=>a-b);return v[Math.floor(.05*v.length)]}))]}));
 const results=[];
 for(const rate of [0,.1,.25])for(let i=0;i<(rate?10:1);i++){
  let state=(94101+i)>>>0;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
  const masked=te.map(r=>({...r,x:r.x.map(v=>rate&&rand()<rate?NaN:v)}));
  for(const name of [...priority,'fallback']){
   const counts={tp:0,fp:0,tn:0,fn:0,unknownNormal:0,unknownFault:0,route:{}};
   for(const r of masked){
    const k=name==='fallback'?priority.find(k=>Number.isFinite(fits[k].score(r))):name;
    const value=k?fits[k].score(r):NaN,known=Number.isFinite(value),alarm=known&&value>=thresholds[k];
    if(known)counts.route[k]=(counts.route[k]||0)+1;
    if(r.pump){if(!known)counts.unknownFault++;if(alarm)counts.tp++;else counts.fn++;}else if(!known)counts.unknownNormal++;else if(alarm)counts.fp++;else counts.tn++;
   }
   results.push({name,rate,seed:94101+i,...counts,recall:counts.tp/328,fpr:counts.fp/(counts.fp+counts.tn),coverage:(735-counts.unknownNormal-counts.unknownFault)/735});
  }
 }
 const summary={};for(const rate of [0,.1,.25])summary[rate]=Object.fromEntries([...priority,'fallback'].map(name=>{const a=results.filter(r=>r.rate===rate&&r.name===name);return [name,Object.fromEntries(['recall','fpr','coverage','fp','tp','unknownFault','unknownNormal'].map(k=>[k,a.reduce((s,r)=>s+r[k],0)/a.length]))]}));
 return {priority,thresholds,summary,results};
}
