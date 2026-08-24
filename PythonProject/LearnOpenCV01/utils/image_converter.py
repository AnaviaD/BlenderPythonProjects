import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap

class ImageConverter:
    """Clase estática para convertir imágenes entre formatos."""
    
    @staticmethod
    def cv_to_qpixmap(cv_image):
        """
        Convierte una imagen de OpenCV (BGR) a QPixmap para Qt.
        
        Args:
            cv_image: Imagen en formato OpenCV (numpy array)
            
        Returns:
            QPixmap: Imagen lista para mostrar en Qt
        """
        if cv_image is None:
            return None
            
        if len(cv_image.shape) == 2:  # Escala de grises
            height, width = cv_image.shape
            bytes_per_line = width
            qimage = QImage(cv_image.data, width, height, 
                          bytes_per_line, QImage.Format_Grayscale8)
        else:  # Color (BGR)
            height, width, channel = cv_image.shape
            bytes_per_line = 3 * width
            # Convertir BGR (OpenCV) a RGB (Qt)
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            qimage = QImage(rgb_image.data, width, height, 
                          bytes_per_line, QImage.Format_RGB888)
        
        return QPixmap.fromImage(qimage)
    
    @staticmethod
    def pil_to_cv(pil_image):
        """
        Convierte una imagen de PIL a OpenCV.
        
        Args:
            pil_image: Imagen en formato PIL
            
        Returns:
            numpy.ndarray: Imagen en formato OpenCV (BGR)
        """
        import numpy as np
        # PIL usa RGB, OpenCV usa BGR
        img = np.array(pil_image)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)