import threading
import cv2
from pyzbar import pyzbar


class QRScannerService:
    def __init__(self, on_detected: callable, camera_index: int = 0):
        self.on_detected = on_detected
        self.camera_index = camera_index
        self._running = False
        self._thread = None
        self.cap = None
        self.latest_frame = None
        self._lock = threading.Lock()

    def start(self) -> bool:
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            return False
        self._running = True
        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self.cap:
            self.cap.release()
        self.cap = None

    def get_frame(self):
        with self._lock:
            return self.latest_frame

    def _scan_loop(self):
        import numpy as np
        detected_codes = set()
        while self._running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            decoded = pyzbar.decode(frame)
            for obj in decoded:
                data = obj.data.decode("utf-8")
                if data not in detected_codes:
                    detected_codes.add(data)
                    pts = obj.polygon
                    if len(pts) == 4:
                        pts_arr = np.array([(p.x, p.y) for p in pts], dtype=np.int32)
                        cv2.polylines(frame, [pts_arr], True, (0, 212, 170), 3)
                    self.on_detected(data)
            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2
            size = min(w, h) // 2
            cv2.rectangle(frame, (cx - size // 2, cy - size // 2), (cx + size // 2, cy + size // 2), (0, 212, 170), 2)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with self._lock:
                self.latest_frame = rgb
        detected_codes.clear()
