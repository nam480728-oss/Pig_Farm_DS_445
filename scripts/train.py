import argparse,json,platform,subprocess,sys,hashlib
from pathlib import Path
import yaml

def main():
    p=argparse.ArgumentParser(); p.add_argument('--config',default='config/train.yaml'); p.add_argument('--device'); p.add_argument('--batch',type=int); p.add_argument('--smoke',action='store_true'); p.add_argument('--resume'); a=p.parse_args()
    cfg=yaml.safe_load(Path(a.config).read_text())
    if a.device is not None: cfg['device']=a.device
    if a.batch is not None: cfg['batch']=a.batch
    if a.smoke: cfg.update(epochs=1,name=cfg['name']+'_smoke',workers=0)
    from ultralytics import YOLO
    import torch,ultralytics
    if a.resume:
        if a.smoke: raise ValueError('resume and smoke incompatible')
        model=YOLO(a.resume); model.train(resume=True)
    else:
        from scripts.data_tools import audit
        report=audit(cfg['data'],None)
        if report['errors']: raise ValueError('Data audit failed: '+str(report['errors'][:5]))
        model=YOLO(cfg.pop('model')); model.train(**cfg)
    cfg=dict(model.trainer.args.__dict__)
    out=Path(model.trainer.save_dir)
    metadata={'python':platform.python_version(),'torch':torch.__version__,'ultralytics':ultralytics.__version__,
      'cuda':torch.cuda.is_available(),'mps':bool(hasattr(torch.backends,'mps') and torch.backends.mps.is_available()),
      'smoke':a.smoke,'resume':a.resume,'config':cfg,'data_yaml_sha256':hashlib.sha256(Path(cfg['data']).read_bytes()).hexdigest() if isinstance(cfg.get('data'),str) and Path(cfg['data']).is_file() else None}
    (out/'environment.json').write_text(json.dumps(metadata,indent=2))
    freeze=subprocess.run([sys.executable,'-m','pip','freeze'],text=True,capture_output=True,check=True)
    (out/'requirements-lock.txt').write_text(freeze.stdout)
if __name__=='__main__': main()
