from fastapi import FastAPI, WebSocket
import cv2
import base64
import numpy as np
from ultralytics import YOLO
import time

app = FastAPI()

# -----------------------------
# Load PPE Model
# -----------------------------
model = YOLO("models/ppe_yolo.pt")
print("📦 Loaded PPE classes:", model.names)

# -----------------------------
# Performance Controls
# -----------------------------
DETECT_INTERVAL = 0.25
RESULT_TTL = 0.6
JPEG_QUALITY = 65
MAX_LOGS = 100
VIOLATION_COOLDOWN = 2.0

last_detect_time = 0.0
last_results = None
last_results_time = 0.0
last_violation_time = {}

SAFETY_LOG = []


@app.websocket("/ws/safety")
async def safety_socket(websocket: WebSocket):
    await websocket.accept()
    print("🔌 Client connected")

    global last_detect_time, last_results, last_results_time

    try:
        while True:
            # ---------------------------------
            # Receive frame
            # ---------------------------------
            data = await websocket.receive_text()
            _, encoded = data.split(",", 1)

            img_bytes = base64.b64decode(encoded)
            img_array = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            now = time.time()

            # ---------------------------------
            # Detection throttling + persistence
            # ---------------------------------
            if now - last_detect_time >= DETECT_INTERVAL:
                last_detect_time = now
                last_results = model(frame, verbose=False)[0]
                last_results_time = now

            results = (
                last_results
                if last_results and (now - last_results_time) <= RESULT_TTL
                else None
            )

            annotated = frame.copy()
            violations = []

            # ---------------------------------
            # PPE Detection ONLY
            # ---------------------------------
            if results:
                for box in results.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = model.names[int(box.cls[0])]
                    conf = float(box.conf[0])

                    if label in ["NO-Hardhat", "NO-Mask", "NO-Safety Vest"]:
                        last_time = last_violation_time.get(label, 0)
                        if now - last_time < VIOLATION_COOLDOWN:
                            continue

                        last_violation_time[label] = now
                        vtype = label.upper().replace("-", "_")

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

                # Draw YOLO annotations
                annotated = results.plot()

            # ---------------------------------
            # Trim logs
            # ---------------------------------
            if len(SAFETY_LOG) > MAX_LOGS:
                SAFETY_LOG[:] = SAFETY_LOG[-MAX_LOGS:]

            # ---------------------------------
            # Encode & send
            # ---------------------------------
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
