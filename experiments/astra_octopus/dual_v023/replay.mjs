import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const read=n=>readFile(new URL(n,import.meta.url),'utf8');
const core=await read('dual_skab.js'),tests=await read('test_dual.js');
const {parseCSV,evaluate,testDual}=new Function(core+tests+'return {parseCSV,evaluate,testDual};')();
console.log(testDual());
let n=0;
for(const file of ['skab_other_retest.json','skab_valve1.json','skab_valve2.json']){
 for(const row of JSON.parse(await read(file))){
  const {path,sha,...expected}=row;
  const r=await fetch('https://api.github.com/repos/waico/SKAB/git/blobs/'+sha,{headers:{accept:'application/vnd.github+json','user-agent':'astra-dual-replay'}});
  if(!r.ok)throw Error('HTTP '+r.status+' '+path);
  const x=await r.json();if(x.encoding!=='base64')throw Error('encoding');
  const buf=Buffer.from(x.content,'base64');if(createHash('sha1').update('blob '+buf.length+'\0').update(buf).digest('hex')!==sha)throw Error('blob mismatch');
  const got=evaluate(parseCSV(buf.toString('utf8')));
  if(JSON.stringify(got)!==JSON.stringify(expected))throw Error('replay mismatch '+path);
  n++;
 }
}
console.log('PASS '+n+' files');
