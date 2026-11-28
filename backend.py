import json
import os
import threading
import time
import traceback
from pathlib import Path
from typing import Any
import cv2
import numpy as np
import torch
import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent


def resolve_model() -> Path:
    env_model = os.getenv("YOLO_MODEL")
    if env_model:
        return Path(env_model)
    for name in ("pig_set.engine", "pig_set.pt"):
        p = BASE_DIR / name
        if p.exists():
            return p
    return BASE_DIR / "pig_set.pt"


MODEL_PATH = resolve_model()
TRACKER_CFG = BASE_DIR / "bytetrack_pig.yaml"
HAS_CUDA = torch.cuda.is_available()
DEVICE = 0 if HAS_CUDA else "cpu"
CONF = float(os.getenv("CONF", "0.28"))
IOU = float(os.getenv("IOU", "0.5"))
IMGSZ = int(os.getenv("IMGSZ", "640" if HAS_CUDA else "320"))
MIN_AREA_RATIO = 0.0045

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Khong tim thay model: {MODEL_PATH}. Hay dat pig_set.pt canh backend.py."
    )

TRACKER_CFG.write_text(
    "tracker_type: bytetrack\n"
    "track_high_thresh: 0.40\n"
    "track_low_thresh: 0.15\n"
    "new_track_thresh: 0.45\n"
    "track_buffer: 45\n"
    "match_thresh: 0.90\n"
    "fuse_score: True\n",
    encoding="utf-8",
)

model = YOLO(str(MODEL_PATH), task="detect")
_dummy = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
model.track(
    source=_dummy,
    persist=True,
    tracker=str(TRACKER_CFG),
    verbose=False,
    conf=CONF,
    iou=IOU,
    imgsz=IMGSZ,
    device=DEVICE,
)
if getattr(model, "predictor", None) is not None:
    for _tr in getattr(model.predictor, "trackers", []) or []:
        if hasattr(_tr, "reset"):
            _tr.reset()

gpu_info = f"GPU: {torch.cuda.get_device_name(0)}" if HAS_CUDA else "CPU"
print(f"\n>>> DANG CHAY: {gpu_info} | model={MODEL_PATH.name} | imgsz={IMGSZ}\n")

app = FastAPI(title="Pig Monitoring YOLO Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
model_lock = threading.Lock()
EVENTS_FILE = BASE_DIR / "events.jsonl"
events_lock = threading.Lock()


@app.exception_handler(Exception)
async def all_errors(request, exc):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.get("/app")
def web_app():
    html = BASE_DIR / "giam_sat_lon.html"
    if not html.is_file():
        raise HTTPException(status_code=404, detail="Dat giam_sat_lon.html canh backend.py")
    return FileResponse(html)


@app.get("/")
def home():
    return {
        "status": "ok",
        "device": gpu_info,
        "model": MODEL_PATH.name,
        "classes": model.names,
        "conf": CONF,
        "imgsz": IMGSZ,
    }


@app.post("/reset")
def reset_tracker():
    with model_lock:
        if getattr(model, "predictor", None) is not None:
            for tr in getattr(model.predictor, "trackers", []) or []:
                if hasattr(tr, "reset"):
                    tr.reset()
    return {
        "status": "ok",
        "message": "Da reset tracker"
    }


@app.post("/events")
def add_event(ev: dict = Body(...)):
    with events_lock:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print("SU KIEN:", ev)
    return {"status": "ok"}


@app.get("/events")
def list_events(limit: int = 100):
    limit = max(1, min(limit, 1000))
    if not EVENTS_FILE.is_file():
        return []
    with events_lock:
        lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    return [
        json.loads(x)
        for x in lines[-limit:]
        if x.strip()
    ]


@app.post("/detect")
async def detect(request: Request):
    t0 = time.perf_counter()
    raw = await request.body()
    if not raw:
        raise HTTPException(status_code=400, detail="Frame rong.")
    frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Khong doc duoc frame anh.")
    height, width = frame.shape[:2]
    try:
        with model_lock:
            results = model.track(
                source=frame,
                persist=True,
                tracker=str(TRACKER_CFG),
                verbose=False,
                conf=CONF,
                iou=IOU,
                imgsz=IMGSZ,
                device=DEVICE,
                max_det=30,
            )
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"YOLO tracking loi: {exc}")

    result = results[0]
    boxes_out: list[dict[str, Any]] = []
    if result.boxes is not None and len(result.boxes) > 0:
        xyxy = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        track_ids = (
            result.boxes.id.cpu().numpy().astype(int)
            if result.boxes.id is not None
            else None
        )
        frame_area = float(width * height)
        areas = [(c[2] - c[0]) * (c[3] - c[1]) for c in xyxy]
        names = model.names
        for i, coords in enumerate(xyxy):
            area = areas[i]
            if area < frame_area * MIN_AREA_RATIO:
                continue
            x1, y1, x2, y2 = [float(v) for v in coords]
            cid = int(classes[i])
            cname = names.get(cid, str(cid)) if isinstance(names, dict) else names[cid]
            tid = int(track_ids[i]) if track_ids is not None else None
            boxes_out.append({
                "xyxy": [x1, y1, x2, y2],
                "norm": [
                    max(0.0, min(1.0, x1 / width)),
                    max(0.0, min(1.0, y1 / height)),
                    max(0.0, min(1.0, x2 / width)),
                    max(0.0, min(1.0, y2 / height)),
                ],
                "track_id": tid,
                "class_id": cid,
                "class_name": str(cname),
                "confidence": float(confs[i]),
            })
    dt = (time.perf_counter() - t0) * 1000
    print(f"/detect: {len(boxes_out)} box ({width}x{height}) - {dt:.1f}ms")
    return {"width": width, "height": height, "boxes": boxes_out, "ms": round(dt, 1)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)