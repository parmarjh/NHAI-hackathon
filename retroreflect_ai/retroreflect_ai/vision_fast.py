import cv2
import time
import threading
from ultralytics import YOLO
import numpy as np

# ── FAST REAL-TIME CV ENGINE ──────────────────────────────────────────────────
# This module implements high-speed object detection for NHAI Highway Health.
# Optimized for 30+ FPS on standard hardware.

class FastVisionEngine:
    def __init__(self, model_path='yolov8n.pt'):
        print(f"[INTEL] Initializing YOLO Engine: {model_path}...")
        self.model = YOLO(model_path)
        self.cap = None
        self.running = False
        self.frame = None
        self.results = None
        self.lock = threading.Lock()
        
        # Performance Metrics
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Colors (Matches RetroReflect AI Palette)
        self.ACCENT = (0, 221, 255)  # Cyan
        self.DANGER = (68, 34, 255)  # Red
        self.OK = (136, 255, 0)      # Green

    def start(self, source=0):
        self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW) # Fast startup on Windows
        if not self.cap.isOpened():
            print("[ERROR] Could not open camera source.")
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        self.infer_thread = threading.Thread(target=self._inference_loop, daemon=True)
        self.infer_thread.start()
        return True

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            with self.lock:
                self.frame = frame
            
            # FPS Calculation
            self.frame_count += 1
            elapsed = time.time() - self.start_time
            if elapsed > 1.0:
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.start_time = time.time()

    def _inference_loop(self):
        while self.running:
            if self.frame is not None:
                # Perform inference on a copy to avoid locking capture too long
                with self.lock:
                    input_frame = self.frame.copy()
                
                # Run YOLO (Stream mode for speed)
                results = self.model(input_frame, verbose=False, device='cpu') # Use 'cuda' if available
                
                with self.lock:
                    self.results = results
            else:
                time.sleep(0.01)

    def draw_hud(self, frame):
        # ── Cyberpunk HUD Overlay ─────────────────────────────────────────────
        h, w = frame.shape[:2]
        
        # 1. Corner Brackets
        thick = 2
        size = 40
        # TL
        cv2.line(frame, (10, 10), (10+size, 10), self.ACCENT, thick)
        cv2.line(frame, (10, 10), (10, 10+size), self.ACCENT, thick)
        # TR
        cv2.line(frame, (w-10, 10), (w-10-size, 10), self.ACCENT, thick)
        cv2.line(frame, (w-10, 10), (w-10, 10+size), self.ACCENT, thick)
        # BL
        cv2.line(frame, (10, h-10), (10+size, h-10), self.ACCENT, thick)
        cv2.line(frame, (10, h-10), (10, h-10-size), self.ACCENT, thick)
        # BR
        cv2.line(frame, (w-10, h-10), (w-10-size, h-10), self.ACCENT, thick)
        cv2.line(frame, (w-10, h-10), (w-10, h-10-size), self.ACCENT, thick)

        # 2. Scanning Line Effect
        line_y = int((time.time() * 200) % h)
        overlay = frame.copy()
        cv2.line(overlay, (0, line_y), (w, line_y), self.ACCENT, 1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        # 3. Telemetry Block
        cv2.rectangle(frame, (20, 20), (220, 100), (0,0,0), -1)
        cv2.putText(frame, "NHAI REAL-TIME", (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.ACCENT, 1)
        cv2.putText(frame, f"FPS: {self.fps:.1f}", (30, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.OK, 2)
        cv2.putText(frame, f"STATUS: ANALYZING", (30, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1)

        # 4. Detected Objects
        if self.results:
            for r in self.results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    conf = float(box.conf[0])
                    
                    if conf > 0.4:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # Custom styling for highway objects
                        color = self.ACCENT
                        if "sign" in label.lower() or "traffic" in label.lower():
                            color = self.OK
                        elif "person" in label.lower() or "car" in label.lower():
                            color = self.ACCENT
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Label background
                        cv2.rectangle(frame, (x1, y1-25), (x1+len(label)*12, y1), color, -1)
                        cv2.putText(frame, f"{label.upper()} {conf:.2f}", (x1+5, y1-7), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)

        return frame

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

def run_realtime_demo():
    engine = FastVisionEngine()
    if engine.start():
        print("[SUCCESS] Real-time engine active. Press 'Q' to exit.")
        while True:
            with engine.lock:
                if engine.frame is not None:
                    # Create a display copy
                    display_frame = engine.frame.copy()
                    display_frame = engine.draw_hud(display_frame)
                    
                    cv2.imshow("RETROREFLECT·AI — REAL-TIME VISION", display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        engine.stop()

if __name__ == "__main__":
    run_realtime_demo()
