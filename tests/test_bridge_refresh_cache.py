import unittest
from datetime import datetime, timezone
import human_bridge_refresh as refresh

class TestBridgeRefreshCache(unittest.TestCase):
    def test_recent_verified_bridge_survives_one_transient_miss(self):
        now=datetime.now(timezone.utc).isoformat()
        cycle={
            "bridge_refresh":{"time":now},
            "human_bridge_result":{
                "bridges":[{
                    "animal_species":"Danio rerio",
                    "animal_gene":"VEGF",
                    "animal_ensembl_species":"danio_rerio",
                    "human_ensembl_id":"ENSG00000112715",
                    "human_symbol":"VEGFA",
                    "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                    "clinical_efficacy_claim":False,
                    "orthology":{}
                }]
            }
        }
        result={
            "attempted_candidates":1,
            "bridged_candidates":0,
            "coverage_ratio":0,
            "bridges":[],
            "candidate_status":[{"candidate":"Danio rerio","status":"NO_VALIDATED_ORTHOLOGUE","bridges":0}],
            "provider_status":{}
        }
        claims=[{"subject":"Danio rerio","status":"SUPPORTED"}]
        got=refresh.retain_last_known_good_strict(cycle,result,claims)
        self.assertEqual(got["bridged_candidates"],1)
        self.assertEqual(got["coverage_ratio"],1.0)
        self.assertEqual(got["cached_subjects"],["Danio rerio"])
        self.assertEqual(got["candidate_status"][0]["status"],"BRIDGED_CACHED")
        self.assertEqual(got["bridges"][0]["verification_mode"],"LAST_KNOWN_GOOD_CACHE")

    def test_cache_expires_after_two_consecutive_misses(self):
        now=datetime.now(timezone.utc).isoformat()
        cycle={
            "bridge_refresh":{"time":now},
            "human_bridge_result":{
                "bridges":[{
                    "animal_species":"Danio rerio",
                    "animal_gene":"VEGF",
                    "animal_ensembl_species":"danio_rerio",
                    "human_ensembl_id":"ENSG00000112715",
                    "human_symbol":"VEGFA",
                    "translation_status":"ORTHOLOGUE_AND_HUMAN_TARGET_VERIFIED",
                    "clinical_efficacy_claim":False,
                    "orthology":{},
                    "verification_mode":"LAST_KNOWN_GOOD_CACHE",
                    "last_live_verified_at":now,
                    "cache_miss_count":2
                }]
            }
        }
        result={
            "attempted_candidates":1,
            "bridged_candidates":0,
            "coverage_ratio":0,
            "bridges":[],
            "candidate_status":[{"candidate":"Danio rerio","status":"NO_VALIDATED_ORTHOLOGUE","bridges":0}],
            "provider_status":{}
        }
        claims=[{"subject":"Danio rerio","status":"SUPPORTED"}]
        got=refresh.retain_last_known_good_strict(cycle,result,claims)
        self.assertEqual(got["bridged_candidates"],0)
        self.assertEqual(got["cached_bridged_candidates"],0)

    def test_unverified_old_record_is_never_cached(self):
        now=datetime.now(timezone.utc).isoformat()
        cycle={
            "bridge_refresh":{"time":now},
            "human_bridge_result":{
                "bridges":[{
                    "animal_species":"Danio rerio",
                    "animal_gene":"VEGF",
                    "human_ensembl_id":"ENSG00000112715",
                    "translation_status":"UNVERIFIED",
                    "orthology":{"provider":"OMA"}
                }]
            }
        }
        result={
            "attempted_candidates":1,
            "bridged_candidates":0,
            "coverage_ratio":0,
            "bridges":[],
            "candidate_status":[{"candidate":"Danio rerio","status":"NO_VALIDATED_ORTHOLOGUE","bridges":0}],
            "provider_status":{}
        }
        claims=[{"subject":"Danio rerio","status":"SUPPORTED"}]
        got=refresh.retain_last_known_good_strict(cycle,result,claims)
        self.assertEqual(got["bridged_candidates"],0)

if __name__=="__main__":
    unittest.main()
