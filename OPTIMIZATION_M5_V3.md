# Pig detection — M5 optimization and integration contract (v3)

## Scope
This release concerns **team member 4**: pig detection, stable count by session, and escape detection. It does not replace the weight, health, human-detection or webapp modules owned by other members.

## Non-negotiable contracts
- Detection model: YOLO11l, image size 960, 1 class `pig` with class id 0; `ultralytics==8.4.48`.
- Trained **handover** checkpoint: `pig_set.pt`. Never rename the initial `yolo11l.pt` pretrained checkpoint to `pig_set.pt`.
- Expand *predicted* bounding-box width and height by 12% around its center (6% on each side), clip to image. Do **not** enlarge source labels or change original box used by tracker without team agreement. Apply this consistently at the agreed crop/output interface. The team must verify whether 12% means total dimensions or each side.
- Preserve existing `train/val/test` splits. The test split is reserved for final reporting.
- Counting: use per-second observations and the maximum count maintained at least 5 seconds; missing count triggers a second count before `dem_thieu`; successful count produces `dem_du`.
- Escape: complete bounding box outside pen for 5 continuous seconds; emit `lac_chuong`, urgent with red-box evidence, with 300-second cooldown. **Clarify with team** whether the expanded or original box is used for the all-outside geometry test: expanded box is more conservative.
- Event payload: `loai`, `o`, `thoi_gian`, `muc`, `anh`, `du_lieu`.

## Mac M5 setup
From inside the extracted `BaoNguyen` directory (which should be next to `pig_det`):

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-train.txt
python -m scripts.preflight
python -m scripts.data_tools visualize --data config/data.yaml --out reports/label_preview
python -m scripts.train --smoke --batch 2
python -m scripts.train --batch 4
```

If memory pressure occurs, retry training with `--batch 2` (or `--batch 1`). The training config uses `workers: 0` for safer macOS behavior. `device: auto` selects Apple MPS when supported. Do not assume the M5 will train YOLO11l faster than a dedicated NVIDIA GPU. Keep Mac powered and sufficiently cooled. If MPS encounters unsupported operations, diagnose the actual error before switching to CPU or setting `PYTORCH_ENABLE_MPS_FALLBACK=1`.

### Evaluation and handover

```bash
python -m scripts.evaluate --weights runs/detect/pig_set_baseline/weights/best.pt --split val
python -m scripts.evaluate --weights runs/detect/pig_set_baseline/weights/best.pt --split test
python -m scripts.package_model --weights runs/detect/pig_set_baseline/weights/best.pt --metrics PATH_TO_TEST_METRICS_JSON --out models/handover
```

Replace `PATH_TO_TEST_METRICS_JSON` with the actual `metrics.json` written by evaluation. Do not treat smoke-run checkpoints as final deliverables. Record mAP50 and mAP50-95 separately; confirm which metric the team's AP>=80 target means. Save actual training loss/metrics and per-day/per-night test results, not synthetic benchmark figures.

## Quality gates
1. Preflight validates image-label pairing, class ID, normalized bounding boxes, split contents, and exact duplicate images across splits.
2. Visually review bounding boxes from each split; automated checks cannot prove that boxes match pigs.
3. Train on `train`, select using `val`, report on `test` once model selection is complete.
4. Test stable counting and escape logic on real video, with manually annotated ground truth; synthetic unit tests are not evidence of real-world performance.
5. Handover `pig_set.pt`, metrics, model card, box-expansion convention and event schema to the integrator.

## Known limits
The dataset is not embedded in this ZIP. The images provided in chat show YOLO-format structure and examples, but do not establish total dataset integrity. Full dataset preflight and actual M5 training must be executed on the user's Mac.
