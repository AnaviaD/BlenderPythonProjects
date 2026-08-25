import cv2
import numpy as np
from datetime import datetime

class ImageProcessor:
    """
    Procesador de imágenes con dos buffers independientes:
    - test_image: para la imagen del botón 1 (Screenshot Test)
    - canvas_image: para la imagen del botón 2 (Screenshot Canvas)
    """
    
    def __init__(self):
        """Inicializa los dos buffers de imagen."""
        # Diccionario para la imagen Test
        self.test_image = {
            'pixels': None,
            'titulo': "Test",
            'fecha': None,
            'descripcion': "",
            'ruta': ""
        }
        
        # Diccionario para la imagen Canvas
        self.canvas_image = {
            'pixels': None,
            'titulo': "Canvas",
            'fecha': None,
            'descripcion': "",
            'ruta': ""
        }
    
    # ================================================================
    # MÉTODOS PARA IMAGEN TEST
    # ================================================================
    
    def set_test_image(self, pixels, titulo="Test", descripcion="", ruta=""):
        """
        Asigna la imagen Test.
        
        Args:
            pixels: array numpy de OpenCV
            titulo: str (opcional)
            descripcion: str (opcional)
            ruta: str (opcional)
        """
        if pixels is not None:
            self.test_image['pixels'] = pixels.copy()
            self.test_image['titulo'] = titulo
            self.test_image['fecha'] = datetime.now()
            self.test_image['descripcion'] = descripcion
            self.test_image['ruta'] = ruta
    
    def get_test_pixels(self):
        """Retorna los píxeles de la imagen Test."""
        return self.test_image['pixels']
    
    def get_test_metadata(self):
        """Retorna el diccionario completo de la imagen Test."""
        return self.test_image
    
    def reset_test_image(self):
        """Limpia la imagen Test."""
        self.test_image = {
            'pixels': None,
            'titulo': "Test",
            'fecha': None,
            'descripcion': "",
            'ruta': ""
        }
    
    # ================================================================
    # MÉTODOS PARA IMAGEN CANVAS
    # ================================================================
    
    def set_canvas_image(self, pixels, titulo="Canvas", descripcion="", ruta=""):
        """
        Asigna la imagen Canvas.
        
        Args:
            pixels: array numpy de OpenCV
            titulo: str (opcional)
            descripcion: str (opcional)
            ruta: str (opcional)
        """
        if pixels is not None:
            self.canvas_image['pixels'] = pixels.copy()
            self.canvas_image['titulo'] = titulo
            self.canvas_image['fecha'] = datetime.now()
            self.canvas_image['descripcion'] = descripcion
            self.canvas_image['ruta'] = ruta
    
    def get_canvas_pixels(self):
        """Retorna los píxeles de la imagen Canvas."""
        return self.canvas_image['pixels']
    
    def get_canvas_metadata(self):
        """Retorna el diccionario completo de la imagen Canvas."""
        return self.canvas_image
    
    def reset_canvas_image(self):
        """Limpia la imagen Canvas."""
        self.canvas_image = {
            'pixels': None,
            'titulo': "Canvas",
            'fecha': None,
            'descripcion': "",
            'ruta': ""
        }
    
    # ================================================================
    # MÉTODOS DE UTILIDAD (para ambas imágenes)
    # ================================================================
    
    def reset_all(self):
        """Limpia ambas imágenes."""
        self.reset_test_image()
        self.reset_canvas_image()
    
    def get_image_info(self, pixels):
        """
        Obtiene información básica de una imagen (si se proporcionan píxeles).
        
        Args:
            pixels: array numpy de OpenCV
            
        Returns:
            dict: Información de la imagen o None si no hay imagen
        """
        if pixels is None:
            return None
            
        info = {
            'dimensions': f"{pixels.shape[1]} x {pixels.shape[0]}",
            'channels': pixels.shape[2] if len(pixels.shape) == 3 else 1,
            'dtype': str(pixels.dtype),
            'total_pixels': pixels.shape[0] * pixels.shape[1],
            'memory_size': f"{pixels.nbytes / 1024:.2f} KB"
        }
        return info
    
    def calculate_statistics(self, pixels):
        """
        Calcula estadísticas de una imagen.
        
        Args:
            pixels: array numpy de OpenCV
            
        Returns:
            dict: Estadísticas o None
        """
        if pixels is None:
            return None
            
        stats = {
            'mean': float(np.mean(pixels)),
            'std': float(np.std(pixels)),
            'min': float(np.min(pixels)),
            'max': float(np.max(pixels))
        }
        
        if len(pixels.shape) == 3:
            b, g, r = cv2.split(pixels)
            stats['channels'] = {
                'B': {'mean': float(np.mean(b)), 'std': float(np.std(b))},
                'G': {'mean': float(np.mean(g)), 'std': float(np.std(g))},
                'R': {'mean': float(np.mean(r)), 'std': float(np.std(r))}
            }
        
        return stats
    
    # ================================================================
    # EJEMPLOS DE PROCESAMIENTO (PARA CUANDO QUIERAS EXPERIMENTAR)
    # ================================================================
    # Puedes añadir métodos que tomen 'pixels' como argumento y devuelvan
    # el resultado procesado. Luego desde la UI llamas a estos métodos
    # con los píxeles de test o canvas según necesites.
    # ================================================================
    
    def convert_to_grayscale(self, pixels):
        """Convierte una imagen a escala de grises."""
        if pixels is None:
            return None
        if len(pixels.shape) == 3:
            return cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
        return pixels
    
    def apply_gaussian_blur(self, pixels, kernel_size=(5, 5)):
        """Aplica desenfoque gaussiano."""
        if pixels is None:
            return None
        return cv2.GaussianBlur(pixels, kernel_size, 0)
    
    def detect_edges(self, pixels, threshold1=50, threshold2=150):
        """Detecta bordes con Canny."""
        if pixels is None:
            return None
        if len(pixels.shape) == 3:
            gray = cv2.cvtColor(pixels, cv2.COLOR_BGR2GRAY)
        else:
            gray = pixels
        return cv2.Canny(gray, threshold1, threshold2)