import pyautogui
from utils.image_converter import ImageConverter

class ScreenshotCapture:
    """
    Clase encargada de capturar pantalla.
    Esta es la capa de captura de datos.
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
            # Capturar con pyautogui (retorna PIL Image)
            pil_image = pyautogui.screenshot()
            
            # Convertir PIL a OpenCV
            cv_image = ImageConverter.pil_to_cv(pil_image)
            
            # Guardar referencia
            self.last_screenshot = cv_image.copy()
            
            return cv_image
            
        except Exception as e:
            print(f"Error al capturar pantalla: {e}")
            return None
    
    def get_last_screenshot(self):
        """Retorna la última captura realizada."""
        return self.last_screenshot