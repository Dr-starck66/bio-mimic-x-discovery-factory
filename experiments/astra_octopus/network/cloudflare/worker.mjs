import capsule from '../capsule.json' with {type:'json'};
const PIN='6a905af56a0c3aef3cb5b8c4ce6adbc96fd37b87583c568e704e8511bbb2641e';
const enc=new TextEncoder();
const canon=x=>Array.isArray(x)?'['+x.map(canon).join(',')+']':x!==null&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}':JSON.stringify(x);
const hex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,'0')).join('');
const bytes=s=>Uint8Array.from(s.match(/../g),v=>parseInt(v,16));
const hash=async s=>hex(await crypto.subtle.digest('SHA-256',enc.encode(s)));
const need=(b,m)=>{if(!b)throw Error(m)};
async function verifyStage(raw,reg,run,stage){
  const c=JSON.parse(raw), m=c.message,sep=',"message":',i=raw.indexOf(sep);
  need(i>0&&raw.endsWith('}'),'encoding');const msg=raw.slice(i+sep.length,-1);
  need(raw==='{"attestations":'+canon(c.attestations)+sep+msg+'}','fields');
  need(m.domain==='ASTRA-SCIENTIFIC-CONSENSUS-v0.16'&&m.run===run&&m.stage===stage,'context');
  const valid=new Set();for(const a of c.attestations){
    const k=reg[a.signer];if(!k||valid.has(a.signer)||!/^[0-9a-f]{128}$/.test(a.signature))continue;
    const key=await crypto.subtle.importKey('raw',bytes(k),{name:'Ed25519'},false,['verify']);
    if(await crypto.subtle.verify('Ed25519',key,bytes(a.signature),enc.encode(msg)))valid.add(a.signer);
  }need(valid.size>=3,'quorum');return {body:m.body,count:valid.size};
}
export async function auditEdge(c){
  const reg=c.registry,ks=Object.values(reg);need(ks.length===4&&new Set(ks).size===4&&ks.every(k=>/^[0-9a-f]{64}$/.test(k))&&await hash(canon(reg))===PIN,'registry');
  const [p,s,v]=await Promise.all([verifyStage(c.pre,reg,c.run,'preregister'),verifyStage(c.sub,reg,c.run,'predictions'),verifyStage(c.certificate,reg,c.run,'verdict')]);
  const ph=await hash(c.pre),sh=await hash(c.sub);need(p.body.registry_sha256===PIN&&s.body.preregistration_sha256===ph&&v.body.preregistration_sha256===ph&&v.body.submission_sha256===sh,'chain');
  const rule=p.body.rule,r=v.body.result;need(rule.tolerance===0&&rule.min_gain===.01&&canon(rule.tasks)===canon(['education','inflation']),'rule');need(canon(r.rows.map(x=>x.task))===canon(rule.tasks),'tasks');
  const regressions=[],gains=[];for(const x of r.rows){need(['candidate','parent','reference','lower_parent','lower_reference'].every(k=>Number.isFinite(x[k]))&&x.candidate>=0&&x.parent>0&&x.reference>0,'metrics');const b=Math.min(x.parent,x.reference);if(x.candidate>b)regressions.push(x.task);if(x.candidate<=.99*b&&Math.min(x.lower_parent,x.lower_reference)>0)gains.push(x.task);}
  const decision=regressions.length===0&&gains.length>0?'PROMOTE':'REJECT';need(decision===r.decision&&canon(regressions)===canon(r.regressions)&&canon(gains)===canon(r.confirmed_gain_tasks),'gate');
  return {status:'VERIFIED_HISTORICAL',run:c.run,decision,signatures:[p.count,s.count,v.count],registry_sha256:PIN,opening_verified:false,rmse_recomputed:false,bootstrap_recomputed:false,independent_authority:false};
}
export default {async fetch(req){const url=new URL(req.url);if(req.method!=='GET')return new Response('Method not allowed',{status:405});if(!['/','/health','/api/verify'].includes(url.pathname))return new Response('Not found',{status:404});try{return Response.json(await auditEdge(capsule),{headers:{'cache-control':'no-store'}})}catch{return Response.json({status:'verification_failed'},{status:500})}}};
