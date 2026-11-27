// Transfer of conservation-inspired features across operating configurations.
// No fault labels in source; synthetic stressors are explicitly marked.
const RULE=Object.freeze({block:100,commission:6,sourceFit:0.5,q:.95,minFraction:.8,seed:270027});
function med(a){const b=a.filter(Number.isFinite).sort((a,b)=>a-b),k=b.length>>1;return b.length?(b.length%2?b[k]:(b[k-1]+b[k])/2):NaN}
function quant(a,p){const b=a.filter(Number.isFinite).sort((a,b)=>a-b);if(!b.length)throw Error('empty quantile');return b[Math.max(0,Math.ceil(p*b.length)-1)]}
function parse(raw){
 const lines=raw.trim().split(/\r?\n/),h=lines.shift().split(',');const cols=['pre1','pre2','flow1','flow2'];const ids=cols.map(k=>h.indexOf(k));if(ids.some(i=>i<0))throw Error('header');
 return lines.map((l,i)=>{const a=l.split(',');return {i,x:ids.map(j=>a[j]?.trim()?Number(a[j]):NaN)}});
}
function block(rows){
 let out=[];for(let i=0;i+RULE.block<=rows.length;i+=RULE.block){
  const rs=rows.slice(i,i+RULE.block),x=Array.from({length:4},(_,j)=>{const a=rs.map(r=>r.x[j]).filter(Number.isFinite);return a.length>=RULE.block*RULE.minFraction?med(a):NaN});out.push(x)
 }return out;
}
// Measurements must be same units, incompressible steady flow and no unmeasured branches.
// Sensor labels don't establish inlet/outlet direction; retain unsigned anomaly score.
function features(x){
 const [p1,p2,q1,q2]=x,good=Number.isFinite(q1)&&Number.isFinite(q2)&&q1>0&&q2>0;
 return {raw_flow:Number.isFinite(q1)?q1:NaN,absolute_difference:good?q1-q2:NaN,log_ratio:good?Math.log(q1/q2):NaN,pressure_difference:Number.isFinite(p1)&&Number.isFinite(p2)?p1-p2:NaN};
}
function fit(a,k){
 const v=a.map(x=>features(x)[k]).filter(Number.isFinite);
 if(v.length<3)throw Error('fit unavailable');const center=med(v);return {center};
}
function run(files){
 const names=['raw_flow','absolute_difference','log_ratio','pressure_difference'];
 const data=files.map(f=>block(parse(f.content)));
 const n=Math.floor(data[0].length*RULE.sourceFit),tr=data[0].slice(0,n),cal=data[0].slice(n);
 const source=Object.fromEntries(names.map(k=>{const m=fit(tr,k),threshold=Math.max(1e-9,quant(cal.map(x=>Math.abs(features(x)[k]-m.center)),RULE.q));return [k,{...m,threshold}]}));
 const results=[];
 for(let c=1;c<data.length;c++){
  const commissioning=data[c].slice(0,RULE.commission),test=data[c].slice(RULE.commission);
  for(const name of names)for(const mode of ['zero_shot','six_blocks']){
   const m=source[name],center=mode==='zero_shot'?m.center:fit(commissioning,name).center;
   for(const perturbation of ['none','flow1_minus_5pct','flow1_minus_10pct','flow2_plus_10pct','common_gain_10pct','missing_flow2']){
    let alarms=0,unknown=0;
    for(const orig of test){const x=orig.slice();if(perturbation==='flow1_minus_5pct')x[2]*=.95;if(perturbation==='flow1_minus_10pct')x[2]*=.9;if(perturbation==='flow2_plus_10pct')x[3]*=1.1;if(perturbation==='common_gain_10pct'){x[2]*=1.1;x[3]*=1.1}if(perturbation==='missing_flow2')x[3]=NaN;const v=features(x)[name];if(!Number.isFinite(v))unknown++;else if(Math.abs(v-center)>m.threshold)alarms++;}
    results.push({configuration:c+1,name,mode,perturbation,n:test.length,alarms,unknown,center,threshold:m.threshold});
   }
  }
 }
 return {rows:files.map(f=>parse(f.content).length),blocks:data.map(a=>a.length),source,results,notes:'100-sample medians; nominal 10 Hz; no actual fault events; injected sensor shifts not simulated physical leaks; no clock continuity verification'};
}
function tests(){
 const x=[1,0.5,2,1.9],a=features(x),b=features([1,0.5,2.2,2.09]);
 return {common_gain_invariance:Math.abs(a.log_ratio-b.log_ratio)<1e-12,missing_abstains:Number.isNaN(features([1,0.5,2,NaN]).log_ratio),zero_abstains:Number.isNaN(features([1,0.5,0,1]).log_ratio),absolute_changes:Math.abs(a.absolute_difference-b.absolute_difference)>1e-3};
}
