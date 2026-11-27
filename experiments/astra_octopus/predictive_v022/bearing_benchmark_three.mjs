function benchmark(raw){
 const median=a=>{let s=[...a].sort((a,b)=>a-b),k=s.length>>1;return s.length%2?s[k]:(s[k-1]+s[k])/2};
 const quant=(a,p)=>[...a].sort((a,b)=>a-b)[Math.min(a.length-1,Math.ceil(p*a.length)-1)];
 const norm=(a,train=100)=>{let b=a.slice(0,train),m=median(b),s=Math.max(1.4826*median(b.map(x=>Math.abs(x-m))),1e-6);return a.map(x=>(x-m)/s)};
 const smooth=a=>a.map((_,i)=>median(a.slice(Math.max(0,i-4),i+1)));
 const ewma=a=>{let x=0;return a.map(v=>x=.2*v+.8*x)};
 const methods=["rms","ewma","kurtosis","multifeature","peer_ratio","astra"];
 const results=[];const failures={1:[3,4],2:[1],3:[3]};
 for(const [run,files] of Object.entries(raw)){
   let arrays=files.map(f=>{let lines=f.content.trim().split(/\r?\n/);if(lines.shift()!==",Max,Min,Mean,std,RMS,Skewness,Kurtosis,Crest Factor,Form Factor")throw Error("header");return lines.map(l=>{let z=l.split(",");let t=Date.parse(z[0].replace(" ","T")+"Z"),r=+z[5],k=+z[7]+3,c=+z[8];if(z.length!==10||![t,r,k,c].every(Number.isFinite)||r<=0||k<=0||c<=0)throw Error("row");return {t,r,k,c}})});
   let n=arrays[0].length;if(n!==({1:2156,2:984,3:6324}[run])||arrays.some(a=>a.length!==n||a.some((x,i)=>x.t!==arrays[0][i].t||(i>0&&x.t<a[i-1].t))))throw Error("alignment");
   let original=n;arrays=arrays.map(a=>a.filter((x,i)=>i===0||x.t>a[i-1].t));n=arrays[0].length;let duplicate=original-n;
   let base=arrays.map(a=>median(a.slice(0,100).map(x=>x.r)));
   while(n>200&&arrays.every((a,j)=>a[n-1].r<.1*base[j]))n--;
   const logR=arrays.map(a=>a.slice(0,n).map(x=>Math.log(x.r)));
   const centered=logR.map(a=>a.map(v=>v-median(a.slice(0,100))));
   const op=[0];for(let i=1;i<n;i++){let d=(arrays[0][i].t-arrays[0][i-1].t)/3600000;op.push(op[i-1]+(d>.25?1/6:d))}
   for(let b=0;b<4;b++){
     const a=arrays[b].slice(0,n),r=norm(logR[b]),k=norm(a.map(x=>Math.log(x.k))),c=norm(a.map(x=>Math.log(x.c))),peer=norm(centered[b].map((v,i)=>v-median(centered.filter((_,j)=>j!==b).map(x=>x[i]))));
     const scores={rms:smooth(r),ewma:ewma(r),kurtosis:smooth(k),multifeature:smooth(r.map((v,i)=>Math.sqrt(v*v+k[i]*k[i]+c[i]*c[i]))),peer_ratio:smooth(peer),astra:smooth(peer.map((v,i)=>Math.max(0,v,Math.sqrt((Math.max(0,v)**2+k[i]**2+c[i]**2)/3))))};
     const row={run:+run,bearing:b+1,failed:failures[run].includes(b+1),n,duplicate,excluded_shutdown:original-duplicate-n,monitor_hours:op[n-1]-op[202],methods:{}};
     for(const m of methods){const s=scores[m],persist=s.map((v,i)=>i<2?0:Math.min(v,s[i-1],s[i-2])),th=quant(persist.slice(102,200),.99);let active=persist.map((v,i)=>i>=202&&v>th),episodes=0,first=null,last=null;for(let i=202;i<n;i++)if(active[i]){if(first===null)first=i;last=i;if(!active[i-1])episodes++}
       let start=null;if(last!==null&&last>=n-6){start=last;while(start>202&&active[start-1])start--;}
       row.methods[m]={threshold:th,episodes,first_snapshot:first,first_lead_hours:first===null?null:op[n-1]-op[first],sustained_snapshot:start,sustained_lead_hours:start===null?null:op[n-1]-op[start],alarm_fraction:active.filter(Boolean).length/(n-202)};
     }results.push(row);
   }
 }return {settings:{train:100,calibration:100,quantile:.99,persistence:3,smoothing:5,clock:"gaps >15min count 10min; endpoint is test stop",no_known_failure:"proxy only"},results,summary:Object.fromEntries(methods.map(m=>{let f=results.filter(r=>r.failed),h=results.filter(r=>!r.failed);return [m,{sustained_4h:f.filter(r=>r.methods[m].sustained_lead_hours>=4).length,failed_total:f.length,proxy_episodes:h.reduce((s,r)=>s+r.methods[m].episodes,0),proxy_hours:h.reduce((s,r)=>s+r.monitor_hours,0),leads:f.map(r=>({run:r.run,bearing:r.bearing,first:r.methods[m].first_lead_hours,sustained:r.methods[m].sustained_lead_hours}))}]}))};
}
export {benchmark};
