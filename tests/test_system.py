import unittest,tempfile,json,copy,subprocess,sys
from pathlib import Path
from PIL import Image
from src.geometry import validate_polygon,inside,outside
from src.counting import CountSession
from src.escape import EscapeDetector
from src.contracts import validate_frame,validate_event
from src.metrics import event_metrics,count_metrics
from src.engine import Engine
from scripts.replay import run
from scripts.data_tools import audit,visualize

P=[[0,0],[10,0],[10,10],[0,10]]
class GeometryTests(unittest.TestCase):
    def test_inside(self):self.assertTrue(inside((5,5),P))
    def test_boundary(self):self.assertTrue(inside((0,5),P))
    def test_outside(self):self.assertTrue(outside([11,1,15,5],P))
    def test_touch(self):self.assertFalse(outside([10,1,15,5],P))
    def test_overlap(self):self.assertFalse(outside([8,8,12,12],P))
    def test_encloses(self):self.assertFalse(outside([-1,-1,11,11],P))
    def test_cross_no_corner(self):self.assertFalse(outside([0,0,10,10],[[4,-5],[6,-5],[6,15],[4,15]]))
    def test_concave(self):self.assertTrue(outside([6,6,9,9],[[0,0],[10,0],[10,3],[3,3],[3,10],[0,10]]))
    def test_self_cross(self):
        with self.assertRaises(ValueError):validate_polygon([[0,0],[10,10],[10,0],[0,10]])
    def test_duplicate(self):
        with self.assertRaises(ValueError):validate_polygon(P+[P[0]])
    def test_zero_area(self):
        with self.assertRaises(ValueError):validate_polygon([[0,0],[1,1],[2,2]])

class CountTests(unittest.TestCase):
    def test_full(self):
        c=CountSession(2,duration=5,recount=5)
        for t in range(5):r=c.sample(t,2,'x')
        self.assertEqual(r['status'],'dem_du')
    def test_recount_short(self):
        c=CountSession(2,duration=5,recount=5)
        for t in range(10):r=c.sample(t,1,'x')
        self.assertEqual(r['status'],'dem_thieu');self.assertEqual(len(c.phase_history),2)
    def test_recount_recovers(self):
        c=CountSession(2,duration=5,recount=5)
        for t in range(10):r=c.sample(t,1 if t<5 else 2,'x')
        self.assertEqual(r['status'],'dem_du')
    def test_spike(self):
        c=CountSession(2,duration=5,recount=5)
        for t,n in enumerate([2,2,9,2,2]):r=c.sample(t,n,'x')
        self.assertEqual(r['count'],2)
    def test_over(self):
        c=CountSession(2,duration=5,recount=5)
        for t in range(5):r=c.sample(t,3,'x')
        self.assertEqual(r['status'],'overcount_review')
    def test_gap(self):
        c=CountSession(2,duration=5,recount=5)
        for t in [0,1,5]:r=c.sample(t,2,'x')
        self.assertEqual(r['status'],'insufficient_data')
    def test_nonmonotonic(self):
        c=CountSession(1);c.sample(1,1,'x')
        with self.assertRaises(ValueError):c.sample(1,1,'x')
    def test_bad_config(self):
        with self.assertRaises(ValueError):CountSession(0)

class EscapeTests(unittest.TestCase):
    def test_exact_five(self):
        e=EscapeDetector()
        for t in range(5):self.assertEqual(e.update('A',t,[1]),[])
        self.assertEqual(e.update('A',5,[1]),[1])
    def test_reentry_reset(self):
        e=EscapeDetector();e.update('A',0,[1]);e.update('A',1,[])
        self.assertEqual(e.update('A',5,[1]),[])
    def test_gap_reset(self):
        e=EscapeDetector();e.update('A',0,[1]);self.assertEqual(e.update('A',5,[1]),[])
    def test_cooldown(self):
        e=EscapeDetector();alerts=[]
        for t in range(306):
            if e.update('A',t,[1]):alerts.append(t)
        self.assertEqual(alerts,[5,305])
    def test_id_switch(self):
        e=EscapeDetector()
        for t in range(5):e.update('A',t,[1])
        self.assertEqual(e.update('A',5,[2]),[])
    def test_multiple_ready(self):
        e=EscapeDetector()
        for t in range(6):r=e.update('A',t,[1,2])
        self.assertEqual(r,[1,2])
    def test_clock(self):
        e=EscapeDetector();e.update('A',2,[])
        with self.assertRaises(ValueError):e.update('A',1,[])

class ContractTests(unittest.TestCase):
    def frame(self):return dict(t=0,size=[10,10],pen='A',wall_time='2026-11-06T00:00:00+07:00',detections=[dict(bbox=[1,1,3,3],confidence=.9,class_id=0,track_id=1)])
    def test_valid(self):validate_frame(self.frame())
    def test_bad_bbox(self):
        f=self.frame();f['detections'][0]['bbox']=[1,1,15,3]
        with self.assertRaises(ValueError):validate_frame(f)
    def test_naive_clock(self):
        f=self.frame();f['wall_time']='2026-11-06T00:00:00'
        with self.assertRaises(ValueError):validate_frame(f)
    def test_duplicate_id(self):
        f=self.frame();f['detections']*=2
        with self.assertRaises(ValueError):validate_frame(f)
    def test_invalid_event(self):
        with self.assertRaises(ValueError):validate_event({})

