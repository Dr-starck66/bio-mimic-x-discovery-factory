#!/usr/bin/env node
/**
 * ASTRA MEDICAL CLAIM AUDIT Ω — real scientific-text NLI, research only.
 * Run with: node nli_scifact_official.mjs
 * Inputs: official SciFact data/claims_dev.jsonl and data/corpus.jsonl.
 * No patient data, clinical treatment decision, or medical recommendation.
 * Uses gold rationale sentences for oracle-condition tests; NOT end-to-end retrieval.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { AutoTokenizer, AutoModelForSequenceClassification, env } from '@huggingface/transformers';

const ROOT=process.env.ASTRA_SCIFACT_ROOT || process.cwd();
const MODEL='onnx-community/EttinX-nli-xxs-ONNX';
const LABELS=['CONTRADICT','SUPPORT','NEI']; // documented model-card logits 0/1/2
const sha=(x)=>crypto.createHash('sha256').update(x).digest('hex');
const read=(file)=>fs.readFileSync(path.join(ROOT,file));
const parseJsonl=(bytes)=>bytes.toString('utf8').split(/\r?\n/).filter(Boolean).map(JSON.parse);
function matrix(){return Object.fromEntries(LABELS.map(k=>[k,Object.fromEntries(LABELS.map(l=>[l,0]))]));}
function evaluate(items,view) {
  const m=matrix();let correct=0;
  for(const x of items){const p=x.pred[view];m[x.gold][p]++;if(x.gold===p)correct++;}
  const TP=m.CONTRADICT.CONTRADICT, FN=m.CONTRADICT.SUPPORT+m.CONTRADICT.NEI, FP=m.SUPPORT.CONTRADICT+m.NEI.CONTRADICT, TN=items.length-TP-FN-FP;
  return {n:items.length,accuracy:correct/items.length,confusion_gold_rows_prediction_cols:m,
    binary_contradiction:{TP,FP,FN,TN,precision:(TP+FP)?TP/(TP+FP):null,
      recall:(TP+FN)?TP/(TP+FN):null,specificity:(TN+FP)?TN/(TN+FP):null}};
}
const claimsBytes=read('data/claims_dev.jsonl');
const corpusBytes=read('data/corpus.jsonl');
const claims=parseJsonl(claimsBytes), docs=new Map(parseJsonl(corpusBytes).map(x=>[String(x.doc_id),x]));
if(claims.length!==300 || docs.size!==5183)throw new Error('Unexpected official SciFact dev/corpus size');
const items=[];
for(const c of claims){
  const eIds=Object.keys(c.evidence||{}).sort((a,b)=>Number(a)-Number(b));
  const goldEntry=eIds.length ? c.evidence[eIds[0]][0] : null;
  const gold=goldEntry?.label || 'NEI';
  if(!LABELS.includes(gold))throw new Error('Invalid gold label '+gold);
  const citedId=c.cited_doc_ids?.[0];
  const docId=eIds[0] || String(citedId);
  const doc=docs.get(String(docId));
  if(!doc || !Array.isArray(doc.abstract))throw new Error('Missing source document for claim '+c.id);
  const rationale=goldEntry && Array.isArray(goldEntry.sentences)
    ? goldEntry.sentences.map(n=>doc.abstract[n]).filter(x=>typeof x==='string').join(' ') : '';
  if(gold!=='NEI' && !rationale)throw new Error('Gold evidence rationale absent '+c.id);
  items.push({id:c.id, gold,claim:c.claim,doc_id:docId,
    oracle_premise: rationale || doc.abstract.join(' '),
    abstract_premise:doc.abstract.join(' '),source_has_gold_rationale:!!rationale,pred:{}});
}
const totalGold=Object.fromEntries(LABELS.map(label=>[label,items.filter(x=>x.gold===label).length]));
if(totalGold.CONTRADICT!==64 || totalGold.SUPPORT!==124 || totalGold.NEI!==112)throw new Error('Unexpected gold label counts');
let modelRevision=null;
try {
  const r=await fetch('https://huggingface.co/api/models/'+MODEL,{signal:AbortSignal.timeout(12000)});
  if(r.ok)modelRevision=(await r.json()).sha;
}catch(e){console.error('model_revision_metadata_unavailable',String(e));}
env.cacheDir=path.join(ROOT,'model_cache');
console.log('NLI_LOADING',MODEL,modelRevision);
const tokenizer=await AutoTokenizer.from_pretrained(MODEL);
const model=await AutoModelForSequenceClassification.from_pretrained(MODEL,{dtype:'int8',device:'cpu'});
console.log('NLI_READY',JSON.stringify(model.config.id2label));
const controls=[
  ['A man is eating a pizza.','A man eats something.','SUPPORT'],
  ['A cat is sitting on a chair.','There is no cat on the chair.','CONTRADICT'],
  ['A scientist is reading a journal.','A farmer grows wheat.','NEI'],
];
async function predict(premise,claim) {
  const encoded=await tokenizer(premise,{text_pair:claim,truncation:true,max_length:384});
  const logits=Array.from((await model(encoded)).logits.data);
  if(logits.length!==3 || logits.some(x=>!Number.isFinite(x)))throw new Error('Unexpected model logits');
  return LABELS[logits.indexOf(Math.max(...logits))];
}
const controlResults=[];
for(const [p,h,gold] of controls){const predicted=await predict(p,h);controlResults.push({gold,predicted,pass:predicted===gold});}
const start=Date.now();
for(let i=0;i<items.length;i++){
  const row=items[i];
  row.pred.oracle_rationale=await predict(row.oracle_premise,row.claim);
  row.pred.abstract_context=await predict(row.abstract_premise,row.claim);
  if((i+1)%50===0)console.log('NLI_PROGRESS',i+1,'of',items.length,'ms',Date.now()-start);
}
const modelFiles=[];const rootCache=env.cacheDir;
function walk(dir){
  if(!fs.existsSync(dir))return;
  for(const d of fs.readdirSync(dir,{withFileTypes:true})){
    const p=path.join(dir,d.name);
    if(d.isDirectory())walk(p);
    else if(d.name.endsWith('.onnx') && d.name.includes('int8')){
      const b=fs.readFileSync(p);modelFiles.push({file:path.relative(rootCache,p),bytes:b.length,sha256:sha(b)});
    }
  }
}
walk(rootCache);
const report={
  audit:'ASTRA MEDICAL CLAIM AUDIT Ω v0.3',utc:new Date().toISOString(),
  environment:{runtime:'Vercel Hobby sandbox isolated',model_library:'@huggingface/transformers',library_version:'4.3.2',
    model_id:MODEL,model_revision_sha:modelRevision,device:'cpu',dtype:'int8',
    model_weight_files:modelFiles,model_label_mapping_source:'official model card (not generic LABEL_0 names)',
    model_mapping_index_to_label:LABELS,model_controls:controlResults},
  source:{official_dataset:'https://github.com/allenai/scifact',download:'https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz',
    claims_dev_sha256:sha(claimsBytes),corpus_sha256:sha(corpusBytes),doc_count:docs.size,
    dev_claim_count:claims.length,label_counts:totalGold,license:'CC BY-NC 2.0; noncommercial research only'},
  protocols:{
    oracle_rationale:'For SUPPORT/CONTRADICT, use first gold-labeled document and its gold rationale sentence indices; NEI uses first cited document full abstract. Oracle evidence is privileged, NOT an independent retrieval system.',
    abstract_context:'Same document selection (gold evidence doc for positives, first cited for NEI); whole abstract as NLI premise. NOT end-to-end retrieval.',
    hypothesis:'Claim text',token_limit:384,positive_class:'CONTRADICT',other_classes:'SUPPORT,NEI',method:'argmax raw NLI logits',
    metrics:'3-way confusion + contradiction binary FP/FN; NOT medical false diagnosis rates',
    threshold:'none; model confidence uncalibrated',data_leakage:'Gold evidence document is selected for labeled positives; optimistic retrieval assumption.',
    clinical_validation:'UNVERIFIED'},
  results:{oracle_rationale:evaluate(items,'oracle_rationale'),abstract_context:evaluate(items,'abstract_context')},
  errors:{oracle_rationale:items.filter(x=>x.pred.oracle_rationale!==x.gold).slice(0,25).map(x=>({id:x.id,gold:x.gold,predicted:x.pred.oracle_rationale,doc_id:x.doc_id})),
    abstract_context:items.filter(x=>x.pred.abstract_context!==x.gold).slice(0,25).map(x=>({id:x.id,gold:x.gold,predicted:x.pred.abstract_context,doc_id:x.doc_id}))},
  limitations:['No clinical decision or treatment suggestions','NLI model is general-domain, not trained or calibrated for medicine','Evidence document selection uses gold labels; precision/recall are NOT end-to-end',
    'Neutral failure in sanity controls is retained, not hidden','No independent external reproducibility run yet',
    'Results cannot be compared head-to-head with a different published SciFact pipeline without identical retrieval protocol'],
  execution_ms:Date.now()-start,
};
const raw=Buffer.from(JSON.stringify(report,null,2)+'\n');
fs.writeFileSync(path.join(ROOT,'astra_nli_report_v03.json'),raw);
console.log('ASTRA_RESULT_JSON',raw.toString('utf8'));
console.log('ASTRA_RESULT_SHA256',sha(raw));
