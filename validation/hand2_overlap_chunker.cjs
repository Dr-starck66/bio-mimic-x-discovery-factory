#!/usr/bin/env node
"use strict";
// Transform a concatenated nucleotide stream (FASTA headers and EOL already
// stripped) into 1-MiB overlapping lines. A seed <= overlap+1 bases can never
// be lost at an artificial line break. No whole chromosome is buffered.
const fs=require("node:fs");
const {once}=require("node:events");
const CHUNK=Number(process.env.BIOMIMIC_CHUNK||1048576);
const OVERLAP=Number(process.env.BIOMIMIC_OVERLAP||31);
if(!Number.isInteger(CHUNK)||!Number.isInteger(OVERLAP)||
   CHUNK<128||OVERLAP<31||CHUNK<OVERLAP*3)throw Error("Invalid chunk/overlap");
async function emit(buf) {
 if(!process.stdout.write(buf)) await once(process.stdout,"drain");
 if(!process.stdout.write("\n")) await once(process.stdout,"drain");
}
async function main(){
 let carry=Buffer.alloc(0), full=0;
 for await(const part of fs.createReadStream(null,{fd:0,autoClose:false,highWaterMark:4*1024*1024})){
  carry=Buffer.concat([carry,part]);
  while(carry.length>=CHUNK) {
   await emit(carry.subarray(0,CHUNK));
   carry=carry.subarray(CHUNK-OVERLAP);
   full++;
  }
 }
 if(carry.length)await emit(carry);
 const total=full*(CHUNK-OVERLAP)+carry.length;
 process.stderr.write("STREAM_BASES="+total+" CHUNKS="+(full+(carry.length?1:0))+" CHUNK="+CHUNK+" OVERLAP="+OVERLAP+"\n");
}
main().catch(e=>{console.error("FAIL_CHUNKER",e.message);process.exitCode=2});
