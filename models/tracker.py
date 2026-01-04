# ============================================================================
# models/tracker.py
# ============================================================================
"""
Implementación de SORT (Simple Online and Realtime Tracking).
Usa Hungarian algorithm para asociar detecciones con tracks.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from .kalman_filter import KalmanBoxTracker


def iou(bb_test, bb_gt):
    """
    Calcula IoU entre dos bounding boxes
    """
    xx1 = np.maximum(bb_test[0], bb_gt[0])
    yy1 = np.maximum(bb_test[1], bb_gt[1])
    xx2 = np.minimum(bb_test[2], bb_gt[2])
    yy2 = np.minimum(bb_test[3], bb_gt[3])
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    wh = w * h
    o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
              + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
    return o


def associate_detections_to_trackers(detections, trackers, iou_threshold=0.3):
    """
    Asocia detecciones con trackers usando IoU
    """
    if len(trackers) == 0:
        return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)
    
    iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
    
    for d, det in enumerate(detections):
        for t, trk in enumerate(trackers):
            iou_matrix[d, t] = iou(det, trk)
    
    # Hungarian algorithm
    if min(iou_matrix.shape) > 0:
        row_ind, col_ind = linear_sum_assignment(-iou_matrix)
        matched_indices = np.column_stack((row_ind, col_ind))
    else:
        matched_indices = np.empty((0, 2), dtype=int)
    
    unmatched_detections = []
    for d in range(len(detections)):
        if d not in matched_indices[:, 0]:
            unmatched_detections.append(d)
    
    unmatched_trackers = []
    for t in range(len(trackers)):
        if t not in matched_indices[:, 1]:
            unmatched_trackers.append(t)
    
    # Filtrar matches con IoU bajo
    matches = []
    for m in matched_indices:
        if iou_matrix[m[0], m[1]] < iou_threshold:
            unmatched_detections.append(m[0])
            unmatched_trackers.append(m[1])
        else:
            matches.append(m.reshape(1, 2))
    
    if len(matches) == 0:
        matches = np.empty((0, 2), dtype=int)
    else:
        matches = np.concatenate(matches, axis=0)
    
    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)


class Sort:
    """
    Tracker SORT (Simple Online and Realtime Tracking)
    """
    
    def __init__(self, max_age=30, min_hits=3):
        """
        Args:
            max_age: Máximo de frames sin detección antes de eliminar tracker
            min_hits: Mínimo de hits para confirmar tracker
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.trackers = []
        self.frame_count = 0
    
    def update(self, detections):
        """
        Actualiza trackers con nuevas detecciones
        
        Args:
            detections: Array de shape (N, 5) con [x1, y1, x2, y2, conf]
            
        Returns:
            tracks: Array de shape (M, 5) con [x1, y1, x2, y2, id]
        """
        self.frame_count += 1
        
        # Predicción de trackers existentes
        trks = np.zeros((len(self.trackers), 5))
        to_del = []
        for t, trk in enumerate(trks):
            pos = self.trackers[t].predict()[0]
            trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_del.append(t)
        
        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_del):
            self.trackers.pop(t)
        
        # Asociación
        matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(
            detections, trks
        )
        
        # Actualizar trackers matched
        for m in matched:
            self.trackers[m[1]].update(detections[m[0], :])
        
        # Crear nuevos trackers
        for i in unmatched_dets:
            trk = KalmanBoxTracker(detections[i, :])
            self.trackers.append(trk)
        
        # Retornar trackers activos
        ret = []
        for trk in self.trackers:
            d = trk.get_state()[0]
            if trk.time_since_update < 1 and (trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits):
                ret.append(np.concatenate((d, [trk.id + 1])).reshape(1, -1))
            
            # Eliminar trackers muertos
            if trk.time_since_update > self.max_age:
                self.trackers.pop(self.trackers.index(trk))
        
        if len(ret) > 0:
            return np.concatenate(ret)
        return np.empty((0, 5))
