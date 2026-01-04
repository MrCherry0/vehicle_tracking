
# ============================================================================
# controllers/app_controller.py
# ============================================================================
"""
Controlador principal que conecta la Vista con el Modelo.
Maneja eventos de UI y coordina el procesamiento de video.
"""

import cv2
import threading
import time


class AppController:
    """
    Controlador de la aplicación
    """
    
    def __init__(self, view, video_processor):
        """
        Args:
            view: Instancia de MainWindow
            video_processor: Instancia de VideoProcessor
        """
        self.view = view
        self.processor = video_processor
        
        # Estado del video
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.current_frame_idx = 0
        self.fps = 30
        
        # Estado de reproducción
        self.is_playing = False
        self.play_thread = None
        
        # Cache de frames procesados
        self.processed_frames = {}
        self.frame_stats = {}
        
        # Conectar callbacks de la vista
        self._connect_callbacks()
    
    def _connect_callbacks(self):
        """
        Conecta los eventos de la vista con los métodos del controlador
        """
        self.view.on_load_video = self.load_video
        self.view.on_play = self.play_video
        self.view.on_pause = self.pause_video
        self.view.on_next_frame = self.next_frame
        self.view.on_prev_frame = self.prev_frame
        self.view.on_forward_5s = self.forward_5s
        self.view.on_backward_5s = self.backward_5s
        self.view.on_progress_change = self.seek_to_frame
    
    def load_video(self):
        """
        Carga un video seleccionado por el usuario
        """
        video_path = self.view.show_file_dialog()
        
        if not video_path:
            return
        
        # Abrir video
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            self.view.show_error("Error", "No se pudo abrir el video")
            return
        
        # Guardar información del video
        self.video_path = video_path
        self.cap = cap
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Reiniciar procesador y cache
        self.processor.reset()
        self.processed_frames = {}
        self.frame_stats = {}
        self.current_frame_idx = 0
        
        # Mostrar primer frame
        self._show_frame(0)
        
        # Actualizar progreso
        self.view.update_progress(0, self.total_frames)
    
    def _process_and_show_frame(self, frame_idx):
        """
        Procesa y muestra un frame específico
        """
        if self.cap is None:
            return
        
        # Verificar si ya está en cache
        if frame_idx in self.processed_frames:
            frame = self.processed_frames[frame_idx]
            stats = self.frame_stats[frame_idx]
        else:
            # Leer frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self.cap.read()
            
            if not ret:
                return
            
            # Procesar frame
            frame, _, stats = self.processor.process_frame(frame)
            
            # Guardar en cache (limitar cache a 100 frames)
            if len(self.processed_frames) > 100:
                # Eliminar frame más antiguo
                oldest = min(self.processed_frames.keys())
                del self.processed_frames[oldest]
                del self.frame_stats[oldest]
            
            self.processed_frames[frame_idx] = frame
            self.frame_stats[frame_idx] = stats
        
        # Mostrar
        self.view.update_video_frame(frame)
        self.view.update_stats(stats)
        self.view.update_progress(frame_idx, self.total_frames)
        
        self.current_frame_idx = frame_idx
    
    def _show_frame(self, frame_idx):
        """
        Muestra un frame sin procesar (más rápido para navegación)
        """
        if self.cap is None:
            return
        
        frame_idx = max(0, min(frame_idx, self.total_frames - 1))
        self._process_and_show_frame(frame_idx)
    
    def play_video(self):
        """
        Inicia la reproducción del video
        """
        if self.cap is None or self.is_playing:
            return
        
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()
    
    def _play_loop(self):
        """
        Loop de reproducción en hilo separado
        """
        target_delay = 1.0 / self.fps
        
        while self.is_playing and self.current_frame_idx < self.total_frames - 1:
            start_time = time.time()
            
            # Procesar y mostrar siguiente frame
            self._process_and_show_frame(self.current_frame_idx + 1)
            
            # Controlar FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, target_delay - elapsed)
            time.sleep(sleep_time)
        
        self.is_playing = False
    
    def pause_video(self):
        """
        Pausa la reproducción
        """
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join(timeout=1.0)
    
    def next_frame(self):
        """
        Avanza un frame
        """
        self.pause_video()
        if self.current_frame_idx < self.total_frames - 1:
            self._show_frame(self.current_frame_idx + 1)
    
    def prev_frame(self):
        """
        Retrocede un frame
        """
        self.pause_video()
        if self.current_frame_idx > 0:
            self._show_frame(self.current_frame_idx - 1)
    
    def forward_5s(self):
        """
        Avanza 5 segundos
        """
        self.pause_video()
        frames_to_skip = int(5 * self.fps)
        new_idx = min(self.current_frame_idx + frames_to_skip, self.total_frames - 1)
        self._show_frame(new_idx)
    
    def backward_5s(self):
        """
        Retrocede 5 segundos
        """
        self.pause_video()
        frames_to_skip = int(5 * self.fps)
        new_idx = max(self.current_frame_idx - frames_to_skip, 0)
        self._show_frame(new_idx)
    
    def seek_to_frame(self, frame_idx):
        """
        Salta a un frame específico
        """
        was_playing = self.is_playing
        self.pause_video()
        self._show_frame(frame_idx)
        
        if was_playing:
            self.play_video()
