import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "validation/ooi_axial_hydrothermal.py"
spec = importlib.util.spec_from_file_location("ooi_axial", MODULE_PATH)
ooi = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ooi
spec.loader.exec_module(ooi)


class OOIValidation(unittest.TestCase):
    def setUp(self):
        self.t = [3999990000 + i*20 for i in range(36)]
        self.v = [100 + (i % 7)*0.01 for i in range(36)]
        self.q = [1]*36

    def test_baseline_realistic_no_spike(self):
        r = ooi.screen(self.t,self.v,self.q)
        self.assertEqual(r["status"], "SCREEN_COMPLETED_NOT_PHYSICALLY_VALIDATED")
        self.assertEqual(r["candidate_anomalies"],[])
        self.assertFalse(r["physical_event_confirmed"])

    def test_synthetic_spike_only_candidate(self):
        v=self.v[:];v[15]=150
        r=ooi.screen(self.t,v,self.q)
        self.assertEqual(len(r["candidate_anomalies"]),1)
        self.assertTrue(r["candidate_anomalies"][0]["not_a_confirmed_event"])

    def test_qartod_bad_spike_excluded(self):
        v=self.v[:];v[15]=150
        q=self.q[:];q[15]=4
        r=ooi.screen(self.t,v,q)
        self.assertEqual(len(r["candidate_anomalies"]),0)
        self.assertEqual(r["n_excluded"],1)

    def test_qartod_not_evaluated_rejected(self):
        q=[2]*36
        r=ooi.screen(self.t,self.v,q)
        self.assertEqual(r["status"],"INSUFFICIENT_QC_PASS_DATA")

    def test_missing_values_excluded(self):
        v=self.v[:];v[3]=-9999999.0
        r=ooi.screen(self.t,v,self.q)
        self.assertEqual(r["n_excluded"],1)

    def test_wrong_sensor_rejected(self):
        with self.assertRaisesRegex(ValueError,"sensor_not_escargot"):
            ooi.screen(self.t,self.v,self.q,sensor="TRHPHA302")

    def test_duplicate_timestamps_rejected(self):
        t=self.t[:];t[3]=t[2]
        with self.assertRaisesRegex(ValueError,"timestamps_not_strictly"):
            ooi.screen(t,self.v,self.q)

    def test_flag_ambiguity_rejected(self):
        q=self.q[:];q[3]=99
        with self.assertRaisesRegex(ValueError,"unknown_qartod"):
            ooi.screen(self.t,self.v,q)

    def test_zero_mad_cannot_claim_event(self):
        r=ooi.screen(self.t,[100]*36,self.q)
        self.assertEqual(r["status"],"INDETERMINATE_ZERO_MAD")
        self.assertEqual(r["candidate_anomalies"],[])

    def test_hdf5_fixture_end_to_end_not_real_measurement(self):
        import h5py
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/ooi.OOI_2026_08_04_FILENAME
            with h5py.File(p,"w") as f:
                f.create_dataset("time",data=self.t)
                f.create_dataset("vent_fluid_temperature",data=self.v)
                f.create_dataset("vent_fluid_temperature_qartod_results",data=self.q)
            r=ooi.analyze_file(p)
            self.assertEqual(r["n_total"],36)
            self.assertEqual(len(r["source_sha256"]),64)
            self.assertEqual(r["analysis_version"],"astra.ooi.axial.escargot.v1")

    def test_malformed_netcdf_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/ooi.OOI_2026_08_04_FILENAME
            p.write_text("not netCDF")
            with self.assertRaisesRegex(ValueError,"not_netcdf4"):
                ooi.analyze_file(p)


if __name__ == "__main__":
    unittest.main()
