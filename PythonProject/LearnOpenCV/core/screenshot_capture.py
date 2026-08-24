import cv2
import numpy as np
import pyautogui
import mss
from PIL import Image
import io

class ScreenshotCapture:
    """Clase para capturar y gestionar screenshots."""
    
    def __init__(self):
        """Inicializa el capturador de pantalla."""
        self.last_screenshot = None
        self.last_screenshot_cv = None
        self.sct = mss.mss()  # Instancia de MSS para capturas rápidas
        
    def capture_fullscreen(self):
        """
        Captura la pantalla completa.
        Retorna: Imagen en formato OpenCV (BGR)
        """
        try:
            # Método 1: Usando MSS (más rápido)
            screenshot = self.sct.shot(output="temp_screenshot.png")
            img_cv = cv2.imread(screenshot)
            
            # Método 2: Usando PyAutoGUI (alternativa)
            # screenshot = pyautogui.screenshot()
            # img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            self.last_screenshot = img_cv
            self.last_screenshot_cv = img_cv.copy()
            return img_cv
            
        except Exception as e:
            print(f"Error al capturar pantalla: {e}")
            return None
    
    def capture_region(self, x, y, width, height):
        """Captura una región específica de la pantalla."""
        try:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = self.sct.grab(monitor)
            img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            self.last_screenshot = img_cv
            return img_cv
        except Exception as e:
            print(f"Error al capturar región: {e}")
            return None
    
    def save_screenshot(self, filepath):
        """Guarda la última captura en disco."""
        if self.last_screenshot is not None:
            cv2.imwrite(filepath, self.last_screenshot)
            return True
        return False
    
    def get_cv_image(self):
        """Retorna la última captura en formato OpenCV."""
        return self.last_screenshot_cv