// ASTRA DUAL INVARIANT v0.23: empirical residuals, not physical conservation laws.
const RULE=Object.freeze({train:100,calibration:100,quantile:.99,window:5,persistence:3,ewma:.2,gapFactor:3,eventWindowSeconds:60});
function med(a){const b=[...a].sort((a,b)=>a-b),k=b.length>>1;return b.length?(b.length%2?b[k]:(b[k-1]+b[k])/2):NaN}
function quant(a,p){const b=a.filter(Number.isFinite).sort((a,b)=>a-b);if(!b.length)throw Error('empty calibration');return b[Math.max(0,Math.ceil(p*b.length)-1)]}
function fitScore(X,t){
 const N=RULE.train,C=N+RULE.calibration,d=X[0].length;
 if(X.length<=C||d<3||t.length!==X.length||X.some(r=>r.length!==d)||t.some((x,i)=>!Number.isFinite(x)||(i&&x<=t[i-1])))throw Error('shape/time');
 const initial=X.slice(0,N),centers=Array.from({length:d},(_,j)=>med(initial.map(r=>r[j]).filter(Number.isFinite))),scales=centers.map((m,j)=>Math.max(1e-6,1.4826*med(initial.map(r=>Math.abs(r[j]-m)).filter(Number.isFinite))));
 if(!centers.every(Number.isFinite)||!scales.every(Number.isFinite))throw Error('baseline');
 const gap=RULE.gapFactor*med(t.slice(1,N).map((v,i)=>v-t[i]));const reset=t.map((v,i)=>i===0||v-t[i-1]>gap);
 const z=X.map(r=>r.map((v,j)=>Number.isFinite(v)?(v-centers[j])/scales[j]:NaN));
 const abs=[],rel=[],multi=[],mean=[],ewma=[];let e=0;
 for(let i=0;i<z.length;i++){
   const a=z[i].filter(Number.isFinite);if(a.length<Math.max(3,Math.ceil(.75*d))){abs.push(NaN);rel.push(NaN);multi.push(NaN);mean.push(NaN);ewma.push(NaN);e=0;reset[i]=true;continue}
   const m=med(a);abs.push(Math.max(...a.map(Math.abs)));rel.push(Math.max(...a.map(v=>Math.abs(v-m))));multi.push(Math.sqrt(a.reduce((s,v)=>s+v*v,0)/a.length));mean.push(Math.abs(m));e=(reset[i]?0:e)*.8+.2*abs[i];ewma.push(e);
 }
 function smooth(a){return a.map((v,i)=>{if(!Number.isFinite(v))return NaN;let k=i;while(k>Math.max(0,i-4)&&!reset[k]&&Number.isFinite(a[k-1]))k--;return med(a.slice(k,i+1))})}
 const A=smooth(abs),R=smooth(rel),M=smooth(multi),G=smooth(mean);
 const sa=Math.max(quant(A.slice(N,C),.95),1e-6),sr=Math.max(quant(R.slice(N,C),.95),1e-6);
 const D=A.map((v,i)=>Math.max(v/sa,R[i]/sr));
 const scores={absolute:A,relative:R,dual:D,multivariate:M,ewma,common:G};
 const out={};
 for(const [name,a] of Object.entries(scores)){
   const p=a.map((v,i)=>i<2||reset[i]||reset[i-1]||![v,a[i-1],a[i-2]].every(Number.isFinite)?NaN:Math.min(v,a[i-1],a[i-2]));
   const threshold=quant(p.slice(N+2,C),RULE.quantile);
   out[name]={threshold,alarm:p.map((v,i)=>i<C+2||!Number.isFinite(v)?null:v>threshold),score:p};
 }
 return out;
}
function parseCSV(raw){
 const lines=raw.trim().replace(/^\uFEFF/,'').split(/\r?\n/);const sep=lines[0].includes(';')?';':',',head=lines.shift().split(sep);
 const cols=['Accelerometer1RMS','Accelerometer2RMS','Current','Pressure','Temperature','Thermocouple','Voltage','RateRMS'];
 const ids=cols.map(c=>head.indexOf(c)),ti=head.indexOf('datetime'),ai=head.indexOf('anomaly'),ci=head.indexOf('changepoint');
 if(ids.some(i=>i<0)||ti<0)throw Error('header');
 const X=[],t=[],labels=[],changes=[];
 for(const line of lines){const a=line.split(sep);if(a.length!==head.length)throw Error('row length');t.push(Date.parse(a[ti].replace(' ','T')+'Z')/1000);X.push(ids.map(i=>a[i].trim()===''?NaN:Number(a[i])));labels.push(ai<0?0:Number(a[ai]));changes.push(ci<0?0:Number(a[ci]));}
 if(labels.some(x=>x!==0&&x!==1)||changes.some(x=>x!==0&&x!==1))throw Error('labels');
 return {X,t,labels,changes};
}
function evaluate(d){
 const {X,t,labels,changes}=d,C=RULE.train+RULE.calibration+2;
 const contaminated=labels.slice(0,C).some(Boolean)||changes.slice(0,C).some(Boolean);
 if(contaminated)return {eligible:false,reason:'labelled anomaly or change during commissioning',rows:X.length};
 const scores=fitScore(X,t);const out={eligible:true,rows:X.length,methods:{}};
 for(const [m,v] of Object.entries(scores)){
   let tp=0,fp=0,tn=0,fn=0,unknown=0,episodes=0;const delays=[];let events=0;
   for(let i=C;i<X.length;i++){
     if(v.alarm[i]===null){unknown++;if(labels[i])fn++;continue}
     if(labels[i]){if(v.alarm[i])tp++;else fn++;}else{if(v.alarm[i])fp++;else tn++;}
     if(v.alarm[i]&&!v.alarm[i-1]&&!labels[i])episodes++;
     if(changes[i]){events++;let k=i;while(k<X.length&&t[k]-t[i]<=RULE.eventWindowSeconds&&!(v.alarm[k]===true&&v.alarm[k-1]!==true))k++;delays.push(k<X.length&&t[k]-t[i]<=RULE.eventWindowSeconds?t[k]-t[i]:null)}
   }
   out.methods[m]={tp,fp,tn,fn,unknown,episodes,events,delays,threshold:v.threshold};
 }return out;
}
