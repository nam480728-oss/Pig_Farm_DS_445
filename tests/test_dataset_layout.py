import tempfile,unittest
from pathlib import Path
from scripts.dataset_layout import locate,configure
import yaml
class DatasetLayoutTest(unittest.TestCase):
    def test_sibling_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            parent=Path(td); project=parent/'BaoNguyen'; (project/'config').mkdir(parents=True)
            root=parent/'pig_det'
            for s in ('train','val','test'):
                (root/'images'/s).mkdir(parents=True)
                (root/'labels'/s).mkdir(parents=True)
            self.assertEqual(locate(project),root)
            self.assertEqual(configure(project),root)
            data=yaml.safe_load((project/'config'/'data.yaml').read_text())
            self.assertEqual(data['path'],str(root))
            self.assertEqual(data['names'],{0:'pig'})
    def test_missing_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError): locate(Path(td)/'project')
if __name__=='__main__':unittest.main()
