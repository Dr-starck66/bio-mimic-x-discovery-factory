import {audit} from '../verifier.mjs';
import capsule from '../capsule.json' with {type:'json'};
export default function handler(req,res){
  res.setHeader('content-type','application/json; charset=utf-8');
  res.setHeader('cache-control','no-store');
  if(req.method!=='GET'){res.statusCode=405;res.setHeader('allow','GET');return res.end(JSON.stringify({error:'method_not_allowed'}));}
  try {const report=audit(capsule);res.statusCode=200;return res.end(JSON.stringify({...report,service:'ASTRA SCIENTIFIC NETWORK',mode:'read_only_historical_audit'}));}
  catch {res.statusCode=500;return res.end(JSON.stringify({status:'verification_failed'}));}
}
