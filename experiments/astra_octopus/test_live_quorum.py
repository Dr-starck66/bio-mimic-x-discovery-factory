"""Full protocol with one of four registered processes deliberately silent."""
import secrets,json
from benchmark_consensus import *

def main():
    run=secrets.token_hex(16);salt=secrets.token_hex(32);data=datasets();inputs=masked(data)
    labs=[Lab('lab-'+str(i)) for i in range(4)];reg={l.identity['name']:l.identity['public'] for l in labs}
    try:
        live=labs[:3]
        base={'run':run,'registry':reg};body={'data_commitment':commitment(data,salt),'public_input_sha256':digest(inputs),'policy':POLICY,'rule':RULE,'code':code(),'registry_sha256':digest(reg)}
        pre=certificate(run,'preregister',body,[l.ask({**base,'stage':'preregister','salt':salt,'body':body}) for l in live],reg)
        p=call('predict',{'inputs':inputs,'policy':POLICY});b={'preregistration_sha256':digest(pre),'predictions_sha256':digest(p)}
        sub=certificate(run,'predictions',b,[l.ask({**base,'stage':'predictions','pre':pre,'predictions':p}) for l in live],reg)
        out=[l.ask({**base,'stage':'verdict','pre':pre,'sub':sub,'predictions':p}) for l in live]
        result=out[0]['result'];require(all(q['result']==result for q in out),'validator disagreement')
        cert=finalize(run,pre,sub,result,[q['attestation'] for q in out],reg)
        bundle={**base,'pre':pre,'sub':sub,'data':data,'salt':salt,'inputs':inputs,'predictions':p,'result':result,'certificate':cert,'validator_results':out}
        require(verify_bundle(bundle,reg),'verification failed')
        try:finalize(run,pre,sub,result,[q['attestation'] for q in out[:2]],reg)
        except ValueError:blocked=True
        else:blocked=False
        require(blocked,'two signatures accepted')
        write('live_quorum_evidence.json',bundle)
        print(json.dumps({'three_of_four':'PASS','two_of_four_blocked':blocked,'result':result,'registered_keys':len(reg),'signatures':len(out),'silent':'lab-3'},indent=2,sort_keys=True))
    finally:
        for l in labs:l.close()
if __name__=='__main__':main()
