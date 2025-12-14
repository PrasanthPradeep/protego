# import cv2
# import time
# from ultralytics import YOLO

# class SafetyDetector:
#     def __init__(self, camera_index=0):
#         self.model = YOLO("yolov8n.pt")
#         self.cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)

#         self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
#         self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#         self.cap.set(cv2.CAP_PROP_FPS, 30)

#         self.last_run = 0
#         self.DETECT_INTERVAL = 0.3  # seconds

#     def get_frame(self):
#         success, frame = self.cap.read()
#         if not success:
#             return None
#         return frame

#     def detect(self, frame):
#         now = time.time()
#         if now - self.last_run < self.DETECT_INTERVAL:
#             return None

#         self.last_run = now
#         results = self.model(frame, verbose=False)
#         return results

#     def extract_scene(self, results, frame_shape):
#         height, width, _ = frame_shape
#         objects = []

#         for i, box in enumerate(results[0].boxes):
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             label = self.model.names[int(box.cls[0])]
#             conf = float(box.conf[0])

#             center_x = (x1 + x2) / 2
#             position = (
#                 "left" if center_x < width / 3 else
#                 "center" if center_x < 2 * width / 3 else
#                 "right"
#             )

#             objects.append({
#                 "id": i,
#                 "label": label,
#                 "confidence": round(conf, 2),
#                 "position": position,
#                 "bbox": {
#                     "x_min": x1,
#                     "y_min": y1,
#                     "x_max": x2,
#                     "y_max": y2
#                 }
#             })

#         return {
#             "timestamp": time.time(),
#             "object_count": len(objects),
#             "objects": objects
#         }
