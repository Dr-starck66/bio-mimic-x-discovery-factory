"""Scientific attestation protocol. Local prototype, not proof of scientific truth."""
import hashlib,json,math
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from cryptography.exceptions import InvalidSignature

QUORUM=3
STAGES=('preregister','predictions','verdict')

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def public(key):return key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()
def require(ok,message):
    if not ok:raise ValueError(message)

def registry_check(reg):
    require(isinstance(reg,dict) and len(reg)==4,'need four pinned keys')
    raw=[bytes.fromhex(k) for k in reg.values()]
    require(len(set(raw))==4,'need four distinct pinned keys')
    for key in raw:Ed25519PublicKey.from_public_bytes(key)

def message(run,stage,body):
    require(stage in STAGES and isinstance(run,str) and bool(run),'invalid context')
    return {'domain':'ASTRA-SCIENTIFIC-CONSENSUS-v0.16','run':run,'stage':stage,'body':body}

class Signer:
    def __init__(self,name,key):self.name=name;self.key=key;self.journal={}
    def sign(self,run,stage,body):
        m=message(run,stage,body);h=digest(m);slot=(run,stage)
        require(self.journal.get(slot,h)==h,'conflicting attestation');self.journal[slot]=h
        return {'signer':self.name,'signature':self.key.sign(canonical(m)).hex()}

def certificate(run,stage,body,attestations,reg):
    registry_check(reg);m=message(run,stage,body);valid=set()
    for a in attestations:
        name=a['signer']
        if name not in reg or name in valid:continue
        try:Ed25519PublicKey.from_public_bytes(bytes.fromhex(reg[name])).verify(bytes.fromhex(a['signature']),canonical(m))
        except (ValueError,InvalidSignature):continue
        valid.add(name)
    require(len(valid)>=QUORUM,'quorum missing')
    return {'message':m,'attestations':attestations}

def verify(cert,reg,run,stage,body):
    require(cert['message']==message(run,stage,body),'wrong context or body')
    certificate(run,stage,body,cert['attestations'],reg);return True

def commitment(data,salt):
    require(isinstance(salt,str) and len(bytes.fromhex(salt))>=32,'salt too short')
    return digest({'domain':'scientific-data-opening-v1','salt':salt,'data':data})

def preregister(run,data_hash,public_hash,policy,rule,code,reg,signers):
    body={'data_commitment':data_hash,'public_input_sha256':public_hash,'policy':policy,'rule':rule,'code':code,'registry_sha256':digest(reg)}
    return certificate(run,'preregister',body,[s.sign(run,'preregister',body) for s in signers],reg)

def bind_predictions(run,pre,predictions,reg,signers):
    verify(pre,reg,run,'preregister',pre['message']['body'])
    body={'preregistration_sha256':digest(pre),'predictions_sha256':digest(predictions)}
    return certificate(run,'predictions',body,[s.sign(run,'predictions',body) for s in signers],reg)

def verify_evidence(run,pre,sub,data,salt,public_inputs,predictions,reg,expected_code,expected_rule):
    b=pre['message']['body'];verify(pre,reg,run,'preregister',b)
    require(b['registry_sha256']==digest(reg) and b['code']==expected_code and b['rule']==expected_rule,'untrusted protocol')
    require(b['data_commitment']==commitment(data,salt),'data opening mismatch')
    require(b['public_input_sha256']==digest(public_inputs),'public inputs changed')
    verify(sub,reg,run,'predictions',{'preregistration_sha256':digest(pre),'predictions_sha256':digest(predictions)})
    return b['policy']

def verdict_body(pre,sub,result):
    require(result['decision'] in ('PROMOTE','REJECT'),'invalid decision')
    return {'preregistration_sha256':digest(pre),'submission_sha256':digest(sub),'result':result}

def finalize(run,pre,sub,result,attestations,reg):
    verify(pre,reg,run,'preregister',pre['message']['body'])
    verify(sub,reg,run,'predictions',sub['message']['body'])
    require(sub['message']['body']['preregistration_sha256']==digest(pre),'unlinked submission')
    return certificate(run,'verdict',verdict_body(pre,sub,result),attestations,reg)

def verify_final(run,pre,sub,result,cert,reg):
    verify(pre,reg,run,'preregister',pre['message']['body']);verify(sub,reg,run,'predictions',sub['message']['body'])
    require(sub['message']['body']['preregistration_sha256']==digest(pre),'unlinked submission')
    return verify(cert,reg,run,'verdict',verdict_body(pre,sub,result))
