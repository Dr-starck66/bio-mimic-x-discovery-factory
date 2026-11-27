import {createHash,createPublicKey,verify} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {createServer} from 'node:http';
import {fileURLToPath} from 'node:url';
const ROOT=new URL('.',import.meta.url);
const PIN='6a905af56a0c3aef3cb5b8c4ce6adbc96fd37b87583c568e704e8511bbb2641e';
const H=s=>createHash('sha256').update(s).digest('hex');
const need=(b,m)=>{if(!b)throw Error(m)};
const canon=x=>Array.isArray(x)?'['+x.map(canon).join(',')+']':x!==null&&typeof x==='object'?'{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canon(x[k])).join(',')+'}':JSON.stringify(x);
const same=(a,b)=>canon(a)===canon(b);
function cert(raw,registry,run,stage){
  const c=JSON.parse(raw), m=c.message, sep=',"message":', i=raw.indexOf(sep);
  need(i>0&&raw.endsWith('}'),'certificate encoding');
  const msg=raw.slice(i+sep.length,-1);
  need(raw==='{"attestations":'+canon(c.attestations)+sep+msg+'}','certificate fields');
  need(same(JSON.parse(msg),m)&&m.domain==='ASTRA-SCIENTIFIC-CONSENSUS-v0.16'&&m.run===run&&m.stage===stage,'context');
  const valid=new Set();
  for(const a of c.attestations){
    const k=registry[a.signer]; if(!k||valid.has(a.signer)||!/^[0-9a-f]{128}$/.test(a.signature))continue;
    const key=createPublicKey({key:Buffer.from('302a300506032b6570032100'+k,'hex'),format:'der',type:'spki'});
    if(verify(null,Buffer.from(msg),key,Buffer.from(a.signature,'hex')))valid.add(a.signer);
  }
  need(valid.size>=3,'quorum'); return {body:m.body,signers:valid.size};
}
export function audit(c,opening=null){
  const reg=c.registry, keys=Object.values(reg);
  need(keys.length===4&&new Set(keys).size===4&&keys.every(k=>/^[0-9a-f]{64}$/.test(k))&&H(canon(reg))===PIN,'unpinned registry');
  const p=cert(c.pre,reg,c.run,'preregister'),s=cert(c.sub,reg,c.run,'predictions'),v=cert(c.certificate,reg,c.run,'verdict');
  need(p.body.registry_sha256===PIN&&s.body.preregistration_sha256===H(c.pre)&&v.body.preregistration_sha256===H(c.pre)&&v.body.submission_sha256===H(c.sub),'broken chain');
  const r=v.body.result,rule=p.body.rule;
  need(rule.tolerance===0&&rule.min_gain===.01&&same(rule.tasks,['education','inflation']),'unexpected protocol');
  need(r.rows.length===rule.tasks.length&&same(r.rows.map(x=>x.task),rule.tasks),'task list');
  const regressed=[],gains=[];
  for(const x of r.rows){
    need(['candidate','parent','reference','lower_parent','lower_reference'].every(k=>Number.isFinite(x[k]))&&x.candidate>=0&&x.parent>0&&x.reference>0,'invalid metric');
    if(x.candidate>Math.min(x.parent,x.reference))regressed.push(x.task);
    if(x.candidate<=.99*Math.min(x.parent,x.reference)&&Math.min(x.lower_parent,x.lower_reference)>0)gains.push(x.task);
  }
  const decision=!regressed.length&&gains.length?'PROMOTE':'REJECT';
  need(r.decision===decision&&same(r.regressions,regressed)&&same(r.confirmed_gain_tasks,gains),'gate disagreement');
  if(opening){
    need(/^[0-9a-f]{64}$/.test(opening.salt),'salt');
    need(H('{"data":'+opening.data+',"domain":"scientific-data-opening-v1","salt":'+JSON.stringify(opening.salt)+'}')===p.body.data_commitment,'data commitment');
    need(H(opening.inputs)===p.body.public_input_sha256&&H(opening.predictions)===s.body.predictions_sha256,'opening hash');
    const data=JSON.parse(opening.data),inputs=JSON.parse(opening.inputs),pred=JSON.parse(opening.predictions);
    for(const row of r.rows){
      const d=data[row.task],i=inputs[row.task],idx=i.test_idx;
      need(idx.length>0&&new Set(idx).size===idx.length&&idx.every(j=>Number.isInteger(j)&&j>=0&&j<d.y.length),'indices');
      const test=new Set(idx);need(same(d.X,i.X)&&d.temporal===i.temporal&&d.period===i.period&&same(d.y.map((y,j)=>test.has(j)?0:y),i.y),'mask mismatch');
      for(const role of ['candidate','parent','reference']){
        const a=pred[row.task][role].prediction;need(a.length===idx.length&&a.every(Number.isFinite),'predictions');
        const rmse=Math.sqrt(idx.reduce((sum,j,k)=>sum+(d.y[j]-a[k])**2,0)/idx.length);
        need(Math.abs(rmse-row[role])<=1e-12,'RMSE mismatch');
      }
    }
  }
  return {status:'VERIFIED_HISTORICAL',run:c.run,decision,signatures:[p.signers,s.signers,v.signers],registry_sha256:PIN,opening_verified:!!opening,rmse_recomputed:!!opening,bootstrap_recomputed:false,independent_authority:false};
}
const load=name=>JSON.parse(readFileSync(new URL(name,ROOT),'utf8'));
if(process.argv[1]===fileURLToPath(import.meta.url)){
  const capsule=load('capsule.json');
  if(process.argv[2]==='serve'){
    const report=audit(capsule);
    createServer((req,res)=>{if(req.method!=='GET'||!['/','/health','/proof'].includes(req.url)){res.writeHead(404);res.end();return;}res.setHeader('content-type','application/json');res.end(JSON.stringify(req.url==='/proof'?capsule:report));}).listen(Number(process.env.PORT||8080),'0.0.0.0');
  }else console.log(JSON.stringify(audit(capsule,process.argv[2]==='full'?load('opening.json'):null),null,2));
}
