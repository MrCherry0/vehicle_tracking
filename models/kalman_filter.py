# ============================================================================
# models/kalman_filter.py
# ============================================================================
"""
Implementación del Filtro de Kalman para tracking de objetos.
Predice y actualiza la posición de los vehículos.
"""

import numpy as np
from filterpy.kalman import KalmanFilter


class KalmanBoxTracker:
    """
    Tracker de bounding box usando Filtro de Kalman.
    Estado: [x, y, s, r, vx, vy, vs] donde:
    - x, y: centro del bbox
    - s: área
    - r: aspect ratio
    - vx, vy, vs: velocidades
    """
    
    count = 0
    
    def __init__(self, bbox):
        """
        Inicializa tracker con bounding box [x1, y1, x2, y2]
        """
        # Filtro de Kalman con 7 estados y 4 observaciones
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        
        # Matriz de transición de estado
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1]
        ])
        
        # Matriz de medición
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0]
        ])
        
        # Covarianza de medición
        self.kf.R[2:, 2:] *= 10.0
        
        # Covarianza del proceso
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01
        
        # Estado inicial
        self.kf.x[:4] = self._convert_bbox_to_z(bbox)
        
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []
        self.hits = 0
        self.hit_streak = 0
        self.age = 0
        
    def _convert_bbox_to_z(self, bbox):
        """
        Convierte [x1, y1, x2, y2] a [x, y, s, r]
        """
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = bbox[0] + w / 2.0
        y = bbox[1] + h / 2.0
        s = w * h
        r = w / float(h)
        return np.array([x, y, s, r]).reshape((4, 1))
    
    def _convert_x_to_bbox(self, x):
        """
        Convierte [x, y, s, r] a [x1, y1, x2, y2]
        """
        w = np.sqrt(x[2] * x[3])
        h = x[2] / w
        return np.array([
            x[0] - w / 2.0,
            x[1] - h / 2.0,
            x[0] + w / 2.0,
            x[1] + h / 2.0
        ]).reshape((1, 4))
    
    def update(self, bbox):
        """
        Actualiza el estado con nueva medición
        """
        self.time_since_update = 0
        self.history = []
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(self._convert_bbox_to_z(bbox))
    
    def predict(self):
        """
        Predice el próximo estado
        """
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0
        self.kf.predict()
        self.age += 1
        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1
        self.history.append(self._convert_x_to_bbox(self.kf.x))
        return self.history[-1]
    
    def get_state(self):
        """
        Retorna el estado actual como bbox
        """
        return self._convert_x_to_bbox(self.kf.x)
