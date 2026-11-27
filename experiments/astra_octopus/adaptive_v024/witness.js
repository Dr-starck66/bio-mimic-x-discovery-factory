// Bounded-error specialization of ASTRA EPISTEMIC/CAUSAL.
// Primary residual p=physical+bias+e; independently calibrated witness w=physical+e_w.
// No independent witness means null vector (physical,bias)=(1,-1): unidentifiable.
function diagnosis({primary,witness=null,contextKnown=true,validatedWitness=false,ep=.05,ew=.05,delta=.2}){
 if(!contextKnown||!Array.isArray(primary)||primary.length<2||!primary.every(Number.isFinite)||![ep,ew,delta].every(x=>Number.isFinite(x)&&x>=0))return {label:'unknown'};
 const status=([l,h])=>l>delta||h< -delta?'present':l>=-delta&&h<=delta?'absent':'uncertain';
 const observed=primary.map(p=>status([p-ep,p+ep]));
 if(!validatedWitness||!Array.isArray(witness)||witness.length!==primary.length||!witness.every(Number.isFinite))return {label:observed.every(x=>x==='absent')?'compatible_normal':'ambiguous_physical_or_sensor',identifiable:false,nullspace:[1,-1]};
 const F=witness.map(w=>[w-ew,w+ew]);const B=primary.map((p,i)=>[p-witness[i]-ep-ew,p-witness[i]+ep+ew]);
 const fs=F.map(status),bs=B.map(status),f=fs.filter(x=>x==='present').length,b=bs.filter(x=>x==='present').length;
 let label='unknown';
 if(![...fs,...bs].includes('uncertain')){
   if(f&&b)label='mixed_physical_sensor';
   else if(f)label=f===1?'individual_physical_candidate':'collective_physical_candidate';
   else if(b)label='sensor_bias_candidate';
   else label='compatible_normal';
 }
 return {label,identifiable:true,physical:F,bias:B};
}
function experiment(){
 let seed=246813579;const u=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};const err=()=>.1*u()-.05;
 const cases={normal:{f:[0,0,0,0],b:[0,0,0,0],expected:'compatible_normal'},individual:{f:[1,0,0,0],b:[0,0,0,0],expected:'individual_physical_candidate'},collective:{f:[1,1,1,1],b:[0,0,0,0],expected:'collective_physical_candidate'},sensor:{f:[0,0,0,0],b:[1,1,1,1],expected:'sensor_bias_candidate'},mixed:{f:[1,0,0,0],b:[0,1,0,0],expected:'mixed_physical_sensor'},weak:{f:[.2,0,0,0],b:[0,0,0,0],expected:'unknown'}};
 const summary={};for(const [name,c] of Object.entries(cases)){let correct=0,labels={};for(let k=0;k<100;k++){const primary=c.f.map((f,i)=>f+c.b[i]+err()),witness=c.f.map(f=>f+err());const a=diagnosis({primary,witness,validatedWitness:true});labels[a.label]=(labels[a.label]||0)+1;correct+=Number(a.label===c.expected)}summary[name]={correct,total:100,labels}}
 const checks={};const p=[1,1,1,1],z=[0,0,0,0];checks.alias_without_witness=diagnosis({primary:p}).label==='ambiguous_physical_or_sensor';checks.physical_with_witness=diagnosis({primary:p,witness:p,validatedWitness:true}).label==='collective_physical_candidate';checks.sensor_with_witness=diagnosis({primary:p,witness:z,validatedWitness:true}).label==='sensor_bias_candidate';checks.unvalidated_witness=diagnosis({primary:p,witness:z}).label==='ambiguous_physical_or_sensor';checks.unknown_context=diagnosis({primary:p,witness:p,validatedWitness:true,contextKnown:false}).label==='unknown';checks.missing=diagnosis({primary:[1,NaN]}).label==='unknown';
 // Negative: if a shared artifact contaminates BOTH paths, falsely declaring independent witness gives false physical conclusion.
 const contaminated=diagnosis({primary:p,witness:p,validatedWitness:true}).label;
 return {summary,checks,negative:{actual:'common sensor bias on both paths',claimed:contaminated,detected:false},assumptions:'bounded errors and genuinely independent witness; simulated only'};
}
