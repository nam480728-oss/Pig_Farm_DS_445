import json
import math
import os
import threading
import traceback
from pathlib import Path
from typing import Any
import cv2
import numpy as np
import uvicorn
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from ultralytics import YOLO
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = Path(os.getenv("YOLO_MODEL", str(BASE_DIR / "pig_det.pt")))
CONF = float(os.getenv("CONF", "0.25"))
IMGSZ = int(os.getenv("IMGSZ", "960"))  
if not MODEL_PATH.is_file():
    raise FileNotFoundError(
        f"Khong tim thay model: {MODEL_PATH}. "
        "Hay dat pig_det.pt canh backend.py hoac dat bien YOLO_MODEL."
    )
model = YOLO(str(MODEL_PATH))
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
tracks: list[dict] = []
next_id = 1
def assign_ids(dets: list[list[float]]) -> list[int]:
    global next_id
    infos = []
    for x1, y1, x2, y2 in dets:
        infos.append(((x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1))
    pairs = []
    for di, (cx, cy, w, h) in enumerate(infos):
        for ti, t in enumerate(tracks):
            gate = max(w, h, t["w"], t["h"]) * 0.8
            dist = math.hypot(cx - t["cx"], cy - t["cy"])
            if dist <= gate:
                pairs.append((dist / gate, di, ti))
    pairs.sort()
    ids: list[int | None] = [None] * len(dets)
    used_t: set[int] = set()
    for _, di, ti in pairs:
        if ids[di] is not None or ti in used_t:
            continue
        cx, cy, w, h = infos[di]
        t = tracks[ti]
        t.update(cx=cx, cy=cy, w=w, h=h, miss=0)
        ids[di] = t["id"]
        used_t.add(ti)
    for ti, t in enumerate(tracks):
        if ti not in used_t:
            t["miss"] += 1
    tracks[:] = [t for t in tracks if t["miss"] <= 8]
    for di, (cx, cy, w, h) in enumerate(infos):
        if ids[di] is None:
            ids[di] = next_id
            tracks.append(dict(id=next_id, cx=cx, cy=cy, w=w, h=h, miss=0))
            next_id += 1
    return [int(i) for i in ids]


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
        "message": "YOLO backend dang hoat dong",
        "model": MODEL_PATH.name,
        "classes": model.names,
        "conf": CONF,
        "imgsz": IMGSZ,
    }


@app.post("/reset")
def reset_tracker():
    global next_id
    with model_lock:
        tracks.clear()
        next_id = 1
    return {"status": "ok", "message": "Da reset ID"}


@app.post("/events")
def add_event(ev: dict = Body(...)):
    with events_lock:
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print("SU KIEN:", ev)
    return {"status": "ok"}


@app.get("/events")
def list_events(limit: int = 100):
    if not EVENTS_FILE.is_file():
        return []
    with events_lock:
        lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    return [json.loads(x) for x in lines[-limit:] if x.strip()]


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Frame rong.")
    frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Khong doc duoc frame anh.")
    height, width = frame.shape[:2]

    try:
        with model_lock:
            results = model.predict(source=frame, verbose=False, conf=CONF, imgsz=IMGSZ)
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"YOLO inference loi: {exc}")

    result = results[0]
    boxes_out: list[dict[str, Any]] = []

    if result.boxes is not None and len(result.boxes) > 0:
        xyxy = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy().astype(int)
        with model_lock:
            ids = assign_ids([[float(v) for v in c] for c in xyxy])

        names = model.names
        for i, coords in enumerate(xyxy):
            x1, y1, x2, y2 = [float(v) for v in coords]
            cid = int(classes[i])
            cname = names.get(cid, str(cid)) if isinstance(names, dict) else names[cid]
            boxes_out.append({
                "xyxy": [x1, y1, x2, y2],
                "norm": [
                    max(0.0, min(1.0, x1 / width)),
                    max(0.0, min(1.0, y1 / height)),
                    max(0.0, min(1.0, x2 / width)),
                    max(0.0, min(1.0, y2 / height)),
                ],
                "track_id": ids[i],
                "class_id": cid,
                "class_name": str(cname),
                "confidence": float(confs[i]),
            })
    else:
        with model_lock:
            assign_ids([])

    print(f"/detect: {len(boxes_out)} box ({width}x{height})")
    return {"width": width, "height": height, "boxes": boxes_out}
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
