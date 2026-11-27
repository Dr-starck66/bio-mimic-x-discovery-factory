// ASTRA INDUSTRIAL SENTINEL v0.25. Fixed before retrieval of sensor observations.
// Target: pump leakage only; other component faults are nuisance conditions.
const RULE=Object.freeze({fitEnd:735,calEnd:1470,block:15,drift:.25,alpha:.05,minFraction:.75,scaleFloor:1e-6,targetReduction:.5});
const SENSORS=['PS1','PS2','PS3','PS4','FS1','FS2','TS1','TS2','EPS1','SE'];
const METHODS=['absolute_cusum','relative_cusum','sequential_dual','sentinel','pointwise_dual'];
function med(a){const b=a.filter(Number.isFinite).sort((a,b)=>a-b),k=b.length>>1;return b.length?(b.length%2?b[k]:(b[k-1]+b[k])/2):NaN}
function quant(a,p){const b=a.filter(Number.isFinite).sort((a,b)=>a-b);if(!b.length)throw Error('empty quantile');return b[Math.max(0,Math.ceil(p*b.length)-1)]}
function parse(raw){
 const l=raw.trim().split(/\r?\n/),h=l.shift().split(','),names=['cycle_id','cooler_condition_percent','valve_condition_percent','pump_leakage_class','accumulator_pressure_bar','stable_flag',...SENSORS.map(s=>s+'_mean')],ids=names.map(s=>h.indexOf(s));
 if(ids.some(i=>i<0))throw Error('schema');
 const rows=l.map((line,i)=>{const a=line.split(',');if(a.length!==h.length)throw Error('row width');const z=ids.map(j=>a[j].trim()===''?NaN:Number(a[j]));if(z[0]!==i+1||!([100,20,3].includes(z[1])&&[100,90,80,73].includes(z[2])&&[0,1,2].includes(z[3])&&[130,115,100,90].includes(z[4])&&[0,1].includes(z[5])))throw Error('label/order');return {id:z[0],cooler:z[1],valve:z[2],pump:z[3],acc:z[4],stable:z[5],x:z.slice(6)};});if(rows.length!==2205)throw Error('count');return rows;
}
function fit(rows){
 const center=SENSORS.map((_,j)=>med(rows.map(r=>r.x[j]))),scale=center.map((m,j)=>Math.max(RULE.scaleFloor,1.4826*med(rows.map(r=>Math.abs(r.x[j]-m)))));
 if(!center.every(Number.isFinite)||!scale.every(Number.isFinite))throw Error('fit missing');
 const z=r=>r.x.map((v,j)=>Number.isFinite(v)?(v-center[j])/scale[j]:NaN);
 // Relative terms are within pressure, flow and temperature modalities only.
 const groups=[[0,1,2,3],[4,5],[6,7]];
 function rel(a){let b=Array(8).fill(NaN);for(const g of groups){const vals=g.map(j=>a[j]).filter(Number.isFinite);if(vals.length<Math.max(2,Math.ceil(g.length*RULE.minFraction)))continue;const m=med(vals);for(const j of g)if(Number.isFinite(a[j]))b[j]=a[j]-m;}return b;}
 const off=Array.from({length:8},(_,j)=>med(rows.map(r=>rel(z(r))[j])));
 const rs=off.map((m,j)=>Math.max(.05,1.4826*med(rows.map(r=>Math.abs(rel(z(r))[j]-m)))));
 return {center,scale,off,rs,transform:r=>{const a=z(r),b=rel(a).map((v,j)=>(v-off[j])/rs[j]);return {a,b}}};
}
function sequence(rows,m){
 let p=Array(18).fill(0),n=Array(18).fill(0),out=[],last=null;
 for(const r of rows){
  if(last===null||r.id!==last+1||(r.id-1)%RULE.block===0){p.fill(0);n.fill(0)}last=r.id;
  const {a,b}=m.transform(r);const present=a.filter(Number.isFinite).length;
  // No forward filling: a missing channel resets only its own accumulation.
  const vals=[...a,...b];for(let j=0;j<vals.length;j++){let v=vals[j];if(!Number.isFinite(v)){p[j]=n[j]=0;continue}p[j]=Math.max(0,p[j]+v-RULE.drift);n[j]=Math.max(0,n[j]-v-RULE.drift);}
  if(present<Math.ceil(SENSORS.length*RULE.minFraction)){p.fill(0);n.fill(0);out.push({r,s:null});continue}
  const v=vals.map((x,j)=>Number.isFinite(x)?Math.max(p[j],n[j]):NaN);
  const max=a=>Math.max(...a.filter(Number.isFinite));const A=max(v.slice(0,10)),R=max(v.slice(10));const RR=Number.isFinite(R)?R:0;
  // Support-weighted fusion: corroborating modalities rather than a single extreme.
  // Power and efficiency are one group; groups are not independent physical witnesses.
  const groupScores=[[0,1,2,3],[4,5],[6,7],[8,9]].map(g=>max(g.map(j=>v[j])));
  const sorted=groupScores.filter(Number.isFinite).sort((a,b)=>b-a);
  const point=Math.max(max(a.map(Math.abs)),max(b.map(Math.abs)));
  const s={absolute_cusum:A,relative_cusum:Number.isFinite(R)?R:null,sequential_dual:Math.max(A,RR),sentinel:sorted.length>=3?Math.max(sorted[1],RR*.5):null,pointwise_dual:point};
  out.push({r,s});
 }return out;
}
function evaluate(rows,seed=0,rate=0){
 const tr=rows.slice(0,RULE.fitEnd).filter(r=>r.pump===0),cal=rows.slice(RULE.fitEnd,RULE.calEnd),test=rows.slice(RULE.calEnd);
 const m=fit(tr);const cleanBlocks=[];
 for(let i=0;i<cal.length;i+=RULE.block){const b=cal.slice(i,i+RULE.block);if(b.length===RULE.block&&b.every(r=>r.pump===0))cleanBlocks.push(b)}
 if(cleanBlocks.length<10)throw Error('insufficient healthy calibration blocks');
 const maxima=cleanBlocks.map(b=>sequence(b,m));
 const thresholds=Object.fromEntries(METHODS.map(k=>[k,quant(maxima.map(b=>Math.max(...b.map(o=>o.s?.[k]).filter(Number.isFinite))),1-RULE.alpha)]));
 let state=seed>>>0;const rand=()=>{state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296};
 const observed=test.map(r=>({...r,x:r.x.map(v=>rate&&rand()<rate?NaN:v)}));
 const scored=sequence(observed,m);const out={};
 for(const k of METHODS){
 const r={tp:0,fp:0,tn:0,fn:0,unknownNormal:0,unknownFault:0,bySeverity:{0:{n:0,alarms:0,unknown:0},1:{n:0,alarms:0,unknown:0},2:{n:0,alarms:0,unknown:0}},fullHealthy:{n:0,alarms:0,unknown:0},byStability:{0:{n:0,alarms:0,unknown:0},1:{n:0,alarms:0,unknown:0}}};
 for(const o of scored){const y=o.r.pump,stable=o.r.stable,a=o.s?.[k],unknown=typeof a!=='number'||!Number.isFinite(a),alarm=!unknown&&a>thresholds[k],b=r.bySeverity[y],c=r.byStability[stable];for(const d of [b,c,...(y===0&&o.r.cooler===100&&o.r.valve===100&&o.r.acc===130?[r.fullHealthy]:[])]){d.n++;d.alarms+=Number(alarm);d.unknown+=Number(unknown)}
 if(y===0){if(unknown)r.unknownNormal++;else if(alarm)r.fp++;else r.tn++}else{if(unknown)r.unknownFault++;if(alarm)r.tp++;else r.fn++}}
 r.fpr=r.fp/(r.fp+r.tn);r.recall=r.tp/(r.tp+r.fn);r.coverage=(test.length-r.unknownFault-r.unknownNormal)/test.length;
 out[k]=r;
 }
 return {fit:tr.length,cal:cal.length,calCleanBlocks:cleanBlocks.length,test:test.length,rate,seed,thresholds,out};
}
