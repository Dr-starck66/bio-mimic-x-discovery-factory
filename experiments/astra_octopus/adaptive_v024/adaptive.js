// ASTRA adaptive fusion v0.24. Frozen before full UTK CSV retrieval.
const RULE=Object.freeze({fit:.5,cal:.25,minNormal:40,q:.99,scaleFloor:.05,window:5,persistence:3,context:"voltage exact rounded 0.1 V",gapSeconds:180,targetFPRReduction:.5});
function median(a){let b=[...a].sort((a,b)=>a-b),k=b.length>>1;return b.length?(b.length%2?b[k]:(b[k-1]+b[k])/2):NaN}
function quant(a,p){let b=a.filter(Number.isFinite).sort((a,b)=>a-b);if(!b.length)throw Error('empty quantile');return b[Math.max(0,Math.ceil(p*b.length)-1)]}
function parse(raw){
 const lines=raw.trim().replace(/^\uFEFF/,'').split(/\r?\n/),h=lines.shift().split(',');
 const names=Array.from({length:4},(_,i)=>'Accelerometer_'+(i+1)+'_RMS_g').concat(['Thermocouple_1_Temperature_F','Thermocouple_2_Temperature_F']);
 const idx=names.map(n=>h.indexOf(n)),ti=h.indexOf('datetime'),vi=h.indexOf('voltage'),si=h.indexOf('status');
 if([...idx,ti,vi,si].some(i=>i<0))throw Error('schema '+h.join(','));
 let rows=lines.map((l,i)=>{const a=l.split(',');if(a.length!==h.length)throw Error('width');const t=Date.parse(a[ti].replace(' ','T')+'Z')/1000;const v=a[vi].trim()?Number(a[vi]):NaN;const state=a[si].trim().toLowerCase();const x=idx.map((j,k)=>{let n=a[j].trim()?Number(a[j]):NaN;return k<4?(n>0?Math.log(n):NaN):n});return {i,t,v,state,x,ctx:Number.isFinite(v)?String(Math.round(v*10)/10):null}});if(rows.some(r=>!Number.isFinite(r.t)||!r.state))throw Error('timestamp/status');
 rows.sort((a,b)=>a.t-b.t||a.i-b.i);return rows;
}
function split(rows){
 const groups={};for(const r of rows)if(r.state==='baseline'&&r.ctx!==null)(groups[r.ctx]??=[]).push(r);
 const fit=[],cal=[],test=[],supported=[];
 for(const [k,g] of Object.entries(groups)){if(g.length<RULE.minNormal)continue;const a=Math.floor(g.length*RULE.fit),b=Math.floor(g.length*(RULE.fit+RULE.cal));fit.push(...g.slice(0,a));cal.push(...g.slice(a,b));supported.push(k);}
 const excluded=new Set([...fit,...cal].map(r=>r.i));
 for(const r of rows)if(!excluded.has(r.i))test.push(r);
 return {fit,cal,test,supported};
}
function model(rows){
 const center=Array.from({length:6},(_,j)=>median(rows.map(r=>r.x[j]).filter(Number.isFinite)));
 const scale=center.map((m,j)=>Math.max(RULE.scaleFloor,1.4826*median(rows.map(r=>Math.abs(r.x[j]-m)).filter(Number.isFinite))));
 if(!center.every(Number.isFinite)||!scale.every(Number.isFinite))throw Error('invalid fit');
 return {center,scale};
}
function residual(r,m){
 if(!m||r.x.some(x=>!Number.isFinite(x)))return null;
 const z=r.x.map((v,j)=>(v-m.center[j])/m.scale[j]),v=z.slice(0,4),t=z.slice(4);
 const rel=Math.max(...v.map(x=>Math.abs(x-median(v))));
 return {A:Math.max(...z.map(Math.abs)),R:rel,M:Math.sqrt(z.reduce((s,x)=>s+x*x,0)/6),V:Math.abs(median(v)),T:Math.max(...t.map(Math.abs))};
}
function seq(rows,fn){
 let out=[],buf=[],pers=[],last=null;
 for(const r of [...rows].sort((a,b)=>a.t-b.t||a.i-b.i)){
 const z=fn(r);
 if(last===null||r.t-last.t>RULE.gapSeconds||r.t<=last.t||r.ctx!==last.ctx||r.i!==last.i+1){buf=[];pers=[]}
 last=r;
 if(!z||!Object.values(z).every(Number.isFinite)){buf=[];pers=[];out.push({r,p:null});continue}
 buf.push(z);if(buf.length>RULE.window)buf.shift();
 const s=Object.fromEntries(Object.keys(z).map(k=>[k,median(buf.map(a=>a[k]))]));
 pers.push(s);if(pers.length>RULE.persistence)pers.shift();
 out.push({r,p:pers.length<RULE.persistence?null:Object.fromEntries(Object.keys(z).map(k=>[k,Math.min(...pers.map(a=>a[k]))]))});
 }return out;
}
function run(rows){
 const {fit,cal,test,supported}=split(rows);if(!fit.length||!cal.length)throw Error('no commissioning');
 const global=model(fit),local=Object.fromEntries(supported.map(k=>[k,model(fit.filter(r=>r.ctx===k))]));
 const c0=cal.map(r=>residual(r,global)).filter(Boolean),c1=cal.map(r=>residual(r,local[r.ctx])).filter(Boolean);
 function scale(c){return {A:Math.max(.001,quant(c.map(z=>z.A),.95)),R:Math.max(.001,quant(c.map(z=>z.R),.95)),M:Math.max(.001,quant(c.map(z=>z.M),.95))}}
 const s0=scale(c0),s1=scale(c1);
 function scores(r){
 const a=residual(r,global),b=residual(r,local[r.ctx]);if(!a||!b)return null;
 return {absolute:a.A,relative:a.R,multivariate:a.M,parent:Math.max(a.A/s0.A,a.R/s0.R),adaptive:Math.max(b.A/s1.A,b.R/s1.R),conditional_absolute:b.A,conditional_relative:b.R,conditional_multivariate:b.M};
 }
 // Evaluate same support for all methods; unknown faults count as misses, unknown normals separately.
 const c=seq(cal,scores).filter(x=>x.p),keys=Object.keys(c[0].p);
 const thresholds=Object.fromEntries(keys.map(k=>[k,quant(c.map(x=>x.p[k]),RULE.q)]));
 const result=Object.fromEntries(keys.map(k=>[k,{tp:0,fp:0,tn:0,fn:0,unknownNormal:0,unknownFault:0,byState:{}}]));
 for(const {r,p} of seq(test,scores)){
  const normal=r.state==='baseline';
  for(const k of keys){let a=result[k],b=a.byState[r.state]??={n:0,alarms:0,unknown:0};b.n++;
    if(!p){b.unknown++;if(normal)a.unknownNormal++;else{a.unknownFault++;a.fn++;}continue}
    const alarm=p[k]>thresholds[k];if(alarm)b.alarms++;if(normal){if(alarm)a.fp++;else a.tn++;}else{if(alarm)a.tp++;else a.fn++}
  }
 }
 return {rows:rows.length,fit:fit.length,cal:cal.length,calScored:c.length,test:test.length,supported,thresholds,result};
}
// Diagnosis is separate from detector. Witness must be independently validated;
// identical measured shifts cannot distinguish physical change and sensor bias.
function classify({contextKnown,withinExpected,alarm,pattern,witness}){
 if(!contextKnown||typeof alarm!=='boolean')return 'unknown';
 if(!alarm)return withinExpected?'compatible_normal':'unknown';
 if(witness==='physical')return pattern==='local'?'individual_physical_candidate':'collective_physical_candidate';
 if(witness==='sensor')return 'sensor_bias_candidate';
 return 'ambiguous_physical_or_sensor';
}
