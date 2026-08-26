import numpy as np
import mss
import cv2
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

    def capture_region(self, x, y, width, height):
        try:
            with mss.mss() as sct:
                # Usar el monitor principal explícitamente
                monitor = sct.monitors[0]  # monitor 0 = todos combinados
                # Ajustar las coordenadas relativas al monitor
                region = {
                    "top": y + monitor["top"],
                    "left": x + monitor["left"],
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(region)
                img_np = np.array(screenshot)
                img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                self.last_screenshot = img_bgr.copy()
                return img_bgr
        except Exception as e:
            print(f"Error al capturar región: {e}")
            return None
     
    
    def get_color_at(self, x, y, radius=2):
        left = max(0, x - radius)
        top = max(0, y - radius)
        right = min(self.screen_width, x + radius + 1)
        bottom = min(self.screen_height, y + radius + 1)
        
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            region = {
                "top": top + monitor["top"],
                "left": left + monitor["left"],
                "width": right - left,
                "height": bottom - top
            }
            img = sct.grab(region)
            img_np = np.array(img)
            avg_color = np.mean(img_np, axis=(0, 1))
            return tuple(int(c) for c in avg_color[:3])