
# ============================================================================
# views/main_window.py
# ============================================================================
"""
Vista principal usando CustomTkinter.
Interfaz con reproductor de video y controles.
VERSIÓN ADAPTATIVA: Se ajusta a cualquier tamaño de pantalla.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2


class MainWindow:
    """
    Ventana principal de la aplicación (adaptativa y responsiva)
    """
    
    def __init__(self):
        """
        Inicializa la interfaz gráfica
        """
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("Sistema de Tracking de Vehículos")
        
        # Obtener resolución de pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Configurar ventana al 85% de la pantalla (con mínimo)
        window_width = max(1024, int(screen_width * 0.85))
        window_height = max(768, int(screen_height * 0.85))
        
        # Centrar ventana
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1024, 768)
        
        # Hacer ventana redimensionable
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        
        # Variables para dimensiones adaptativas del canvas
        self.canvas_width = 0
        self.canvas_height = 0
        self.aspect_ratio = 16 / 9  # Ratio por defecto
        
        # Callbacks (serán asignados por el controlador)
        self.on_load_video = None
        self.on_play = None
        self.on_pause = None
        self.on_next_frame = None
        self.on_prev_frame = None
        self.on_forward_5s = None
        self.on_backward_5s = None
        self.on_progress_change = None
        
        self._create_widgets()
        
        # Bind para redimensionamiento
        self.root.bind("<Configure>", self._on_window_resize)
    
    def _calculate_canvas_size(self):
        """
        Calcula el tamaño óptimo del canvas según la ventana
        """
        # Obtener tamaño disponible (dejando espacio para controles)
        available_width = self.root.winfo_width() - 40
        available_height = self.root.winfo_height() - 350  # Espacio para controles
        
        # Calcular dimensiones manteniendo aspect ratio
        width_by_height = int(available_height * self.aspect_ratio)
        height_by_width = int(available_width / self.aspect_ratio)
        
        if width_by_height <= available_width:
            self.canvas_width = width_by_height
            self.canvas_height = available_height
        else:
            self.canvas_width = available_width
            self.canvas_height = height_by_width
        
        # Mínimos
        self.canvas_width = max(640, self.canvas_width)
        self.canvas_height = max(360, self.canvas_height)
    
    def _on_window_resize(self, event):
        """
        Maneja el redimensionamiento de la ventana
        """
        if event.widget == self.root:
            self._calculate_canvas_size()
            self.video_canvas.configure(
                width=self.canvas_width,
                height=self.canvas_height
            )
    
    def _create_widgets(self):
        """
        Crea los widgets de la interfaz (adaptativa)
        """
        # Frame principal con scroll si es necesario
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.rowconfigure(1, weight=1)  # Video canvas expandible
        main_frame.columnconfigure(0, weight=1)
        
        # ==================== BOTÓN DE CARGA ====================
        load_btn = ctk.CTkButton(
            main_frame,
            text="📁 Cargar Video",
            command=self._handle_load_video,
            height=40,
            font=("Arial", 14, "bold")
        )
        load_btn.grid(row=0, column=0, pady=10, sticky="ew", padx=20)
        
        # ==================== CANVAS PARA VIDEO ====================
        # Calcular tamaño inicial
        self._calculate_canvas_size()
        
        video_frame = ctk.CTkFrame(main_frame)
        video_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        video_frame.rowconfigure(0, weight=1)
        video_frame.columnconfigure(0, weight=1)
        
        self.video_canvas = ctk.CTkCanvas(
            video_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="black",
            highlightthickness=0
        )
        self.video_canvas.pack(expand=True)
        
        # ==================== CONTROLES DE REPRODUCCIÓN ====================
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.grid(row=2, column=0, pady=10, sticky="ew", padx=20)
        
        # Fila de botones (adaptativa)
        btn_frame = ctk.CTkFrame(controls_frame)
        btn_frame.pack(pady=5)
        
        # Botones con tamaño adaptativo
        button_width = 70
        
        self.backward_5s_btn = ctk.CTkButton(
            btn_frame, text="⏮ -5s", command=self._handle_backward_5s, 
            width=button_width
        )
        self.backward_5s_btn.pack(side="left", padx=3)
        
        self.prev_frame_btn = ctk.CTkButton(
            btn_frame, text="◀ -1F", command=self._handle_prev_frame, 
            width=button_width
        )
        self.prev_frame_btn.pack(side="left", padx=3)
        
        self.play_btn = ctk.CTkButton(
            btn_frame, text="▶ Play", command=self._handle_play, 
            width=button_width + 20
        )
        self.play_btn.pack(side="left", padx=3)
        
        self.pause_btn = ctk.CTkButton(
            btn_frame, text="⏸ Pausa", command=self._handle_pause, 
            width=button_width + 20, state="disabled"
        )
        self.pause_btn.pack(side="left", padx=3)
        
        self.next_frame_btn = ctk.CTkButton(
            btn_frame, text="▶ +1F", command=self._handle_next_frame, 
            width=button_width
        )
        self.next_frame_btn.pack(side="left", padx=3)
        
        self.forward_5s_btn = ctk.CTkButton(
            btn_frame, text="⏭ +5s", command=self._handle_forward_5s, 
            width=button_width
        )
        self.forward_5s_btn.pack(side="left", padx=3)
        
        # ==================== BARRA DE PROGRESO ====================
        progress_frame = ctk.CTkFrame(controls_frame)
        progress_frame.pack(pady=10, fill="x")
        
        self.progress_label = ctk.CTkLabel(
            progress_frame, text="Frame: 0 / 0", font=("Arial", 11)
        )
        self.progress_label.pack()
        
        self.progress_slider = ctk.CTkSlider(
            progress_frame,
            from_=0,
            to=100,
            command=self._handle_progress_change
        )
        self.progress_slider.pack(pady=5, fill="x", padx=10)
        self.progress_slider.set(0)
        
        # ==================== TABLA DE ESTADÍSTICAS ====================
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.grid(row=3, column=0, pady=10, sticky="ew", padx=20)
        
        ctk.CTkLabel(
            stats_frame, text="📊 Estadísticas", font=("Arial", 14, "bold")
        ).pack(pady=5)
        
        # Tabla adaptativa con grid
        table_frame = ctk.CTkFrame(stats_frame)
        table_frame.pack(pady=5, fill="x", padx=10)
        
        # Configurar columnas para que se expandan
        for i in range(3):
            table_frame.columnconfigure(i, weight=1)
        
        # Headers
        headers = ["Frame Actual", "Autos Detectados (Total)", "Autos Visibles"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                table_frame, text=header, font=("Arial", 11, "bold")
            ).grid(row=0, column=i, padx=5, pady=5, sticky="ew")
        
        # Valores
        self.frame_label = ctk.CTkLabel(
            table_frame, text="0", font=("Arial", 11)
        )
        self.frame_label.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.total_vehicles_label = ctk.CTkLabel(
            table_frame, text="0", font=("Arial", 11)
        )
        self.total_vehicles_label.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.current_vehicles_label = ctk.CTkLabel(
            table_frame, text="0", font=("Arial", 11)
        )
        self.current_vehicles_label.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
    
    def _handle_load_video(self):
        if self.on_load_video:
            self.on_load_video()
    
    def _handle_play(self):
        if self.on_play:
            self.on_play()
        self.play_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
    
    def _handle_pause(self):
        if self.on_pause:
            self.on_pause()
        self.play_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
    
    def _handle_next_frame(self):
        if self.on_next_frame:
            self.on_next_frame()
    
    def _handle_prev_frame(self):
        if self.on_prev_frame:
            self.on_prev_frame()
    
    def _handle_forward_5s(self):
        if self.on_forward_5s:
            self.on_forward_5s()
    
    def _handle_backward_5s(self):
        if self.on_backward_5s:
            self.on_backward_5s()
    
    def _handle_progress_change(self, value):
        if self.on_progress_change:
            self.on_progress_change(int(value))
    
    def show_file_dialog(self):
        """
        Muestra diálogo para seleccionar video
        """
        return filedialog.askopenfilename(
            title="Seleccionar Video",
            filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv"), ("Todos", "*.*")]
        )
    
    def show_error(self, title, message):
        """
        Muestra mensaje de error
        """
        messagebox.showerror(title, message)
    
    def update_video_frame(self, frame):
        """
        Actualiza el frame mostrado en el canvas (adaptativamente)
        """
        # Convertir BGR a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Redimensionar frame para ajustarse al canvas
        frame_height, frame_width = frame_rgb.shape[:2]
        
        # Calcular escala manteniendo aspect ratio
        scale_w = self.canvas_width / frame_width
        scale_h = self.canvas_height / frame_height
        scale = min(scale_w, scale_h)
        
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        
        # Redimensionar
        frame_resized = cv2.resize(frame_rgb, (new_width, new_height), 
                                   interpolation=cv2.INTER_AREA)
        
        # Convertir a PIL Image
        img = Image.fromarray(frame_resized)
        
        # Convertir a PhotoImage
        photo = ImageTk.PhotoImage(image=img)
        
        # Centrar en canvas
        x_offset = (self.canvas_width - new_width) // 2
        y_offset = (self.canvas_height - new_height) // 2
        
        # Actualizar canvas
        self.video_canvas.delete("all")
        self.video_canvas.create_image(x_offset, y_offset, anchor="nw", image=photo)
        self.video_canvas.image = photo
    
    def update_stats(self, stats):
        """
        Actualiza la tabla de estadísticas
        """
        self.frame_label.configure(text=str(stats['frame']))
        self.total_vehicles_label.configure(text=str(stats['total_vehicles']))
        self.current_vehicles_label.configure(text=str(stats['current_vehicles']))
    
    def update_progress(self, current, total):
        """
        Actualiza la barra de progreso
        """
        self.progress_label.configure(text=f"Frame: {current} / {total}")
        if total > 0:
            self.progress_slider.configure(to=total)
            self.progress_slider.set(current)
    
    def run(self):
        """
        Inicia el loop de la aplicación
        """
        self.root.mainloop()
