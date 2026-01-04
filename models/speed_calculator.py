# ============================================================================
# models/speed_calculator.py
# ============================================================================
"""
Calculador de velocidad basado en desplazamiento de centroides.
Convierte píxeles/frame a km/h usando calibración.
OPTIMIZADO: Suaviza velocidades con promedio móvil.
"""

import numpy as np
from collections import deque


class SpeedCalculator:
    """
    Calcula velocidad de vehículos rastreados con suavizado
    """
    
    def __init__(self, fps=30, pixels_per_meter=20, smoothing_window=5):
        """
        Args:
            fps: Frames por segundo del video
            pixels_per_meter: Calibración de píxeles por metro
            smoothing_window: Ventana para promedio móvil de velocidad
        """
        self.fps = fps
        self.pixels_per_meter = pixels_per_meter
        self.previous_positions = {}
        
        # OPTIMIZACIÓN: Suavizado de velocidades
        self.smoothing_window = smoothing_window
        self.speed_history = {}
    
    def calculate_speed(self, track_id, bbox):
        """
        Calcula velocidad en km/h con suavizado
        
        Args:
            track_id: ID del track
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            speed: Velocidad suavizada en km/h
        """
        # Calcular centroide
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        
        if track_id not in self.previous_positions:
            self.previous_positions[track_id] = (cx, cy)
            self.speed_history[track_id] = deque(maxlen=self.smoothing_window)
            return 0.0
        
        # Calcular desplazamiento en píxeles
        prev_cx, prev_cy = self.previous_positions[track_id]
        dx = cx - prev_cx
        dy = cy - prev_cy
        distance_pixels = np.sqrt(dx**2 + dy**2)
        
        # Convertir a metros
        distance_meters = distance_pixels / self.pixels_per_meter
        
        # Convertir a km/h
        speed_mps = distance_meters * self.fps
        speed_kmh = speed_mps * 3.6
        
        # OPTIMIZACIÓN: Suavizado con promedio móvil
        self.speed_history[track_id].append(speed_kmh)
        smoothed_speed = np.mean(self.speed_history[track_id])
        
        # Actualizar posición
        self.previous_positions[track_id] = (cx, cy)
        
        return smoothed_speed
    
    def reset(self):
        """
        Reinicia el calculador
        """
        self.previous_positions = {}
        self.speed_history = {}