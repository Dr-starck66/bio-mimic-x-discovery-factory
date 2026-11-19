#!/usr/bin/env node
"use strict";
/**
 * Extract all bounded target windows from an authentic full assembly FASTA
 * projected on a concatenated nucleotide stream. Handles cross-read boundaries.
 * This MUST consume the unmodified nucleotide stream after FASTA headers/newlines
 * have been stripped, not the overlapping chunker.
 */
const fs=require("node:fs"),{once}=require("node:events");
async function main(){
 const [manifestFile,outFile]=process.argv.slice(2);
 if(!manifestFile||!outFile)throw Error("usage: node extract.js candidates.json out.fasta");
 const doc=JSON.parse(fs.readFileSync(manifestFile,"utf8"));
 const max=doc.reference_bases;
 const candidates=doc.candidates.slice().sort((a,b)=>a.global_interval_0based[0]-b.global_interval_0based[0]);
 const stream=fs.createWriteStream(outFile,{highWaterMark:1024*1024});
 const write=async(v)=>{if(!stream.write(v))await once(stream,"drain")};
 let pos=0,next=0,nExtracted=0,active=[];
 for await (const data of fs.createReadStream(null,{fd:0,autoClose:false,highWaterMark:4*1024*1024})){
   const right=pos+data.length;
   if(right>max)throw Error("REFERENCE_EXCEEDS_EXPECTED_BASE_COUNT");
   while(next<candidates.length&&candidates[next].global_interval_0based[0]<right){
      active.push({c:candidates[next],parts:[],len:0});
      next++;
   }
   const remain=[];
   for(const item of active){
      const [begin,end]=item.c.global_interval_0based;
      const from=Math.max(pos,begin),to=Math.min(right,end);
      if(from<to){ const piece=Buffer.from(data.subarray(from-pos,to-pos));item.parts.push(piece);item.len+=piece.length; }
      if(end<=right){
        if(item.len!==end-begin)throw Error("INCOMPLETE_WINDOW_"+item.c.candidate_id);
        await write(">cand_"+item.c.candidate_id+"\n");
        await write(Buffer.concat(item.parts));
        await write("\n");
        nExtracted++;
      }else remain.push(item);
   }
   active=remain;
   pos=right;
 }
 stream.end();
 await once(stream,"finish");
 if(pos!==max||next!==candidates.length||active.length||nExtracted!==candidates.length){
    throw Error("INCOMPLETE_STREAM_OR_CANDIDATE_OUTPUT "+JSON.stringify({pos,max,next,active:active.length,nExtracted,expected:candidates.length}));
 }
 console.error("EXTRACT_ALL_CANDIDATE_WINDOWS_PASS total_bases="+pos+" candidates="+nExtracted);
}
main().catch(e=>{console.error("FAIL_EXTRACT",e.stack||e);process.exitCode=2});
