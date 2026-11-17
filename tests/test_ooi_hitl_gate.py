import sys,unittest,json,tempfile
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'validation'))
import ooi_hitl_gate as h

T=[3999990000+i*20 for i in range(36)]
D=h.NTP_EPOCH
start=(D+h.timedelta(seconds=T[9])).isoformat()
end=(D+h.timedelta(seconds=T[11])).isoformat()

def hitl(flag=4,**extra):
    return {'refdes':h.SENSOR,'beginDT':start,'endDT':end,'qcFlag':flag,**extra}

class HITL(unittest.TestCase):
 def test_reject_bad_time(self):
    with self.assertRaisesRegex(ValueError,'timezone'):h.parse_annotations([hitl(beginDT='2026-08-04T11:00:00')])
 def test_reject_wrong_interval(self):
    with self.assertRaisesRegex(ValueError,'negative_interval'):h.parse_annotations([hitl(beginDT=end,endDT=start)])
 def test_reject_unknown_qc(self):
    with self.assertRaisesRegex(ValueError,'qc_flag'):h.parse_annotations([hitl(7)])
 def test_milliseconds(self):
    r=h.parse_annotations([hitl(beginDT=1785844212192,endDT=1785844252192)])[0]
    self.assertEqual(r['start'].year,2026)
 def test_no_second_timestamp_ambiguity(self):
    with self.assertRaisesRegex(ValueError,'milliseconds'):h.parse_annotations([hitl(beginDT=1785844212)])
 def test_ignore_other_sensor(self):
    rec=hitl(refdes='RS03INT1-MJ03C-09-TRHPHA302')
    self.assertEqual(h.parse_annotations([rec]),[])
 def test_qartod_pass_overridden_by_human_failure(self):
    mask,gate=h.apply_hitl(T,[1]*36,h.parse_annotations([hitl(4)]))
    self.assertEqual(gate['n_hitl_excluded_from_qartod_pass'],3)
    self.assertEqual(mask[9:12],[4,4,4])
 def test_unclassified_annotation_fails_closed(self):
    mask,gate=h.apply_hitl(T,[1]*36,h.parse_annotations([hitl(None)]))
    self.assertEqual(gate['unclassified_annotation_indices'],[9,10,11])
    self.assertEqual(gate['n_hitl_excluded_from_qartod_pass'],3)
 def test_information_only_pass_kept(self):
    mask,gate=h.apply_hitl(T,[1]*36,h.parse_annotations([hitl(1)]))
    self.assertEqual(mask,[1]*36)
    self.assertEqual(gate['hitl_pass_annotated_indices'],[9,10,11])
 def test_outside_annotated_interval_untouched(self):
    mask,gate=h.apply_hitl(T,[1]*36,h.parse_annotations([hitl(4)]))
    self.assertEqual(mask[8],1); self.assertEqual(mask[12],1)
 def test_original_fail_retained(self):
    orig=[1]*36;orig[10]=4
    mask,gate=h.apply_hitl(T,orig,h.parse_annotations([hitl(4)]))
    self.assertEqual(mask[10],4);self.assertEqual(gate['n_hitl_excluded_from_qartod_pass'],2)
 def test_empty_official_export_not_auto_fabricate(self):
    mask,gate=h.apply_hitl(T,[1]*36,h.parse_annotations([]))
    self.assertEqual(mask,[1]*36);self.assertEqual(gate['n_hitl_excluded_from_qartod_pass'],0)
 def test_sensor_missing_identity_not_assumed(self):
    self.assertEqual(h.parse_annotations([{'beginDT':start,'endDT':end,'qcFlag':4}]),[])
 def test_improper_structure_rejected(self):
    with self.assertRaisesRegex(ValueError,'list'):h.parse_annotations({'foo':[]})

if __name__=='__main__':unittest.main()
