# Dataset integration — member 4 / Apple Silicon M5

## Confirmed from screenshots

The dataset is **already in YOLO detection format** (not COCO JSON):

```
pig_det/
  images/{train,val,test}/<image>.jpg
  labels/{train,val,test}/<same-stem>.txt
```

Each label line contains `0 x_center y_center width height`, normalized to 0–1. Class 0 = pig. No COCO conversion or dataset re-splitting is needed. Screenshots show RGB and grayscale/night scenes; these are examples, not proof of the full dataset composition.

## Folder placement

Keep `pig_det` as a **sibling** of `BaoNguyen` (as shown in VS Code). Alternatively, place it inside `BaoNguyen/pig_det`, `BaoNguyen/data/pig_det`, or `BaoNguyen/data/PigDetectYOLO`. Dataset detection supports all four. Never move or rename images just to satisfy a hardcoded path.

## Run from BaoNguyen project root

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-train.txt
python -m scripts.doctor
python -m scripts.prepare_data
python -m scripts.data_tools visualize --data config/data.yaml --out reports/label_preview
python -m unittest discover -s tests -v
python -m scripts.train --smoke --batch 2
python -m scripts.train --batch 4
```

The first `prepare_data` call discovers the dataset, writes an absolute path into `config/data.yaml`, audits all splits, checks image/label pairs and normalized boxes, and produces `reports/data_audit`. It **does not edit** the original data. Training also auto-configures the dataset when using default config. For a different location, use `--dataset /absolute/path/to/pig_det` with `prepare_data` or `train`.

## Team contract

- Ultralytics pinned to `8.4.48`.
- Final export is `pig_set.pt`, after training/evaluation/packaging, not an untrained placeholder.
- Expand **predicted** boxes by 12% in total (6% on each side), once, for downstream crop/count/escape processing; leave ground-truth labels and YOLO AP evaluation untouched. Confirm the meaning of “12%” with team if they intended 12% on each side.
- M5: prefer MPS if available; start batch 2 for smoke and batch 4 for full training, reduce if out of memory.
- Keep test split reserved for final evaluation; tune against validation split only.

## Important limitations

Only folder layout and a few example labels are visible in screenshots. The dataset itself is not included in this ZIP; full audit, actual M5 training, AP metrics, and model export require running these commands with the local dataset. A smoke run validates the pipeline, not model quality.
