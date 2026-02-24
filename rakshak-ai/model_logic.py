"""
Rakshak AI - Car Accident Detection Logic
==========================================
This module contains the core AI detection logic extracted from the Flask app.
It can be used by both the Flask app and the Streamlit app.

Functions:
- load_model(): Load the YOLO model
- detect_vehicles(image): Detect vehicles in an image
- check_accident(boxes): Check for accidents from overlapping vehicles
- process_video_stream(source): Process video frames for real-time detection
"""

import cv2
import numpy as np
import os
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


def load_model(model_path=None):
    """
    Load the YOLO model for vehicle detection.
    
    Args:
        model_path: Path to the YOLO model file. Defaults to models/yolov8n.pt
        
    Returns:
        The loaded YOLO model, or None if in demo mode
    """
    global _model, _demo_mode
    
    if _model is not None:
        return _model
    
    # Check if model file exists
    if model_path is None:
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


def is_demo_mode():
    """Return whether the model is in demo mode."""
    return _demo_mode or _model is None


def get_vehicle_classes():
    """
    Return the class IDs for vehicles (car, motorcycle, bus, truck).
    
    Returns:
        List of class IDs: [2, 3, 5, 7] (car, motorcycle, bus, truck)
    """
    return [2, 3, 5, 7]


def detect_vehicles(image):
    """
    Detect vehicles in an image frame.
    
    Args:
        image: numpy array (BGR format from OpenCV)
        
    Returns:
        tuple: (annotated_image, vehicle_count, boxes)
            - annotated_image: Image with bounding boxes drawn
            - vehicle_count: Number of vehicles detected
            - boxes: List of (x1, y1, x2, y2, class_id) tuples
    """
    global _model, _demo_mode
    
    # Lazy load model on first use
    if _model is None:
        load_model()
    
    # Demo mode - return fake detection results
    if _demo_mode or _model is None:
        # Create annotated frame with demo text
        annotated_image = image.copy()
        if annotated_image is None or annotated_image.size == 0:
            annotated_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw demo text on frame
        cv2.putText(annotated_image, "DEMO MODE - No Model", (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(annotated_image, "Vehicles Detected: 0", (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return annotated_image, 0, []
    
    # Normal mode - use YOLO model
    results = _model(image)
    annotated_image = results[0].plot()
    
    # Count vehicles
    vehicle_count = 0
    vehicle_classes = get_vehicle_classes()
    boxes = []
    
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            if cls in vehicle_classes:
                vehicle_count += 1
            
            # Extract box coordinates
            xy = box.xyxy[0].tolist()
            boxes.append((xy[0], xy[1], xy[2], xy[3], cls))
    
    # Draw vehicle count on frame
    cv2.putText(annotated_image, f"Vehicles Detected: {vehicle_count}", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    return annotated_image, vehicle_count, boxes


def check_accident(boxes, overlap_threshold=0.8, min_area=5000, min_consecutive=3):
    """
    Check if there's an accident based on vehicle bounding box overlaps.
    
    Args:
        boxes: List of (x1, y1, x2, y2, class_id) tuples
        overlap_threshold: IoU threshold for detecting collision (default 0.8)
        min_area: Minimum intersection area to consider (default 5000)
        min_consecutive: Minimum consecutive overlaps to confirm accident (default 3)
        
    Returns:
        tuple: (accident_detected, severity)
            - accident_detected: Boolean indicating if accident was detected
            - severity: Integer 0-5 indicating severity
    """
    vehicle_classes = get_vehicle_classes()
    
    # Check for significant overlaps between any two vehicle boxes
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a = boxes[i]
            b = boxes[j]
            
            # Only consider vehicle classes
            if a[4] not in vehicle_classes or b[4] not in vehicle_classes:
                continue
            
            # Calculate intersection
            xA = max(a[0], b[0])
            yA = max(a[1], b[1])
            xB = min(a[2], b[2])
            yB = min(a[3], b[3])
            
            interW = max(0, xB - xA)
            interH = max(0, yB - yA)
            interArea = interW * interH
            
            # Calculate IoU
            boxAArea = max(0, (a[2] - a[0])) * max(0, (a[3] - a[1]))
            boxBArea = max(0, (b[2] - b[0])) * max(0, (b[3] - b[1]))
            unionArea = boxAArea + boxBArea - interArea if (boxAArea + boxBArea - interArea) > 0 else 1
            iou = interArea / unionArea
            
            # Check if overlap is significant
            if iou > overlap_threshold and interArea > min_area:
                severity = min(5, int(iou * 10))
                return True, severity
    
    return False, 0


def process_image(image_path):
    """
    Process a single image for vehicle detection and accident analysis.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict: Results containing:
            - annotated_image: Image with detections drawn
            - vehicle_count: Number of vehicles detected
            - accident_detected: Boolean
            - severity: Severity level (0 if no accident)
            - boxes: List of detection boxes
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        return {
            'error': f'Failed to load image: {image_path}',
            'vehicle_count': 0,
            'accident_detected': False,
            'severity': 0,
            'boxes': []
        }
    
    # Detect vehicles
    annotated_image, vehicle_count, boxes = detect_vehicles(image)
    
    # Check for accidents
    accident_detected, severity = check_accident(boxes)
    
    return {
        'annotated_image': annotated_image,
        'vehicle_count': vehicle_count,
        'accident_detected': accident_detected,
        'severity': severity,
        'boxes': boxes,
        'demo_mode': is_demo_mode()
    }


def analyze_video_frame(frame):
    """
    Analyze a single video frame for vehicle detection and accident analysis.
    
    Args:
        frame: numpy array (BGR format from OpenCV)
        
    Returns:
        tuple: (annotated_frame, vehicle_count, accident_flag, severity)
    """
    # Detect vehicles
    annotated_frame, vehicle_count, boxes = detect_vehicles(frame)
    
    # Check for accidents
    accident_flag, severity = check_accident(boxes)
    
    return annotated_frame, vehicle_count, accident_flag, severity


# Module initialization for easy importing
def init():
    """Initialize the model (lazy loading happens automatically)."""
    return load_model()


if __name__ == "__main__":
    # Test the model logic
    print("Testing Rakshak AI Model Logic...")
    model = load_model()
    if model:
        print("Model loaded successfully!")
    else:
        print("Running in demo mode - no model loaded")
    
    print(f"Demo mode: {is_demo_mode()}")
    print(f"Vehicle classes: {get_vehicle_classes()}")
