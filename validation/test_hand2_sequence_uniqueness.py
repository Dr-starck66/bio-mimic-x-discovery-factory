import random
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from validation.hand2_sequence_uniqueness import scan, reverse_complement

class TestHand2SequenceScreen(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"assembly.fa"
        random.seed(77)
        self.query="".join(random.choices("ACGT",k=160))
    def write(self,seq):
        self.path.write_text(">chrTest\n"+seq+"\n")
    def test_both_strands_and_coordinates(self):
        self.write("N"*50+self.query+"N"*100+reverse_complement(self.query)+"N"*50)
        result=scan(self.query,[self.path],k=15,stride=9)
        self.assertEqual([(x["strand"],x["start_1based"]) for x in result["candidates"]],[("+",51),("-",311)])
    def test_substitution(self):
        changed=self.query[:70]+("A" if self.query[70]!="A" else "C")+self.query[71:]
        self.write("N"*20+changed+"N"*20)
        r=scan(self.query,[self.path],k=15,stride=9)
        self.assertEqual(r["candidate_count"],1)
        self.assertEqual(r["candidates"][0]["substitutions"],1)
    def test_no_false_uniqueness(self):
        self.write("N"*20+self.query+"N"*20)
        self.assertEqual(scan(self.query,[self.path],k=15,stride=9)["whole_genome_unique"],"UNVERIFIED")
    def test_repeats(self):
        self.write("A"*200000)
        r=scan("A"*160,[self.path],k=15,stride=9)
        self.assertEqual(r["whole_genome_unique"],"UNVERIFIED")
        self.assertGreater(r["candidate_count"],1)
if __name__=="__main__":unittest.main()
