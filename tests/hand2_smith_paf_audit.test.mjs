import test from "node:test";
import assert from "node:assert/strict";
import {audit} from "../validation/hand2_smith_paf_audit.mjs";

const old = "legacy_HAND2\t4341\t0\t4210\t-\tNC_090937.1\t1000000000\t910028724\t910032934\t4196\t4210\t60\tNM:i:14\ttp:A:P";
const modern = "modern_HAND2\t4212\t0\t4212\t-\tCM010938.2\t900000000\t884794793\t884799005\t4198\t4212\t60\tNM:i:14\ttp:A:P";

test("two targeted reciprocal hits only mean PARTIAL",()=>{
 const r=audit(old,modern);
 assert.equal(r.status,"PARTIAL_EXPECTED_RECIPROCAL_HITS_IN_REPORTED_PAF");
 assert.equal(r.directions.modern_to_legacy.top.edit_count,14);
 assert.equal(r.genome_wide_uniqueness,"UNVERIFIED");
});
test("competing unplaced scaffold is visible",()=>{
 const alt="modern_HAND2\t4212\t0\t4212\t+\tUNPLACED_2\t8000\t1000\t5212\t4190\t4212\t0\tNM:i:18\ttp:A:S";
 assert.equal(audit(old,modern+"\n"+alt).status,"UNVERIFIED_ALTERNATIVE_FULL_LENGTH_HITS");
});
test("forward strand is not expected reverse mapping",()=>{
 assert.equal(audit(old.replace("\t-\t","\t+\t"),modern).status,"UNVERIFIED_NO_EXPECTED_RECIPROCAL_MAPPING");
});
test("partial alignment cannot be promoted",()=>{
 const short=modern.replace("\t0\t4212\t","\t0\t2000\t").replace("\t4198\t4212\t","\t1990\t2000\t");
 assert.equal(audit(old,short).status,"UNVERIFIED_NO_EXPECTED_RECIPROCAL_MAPPING");
});
test("wrong query identity rejected",()=>assert.throws(()=>audit(old.replace("legacy_HAND2","HAND1"),modern)));
test("NM missing rejected",()=>assert.throws(()=>audit(old.replace("\tNM:i:14",""),modern)));
test("invalid target coordinates rejected",()=>assert.throws(()=>audit(old.replace("\t910032934\t","\t1000000001\t"),modern)));
test("secondary duplicate at same locus is not an independent second locus",()=>{
 assert.equal(audit(old,modern+"\n"+modern.replace("tp:A:P","tp:A:S")).directions.modern_to_legacy.n_distinct_loci,1);
});
test("empty source cannot yield PASS",()=>{
 assert.equal(audit("",modern).status,"UNVERIFIED_NO_EXPECTED_RECIPROCAL_MAPPING");
});
