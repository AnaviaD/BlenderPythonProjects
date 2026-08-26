import cv2
import numpy as np
from datetime import datetime

class ImageProcessor:
    """
    Procesador de imágenes con dos buffers independientes:
    - image_test: Para imágenes pequeñas (5x5 px)
    - image_canvas: Para imágenes grandes (capturas de pantalla)
    """
    
    def __init__(self):
        """Inicializa el procesador con dos buffers vacíos."""
        # Buffer para imágenes de test (pequeñas)
        self.image_test = {
            'color': None,           # Tupla BGR (b, g, r)
            'titulo': "Test",
            'fecha': None,
            'descripcion': "",
            'coordenadas': None      # (x, y) del centro
        }
        
        # Buffer para imágenes de canvas (grandes)
        self.image_canvas = {
            'pixels': None,
            'titulo': "Canvas",
            'fecha': None,
            'descripcion': "",
            'ruta': "",
            'coordenadas': None  # (x, y, w, h)
        }

        self.canvas_processed = None
        self.canvas_original = None
        self.last_squares = []
    
    # ================================================================
    # MÉTODOS PARA IMAGEN TEST
    # ================================================================

    def set_last_squares(self, squares):
        """Guarda la lista de cuadrados del último análisis."""
        self.last_squares = squares

    def get_last_squares(self):
        """Recupera la lista de cuadrados del último análisis."""
        return self.last_squares


    def set_test_color(self, color, coordenadas=None):
        if color is not None:
            self.image_test['color'] = color
            self.image_test['fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.image_test['coordenadas'] = coordenadas    

    def get_test_color(self):
        """Retorna el color almacenado en la imagen test."""
        return self.image_test['color']
    
    def get_test_pixels(self):
        """Retorna los píxeles de la imagen test."""
        return self.image_test['pixels']
    
    def get_test_metadata(self):
        """Retorna todos los metadatos de la imagen test."""
        return self.image_test.copy()
    
    def reset_test_image(self):
        """Limpia la imagen test."""
        self.image_test['pixels'] = None
        self.image_test['fecha'] = None
        self.image_test['descripcion'] = ""
        self.image_test['ruta'] = ""
    
    # ================================================================
    # MÉTODOS PARA IMAGEN CANVAS
    # ================================================================
    
    def set_canvas_image(self, pixels, titulo="Canvas", descripcion="", ruta="", coordenadas=None):
        if pixels is not None:
            self.image_canvas['pixels'] = pixels.copy()
            self.image_canvas['titulo'] = titulo
            self.image_canvas['fecha'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.image_canvas['descripcion'] = descripcion
            self.image_canvas['ruta'] = ruta
            self.image_canvas['coordenadas'] = coordenadas

    def get_canvas_coordenadas(self):
        return self.image_canvas['coordenadas']            
    
    def get_canvas_pixels(self):
        """Retorna los píxeles de la imagen canvas."""
        return self.image_canvas['pixels']
    
    def get_canvas_metadata(self):
        """Retorna todos los metadatos de la imagen canvas."""
        return self.image_canvas.copy()
    
    def reset_canvas_image(self):
        """Limpia la imagen canvas."""
        self.image_canvas['pixels'] = None
        self.image_canvas['fecha'] = None
        self.image_canvas['descripcion'] = ""
        self.image_canvas['ruta'] = ""
    
    # ================================================================
    # MÉTODOS DE UTILIDAD Y COMPARACIÓN
    # ================================================================
    
    def get_image_info(self, image_type="test"):
        """
        Obtiene información de una imagen específica.
        
        Args:
            image_type: "test" o "canvas"
            
        Returns:
            dict: Información de la imagen
        """
        if image_type == "test":
            img = self.image_test['pixels']
            nombre = "Test"
            coords = self.image_test.get('coordenadas')
        else:
            img = self.image_canvas['pixels']
            nombre = "Canvas"
            coords = self.image_canvas.get('coordenadas')
        
        if img is None:
            return None
        
        info = {
            'nombre': nombre,
            'titulo': self.image_test['titulo'] if image_type == "test" else self.image_canvas['titulo'],
            'fecha': self.image_test['fecha'] if image_type == "test" else self.image_canvas['fecha'],
            'dimensiones': f"{img.shape[1]} x {img.shape[0]}",
            'canales': img.shape[2] if len(img.shape) == 3 else 1,
            'tipo_dato': str(img.dtype),
            'pixeles_totales': img.shape[0] * img.shape[1],
            'memoria': f"{img.nbytes / 1024:.2f} KB",
            'coordenadas': coords  # ← Agregar coordenadas
        }
        return info
        
    
    def get_image_stats(self, image_type="test"):
        """
        Calcula estadísticas de una imagen.
        
        Args:
            image_type: "test" o "canvas"
            
        Returns:
            dict: Estadísticas de la imagen
        """
        if image_type == "test":
            img = self.image_test['pixels']
        else:
            img = self.image_canvas['pixels']
            
        if img is None:
            return None
            
        stats = {
            'media': float(np.mean(img)),
            'desviacion': float(np.std(img)),
            'minimo': float(np.min(img)),
            'maximo': float(np.max(img))
        }
        
        # Si es a color, estadísticas por canal
        if len(img.shape) == 3:
            b, g, r = cv2.split(img)
            stats['canales'] = {
                'B': {'media': float(np.mean(b)), 'desviacion': float(np.std(b))},
                'G': {'media': float(np.mean(g)), 'desviacion': float(np.std(g))},
                'R': {'media': float(np.mean(r)), 'desviacion': float(np.std(r))}
            }
        
        return stats
    
    def compare_images(self):
        """
        Compara las dos imágenes (test y canvas).
        
        Returns:
            dict: Resultados de la comparación
        """
        img_test = self.image_test['pixels']
        img_canvas = self.image_canvas['pixels']
        
        if img_test is None or img_canvas is None:
            return {"error": "Una o ambas imágenes están vacías"}
        
        # Verificar que tengan el mismo tamaño
        if img_test.shape != img_canvas.shape:
            return {
                "error": "Las imágenes tienen diferentes dimensiones",
                "test_shape": img_test.shape,
                "canvas_shape": img_canvas.shape
            }
        
        # Calcular diferencia absoluta
        diff = cv2.absdiff(img_test, img_canvas)
        
        # Calcular métricas
        mse = np.mean((img_test.astype(float) - img_canvas.astype(float)) ** 2)
        
        # Calcular similitud estructural (SSIM) simple
        # Nota: Para una SSIM más precisa, usar skimage.metrics.structural_similarity
        mean_test = np.mean(img_test)
        mean_canvas = np.mean(img_canvas)
        std_test = np.std(img_test)
        std_canvas = np.std(img_canvas)
        covariance = np.cov(img_test.flatten(), img_canvas.flatten())[0, 1]
        
        # Similitud simplificada
        if std_test * std_canvas > 0:
            similarity = covariance / (std_test * std_canvas)
        else:
            similarity = 0
        
        return {
            "diferencias": diff,
            "mse": float(mse),
            "similitud": float(similarity),
            "media_test": float(mean_test),
            "media_canvas": float(mean_canvas)
        }