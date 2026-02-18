import cv2
import numpy as np
import os
import time
import torch

# BASE_DIR for safe path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Patch torch.load to use weights_only=False for YOLO model compatibility
_original_torch_load = torch.load

def _patched_torch_load(f, *args, **kwargs):
    """Patched torch.load that defaults to weights_only=False"""
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(f, *args, **kwargs)

torch.load = _patched_torch_load

# Global cached model variable for lazy loading
_model = None
_demo_mode = False

def _get_model():
    """Lazy load the YOLO model - only loads when first needed"""
    global _model, _demo_mode
    
    if _model is not None:
        return _model
    
    # Check if model file exists
    model_path = os.path.join(BASE_DIR, 'models', 'yolov8n.pt')
    
    if not os.path.exists(model_path):
        print("Running in DEMO MODE – model not loaded")
        print(f"Model file not found at: {model_path}")
        _demo_mode = True
        return None
    
    try:
        from ultralytics import YOLO
        print(f"Loading YOLO model from: {model_path}")
        _model = YOLO(model_path)
        print("YOLO model loaded successfully")
        return _model
    except Exception as e:
        print(f"Failed to load YOLO model: {e}")
        print("Running in DEMO MODE – model not loaded")
        _demo_mode = True
        return None

class CarDetector:
    def __init__(self, model_path=None):
        # Use provided path or default to BASE_DIR/models/yolov8n.pt
        self.model_path = model_path if model_path else os.path.join(BASE_DIR, 'models', 'yolov8n.pt')
        self.model = None  # Will be loaded lazily
        # counter for consecutive-frame overlaps to confirm collisions
        self.overlap_count = 0
        self.prev_boxes = []
        
        # Check if model exists but don't load yet
        if not os.path.exists(self.model_path):
            global _demo_mode
            _demo_mode = True
            print("Running in DEMO MODE – model not loaded")
            print(f"Model file not found at: {self.model_path}")

    def detect_cars(self, results):
        car_count = 0
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                if cls in [2, 3, 5, 7]:  # car, motorcycle, bus, truck
                    car_count += 1
        return car_count

    def process_frame(self, frame):
        # Lazy load model on first use
        if self.model is None:
            self.model = _get_model()
        
        # Demo mode - return fake detection results
        if _demo_mode or self.model is None:
            # Create annotated frame with demo text
            annotated_frame = frame.copy()
            if annotated_frame is None or annotated_frame.size == 0:
                annotated_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Draw demo text on frame
            cv2.putText(annotated_frame, "DEMO MODE - No Model", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(annotated_frame, "Cars Detected: 0", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            return annotated_frame, 0, []
        
        # Normal mode - use YOLO model
        results = self.model(frame)
        annotated_frame = results[0].plot()

        car_count = self.detect_cars(results)
        cv2.putText(annotated_frame, f"Cars Detected: {car_count}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # extract boxes as (x1,y1,x2,y2,cls)
        boxes = []
        if len(results) > 0:
            for box in results[0].boxes:
                xy = box.xyxy[0].tolist()
                cls = int(box.cls[0])
                boxes.append((xy[0], xy[1], xy[2], xy[3], cls))

        return annotated_frame, car_count, boxes

    def process_video(self, source):
        if source == 'webcam':
            cap = cv2.VideoCapture(0)
        elif source.startswith('rtsp://'):
            cap = cv2.VideoCapture(source)
        else:
            cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            print(f"Error: Could not open video source {source}")
            return

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            processed_frame, car_count, boxes = self.process_frame(frame)

            accident_flag = False
            severity = 0

            # Only detect accidents in non-demo mode
            if not _demo_mode and self.model is not None:
                # detect significant overlap between any two vehicle boxes
                for i in range(len(boxes)):
                    for j in range(i+1, len(boxes)):
                        a = boxes[i]
                        b = boxes[j]
                        # only consider vehicle classes
                        if a[4] not in [2,3,5,7] or b[4] not in [2,3,5,7]:
                            continue
                        xA = max(a[0], b[0])
                        yA = max(a[1], b[1])
                        xB = min(a[2], b[2])
                        yB = min(a[3], b[3])
                        interW = max(0, xB - xA)
                        interH = max(0, yB - yA)
                        interArea = interW * interH
                        boxAArea = max(0, (a[2] - a[0])) * max(0, (a[3] - a[1]))
                        boxBArea = max(0, (b[2] - b[0])) * max(0, (b[3] - b[1]))
                        unionArea = boxAArea + boxBArea - interArea if (boxAArea + boxBArea - interArea) > 0 else 1
                        iou = interArea / unionArea
                        # require both a sufficiently large IoU and a minimum intersection area to avoid tiny overlaps
                        if iou > 0.8 and interArea > 5000:
                            # debug log to help tune thresholds
                            print(f"[detector] Overlap candidate: iou={iou:.2f} interArea={interArea} (frame)")
                            self.overlap_count += 1
                            print(f"[detector] overlap_count={self.overlap_count}")
                            if self.overlap_count >= 3:
                                accident_flag = True
                                severity = min(5, int(iou * 10))
                                self.overlap_count = 0
                            break
                    if accident_flag:
                        break

                # decay overlap_count when no qualifying overlap found
                if not accident_flag:
                    if self.overlap_count > 0:
                        self.overlap_count = max(0, self.overlap_count - 1)

            yield processed_frame, car_count, accident_flag, severity

        cap.release()
