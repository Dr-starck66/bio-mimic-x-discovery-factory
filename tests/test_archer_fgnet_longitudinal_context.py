import unittest
from validation.archer_fgnet_longitudinal_context import (
    parse_age, split_longitudinal, MIN_AGE_GAP, MIN_SUBJECTS, MIN_TESTS, MASK, METHODS
)


def r(stem, age):
    return (stem,age, {'aligned_full':None},stem)


class LongitudinalSplitTests(unittest.TestCase):
    def test_age_parser(self):
        self.assertEqual(parse_age('078A11'),('078',11))
        self.assertEqual(parse_age('fgnet/045A03b'),('045',3))
        with self.assertRaises(ValueError):parse_age('no_age')
        with self.assertRaises(ValueError):parse_age('001A101')

    def test_earliest_two_distinct_ages_fixed(self):
        rows={'001':[r('001A07',7),r('001A02',2),r('001A03',3),r('001A04',4)]}
        subjects,ignored=split_longitudinal(rows)
        self.assertEqual([x[1] for x in subjects['001']['enroll']],[2,3])
        self.assertEqual([x[1] for x in subjects['001']['test']],[7])
        self.assertEqual(subjects['001']['first_test_age_gap'],4)
        self.assertEqual(ignored,{})

    def test_same_age_photos_not_enrolled_together(self):
        rows={'001':[r('001A02a',2),r('001A02b',2),r('001A03',3),r('001A06',6)]}
        subjects,_=split_longitudinal(rows)
        self.assertEqual([x[1] for x in subjects['001']['enroll']],[2,3])
        self.assertEqual([x[1] for x in subjects['001']['test']],[6])

    def test_fail_closed_when_age_gap_missing(self):
        subjects,ignored=split_longitudinal({'001':[r('001A02',2),r('001A04',4),r('001A05',5)]})
        self.assertFalse(subjects)
        self.assertEqual(ignored['no_test_age_gap'],1)

    def test_duplicate_photo_sha_rejected(self):
        a=('001A02',2,{},'same')
        b=('001A04',4,{},'same')
        c=('001A07',7,{},'same')
        with self.assertRaisesRegex(ValueError,'Leakage'):
            split_longitudinal({'001':[a,b,c]})

    def test_constants_frozen(self):
        self.assertEqual(MIN_AGE_GAP,2)
        self.assertEqual(MIN_SUBJECTS,25)
        self.assertEqual(MIN_TESTS,100)
        self.assertEqual(MASK.shape,(64,64))
        self.assertEqual(METHODS,('pixels','hog','retina_pool'))

if __name__=='__main__':unittest.main()
