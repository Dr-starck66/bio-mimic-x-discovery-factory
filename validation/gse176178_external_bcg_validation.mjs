#!/usr/bin/env node
/**
 * BIO-MIMIC X / ASTRA CG Oncology — independent BCG-outcome cohort check.
 * Only public GSE176178 cohort; NOT cretostimogene patients.
 * No patient-level data are persisted. Read-only HTTP GET and stdout report.
 * Node >=18. No npm dependencies.
 */
import assert from 'node:assert/strict';
import { gunzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';

const accession='GSE176178';
const base='https://ftp.ncbi.nlm.nih.gov/geo/series/GSE176nnn/GSE176178/';
const urls={
  counts:base+'suppl/GSE176178_RNA.featurecounts.txt.gz',
  metadata:base+'matrix/GSE176178_series_matrix.txt.gz',
};
const expectedSha256={
  counts:'f785ffeae2ef4f6b5f673fd46e1c7bc3b121fae91c49d22001b75e2daba75c4c',
  metadata:'ef5232392e1da3b91c995cd750098bb5a51aacdf4eda6d471101b8832421c565',
};
const signatures={
  IFN_CHEMOKINE_PROXY:['CXCL9','CXCL10'],
  T_CELL_CD8_PROXY:['CD8A','CD8B'],
  MACROPHAGE_PROXY:['CD68','CD163'],
};
const targets=[...new Set(Object.values(signatures).flat())];
const seed=20261111, nPerm=20000, nBoot=2000;
const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
const hash=x=>createHash('sha256').update(x).digest('hex');
function rng(seed){let a=seed>>>0;return()=>{a=(a+0x6D2B79F5)>>>0;let t=Math.imul(a^(a>>>15),1|a);t^=t+Math.imul(t^(t>>>7),61|t);return ((t^(t>>>14))>>>0)/4294967296}}
function fisher(a,rand){let out=a.slice();for(let j=out.length-1;j>0;j--){let k=Math.floor(rand()*(j+1));[out[j],out[k]]=[out[k],out[j]]}return out}
function auc(yes,no){let a=0;for(const y of yes)for(const n of no){a+=y>n?1:y===n?.5:0}return a/(yes.length*no.length)}
function split(vals,groups){return [vals.filter((_,i)=>groups[i]==='Yes'),vals.filter((_,i)=>groups[i]==='No')]}
function contrast(vals,labels){const [yes,no]=split(vals,labels);if(!yes.length||!no.length)throw Error('empty outcome cell');return mean(yes)-mean(no)}
function BH(ps){const sorted=ps.map((p,i)=>({p,i})).sort((a,b)=>a.p-b.p);const res=Array(ps.length);let q=1;for(let j=sorted.length-1;j>=0;j--){q=Math.min(q,sorted[j].p*sorted.length/(j+1));res[sorted[j].i]=+q.toFixed(8)}return res}
function percentile(values,p){let x=[...values].sort((a,b)=>a-b);const k=(x.length-1)*p,lo=Math.floor(k),hi=Math.ceil(k);return x[lo]*(hi-k)+x[hi]*(k-lo)}
function round(x){return Math.round((x+Number.EPSILON)*1e8)/1e8}
function permuteLabels(labels,strata,rand){
  let out=labels.slice();let blocks=new Map();for(let i=0;i<strata.length;i++){let k=strata[i];if(!blocks.has(k))blocks.set(k,[]);blocks.get(k).push(i)}
  for(const idx of blocks.values()){const l=fisher(idx.map(i=>labels[i]),rand);for(let j=0;j<idx.length;j++)out[idx[j]]=l[j]}
  return out;
}
function pPermutation(values,labels,strata,seed0,iterations=nPerm){const rand=rng(seed0);const observed=Math.abs(contrast(values,labels));let exceed=0;for(let p=0;p<iterations;p++){const perm=permuteLabels(labels,strata,rand);if(Math.abs(contrast(values,perm))+1e-12>=observed)exceed++}return (exceed+1)/(iterations+1)}
function bootCI(values,labels,seed0,iterations=nBoot){const [yes,no]=split(values,labels);const random=rng(seed0);const deltas=[];for(let k=0;k<iterations;k++){let a=0,b=0;for(let j=0;j<yes.length;j++)a+=yes[Math.floor(random()*yes.length)];for(let j=0;j<no.length;j++)b+=no[Math.floor(random()*no.length)];deltas.push(a/yes.length-b/no.length)}return [round(percentile(deltas,.025)),round(percentile(deltas,.975))]}
async function retrieve(url,sha){const res=await fetch(url,{headers:{'User-Agent':'BIO-MIMIC-X independent public GEO research/1.0'}});if(!res.ok)throw Error('HTTP '+res.status+' '+url);const data=Buffer.from(await res.arrayBuffer());if(data[0]!==31||data[1]!==139)throw Error('not gzip '+url);if(hash(data)!==sha)throw Error('UNEXPECTED_DATASET_SHA256 '+url);return {compressed:data,source:gunzipSync(data).toString('utf8')};}
function parseMetadata(s){const rows=s.split(/\r?\n/);function lines(prefix){return rows.filter(x=>x.startsWith(prefix+'\t')).map(x=>x.split('\t').slice(1).map(v=>v.replace(/^"|"$/g,'')))}
  const titles=lines('!Sample_title')[0],gsm=lines('!Sample_geo_accession')[0], characteristics=lines('!Sample_characteristics_ch1');
  if(titles?.length!==40||gsm?.length!==40||characteristics.length<3||characteristics.some(x=>x.length!==40))throw Error('GEO_SAMPLE_METADATA_SHAPE');
  function category(label){let x=characteristics.find(z=>z.every(v=>v.startsWith(label+': ')));if(!x)throw Error('Missing '+label);return x.map(v=>v.slice(label.length+2))}
  const response=category('bcg response'),age=category('age').map(Number),sex=category('gender');
  if(response.filter(x=>x==='Yes').length!==17||response.filter(x=>x==='No').length!==23||new Set(titles).size!==40||age.some(x=>!Number.isFinite(x)))throw Error('GEO_GROUP_QC_FAILURE');
  return {titles,gsm,response,age,sex};
}
function parseCounts(s,meta){const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split('\t');if(h.length!==46||h.slice(0,6).join('|')!=='Geneid|Chr|Start|End|Strand|Length')throw Error('UNEXPECTED_FEATURECOUNTS_HEADER');
  const sampleIds=h.slice(6);if(sampleIds.length!==40||new Set(sampleIds).size!==40)throw Error('INVALID_COUNT_SAMPLES');
  const map=sampleIds.map(id=>meta.titles.indexOf(id));if(map.some(i=>i<0)||new Set(map).size!==40)throw Error('COUNT_METADATA_MISMATCH');
  const totals=Array(40).fill(0),observed={},genes=new Set();let rows=0;
  for(const line of lines){if(!line.trim())continue;const c=line.split('\t');if(c.length!==46)throw Error('INVALID_GENE_ROW '+(rows+2));const name=c[0];if(genes.has(name))throw Error('DUPLICATE_GENE '+name);genes.add(name);
    for(let j=6;j<46;j++){let value=Number(c[j]);if(!Number.isFinite(value)||value<0||!Number.isInteger(value))throw Error('INVALID_COUNT '+name);totals[j-6]+=value}
    if(targets.includes(name))observed[name]=c.slice(6).map(Number);
    rows++;
  }
  if(rows!==59412||totals.some(x=>x<=0))throw Error('SOURCE_MATRIX_QC_FAILURE '+rows);
  const missing=targets.filter(g=>!(g in observed));if(missing.length)throw Error('MISSING_PREFIXED_SIGNATURE_FEATURES '+missing.join(','));
  const expr={};for(const gene of targets){let out=Array(40);for(let j=0;j<40;j++){out[map[j]]=Math.log2(1+observed[gene][j]/totals[j]*1e6)}expr[gene]=out}
  return {expr,totals,rows,sampleIds};
}
function analyze(meta,data){const report={source:'GSE176178',contrast:'BCG durable responders Yes vs No, bulk RNA-seq',design:'cross-sectional nonrandomized; not direct cretostimogene data',n_samples:40,n_yes:17,n_no:23,sex_response:{Yes:{Female:0,Male:0},No:{Female:0,Male:0}},age_response_mean:{Yes:0,No:0},source_gene_rows:data.rows,method:'featureCounts total mapped per gene normalization; log2(1+CPM); unweighted mean of two genes; label permutation; BH three tests',seed,n_permutations:nPerm,n_bootstrap:nBoot,results:{},caveat:'descriptive association; sex imbalanced; NO clinical predictor validation, independent clinical replication, or cretostimogene response labels'};
  meta.response.forEach((g,i)=>report.sex_response[g][meta.sex[i]]++);
  report.age_response_mean.Yes=round(mean(meta.age.filter((_,i)=>meta.response[i]==='Yes')));
  report.age_response_mean.No=round(mean(meta.age.filter((_,i)=>meta.response[i]==='No')));
  const list=[];
  let k=0;
  for(const [name,genes] of Object.entries(signatures)){
    const values=Array.from({length:40},(_,i)=>mean(genes.map(g=>data.expr[g][i])));
    const [yes,no]=split(values,meta.response);
    const maleIdx=meta.sex.map((s,i)=>s==='Male'?i:-1).filter(i=>i>=0);
    const maleValues=maleIdx.map(i=>values[i]),maleLabels=maleIdx.map(i=>meta.response[i]);
    const maleParts=split(maleValues,maleLabels);
    const globalP=pPermutation(values,meta.response,Array(40).fill('all'),seed+10+k);
    const sexP=pPermutation(values,meta.response,meta.sex,seed+100+k);
    const maleP=pPermutation(maleValues,maleLabels,Array(maleIdx.length).fill('male'),seed+200+k,10000);
    report.results[name]={genes,mean_yes_log2cpm1:round(mean(yes)),mean_no_log2cpm1:round(mean(no)),effect_yes_minus_no_log2cpm1:round(mean(yes)-mean(no)),auc_descriptive:round(auc(yes,no)),permutation_p_global:round(globalP),permutation_p_sex_stratified:round(sexP),bootstrap_ci95_unadjusted:bootCI(values,meta.response,seed+300+k),male_only:{n_yes:maleParts[0].length,n_no:maleParts[1].length,effect:round(contrast(maleValues,maleLabels)),auc:round(auc(...maleParts)),permutation_p:round(maleP)}};
    list.push(name);k++;
  }
  const qall=BH(list.map(x=>report.results[x].permutation_p_global)),qsex=BH(list.map(x=>report.results[x].permutation_p_sex_stratified));
  for(let j=0;j<list.length;j++){report.results[list[j]].BH_q_global=qall[j];report.results[list[j]].BH_q_sex_stratified=qsex[j]}
  return report;
}
function selfTest(){assert.equal(auc([1,2],[0,1]),.875);assert.deepEqual(BH([.01,.02,.7]),[.03,.03,.7]);assert.equal(contrast([1,3,3,4],['No','No','Yes','Yes']),1.5);const l=['No','Yes','No','Yes'];const r=rng(2);for(let j=0;j<10;j++){const p=permuteLabels(l,['F','F','M','M'],r);assert.equal(p.slice(0,2).filter(x=>x==='Yes').length,1);assert.equal(p.slice(2).filter(x=>x==='Yes').length,1)}assert.throws(()=>parseMetadata('!Sample_title\t"a"'));const fixed=rng(7);assert.equal(fixed(),rng(7)());console.log(JSON.stringify({status:'PASS',tests:6,scope:'pure helper and integrity tests, no biological input'}))}
if(process.argv.includes('--self-test'))selfTest();
else {const [c,m]=await Promise.all([retrieve(urls.counts,expectedSha256.counts),retrieve(urls.metadata,expectedSha256.metadata)]);const meta=parseMetadata(m.source),matrix=parseCounts(c.source,meta);const report=analyze(meta,matrix);report.source_sha256={counts:hash(c.compressed),metadata:hash(m.compressed)};report.source_bytes={counts:c.compressed.length,metadata:m.compressed.length};report.analysis_code_sha256='provided separately from GitHub blob';report.status='EXPLORATORY_REAL_DATA_SEX_ADJUSTED';console.log('ASTRA_GSE176178_REPORT_START'+JSON.stringify(report)+'ASTRA_GSE176178_REPORT_END')}
