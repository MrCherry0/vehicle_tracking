# ============================================================================
# main.py
# ============================================================================
"""
Punto de entrada de la aplicación.
Instancia el patrón MVC y ejecuta la aplicación.
"""

from views.main_window import MainWindow
from models.video_processor import VideoProcessor
from controllers.app_controller import AppController


def main():
    """
    Función principal
    """
    # Crear instancias del patrón MVC
    
    # MODELO: Procesador de video con detección y tracking
    video_processor = VideoProcessor()
    
    # VISTA: Interfaz gráfica
    view = MainWindow()
    
    # CONTROLADOR: Lógica de control que conecta vista y modelo
    controller = AppController(view, video_processor)
    
    # Iniciar aplicación
    view.run()


if __name__ == "__main__":
    main()