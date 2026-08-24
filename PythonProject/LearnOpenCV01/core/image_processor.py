import cv2
import numpy as np

class ImageProcessor:
    """
    📍 PUNTO DE ENTRADA PARA EL ANÁLISIS DE IMÁGENES
    
    Esta clase es donde TODAS las operaciones de procesamiento
    y análisis de imágenes deben ir. Aquí es donde empezarás
    a experimentar con OpenCV.
    
    FLUJO DE TRABAJO:
    1. La imagen llega desde ScreenshotCapture o se carga desde archivo
    2. Pasa por los métodos de esta clase para su procesamiento
    3. Los resultados se devuelven a la UI para mostrar
    """
    
    def __init__(self):
        """Inicializa el procesador de imágenes."""
        self.original_image = None
        self.processed_image = None
        self.image_history = []  # Para deshacer operaciones
    
    def set_image(self, image):
        """
        Establece la imagen a procesar.
        
        Args:
            image: Imagen en formato OpenCV (numpy array)
        """
        if image is not None:
            self.original_image = image.copy()
            self.processed_image = image.copy()
            self.image_history = [image.copy()]
    
    def get_current_image(self):
        """Retorna la imagen actual (procesada o no)."""
        return self.processed_image
    
    def get_original_image(self):
        """Retorna la imagen original sin procesar."""
        return self.original_image
    
    def reset_to_original(self):
        """Restablece la imagen procesada a la original."""
        if self.original_image is not None:
            self.processed_image = self.original_image.copy()
            self.image_history = [self.original_image.copy()]
            return self.processed_image
        return None
    
    # ================================================================
    # 📍 AQUÍ COMIENZAN LAS OPERACIONES DE PROCESAMIENTO
    # ================================================================
    # Desde aquí hacia abajo, TODAS las funciones son para analizar
    # y procesar imágenes con OpenCV.
    #
    # Cuando quieras añadir una nueva funcionalidad:
    # 1. Crea un nuevo método aquí
    # 2. Modifica la imagen self.processed_image
    # 3. Retorna el resultado
    # ================================================================
    
    def get_image_info(self):
        """
        📍 PRIMERA FUNCIÓN DE ANÁLISIS
        Obtiene información básica de la imagen.
        
        Returns:
            dict: Información de la imagen
        """
        if self.processed_image is None:
            return None
            
        img = self.processed_image
        info = {
            'dimensions': f"{img.shape[1]} x {img.shape[0]}",  # width x height
            'channels': img.shape[2] if len(img.shape) == 3 else 1,
            'dtype': str(img.dtype),
            'total_pixels': img.shape[0] * img.shape[1],
            'memory_size': f"{img.nbytes / 1024:.2f} KB"
        }
        return info
    
    def calculate_statistics(self):
        """
        📍 SEGUNDA FUNCIÓN DE ANÁLISIS
        Calcula estadísticas básicas de la imagen.
        
        Returns:
            dict: Estadísticas de la imagen
        """
        if self.processed_image is None:
            return None
            
        img = self.processed_image
        stats = {
            'mean': float(np.mean(img)),
            'std': float(np.std(img)),
            'min': float(np.min(img)),
            'max': float(np.max(img))
        }
        
        # Si es a color, estadísticas por canal
        if len(img.shape) == 3:
            b, g, r = cv2.split(img)
            stats['channels'] = {
                'B': {'mean': float(np.mean(b)), 'std': float(np.std(b))},
                'G': {'mean': float(np.mean(g)), 'std': float(np.std(g))},
                'R': {'mean': float(np.mean(r)), 'std': float(np.std(r))}
            }
        
        return stats
    
    def get_pixel_at(self, x, y):
        """
        📍 TERCERA FUNCIÓN DE ANÁLISIS
        Obtiene el valor de un pixel específico.
        
        Args:
            x: Coordenada X (columna)
            y: Coordenada Y (fila)
            
        Returns:
            tuple: Valor del pixel en BGR
        """
        if self.processed_image is None:
            return None
            
        if 0 <= y < self.processed_image.shape[0] and 0 <= x < self.processed_image.shape[1]:
            pixel = self.processed_image[y, x]
            return tuple(pixel)
        return None
    
    def convert_to_grayscale(self):
        """
        Ejemplo de procesamiento: Convertir a escala de grises.
        ¡TÚ PUEDES AÑADIR MÁS FUNCIONES AQUÍ!
        """
        if self.processed_image is None:
            return None
            
        if len(self.processed_image.shape) == 3:
            gray = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2GRAY)
            self.processed_image = gray
            return gray
        return self.processed_image
    
    def apply_gaussian_blur(self, kernel_size=(5, 5)):
        """
        Ejemplo de procesamiento: Aplicar desenfoque.
        ¡TÚ PUEDES AÑADIR MÁS FUNCIONES AQUÍ!
        """
        if self.processed_image is None:
            return None
            
        blurred = cv2.GaussianBlur(self.processed_image, kernel_size, 0)
        self.processed_image = blurred
        return blurred
    
    def detect_edges(self, threshold1=50, threshold2=150):
        """
        Ejemplo de procesamiento: Detectar bordes con Canny.
        ¡TÚ PUEDES AÑADIR MÁS FUNCIONES AQUÍ!
        """
        if self.processed_image is None:
            return None
            
        # Si es a color, convertir a grises primero
        if len(self.processed_image.shape) == 3:
            gray = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = self.processed_image
            
        edges = cv2.Canny(gray, threshold1, threshold2)
        self.processed_image = edges
        return edges
    
    # ================================================================
    # AÑADE TUS PROPIAS FUNCIONES DE PROCESAMIENTO AQUÍ
    # ================================================================
    # 
    # Ejemplos de lo que puedes añadir:
    # 
    # def adjust_brightness(self, value):
    #     """Ajusta el brillo de la imagen."""
    #     ...
    # 
    # def rotate(self, angle):
    #     """Rota la imagen."""
    #     ...
    # 
    # def resize(self, width, height):
    #     """Redimensiona la imagen."""
    #     ...
    # 
    # def draw_rectangle(self, x1, y1, x2, y2, color=(0,255,0)):
    #     """Dibuja un rectángulo en la imagen."""
    #     ...
    # 
    # ================================================================