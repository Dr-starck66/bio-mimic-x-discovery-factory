import assert from 'node:assert/strict';
import capsule from '../capsule.json' with {type:'json'};
import worker,{auditEdge} from './worker.mjs';
import {audit} from '../verifier.mjs';
assert.deepEqual(await auditEdge(capsule),audit(capsule));
let bad=structuredClone(capsule);bad.certificate=bad.certificate.replace('"decision":"REJECT"','"decision":"PROMOTE"');await assert.rejects(auditEdge(bad));
bad=structuredClone(capsule);bad.registry['lab-0']=bad.registry['lab-1'];await assert.rejects(auditEdge(bad));
bad=structuredClone(capsule);bad.sub=bad.pre;await assert.rejects(auditEdge(bad));
const r=await worker.fetch(new Request('https://example.invalid/health'));assert.equal(r.status,200);assert.equal((await r.json()).decision,'REJECT');assert.equal((await worker.fetch(new Request('https://example.invalid/health',{method:'POST'}))).status,405);console.log('7 assertions passed');
