import importlib.util
from pathlib import Path
import sys
import unittest

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))

def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,BASE/rel)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

probe=load('probe_identity','validation/acomys_probe_identity_gate.py')
hitl=load('ooi_hitl','validation/ooi_hitl_annotation_gate.py')

class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.probes={f'p{i}':{'gene_id':f'G{i}', 'sequence':'A'*25} for i in range(5)}
    def line(self,q,nm,ref='tx',pos=1,flag=0):
        return '\t'.join([q,str(flag),ref,str(pos),'255','25M','*','0','0','A'*25,'*',f'NM:i:{nm}'])+'\n'
    def test_all_identity_bands_and_unmapped(self):
        rows=probe.sam_best_matches([self.line('p0',0),self.line('p1',1),self.line('p2',2),self.line('p3',3)],self.probes)
        self.assertEqual([x['identity_band'] for x in rows],['high_ge96','high_ge96','intermediate_eq92','low_lt92','unresolved_no_hit_within_3_mismatches'])
    def test_tied_best_hits_not_interpretable(self):
        r=probe.sam_best_matches([self.line('p0',0,pos=1),self.line('p0',0,pos=100)],self.probes)
        self.assertFalse(r[0]['interpretable_probe']);self.assertEqual(r[0]['n_best_loci'],2)
    def test_best_stratum_selected(self):
        r=probe.sam_best_matches([self.line('p0',3),self.line('p0',1)],self.probes)
        self.assertEqual(r[0]['best_mismatches'],1)
    def test_missing_nm_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError,'missing_NM'):
            probe.sam_best_matches([self.line('p0',0).replace('NM:i:0','XX:i:0')],self.probes)
    def test_unknown_probe_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown_probe'):
            probe.sam_best_matches([self.line('alien',0)],self.probes)

class OOIAnnotationTests(unittest.TestCase):
    def setUp(self):
        self.t=[3999990000+i*20 for i in range(36)]
        self.v=[100+(i%7)*0.01 for i in range(36)]
        self.q=[1]*36
    def stamp(self,i):
        from datetime import timedelta
        return (hitl.NTP_EPOCH+timedelta(seconds=self.t[i])).isoformat()
    def test_hitl_cancels_synthetic_qartod_pass_spike(self):
        v=self.v[:];v[15]=150
        ann=[{'start':self.stamp(15),'end':self.stamp(15),'annotation':'HITL sensor outage'}]
        r=hitl.screen_with_annotations(self.t,v,self.q,ann)
        self.assertEqual(len(r['candidate_anomalies_before_annotation']),1)
        self.assertEqual(len(r['candidate_anomalies_after_annotation']),0)
        self.assertEqual(r['n_qartod_pass_overlapping_hitl'],1)
        self.assertFalse(r['physical_event_confirmed'])
    def test_clear_annotations_do_not_change_screen(self):
        r=hitl.screen_with_annotations(self.t,self.v,self.q,[])
        self.assertEqual(r['n_qartod_pass_overlapping_annotation'],0)
        self.assertEqual(r['n_original_qartod_pass_valid'],r['n_after_annotation_qartod_pass_valid'])
    def test_non_hitl_annotations_conservatively_excluded(self):
        ann=[{'start':self.stamp(10),'end':self.stamp(10),'annotation':'deployment maintenance'}]
        r=hitl.screen_with_annotations(self.t,self.v,self.q,ann)
        self.assertEqual(r['n_qartod_pass_overlapping_annotation'],1)
        self.assertEqual(r['n_qartod_pass_overlapping_hitl'],0)
    def test_unknown_timezone_rejected(self):
        with self.assertRaisesRegex(ValueError,'without_timezone'):
            hitl.normalize_annotations([{'start':'2026-01-01T00:00:00','end':'2026-01-01T00:01:00'}])
    def test_reversed_interval_rejected(self):
        with self.assertRaisesRegex(ValueError,'reversed_interval'):
            hitl.normalize_annotations([{'start':self.stamp(5),'end':self.stamp(4)}])
    def test_ms_epoch_annotation(self):
        from datetime import timedelta
        dt=hitl.NTP_EPOCH+timedelta(seconds=self.t[15]);ms=int(dt.timestamp()*1000)
        self.assertEqual(hitl.normalize_annotations([{'beginDT':ms,'endDT':ms}])[0]['start'],dt)
    def test_qartod_fail_not_counted_as_hitl_extra(self):
        q=self.q[:];q[15]=4
        ann=[{'start':self.stamp(15),'end':self.stamp(15),'annotation':'HITL'}]
        r=hitl.screen_with_annotations(self.t,self.v,q,ann)
        self.assertEqual(r['n_qartod_pass_overlapping_hitl'],0)

if __name__=='__main__':unittest.main()
