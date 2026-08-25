import numpy as np
import mss
import pyautogui
from utils.image_converter import ImageConverter

class ScreenshotCapture:
    """
    Clase encargada de capturar pantalla.
    """
    
    def __init__(self):
        """Inicializa el capturador de pantalla."""
        self.last_screenshot = None
        # Obtener dimensiones de la pantalla una sola vez
        self.screen_width, self.screen_height = pyautogui.size()
    
    def capture(self):
        """
        Captura la pantalla completa.
        
        Returns:
            numpy.ndarray: Imagen en formato OpenCV (BGR)
        """
        try:
            pil_image = pyautogui.screenshot()
            cv_image = ImageConverter.pil_to_cv(pil_image)
            self.last_screenshot = cv_image.copy()
            return cv_image
        except Exception as e:
            print(f"Error al capturar pantalla: {e}")
            return None
    
    def get_last_screenshot(self):
        """Retorna la última captura realizada."""
        return self.last_screenshot
    
    def get_color_at(self, x, y, radius=2):
        """
        Obtiene el color promedio de una región cuadrada alrededor de (x, y).
        
        Args:
            x, y: Coordenadas del centro
            radius: Radio en píxeles (la región será (2*radius+1) x (2*radius+1))
        
        Returns:
            tuple: Color en formato BGR (blue, green, red) como enteros 0-255
        """
        # Calcular región con límites de pantalla
        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(self.screen_width, x + radius + 1)
        bottom = min(self.screen_height, y + radius + 1)
        
        # Capturar la región con mss
        with mss.mss() as sct:
            monitor = {
                "top": top, 
                "left": left, 
                "width": right - left, 
                "height": bottom - top
            }
            img = sct.grab(monitor)
            img_np = np.array(img)
            # Calcular promedio por canal (BGR)
            avg_color = np.mean(img_np, axis=(0, 1))
            return tuple(int(c) for c in avg_color[:3])  # BGR