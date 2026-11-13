import unittest
from scripts.preflight import REQUIRED_VERSION
from src.box_policy import expand_xyxy

class PreflightContractTest(unittest.TestCase):
    def test_ultralytics_pin(self):
        self.assertEqual(REQUIRED_VERSION, '8.4.48')
    def test_12_percent_total_size(self):
        self.assertEqual(expand_xyxy([20,20,120,70], 200,100), [14.,17.,126.,73.])
    def test_edge_clip(self):
        self.assertEqual(expand_xyxy([0,0,100,50],100,50), [0.,0.,100.,50.])

if __name__ == '__main__':
    unittest.main()
