import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "factory"))

import ecosystem_gbif_ingest as gbif


class TestGBIFEcosystemIngest(unittest.TestCase):
    def test_complete_month_windows_excludes_current_month(self):
        windows = gbif.complete_month_windows(3, date(2026, 9, 26))
        self.assertEqual(
            windows,
            [
                (date(2026, 6, 1), date(2026, 6, 30)),
                (date(2026, 7, 1), date(2026, 7, 31)),
                (date(2026, 8, 1), date(2026, 8, 31)),
            ],
        )

    def test_aggregate_records_counts_occurrences_not_abundance(self):
        records = [
            {"key": 2, "species": "Phoenicopterus roseus", "datasetKey": "d1", "license": "CC_BY_4_0"},
            {"key": 1, "species": "Phoenicopterus roseus", "datasetKey": "d1", "license": "CC_BY_4_0"},
            {"key": 3, "species": "Anas platyrhynchos", "datasetKey": "d2", "license": "CC0_1_0"},
            {"key": 4, "genus": "Anas"},
        ]
        got = gbif.aggregate_records(records)
        self.assertEqual(got["taxa"]["Phoenicopterus roseus"], 2)
        self.assertEqual(got["taxa"]["Anas platyrhynchos"], 1)
        self.assertEqual(got["records_used"], 3)
        self.assertEqual(got["records_without_species_resolution"], 1)
        self.assertEqual(len(got["gbif_id_sha256"]), 64)
        self.assertEqual(got["dataset_keys"], ["d1", "d2"])

    def test_fetch_month_refuses_truncation(self):
        config = {
            "study_area": {"bbox": {"min_lon": 4.48, "max_lon": 4.68, "min_lat": 43.44, "max_lat": 43.59}},
            "source": {"max_records_per_month": 2, "basis_of_record": ["HUMAN_OBSERVATION"]},
        }

        def fake(url, timeout=30):
            return {"count": 3, "results": []}

        with self.assertRaises(RuntimeError):
            gbif.fetch_month(config, date(2026, 8, 1), date(2026, 8, 31), fetcher=fake)

    def test_build_document_keeps_provenance_and_semantics(self):
        config = {
            "ecosystem_id": "test-wetland",
            "study_area": {
                "label": "test",
                "area_semantics": "test rectangle",
                "bbox": {"min_lon": 4.48, "max_lon": 4.68, "min_lat": 43.44, "max_lat": 43.59},
            },
            "source": {
                "basis_of_record": ["HUMAN_OBSERVATION"],
                "lookback_complete_months": 2,
                "minimum_observation_months": 2,
                "max_records_per_month": 100,
            },
        }

        def fake(url, timeout=30):
            return {
                "count": 2,
                "results": [
                    {"key": 10, "species": "Species alpha", "datasetKey": "d1", "license": "CC_BY_4_0"},
                    {"key": 11, "species": "Species beta", "datasetKey": "d1", "license": "CC_BY_4_0"},
                ],
            }

        doc = gbif.build_document(config, fetcher=fake, today=date(2026, 9, 26))
        self.assertEqual(doc["measurement_semantics"], "GBIF_OCCURRENCE_RECORD_COUNT_NOT_ABUNDANCE")
        self.assertEqual(len(doc["observations"]), 2)
        self.assertEqual(doc["source"]["provider"], "GBIF")
        self.assertTrue(all(o["provenance"]["provider"] == "GBIF" for o in doc["observations"]))
        self.assertTrue(all(len(o["provenance"]["record_id_sha256"]) == 64 for o in doc["observations"]))
        self.assertEqual(len(doc["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
