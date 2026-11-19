import {readFileSync,writeFileSync} from "node:fs";
import {createHash} from "node:crypto";

function parsePaf(data, queryName, queryLength) {
  if (typeof data !== "string") throw new Error("PAF_TEXT_REQUIRED");
  const out=[];
  for (const line of data.split(/\r?\n/).filter(Boolean)) {
    const p=line.split("\t");
    if (p.length<13) throw new Error("PAF_COLUMNS_OR_NM_MISSING");
    const nums=[1,2,3,6,7,8,9,10,11].map(i=>Number(p[i]));
    if (nums.some(x=>!Number.isSafeInteger(x)||x<0)) throw new Error("PAF_NONINTEGER");
    const [qlen,qs,qe,tlen,ts,te,matches,block,mapq]=nums;
    if(p[0]!==queryName||qlen!==queryLength) throw new Error("QUERY_ID_OR_LENGTH_MISMATCH");
    if(!p[5]||!["-","+"].includes(p[4])||qs>=qe||qe>qlen||ts>=te||te>tlen||matches>block||block<qe-qs) throw new Error("INVALID_PAF_COORDINATES");
    const nmTags=p.slice(12).filter(x=>/^NM:i:\d+$/.test(x));
    if(nmTags.length!==1) throw new Error("UNIQUE_NM_TAG_REQUIRED");
    const nm=Number(nmTags[0].slice(5));
    if(nm>block) throw new Error("INVALID_EDIT_COUNT");
    out.push({query:p[0],qlen,qs,qe,strand:p[4],target:p[5],tlen,ts,te,matches,block,mapq,nm,coverage:(qe-qs)/qlen,editRate:(nm+qlen-(qe-qs))/qlen,primary:p.slice(12).includes("tp:A:P")});
  }
  return out;
}

function summarizeDirection(rows, expected) {
  const eligible=rows.filter(r=>r.coverage>=0.95&&r.nm<=175).sort((a,b)=>a.editRate-b.editRate||b.coverage-a.coverage||a.target.localeCompare(b.target)||a.ts-b.ts);
  const dedup=[];
  for(const row of eligible){
    const same=dedup.some(h=>h.target===row.target&&h.strand===row.strand&&Math.max(0,Math.min(h.te,row.te)-Math.max(h.ts,row.ts))/Math.min(h.te-h.ts,row.te-row.ts)>=0.8);
    if(!same)dedup.push(row);
  }
  const first=dedup[0]||null;
  const [target,lo,hi]=expected;
  const correct=Boolean(first&&first.target===target&&first.strand==="-"&&Math.max(0,Math.min(first.te,hi)-Math.max(first.ts,lo))/(hi-lo)>=0.9);
  function view(row) {return row?{target:row.target,start_1based:row.ts+1,end_1based:row.te,strand:row.strand,edit_count:row.nm,edit_rate_with_unaligned_query:Number(row.editRate.toFixed(6)),query_coverage:Number(row.coverage.toFixed(6)),mapq:row.mapq,primary:row.primary}:null;}
  return {n_paf_rows:rows.length,n_full_length_cutoff_hits:eligible.length,n_distinct_loci:dedup.length,expected_mapping_is_best:correct,top:view(first),second:view(dedup[1]||null),all_distinct:dedup.slice(0,25).map(view),limited_to_reported_hits:true};
}

function audit(oldPaf, modernPaf) {
  const old=summarizeDirection(parsePaf(oldPaf,"legacy_HAND2",4341),["NC_090937.1",910028724,910032936]);
  const modern=summarizeDirection(parsePaf(modernPaf,"modern_HAND2",4212),["CM010938.2",884794725,884799066]);
  let status="UNVERIFIED_NO_EXPECTED_RECIPROCAL_MAPPING";
  if(old.expected_mapping_is_best&&modern.expected_mapping_is_best) {
    status=(old.n_distinct_loci>1||modern.n_distinct_loci>1)?"UNVERIFIED_ALTERNATIVE_FULL_LENGTH_HITS":"PARTIAL_EXPECTED_RECIPROCAL_HITS_IN_REPORTED_PAF";
  }
  return {schema:"BIO-MIMIC-X/SMITH-PAF-INDEPENDENT-AUDIT/1",status,legacy_assembly:"GCA_002915635.3",modern_assembly:"GCF_040938575.1",legacy_HAND2:"CM010938.2:884794726-884799066",modern_HAND2:"NC_090937.1:910028725-910032936",directions:{legacy_to_modern:old,modern_to_legacy:modern},genome_wide_uniqueness:"UNVERIFIED",curator_confirmation:"UNVERIFIED",assembly_completeness_and_fasta_sha256:"UNVERIFIED_UNTIL_EXTERNAL_RECEIPTS",liftoff_annotation_transfer:"NOT_RUN",limits:["Minimap2 uses heuristic seeding; absence of a reported alternative is NOT genome-wide exclusion.","Large multipart indices and capped secondary alignments may hide candidate loci.","PAF NM and coverage differ from exact full-window Levenshtein; compare metrics without equating them.","HAND1 and other paralogs require independent negative controls.","Author communication permits analysis of a handful of genes, not unrestricted genome-wide publication or commercial reuse."]};
}

export {parsePaf,summarizeDirection,audit};

if(process.argv[1]&&import.meta.url===new URL("file://"+process.argv[1]).href){
  if(process.argv.length!==5){console.error("Usage: node validation/hand2_smith_paf_audit.mjs old_to_modern.paf modern_to_old.paf result.json");process.exit(2)}
  const a=readFileSync(process.argv[2],"utf8"),b=readFileSync(process.argv[3],"utf8");
  try {
    const report=audit(a,b);
    report.inputs={legacy_to_modern_paf_sha256:createHash("sha256").update(a).digest("hex"),modern_to_legacy_paf_sha256:createHash("sha256").update(b).digest("hex")};
    writeFileSync(process.argv[4],JSON.stringify(report,null,2)+"\n");
    console.log(report.status);
    process.exit(report.status==="PARTIAL_EXPECTED_RECIPROCAL_HITS_IN_REPORTED_PAF"?0:1);
  } catch(e) {console.error("FAIL_PAF_VALIDATION:",e.message);process.exit(2)}
}
