function auditSentinel(){
 const rows=Array.from({length:60},(_,i)=>({id:i+1,pump:0,x:Array.from({length:10},(_,j)=>Math.sin(i*.17+j)+j)}));
 const model=fit(rows.slice(0,30)),base=sequence(rows,model);
 const changed=rows.map((r,i)=>i<40?r:{...r,x:r.x.map(v=>v+1000)});
 const missing=rows.map((r,i)=>i===40?{...r,x:r.x.map(()=>NaN)}:r);
 const partial=rows.map((r,i)=>i===40?{...r,x:r.x.map((v,j)=>j===0?NaN:v)}:r);
 const results={
  causal_prefix:JSON.stringify(base.slice(0,40))===JSON.stringify(sequence(changed,model).slice(0,40)),
  all_missing_abstains:sequence(missing,model)[40].s===null,
  partial_sensor_scored:Number.isFinite(sequence(partial,model)[40].s?.absolute_cusum),
  block_reset:JSON.stringify(base[45].s)===JSON.stringify(sequence([rows[45]],model)[0].s),
  gap_reset:JSON.stringify(sequence([rows[0],rows[2]],model)[1].s)===JSON.stringify(sequence([rows[2]],model)[0].s),
  labels_not_scoring:JSON.stringify(sequence(rows.map(r=>({...r,pump:2})),model).map(r=>r.s))===JSON.stringify(base.map(r=>r.s)),
  model_fit_unchanged:JSON.stringify(model.center)===JSON.stringify(fit(changed.slice(0,30)).center)
 };
 if(!Object.values(results).every(Boolean))throw Error(JSON.stringify(results));return results;
}
