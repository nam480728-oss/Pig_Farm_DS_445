import unittest
from src.box_policy import expand_xyxy

class BoxPolicyTests(unittest.TestCase):
    def test_expands_12_percent_total(self):
        self.assertEqual(expand_xyxy([10,20,110,70],200,100), [4.,17.,116.,73.])
    def test_clips_edges(self):
        self.assertEqual(expand_xyxy([0,0,100,100],100,100), [0.,0.,100.,100.])
    def test_rejects_invalid(self):
        with self.assertRaises(ValueError): expand_xyxy([10,10,5,20],100,100)

if __name__ == '__main__': unittest.main()