class MetricsTests(unittest.TestCase):
    def test_one_to_one(self):
        g=[dict(pen='A',kind='lac_chuong',t=5)]
        r=event_metrics(g,g*2);self.assertEqual((r['tp'],r['fp'],r['fn']),(1,1,0))
    def test_empty(self):self.assertIsNone(event_metrics([],[])['precision'])
    def test_wrong_pen(self):
        r=event_metrics([dict(pen='A',kind='x',t=0)],[dict(pen='B',kind='x',t=0)])
        self.assertEqual(r['tp'],0)
    def test_count_metric(self):self.assertEqual(count_metrics([(2,2),(2,1)])['mae'],.5)

class IntegrationTests(unittest.TestCase):
    def test_replay_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            engine=run('examples/demo_config.json','examples/frames.jsonl',td)
            self.assertEqual([e['loai'] for e in engine.events],['lac_chuong','dem_thieu'])
            for e in engine.events:
                validate_event(e);self.assertTrue(Path(e['anh']).exists())
            self.assertEqual(engine.counter.phase,'done')
    def test_resize_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=json.loads(Path('examples/demo_config.json').read_text());e=Engine(cfg,td)
            f=json.loads(Path('examples/frames.jsonl').read_text().splitlines()[0]);f['size']=[1000,1000]
            with self.assertRaises(ValueError):e.process(f)
    def test_missing_image(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=json.loads(Path('examples/demo_config.json').read_text());e=Engine(cfg,td)
            f=json.loads(Path('examples/frames.jsonl').read_text().splitlines()[0]);f['image']='absent.png'
            with self.assertRaises(FileNotFoundError):e.process(f)
    def test_analysis(self):
        from scripts.analyze import analyze
        with tempfile.TemporaryDirectory() as td:
            r=analyze('examples/SYNTHETIC_results.csv',td)
            self.assertEqual(r['epochs'],3);self.assertTrue((Path(td)/'loss.png').exists())

class DatasetTests(unittest.TestCase):
    def setup_data(self,td):
        import yaml
        root=Path(td)
        for i,s in enumerate(['train','val','test']):
            (root/'images'/s).mkdir(parents=True);(root/'labels'/s).mkdir(parents=True)
            Image.new('RGB',(20,20),(i*70,10,20)).save(root/'images'/s/'x.png')
            (root/'labels'/s/'x.txt').write_text('0 0.5 0.5 0.4 0.4')
        cfg=root/'data.yaml';cfg.write_text(yaml.safe_dump(dict(path=str(root.resolve()),train='images/train',val='images/val',test='images/test',names={0:'pig'})))
        return cfg
    def test_valid_audit_visualize(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self.setup_data(td);r=audit(cfg,Path(td)/'out');self.assertFalse(r['errors']);visualize(cfg,Path(td)/'viz');self.assertEqual(len(list((Path(td)/'viz').glob('*.jpg'))),3)
    def test_invalid_label(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self.setup_data(td);(Path(td)/'labels/train/x.txt').write_text('0 nan .5 1 1');self.assertTrue(audit(cfg,None)['errors'])
    def test_duplicate_split(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            cfg=self.setup_data(td);shutil.copy2(Path(td)/'images/train/x.png',Path(td)/'images/test/x.png');self.assertTrue(audit(cfg,None)['errors'])
    def test_missing_label(self):
        with tempfile.TemporaryDirectory() as td:
            cfg=self.setup_data(td);(Path(td)/'labels/train/x.txt').unlink();self.assertTrue(audit(cfg,None)['errors'])

class PackagingTests(unittest.TestCase):
    def test_package_actual_hash(self):
        import hashlib
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);w=root/'dummy.pt';w.write_bytes(b'SYNTHETIC NOT A MODEL')
            m=root/'metrics.json';m.write_text(json.dumps({'weights_sha256':hashlib.sha256(w.read_bytes()).hexdigest(),'split':'test'}))
            result=subprocess.run([sys.executable,'-m','scripts.package_model','--weights',str(w),'--metrics',str(m),'--out',str(root/'handover')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertTrue((root/'handover/model_card.json').exists())
    def test_package_reject_wrong_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);w=root/'dummy.pt';w.write_bytes(b'SYNTHETIC')
            m=root/'metrics.json';m.write_text(json.dumps({'weights_sha256':'wrong','split':'test'}))
            result=subprocess.run([sys.executable,'-m','scripts.package_model','--weights',str(w),'--metrics',str(m),'--out',str(root/'handover')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)

if __name__=='__main__':unittest.main()
