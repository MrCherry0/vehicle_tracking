# ============================================================================
# models/detector.py
# ============================================================================
"""
Detector de vehículos usando YOLOv8.
Detecta cars, trucks y buses en cada frame.
"""

from ultralytics import YOLO
import numpy as np


class VehicleDetector:
    """
    Detector de vehículos usando YOLOv8
    """
    
    def __init__(self, model_name='yolov8n.pt', conf_threshold=0.3):
        """
        Inicializa el detector
        
        Args:
            model_name: Modelo YOLOv8 a usar
            conf_threshold: Umbral de confianza
        """
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        
        # IDs de COCO para vehículos
        self.vehicle_classes = {
            2: 'car',
            5: 'bus',
            7: 'truck'
        }
    
    def detect(self, frame):
        """
        Detecta vehículos en un frame
        
        Args:
            frame: Imagen BGR de OpenCV
            
        Returns:
            detections: Array numpy de shape (N, 5) con [x1, y1, x2, y2, conf]
            classes: Lista de nombres de clases detectadas
        """
        # Inferencia
        results = self.model(frame, verbose=False)[0]
        
        detections = []
        classes = []
        
        # Filtrar solo vehículos
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            if cls_id in self.vehicle_classes and conf >= self.conf_threshold:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append([x1, y1, x2, y2, conf])
                classes.append(self.vehicle_classes[cls_id])
        
        if len(detections) == 0:
            return np.empty((0, 5)), []
        
        return np.array(detections), classes
