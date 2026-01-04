# ============================================================================
# models/video_processor.py
# ============================================================================
"""
Procesador de video que coordina detección, tracking y cálculo de velocidad.
Preprocesa el video a 30 FPS y 1280x720.
"""

import cv2
import numpy as np
from .detector import VehicleDetector
from .tracker import Sort
from .speed_calculator import SpeedCalculator


class VideoProcessor:
    """
    Procesador de video con detección y tracking
    """
    
    def __init__(self):
        """
        Inicializa el procesador
        """
        self.detector = VehicleDetector()
        self.tracker = Sort(max_age=30, min_hits=3)
        self.speed_calculator = SpeedCalculator(fps=15, pixels_per_meter=20)
        
        self.target_fps = 15
        self.target_size = (1280, 720)
        
        self.total_vehicles_seen = set()
        self.current_frame_number = 0
    
    def process_frame(self, frame):
        """
        Procesa un frame: detecta, trackea y calcula velocidades
        
        Args:
            frame: Frame BGR de OpenCV
            
        Returns:
            processed_frame: Frame con anotaciones
            tracks: Lista de (id, bbox, speed)
            stats: Diccionario con estadísticas
        """
        # Redimensionar
        frame = cv2.resize(frame, self.target_size)
        
        # Detección
        detections, _ = self.detector.detect(frame)
        
        # Tracking
        tracks = self.tracker.update(detections)
        
        # Calcular velocidades y dibujar
        track_data = []
        for track in tracks:
            x1, y1, x2, y2, track_id = track
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)
            
            # Registrar vehículo
            self.total_vehicles_seen.add(track_id)
            
            # Calcular velocidad
            speed = self.speed_calculator.calculate_speed(track_id, [x1, y1, x2, y2])
            
            # Dibujar bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Dibujar ID
            label = f"ID: {track_id}"
            cv2.putText(frame, label, (x1, y1 - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Dibujar velocidad
            speed_label = f"{speed:.1f} km/h"
            cv2.putText(frame, speed_label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            track_data.append((track_id, [x1, y1, x2, y2], speed))
        
        # Estadísticas
        stats = {
            'frame': self.current_frame_number,
            'total_vehicles': len(self.total_vehicles_seen),
            'current_vehicles': len(tracks)
        }
        
        self.current_frame_number += 1
        
        return frame, track_data, stats
    
    def reset(self):
        """
        Reinicia el procesador
        """
        self.tracker = Sort(max_age=30, min_hits=3)
        self.speed_calculator.reset()
        self.total_vehicles_seen = set()
        self.current_frame_number = 0

