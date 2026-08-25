import pyautogui
from utils.image_converter import ImageConverter

class ScreenshotCapture:
    """
    Clase encargada de capturar pantalla.
    """
    
    def __init__(self):
        """Inicializa el capturador de pantalla."""
        self.last_screenshot = None
    
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