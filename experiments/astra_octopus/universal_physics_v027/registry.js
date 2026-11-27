// Explicit capability contracts; no inferred sensor identity or synchronization.
// Registry is finite, not an unrestricted discovery engine.
const contracts=[
 {name:'steady_flow_ratio',roles:{q_in:'flow',q_out:'flow'},conditions:['synchronized','same_fluid','steady','no_unmeasured_branch'],formula:'log(Qin/Qout)',scope:'relative discrepancy, not leak attribution'},
 {name:'hydraulic_power',roles:{p_in:'pressure',p_out:'pressure',q:'flow'},conditions:['synchronized','same_control_volume'],formula:'(Pout-Pin)*Q',scope:'pressure work only; excludes elevation/kinetic terms'},
 {name:'wire_to_water_efficiency',roles:{p_in:'pressure',p_out:'pressure',q:'flow',power:'electric_power'},conditions:['synchronized','same_control_volume','same_power_boundary','negligible_head_corrections'],formula:'(Pout-Pin)*Q/Pe',scope:'wire-to-water estimate'},
 {name:'three_phase_active_power',roles:{v1:'voltage',v2:'voltage',v3:'voltage',i1:'current',i2:'current',i3:'current'},conditions:['synchronized','phase_pairs_verified','voltage_reference_verified'],formula:'sum(Vphase*Iphase)',scope:'instantaneous electrical power, average over aligned samples'}
];
const factors={flow:{'m3/s':1,'L/min':1/60000,'m3/h':1/3600},pressure:{Pa:1,bar:100000,MPa:1000000},electric_power:{W:1,kW:1000},voltage:{V:1},current:{A:1}};
function selectRelations(manifest){
 return contracts.map(c=>{
  const missing=[],invalid=[],unverified=[];
  for(const [role,type] of Object.entries(c.roles)){const s=manifest.channels?.[role];if(!s){missing.push(role);continue}if(s.kind!==type||!Number.isFinite(factors[type]?.[s.unit])||s.origin!=='measured')invalid.push(role)}
  for(const x of c.conditions)if(manifest.conditions?.[x]!==true)unverified.push(x);
  const ids=Object.keys(c.roles).map(k=>manifest.channels?.[k]?.id).filter(Boolean);
  if(ids.length!==new Set(ids).size)invalid.push('reused_channel');
  if(ids.length!==Object.keys(c.roles).length&&!missing.length)invalid.push('missing_channel_identity');
  return {name:c.name,eligible:!missing.length&&!invalid.length&&!unverified.length,missing,invalid,unverified,scope:c.scope};
 });
}
function compute(name,manifest,values){
 const a=selectRelations(manifest).find(r=>r.name===name);if(!a?.eligible)return {status:'unavailable'};
 const c=contracts.find(r=>r.name===name),v={};
 for(const [k,type] of Object.entries(c.roles)){const x=values[k];if(!Number.isFinite(x))return {status:'unavailable'};v[k]=x*factors[type][manifest.channels[k].unit]}
 let n;
 if(name==='steady_flow_ratio'){if(v.q_in<=0||v.q_out<=0)return {status:'unavailable'};n=Math.log(v.q_in/v.q_out)}
 if(name==='hydraulic_power'||name==='wire_to_water_efficiency'){if(v.q<0)return {status:'unavailable'};n=(v.p_out-v.p_in)*v.q;if(name==='wire_to_water_efficiency'){if(v.power<=0)return {status:'unavailable'};n/=v.power}}
 if(name==='three_phase_active_power')n=v.v1*v.i1+v.v2*v.i2+v.v3*v.i3;
 return Number.isFinite(n)?{status:'computed',value:n}:{status:'unavailable'};
}
function registryTests(){
 const m={channels:{p_in:{id:'p0',kind:'pressure',unit:'bar',origin:'measured'},p_out:{id:'p1',kind:'pressure',unit:'bar',origin:'measured'},q:{id:'q',kind:'flow',unit:'L/min',origin:'measured'},power:{id:'pe',kind:'electric_power',unit:'W',origin:'measured'}},conditions:{synchronized:true,same_control_volume:true,same_power_boundary:true,negligible_head_corrections:true}};
 const v={p_in:1,p_out:61,q:1,power:200},calc=(x,y)=>compute('wire_to_water_efficiency',x,y);
 const nominal=JSON.parse(JSON.stringify(m));nominal.channels.power.origin='nameplate';
 const unsync=JSON.parse(JSON.stringify(m));unsync.conditions.synchronized=false;
 const duplicate=JSON.parse(JSON.stringify(m));duplicate.channels.p_out.id='p0';
 const wrong=JSON.parse(JSON.stringify(m));wrong.channels.q.unit='V';
 const unknown=JSON.parse(JSON.stringify(m));delete unknown.conditions.same_power_boundary;
 const checks={conversion:Math.abs(calc(m,v).value-.5)<1e-12,missing_value:calc(m,{...v,q:NaN}).status==='unavailable',nominal_not_measured:calc(nominal,v).status==='unavailable',unsynchronized_rejected:calc(unsync,v).status==='unavailable',duplicate_rejected:calc(duplicate,v).status==='unavailable',unit_mismatch:calc(wrong,v).status==='unavailable',unknown_boundary:calc(unknown,v).status==='unavailable',zero_power:calc(m,{...v,power:0}).status==='unavailable'};
 if(!Object.values(checks).every(Boolean))throw Error(JSON.stringify(checks));return checks;
}
