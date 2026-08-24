import cv2
import numpy as np

class ImageProcessor:
    """Clase para procesar imágenes con OpenCV."""
    
    def __init__(self):
        """Inicializa el procesador de imágenes."""
        self.processed_image = None
        
    def to_grayscale(self, image):
        """Convierte una imagen a escala de grises."""
        if image is None:
            return None
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        self.processed_image = gray
        return gray
    
    def apply_blur(self, image, kernel_size=(5, 5)):
        """Aplica desenfoque a la imagen."""
        if image is None:
            return None
        blurred = cv2.GaussianBlur(image, kernel_size, 0)
        self.processed_image = blurred
        return blurred
    
    def detect_edges(self, image, threshold1=50, threshold2=150):
        """Detecta bordes usando Canny."""
        if image is None:
            return None
        # Si la imagen es a color, convertir a grises
        if len(image.shape) == 3:
            gray = self.to_grayscale(image)
        else:
            gray = image
            
        edges = cv2.Canny(gray, threshold1, threshold2)
        self.processed_image = edges
        return edges
    
    def resize(self, image, width=None, height=None, scale_percent=None):
        """Redimensiona la imagen manteniendo aspecto."""
        if image is None:
            return None
            
        h, w = image.shape[:2]
        
        if scale_percent:
            new_width = int(w * scale_percent / 100)
            new_height = int(h * scale_percent / 100)
        elif width and height:
            new_width = width
            new_height = height
        else:
            return image
            
        resized = cv2.resize(image, (new_width, new_height))
        self.processed_image = resized
        return resized
    
    def apply_effect(self, image, effect_type):
        """Aplica diferentes efectos a la imagen."""
        if image is None:
            return None
            
        if effect_type == "negative":
            result = cv2.bitwise_not(image)
        elif effect_type == "sepia":
            # Filtro sepia simple
            sepia_filter = np.array([[0.272, 0.534, 0.131],
                                     [0.349, 0.686, 0.168],
                                     [0.393, 0.769, 0.189]])
            result = cv2.transform(image, sepia_filter)
            result = np.clip(result, 0, 255).astype(np.uint8)
        elif effect_type == "cartoon":
            # Efecto cartoon simple
            gray = self.to_grayscale(image)
            edges = self.detect_edges(gray, 50, 150)
            # Invertir bordes y aplicar a imagen original
            edges_inv = cv2.bitwise_not(edges)
            result = cv2.bitwise_and(image, image, mask=edges_inv)
        else:
            result = image
            
        self.processed_image = result
        return result