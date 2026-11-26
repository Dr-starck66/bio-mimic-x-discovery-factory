import copy,tempfile,unittest
from pathlib import Path
import numpy as np
from external_challenge import *
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name);cls.priv=root/'private';cls.pub=root/'public';rng=np.random.default_rng(42);cls.task={};cls.labels=[]
        for name in ['train','validation','test']:
            x=rng.normal(size=(30,2));y=(x[:,0]*3+x[:,1]+rng.normal(0,.1,30)).tolist();cls.task[name]={'X':x.tolist(),'groups':[name]*30}
            if name=='test':cls.labels=y
            else:cls.task[name]['y']=y
        cls.auth=prepare(cls.task,cls.labels,cls.priv,cls.pub);cls.pin=cls.auth['pin'];cls.ex=cls.auth['prereg_sha256'];cls.pre=read(cls.pub/'prereg.json');cls.s=submit(cls.task,cls.pre,cls.pin,cls.ex);cls.r=judge(cls.task,cls.pre,cls.s,cls.pin,cls.ex,cls.priv)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_receipt(self):self.assertFalse(verify_receipt(self.r,self.pre,self.s,self.pin,self.ex)['promotion'])
    def test_no_labels(self):self.assertNotIn('y',read(self.pub/'task.json')['test']);self.assertEqual({p.name for p in self.pub.iterdir()},{'task.json','prereg.json'})
    def test_group_leak(self):
        t=copy.deepcopy(self.task);t['test']['groups'][0]='train'
        with self.assertRaises(ValueError):arrays(t)
    def test_label_in_input(self):
        t=copy.deepcopy(self.task);t['test']['y']=self.labels
        with self.assertRaises(ValueError):arrays(t)
    def test_replay(self):self.assertEqual(submit(self.task,self.pre,self.pin,self.ex),self.s)
    def test_wrong_pin(self):
        with self.assertRaises(Exception):submit(self.task,self.pre,'00'*32,self.ex)
    def test_wrong_prereg(self):
        with self.assertRaises(ValueError):submit(self.task,self.pre,self.pin,'00'*32)
    def test_changed_input(self):
        t=copy.deepcopy(self.task);t['test']['X'][0][0]+=1
        with self.assertRaises(ValueError):submit(t,self.pre,self.pin,self.ex)
    def test_faked_prediction(self):
        s=copy.deepcopy(self.s);s['predictions']['candidate']['prediction'][0]+=1
        with self.assertRaises(ValueError):judge(self.task,self.pre,s,self.pin,self.ex,self.priv)
    def test_faked_receipt(self):
        r=copy.deepcopy(self.r);r['body']['scores']['candidate']=0
        with self.assertRaises(Exception):verify_receipt(r,self.pre,self.s,self.pin,self.ex)
    def test_changed_private_labels(self):
        p=self.priv/'opening.json';old=read(p);new=copy.deepcopy(old);new['labels'][0]+=1
        try:
            write(p,new)
            with self.assertRaises(ValueError):judge(self.task,self.pre,self.s,self.pin,self.ex,self.priv)
        finally:write(p,old)
    def test_public_verification_without_opening(self):
        self.assertIn('decision',verify_receipt(self.r,self.pre,self.s,self.pin,self.ex));self.assertNotIn('labels',self.r['body'])
if __name__=='__main__':unittest.main()
