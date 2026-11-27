import copy,itertools,json,unittest
from scientific_consensus import *
from benchmark_consensus import ROOT,verify_bundle,Lab,datasets,masked,POLICY,RULE,code,score

class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.ss=[Signer(str(i),Ed25519PrivateKey.generate()) for i in range(4)]
        self.reg={s.name:public(s.key) for s in self.ss};self.run='test-run';self.body={'decision':'REJECT'}
    def signed(self,stage='verdict',body=None):
        b=self.body if body is None else body;return [s.sign(self.run,stage,b) for s in self.ss]
    def test_all_subsets(self):
        a=self.signed()
        for n in range(5):
            for sub in itertools.combinations(a,n):
                if n>=3:certificate(self.run,'verdict',self.body,sub,self.reg)
                else:
                    with self.assertRaises(ValueError):certificate(self.run,'verdict',self.body,sub,self.reg)
    def test_one_wrong_attestation(self):
        a=self.signed();b={'decision':'PROMOTE'};fake=Signer('0',self.ss[0].key).sign(self.run,'verdict',b)
        certificate(self.run,'verdict',self.body,[fake,*a[1:]],self.reg)
        with self.assertRaises(ValueError):certificate(self.run,'verdict',b,[fake,*a[1:]],self.reg)
    def test_duplicate_signer(self):
        a=self.signed()
        with self.assertRaises(ValueError):certificate(self.run,'verdict',self.body,[a[0]]*4,self.reg)
    def test_duplicate_key_alias(self):
        r=self.reg.copy();r['1']=r['0'].upper()
        with self.assertRaises(ValueError):registry_check(r)
    def test_unknown_key(self):
        a=self.signed();fake=Signer('outsider',Ed25519PrivateKey.generate()).sign(self.run,'verdict',self.body)
        with self.assertRaises(ValueError):certificate(self.run,'verdict',self.body,[*a[:2],fake],self.reg)
    def test_cross_run_replay(self):
        with self.assertRaises(ValueError):certificate('another','verdict',self.body,self.signed(),self.reg)
    def test_cross_stage_replay(self):
        with self.assertRaises(ValueError):certificate(self.run,'predictions',self.body,self.signed(),self.reg)
    def test_sign_once(self):
        self.signed()
        with self.assertRaises(ValueError):self.ss[0].sign(self.run,'verdict',{'decision':'PROMOTE'})
    def test_quorum_intersection(self):
        for a,b in itertools.combinations(list(itertools.combinations(range(4),3)),2):self.assertGreaterEqual(len(set(a)&set(b)),2)
    def test_commitment(self):
        self.assertNotEqual(commitment([1],'00'*32),commitment([2],'00'*32));self.assertNotEqual(commitment([1],'00'*32),commitment([1],'01'*32))
    def test_salt_length(self):
        with self.assertRaises(ValueError):commitment([1],'00')
    def test_real_lab_rejects_bad_manifest(self):
        lab=Lab('0')
        try:
            r=self.reg.copy();r['0']=lab.identity['public'];d=datasets();salt='0a'*32
            b={'data_commitment':commitment(d,salt),'public_input_sha256':digest(masked(d)),'policy':POLICY,'rule':RULE,'code':code(),'registry_sha256':digest(r)}
            with self.assertRaises(ValueError):lab.ask({'stage':'preregister','run':self.run,'registry':r,'salt':salt,'body':{**b,'data_commitment':'fake'}})
            self.assertEqual(lab.ask({'stage':'preregister','run':self.run,'registry':r,'salt':salt,'body':b})['signer'],'0')
            with self.assertRaises(ValueError):lab.ask({'stage':'verdict','run':self.run,'registry':r})
        finally:lab.close()

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b=json.loads((ROOT/'consensus_evidence.json').read_text());cls.reg=json.loads((ROOT/'registry.json').read_text())
    def changed(self,key):return copy.deepcopy(self.b)
    def test_full_verification(self):self.assertTrue(verify_bundle(self.b,self.reg))
    def test_changed_truth(self):
        b=self.changed('data');b['data']['education']['y'][b['inputs']['education']['test_idx'][0]]+=1
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_changed_salt(self):
        b=self.changed('salt');b['salt']='00'*32
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_changed_predictions(self):
        b=self.changed('predictions');b['predictions']['education']['candidate']['prediction'][0]+=1
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_changed_rule(self):
        b=self.changed('pre');b['pre']['message']['body']['rule']['tolerance']=1
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_changed_registry(self):
        b=self.changed('registry');b['registry']['lab-0']=public(Ed25519PrivateKey.generate())
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_changed_verdict(self):
        b=self.changed('result');b['result']['decision']='PROMOTE'
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_three_signatures(self):
        b=self.changed('certificate');b['certificate']['attestations'].pop();self.assertTrue(verify_bundle(b,self.reg))
    def test_two_signatures(self):
        b=self.changed('certificate');b['certificate']['attestations']=b['certificate']['attestations'][:2]
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_missing_task(self):
        b=self.changed('data');del b['data']['inflation']
        with self.assertRaises(ValueError):verify_bundle(b,self.reg)
    def test_no_private_keys(self):self.assertNotIn('private',json.dumps(self.b))
    def test_reject_result(self):self.assertEqual(self.b['result']['decision'],'REJECT')
if __name__=='__main__':unittest.main()
