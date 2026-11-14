/** ASTRA DINO Ω — external fossil and modern bird morphology benchmark.
 * Independent matrix pinned by upstream git commit AND Git blob SHA-1.
 * This is masked-character inference, NOT true ancient genome recovery.
 */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {parseNexus, individualTaxa, evaluateMorph, bootstrapDelta, permutedLabelNull, downloadText} from './astra_dino_ancestry.mjs';

export const EXTERNAL_SOURCE=Object.freeze({
  paper:'Wang, Lloyd, Zhang & Zhou (2021), Proc. R. Soc. B, doi:10.1098/rspb.2020.3105',
  repository:'graemetlloyd/ProjectAncientBeak',
  commit:'67e7d4375374395e1c17a98a85b8314a71feb685',
  blobSha1:'a083926bc99c7f1c37aecab6ffdc4ad1489a6f1f',
  url:'https://raw.githubusercontent.com/graemetlloyd/ProjectAncientBeak/67e7d4375374395e1c17a98a85b8314a71feb685/data/matrix.nex',
  nTax:80,nChar:280,extant:['Anas','Gallus'],excluded:['Dromaeosauridae']
});

export function gitBlobSha1(utf8Text){
  const bytes=Buffer.from(utf8Text,'utf8');
  return createHash('sha1').update('blob '+bytes.length+'\0','utf8').update(bytes).digest('hex');
}
export function assertExternalSource(text,{checkHash=true}={}){
  if(checkHash&&gitBlobSha1(text)!==EXTERNAL_SOURCE.blobSha1)
    throw new Error('FAIL_CLOSED: Git blob mismatch in external fossil matrix');
  const parsed=parseNexus(text);
  if(parsed.nTax!==80||parsed.nChar!==280)
    throw new Error('FAIL_CLOSED: Unexpected 2021 matrix dimensions');
  if(!parsed.rows.some(r=>r.taxon==='Anas')||!parsed.rows.some(r=>r.taxon==='Gallus')||
     !parsed.rows.some(r=>r.taxon==='Dromaeosauridae'))
    throw new Error('FAIL_CLOSED: Extant bird or theropod outgroup missing');
  if(!individualTaxa(parsed.rows).every(r=>r.taxon!=='Dromaeosauridae'))
    throw new Error('FAIL_CLOSED: Composite outgroup should be excluded');
  return parsed;
}
export function subsetMetrics(perTaxon,predicate){
  const group=perTaxon.filter(predicate);
  const tests=group.reduce((s,r)=>s+r.n,0);
  const modelCorrect=group.reduce((s,r)=>s+r.modelCorrect,0);
  const baselineCorrect=group.reduce((s,r)=>s+r.baselineCorrect,0);
  if(!tests)return {taxa:group.length,tests:0,status:'UNVERIFIED',reason:'No evaluable labels'};
  return {taxa:group.length,tests,modelCorrect,baselineCorrect,
    accuracy:modelCorrect/tests,baselineAccuracy:baselineCorrect/tests,
    deltaPoints:100*(modelCorrect-baselineCorrect)/tests};
}
export function evaluateExternalMatrix(text,{checkHash=true,nullReplicates=30,bootstrapIterations=2000}={}){
  const parsed=assertExternalSource(text,{checkHash});
  const {cells,...overall}=evaluateMorph(parsed,20,3);
  const birdNames=new Set(EXTERNAL_SOURCE.extant);
  const modern=subsetMetrics(overall.perTaxon,r=>birdNames.has(r.taxon));
  const fossil=subsetMetrics(overall.perTaxon,r=>!birdNames.has(r.taxon));
  if(overall.taxa!==79||modern.taxa!==2||fossil.taxa!==77)
    throw new Error('FAIL_CLOSED: cohort membership changed');
  return {benchmark:'ASTRA_DINO_EXTERNAL_2021_V1',status:'EXPLORATORY_NOT_GENOME_TO_TRAIT',
    reference:{...EXTERNAL_SOURCE},
    parameters:{neighbors:3,minOverlap:20,validation:'leave_one_taxon_out',
      targetFeatureExcluded:true,polymorphicMissing:true,fitToExternalData:true},
    overall,modern,fossil,negativeControl:permutedLabelNull(cells,nullReplicates,3,20261114),
    bootstrap:bootstrapDelta(overall.perTaxon,bootstrapIterations,20261114),
    limitations:['Morphological method re-fit within external matrix, not a frozen Holtz model',
      'Other known characters of withheld taxon used to infer the hidden character',
      'No homologous character mapping across Holtz/Wang-2021 datasets',
      'Not a genome-to-morphology or truly unknown ancient trait prediction']};
}
async function main(){
  const args=process.argv.slice(2);
  if(args.includes('--help')){
    console.log('Usage: node validation/astra_dino_external_2021.mjs --online | --file <pinned-matrix.nex>');return;
  }
  const idx=args.indexOf('--file');
  if(idx>=0&&!args[idx+1])throw new Error('Missing --file path');
  if(idx<0&&!args.includes('--online'))throw new Error('Missing --online or --file');
  const text=idx>=0?fs.readFileSync(args[idx+1],'utf8'):await downloadText(EXTERNAL_SOURCE.url);
  const r=evaluateExternalMatrix(text);
  console.log(JSON.stringify(r,null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)
  main().catch(e=>{console.error('FAIL_CLOSED:',e.message);process.exitCode=1;});
