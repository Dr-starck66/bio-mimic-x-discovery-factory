function testDual(){
 const checks={};function check(name,condition){checks[name]=!!condition;if(!condition)throw Error(name)}
 const t=Array.from({length:400},(_,i)=>i);
 // Exactly equal commissioning distributions: permutations of a 100-periodic signal.
 const X=t.map(i=>Array.from({length:4},(_,j)=>Math.sin(2*Math.PI*((i+25*j)%100)/100)));
 const B=fitScore(X,t);
 const common=X.map((r,i)=>r.map(v=>v+(i>=250?6:0))),C=fitScore(common,t);
 check('relative_common_mode_cancels',B.relative.score.slice(255).every((v,i)=>Math.abs(v-C.relative.score[i+255])<1e-10));
 check('absolute_common_mode_visible',C.absolute.alarm.slice(260).every(Boolean));
 check('dual_common_mode_visible',C.dual.alarm.slice(260).every(Boolean));
 const local=X.map((r,i)=>r.map((v,j)=>v+(i>=250&&j===0?6:0))),L=fitScore(local,t);
 check('relative_local_visible',L.relative.alarm.slice(260).every(Boolean));
 check('dual_local_visible',L.dual.alarm.slice(260).every(Boolean));
 const lost=X.map((r,i)=>i>=250?r.map(()=>NaN):r);const U=fitScore(lost,t);
 check('missing_data_abstention',Object.values(U).every(m=>m.alarm.slice(250).every(v=>v===null)));
 const g=t.map((v,i)=>i>=250?v+20:v),G=fitScore(X,g);
 check('gap_resets_persistence',Object.values(G).every(m=>m.alarm[250]===null&&m.alarm[251]===null));
 check('causal_prefix',Object.keys(B).every(k=>B[k].threshold===C[k].threshold&&JSON.stringify(B[k].alarm.slice(0,250))===JSON.stringify(C[k].alarm.slice(0,250))));
 let invalid=false;try{fitScore(X,t.map((v,i)=>i===250?249:v))}catch{invalid=true}check('duplicate_timestamp_rejected',invalid);
 const p=parseCSV('datetime;Accelerometer1RMS;Accelerometer2RMS;Current;Pressure;Temperature;Thermocouple;Voltage;Volume Flow RateRMS;anomaly;changepoint\n2020-01-01 00:00:00;1;2;3;4;5;6;7;8;0;0');
 check('actual_flow_header',p.X[0].length===8&&p.X[0][7]===8);
 check('commissioning_contamination',evaluate({X,t,labels:t.map(i=>i===10?1:0),changes:t.map(()=>0)}).eligible===false);
 return checks;
}
