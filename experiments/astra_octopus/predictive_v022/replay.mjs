import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {benchmark} from './bearing_benchmark_three.mjs';
const a=JSON.parse(await readFile(new URL('./bearing_results.json',import.meta.url),'utf8'));
const b=JSON.parse(await readFile(new URL('./bearing_test3.json',import.meta.url),'utf8'));
const hashes={...a.hashes,...b.hashes};
const raw={};
for(const [run,list] of Object.entries(hashes)){
  raw[run]=[];
  for(const sha of list){
    const res=await fetch('https://api.github.com/repos/'+a.source+'/git/blobs/'+sha,{headers:{accept:'application/vnd.github+json','user-agent':'astra-ims-replay'}});
    if(!res.ok)throw Error('GitHub blob HTTP '+res.status);
    const obj=await res.json();
    if(obj.encoding!=='base64')throw Error('Unexpected encoding');
    const buf=Buffer.from(obj.content,'base64');
    const actual=createHash('sha1').update('blob '+buf.length+'\0').update(buf).digest('hex');
    if(actual!==sha)throw Error('Blob mismatch');
    raw[run].push({sha,content:buf.toString('utf8')});
  }
}
const result=benchmark(raw);
const expected=[...a.results,...b.results];
if(JSON.stringify(result.results)!==JSON.stringify(expected))throw Error('Replay mismatch');
console.log(JSON.stringify({status:'PASS',bearings:expected.length,summary:result.summary},null,2));
