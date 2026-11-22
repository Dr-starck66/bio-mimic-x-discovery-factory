import csv
import tempfile
import unittest
from pathlib import Path
from validation.bsh_longevity_audit import auc, load_subjects, run

FIELDS = ["subject_id","group","cbh_K01442","recA","negative_control","sex","batch"]


def save(path, rows):
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def row(idx,grp,bsh,ctrl=10,sex="F",batch="batch1"):
    return dict(subject_id=f"sub{idx}",group=grp,cbh_K01442=bsh,recA=10,
                negative_control=ctrl,sex=sex,batch=batch)


class BshAuditTests(unittest.TestCase):
    def test_auc_ties(self):
        self.assertEqual(auc([2,2],[1,2]),.75)

    def test_reject_metadata_only(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"metadata.tsv"
            f.write_text("subject_id\tgroup\nA\tCentenarian\n")
            with self.assertRaisesRegex(ValueError,"Missing measured fields"):
                load_subjects(f)

    def test_subject_repeats_are_not_independent(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"values.tsv"
            x=row(1,"Centenarian",30)
            save(f,[x,x,row(2,"Elderly_control",10)])
            people=load_subjects(f)
            self.assertEqual(len(people),2)
            self.assertEqual(sum(z["replicates"] for z in people),3)

    def test_reject_conflicting_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"values.tsv"
            x=row(1,"Centenarian",30)
            y=row(1,"Elderly_control",10)
            save(f,[x,y])
            with self.assertRaisesRegex(ValueError,"contradictory"):
                load_subjects(f)

    def test_reject_invalid_reference(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"values.tsv"
            save(f,[row(1,"Centenarian",30)|{"recA":0}])
            with self.assertRaisesRegex(ValueError,"Zero recA"):
                load_subjects(f)

    def test_synthetic_association_not_predictive(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"synthetic.tsv"
            rows=[row(i,"Centenarian",30+i*.1) for i in range(20)]
            rows += [row(i+20,"Elderly_control",3+i*.1) for i in range(20)]
            save(f,rows)
            report=run(f,iterations=99)
            self.assertEqual(report["status"],"PARTIAL_ASSOCIATION_ONLY")
            self.assertEqual(report["bsh_auc_retrospective"],1.)
            self.assertEqual(report["negative_control_auc_retrospective"],.5)
            self.assertEqual(report["prospective_biomarker_validation"],"UNVERIFIED")
            self.assertFalse(report["metabolic_phenotype_measured"])

    def test_no_cross_group_strata_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"synthetic.tsv"
            rows=[row(i,"Centenarian",30,batch="case") for i in range(10)]
            rows +=[row(i+10,"Elderly_control",5,batch="control") for i in range(10)]
            save(f,rows)
            with self.assertRaisesRegex(ValueError,"no overlapping"):
                run(f,iterations=19)


if __name__=="__main__": unittest.main()
