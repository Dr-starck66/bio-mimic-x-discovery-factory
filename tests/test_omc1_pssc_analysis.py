import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from omc1_pssc_analysis import analyze


class OMC1PSSCTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'toy_not_real_science.csv'

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, groups):
        with self.path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['oocyte_id', 'animal_id', 'experiment_id', 'age_weeks', 'genotype', 'pssc'])
            writer.writeheader()
            for batch, genotype, animal, values in groups:
                for i, value in enumerate(values):
                    writer.writerow(dict(oocyte_id=f'{animal}-{i}', animal_id=animal, experiment_id=batch,
                                         age_weeks='8', genotype=genotype, pssc=str(value)))

    def standard(self):
        return [('b1', 'WT', 'w1', [0, 0, 1, 0]), ('b1', 'KO', 'k1', [1, 1, 1, 0]),
                ('b2', 'WT', 'w2', [0, 0, 0, 0]), ('b2', 'KO', 'k2', [1, 1, 1, 1])]

    def test_cluster_difference_and_exact_permutations(self):
        self.write(self.standard())
        r = analyze(self.path, 100)
        self.assertAlmostEqual(r['difference_KO_minus_WT'], 0.75)
        self.assertEqual(r['n_animals'], {'KO': 2, 'WT': 2})
        self.assertEqual(r['number_of_permutations'], 4)
        self.assertEqual(r['exact_stratified_permutation_p_two_sided'], 0.5)
        self.assertEqual(r['n_oocytes'], {'KO': 8, 'WT': 8})
        self.assertEqual(len(r['source_sha256']), 64)

    def test_null_effect(self):
        self.write([('b1', 'WT', 'w1', [1, 0]), ('b1', 'KO', 'k1', [1, 0]),
                    ('b2', 'WT', 'w2', [0, 1]), ('b2', 'KO', 'k2', [0, 1])])
        self.assertEqual(analyze(self.path, 100)['exact_stratified_permutation_p_two_sided'], 1)

    def test_reject_missing_animal_replicates(self):
        self.write([('b1', 'WT', 'w1', [0, 0]), ('b1', 'KO', 'k1', [1, 1])])
        with self.assertRaisesRegex(ValueError, 'two independent animals'):
            analyze(self.path, 100)

    def test_reject_batch_confounding(self):
        self.write([('b1', 'WT', 'w1', [0]), ('b1', 'WT', 'w2', [0]),
                    ('b2', 'KO', 'k1', [1]), ('b2', 'KO', 'k2', [1])])
        with self.assertRaisesRegex(ValueError, 'lacks a WT or KO'):
            analyze(self.path, 100)

    def test_reject_duplicate_oocyte(self):
        self.write(self.standard())
        with self.path.open('a') as f:
            f.write('w1-0,w1,b1,8,WT,0\n')
        with self.assertRaisesRegex(ValueError, 'Duplicate oocyte'):
            analyze(self.path, 100)

    def test_reject_missing_required_column(self):
        self.path.write_text('animal_id,genotype\nw1,WT\n')
        with self.assertRaisesRegex(ValueError, 'Missing required'):
            analyze(self.path, 100)

    def test_reject_non_binary_outcome(self):
        self.write(self.standard())
        s = self.path.read_text().replace('8,KO,1', '8,KO,2', 1)
        self.path.write_text(s)
        with self.assertRaisesRegex(ValueError, 'Invalid PSSC'):
            analyze(self.path, 100)

    def test_reject_inconsistent_genotype(self):
        self.write(self.standard())
        with self.path.open('a') as f:
            f.write('z,w1,b1,8,KO,1\n')
        with self.assertRaisesRegex(ValueError, 'inconsistent genotype'):
            analyze(self.path, 100)

    def test_reject_missing_week8(self):
        self.write(self.standard())
        self.path.write_text(self.path.read_text().replace(',8,', ',4,'))
        with self.assertRaisesRegex(ValueError, 'No age-8-week'):
            analyze(self.path, 100)


if __name__ == '__main__':
    unittest.main()
