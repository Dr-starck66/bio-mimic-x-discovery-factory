import copy,unittest
from unittest.mock import patch
import scientific_arbiter as a
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=a.read('arbiter_lock.json');cls.s=a.read('committed_predictions.json');cls.t=a.read('evaluation_truth.json');cls.r=a.read('falsifier_report.json')
    def mutated(self):return copy.deepcopy(self.s)
    def rehash(self,s):s['sha256']=a.digest(s['body']);return s
    def test_valid(self):self.assertTrue(a.verify_submission(self.f,self.s,self.t))
    def test_lock_tamper(self):
        f=copy.deepcopy(self.f);f['lock']['rule']['tolerance']=1
        with self.assertRaises(ValueError):a.validate_lock(f)
    def test_protocol_rehash(self):
        f=copy.deepcopy(self.f);f['lock']['rule']['tolerance']=1;f['sha256']=a.digest(f['lock'])
        with self.assertRaises(ValueError):a.validate_lock(f)
    def test_prediction_tamper(self):
        s=self.mutated();s['body']['predictions'][a.TASKS[0]]['candidate']['prediction'][0]+=1
        with self.assertRaises(ValueError):a.verify_submission(self.f,s,self.t)
    def test_missing_task_rehash(self):
        s=self.mutated();del s['body']['predictions'][a.TASKS[0]]
        with self.assertRaises(ValueError):a.verify_submission(self.f,self.rehash(s),self.t)
    def test_wrong_role_rehash(self):
        s=self.mutated();s['body']['predictions'][a.TASKS[0]]['candidate']['role']='parent'
        with self.assertRaises(ValueError):a.verify_submission(self.f,self.rehash(s),self.t)
    def test_wrong_index_rehash(self):
        s=self.mutated();s['body']['predictions'][a.TASKS[0]]['candidate']['test_idx'].reverse()
        with self.assertRaises(ValueError):a.verify_submission(self.f,self.rehash(s),self.t)
    def test_missing_prediction_rehash(self):
        s=self.mutated();s['body']['predictions'][a.TASKS[0]]['candidate']['prediction'].pop()
        with self.assertRaises(ValueError):a.verify_submission(self.f,self.rehash(s),self.t)
    def test_rehashed_fabricated_prediction(self):
        s=self.mutated();s['body']['predictions'][a.TASKS[0]]['candidate']['prediction'][0]+=1;self.rehash(s)
        with patch.object(a,'call_worker',a.worker):self.assertFalse(a.falsify(self.f,s,self.t)['passed'])
    def test_forged_report(self):
        r=copy.deepcopy(self.r);r['checks']={}
        with patch.object(a,'falsify',return_value=self.r):
            with self.assertRaises(ValueError):a.arbitrate(self.f,self.s,self.t,r)
    def test_actual_reject(self):self.assertEqual(a.read('arbiter_results.json')['gate']['decision'],'REJECT')
    def test_unmasked_target(self):
        inp=copy.deepcopy(self.t[a.TASKS[0]]['input']);inp['visible_y'][inp['test_idx'][0]]=3
        with self.assertRaises(ValueError):a.worker({'input':inp,'policy':self.f['lock']['policy'],'role':'candidate'})
    def test_truth_trust_boundary(self):
        t=copy.deepcopy(self.t);t[a.TASKS[0]]['y'][0]+=100
        # Same-host evaluator is trusted: the submission commitment does not bind private labels.
        self.assertTrue(a.verify_submission(self.f,self.s,t))
if __name__=='__main__':unittest.main()
