from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import cv2
import base64
import numpy as np
from ultralytics import YOLO
import time
import os

app = FastAPI()

# -----------------------------
# Serve Frontend
# -----------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# -----------------------------
# Load PPE Models
# -----------------------------
models = [
    YOLO("models/ppe_yolo26s_v27.pt"),
    YOLO("models/ppe_yolo.pt"),
]
model = models[0]
print("📦 Loaded PPE classes:", model.names)

# -----------------------------
# Performance Controls
# -----------------------------
DETECT_INTERVAL = 0.25
RESULT_TTL = 0.6
JPEG_QUALITY = 65
MAX_LOGS = 100
VIOLATION_COOLDOWN = 2.0
ENSEMBLE_IOU_THRESHOLD = 0.5

last_detect_time = 0.0
last_results = None
last_results_time = 0.0
last_violation_time = {}

SAFETY_LOG = []


def intersection_over_union(first_box, second_box):
    first_x1, first_y1, first_x2, first_y2 = first_box
    second_x1, second_y1, second_x2, second_y2 = second_box
    intersection_x1 = max(first_x1, second_x1)
    intersection_y1 = max(first_y1, second_y1)
    intersection_x2 = min(first_x2, second_x2)
    intersection_y2 = min(first_y2, second_y2)
    intersection = max(0, intersection_x2 - intersection_x1) * max(0, intersection_y2 - intersection_y1)
    first_area = max(0, first_x2 - first_x1) * max(0, first_y2 - first_y1)
    second_area = max(0, second_x2 - second_x1) * max(0, second_y2 - second_y1)
    union = first_area + second_area - intersection
    return intersection / union if union else 0.0


def merge_model_results(frame):
    detections = []
    for detector in models:
        result = detector(frame, verbose=False)[0]
        for box, class_id, confidence in zip(result.boxes.xyxy.tolist(), result.boxes.cls.tolist(), result.boxes.conf.tolist()):
            detections.append({
                "box": box,
                "class_id": int(class_id),
                "confidence": float(confidence),
            })

    merged = []
    for detection in sorted(detections, key=lambda item: item["confidence"], reverse=True):
        duplicate = any(
            detection["class_id"] == existing["class_id"]
            and intersection_over_union(detection["box"], existing["box"]) >= ENSEMBLE_IOU_THRESHOLD
            for existing in merged
        )
        if not duplicate:
            merged.append(detection)
    return merged


@app.websocket("/ws/safety")
async def safety_socket(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Client connected")

    global last_detect_time, last_results, last_results_time

    try:
        while True:
            data = await websocket.receive_text()
            _, encoded = data.split(",", 1)

            img_bytes = base64.b64decode(encoded)
            frame = cv2.imdecode(
                np.frombuffer(img_bytes, np.uint8),
                cv2.IMREAD_COLOR
            )

            if frame is None:
                continue

            now = time.time()

            # Throttled detection
            if now - last_detect_time >= DETECT_INTERVAL:
                last_detect_time = now
                last_results = merge_model_results(frame)
                last_results_time = now

            results = (
                last_results
                if last_results and (now - last_results_time) <= RESULT_TTL
                else None
            )

            annotated = frame.copy()
            violations = []

            # -----------------------------
            # PPE ONLY
            # -----------------------------
            if results:
                for detection in results:
                    x1, y1, x2, y2 = map(int, detection["box"])
                    label = model.names[detection["class_id"]]
                    conf = detection["confidence"]

                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 220, 120), 2)
                    cv2.putText(
                        annotated,
                        f"{label} {conf:.2f}",
                        (x1, max(y1 - 8, 18)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 220, 120),
                        2,
                        cv2.LINE_AA,
                    )

                    if label in ["NO-Hardhat", "NO-Mask", "NO-Safety Vest"]:
                        last_time = last_violation_time.get(label, 0)
                        if now - last_time < VIOLATION_COOLDOWN:
                            continue

                        last_violation_time[label] = now
                        vtype = label.upper().replace("-", "_").replace(" ", "_")

                        violations.append({
                            "type": vtype,
                            "severity": "HIGH",
                            "bbox": (x1, y1, x2, y2),
                            "confidence": round(conf, 2)
                        })

                        SAFETY_LOG.append({
                            "time": time.strftime("%H:%M:%S"),
                            "type": vtype,
                            "severity": "HIGH",
                            "confidence": round(conf, 2)
                        })

            if len(SAFETY_LOG) > MAX_LOGS:
                SAFETY_LOG[:] = SAFETY_LOG[-MAX_LOGS:]

            _, jpeg = cv2.imencode(
                ".jpg",
                annotated,
                [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            )

            await websocket.send_json({
                "frame": base64.b64encode(jpeg).decode("utf-8"),
                "violations": violations,
                "logs": SAFETY_LOG
            })

    except Exception as e:
        print("❌ Client disconnected:", e)
