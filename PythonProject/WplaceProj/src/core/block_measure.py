"""
Módulo para medir bloques y marcos en la imagen.
"""

import numpy as np
import cv2
from typing import Tuple, Optional

from src.utils.logger import logger


class BlockMeasurer:
    """
    Mide tamaños de bloques y marcos en la imagen.
    """
    
    def __init__(self):
        self.last_measured_size: Optional[int] = None
        self.last_outline_thickness: Optional[int] = None
        logger.info("BlockMeasurer inicializado")
    
    def measure_block_size(self, image: np.ndarray, area: dict) -> int:
        """
        Mide el tamaño de un bloque individual.
        
        Args:
            image: Imagen YA RECORTADA del área seleccionada
            area: Área seleccionada (usamos solo para referencia)
            
        Returns:
            int: Tamaño del bloque en píxeles
        """
        try:
            logger.info(f"Midiendo tamaño de bloque")
            
            # Validar que la imagen no esté vacía
            if image is None or image.size == 0:
                logger.error("Imagen vacía o None")
                # Fallback: usar el tamaño del área
                block_size = min(area.get('width', 10), area.get('height', 10))
                logger.warning(f"Usando fallback: {block_size}x{block_size} px")
                self.last_measured_size = block_size
                return block_size
            
            # Obtener dimensiones de la imagen recortada
            h, w = image.shape[:2]
            
            logger.info(f"Dimensiones de la imagen: {w}x{h}")
            
            # Si la imagen es aproximadamente cuadrada, ese es el bloque
            aspect_ratio = w / h if h > 0 else 1
            if 0.8 <= aspect_ratio <= 1.2:
                block_size = (w + h) // 2
                logger.info(f"Usando tamaño directo de la imagen: {block_size}x{block_size} px")
                self.last_measured_size = block_size
                return block_size
            
            # Si no es cuadrada, intentar detectar bordes
            try:
                # Convertir a grises
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # Detectar bordes
                edges = cv2.Canny(gray, 50, 150)
                
                # Encontrar contornos
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if contours:
                    # Tomar el contorno más grande
                    largest_contour = max(contours, key=cv2.contourArea)
                    
                    # Obtener rectángulo delimitador
                    x_c, y_c, w_c, h_c = cv2.boundingRect(largest_contour)
                    
                    if w_c > 0 and h_c > 0:
                        block_size = int((w_c + h_c) / 2)
                        logger.info(f"Bloque medido por detección de bordes: {block_size}x{block_size} px")
                        self.last_measured_size = block_size
                        return block_size
            except Exception as e:
                logger.warning(f"No se pudo detectar bordes: {e}")
            
            # Fallback final
            block_size = min(w, h)
            logger.info(f"Usando fallback final: {block_size}x{block_size} px")
            self.last_measured_size = block_size
            return block_size
            
        except Exception as e:
            logger.error(f"Error midiendo bloque: {e}")
            block_size = min(area.get('width', 10), area.get('height', 10))
            self.last_measured_size = block_size
            return block_size
    
    def measure_outline_thickness(self, image: np.ndarray, area: dict, block_size: Optional[int] = None) -> int:
        """
        Mide el grosor del marco de un bloque.
        
        Args:
            image: Imagen YA RECORTADA del área seleccionada
            area: Área seleccionada (usamos solo para referencia)
            block_size: Tamaño conocido del bloque (opcional)
            
        Returns:
            int: Grosor del marco en píxeles
        """
        try:
            logger.info("Midiendo grosor de marco")
            
            # Validar que la imagen no esté vacía
            if image is None or image.size == 0:
                logger.error("Imagen vacía o None")
                return 1
            
            # Obtener dimensiones
            h, w = image.shape[:2]
            
            # Si el bloque es muy pequeño
            if h < 5 or w < 5:
                logger.warning(f"Imagen demasiado pequeña: {w}x{h}")
                return 1
            
            # Si no se proporcionó block_size, estimarlo
            if block_size is None:
                block_size = min(w, h)
            
            # Intentar detectar marco
            try:
                # Convertir a grises
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # Análisis de colores en borde vs interior
                # Borde: primeras filas/columnas
                border_size = min(3, h // 4, w // 4)
                border_size = max(1, border_size)
                
                # Píxeles del borde
                border_pixels = []
                for i in range(border_size):
                    # Borde superior
                    if i < h:
                        border_pixels.extend(image[i, :].reshape(-1, 3).tolist())
                    # Borde inferior
                    if h - 1 - i >= 0:
                        border_pixels.extend(image[h - 1 - i, :].reshape(-1, 3).tolist())
                    # Borde izquierdo
                    if i < w:
                        border_pixels.extend(image[:, i].reshape(-1, 3).tolist())
                    # Borde derecho
                    if w - 1 - i >= 0:
                        border_pixels.extend(image[:, w - 1 - i].reshape(-1, 3).tolist())
                
                # Píxeles interiores (centro)
                inner_margin = border_size * 2
                inner_pixels = []
                for i in range(inner_margin, h - inner_margin):
                    for j in range(inner_margin, w - inner_margin):
                        if i < h and j < w:
                            inner_pixels.append(image[i, j])
                
                if not border_pixels or not inner_pixels:
                    logger.warning("No se pudieron recolectar píxeles suficientes")
                    return 1
                
                # Convertir a arrays
                border_pixels = np.array(border_pixels)
                inner_pixels = np.array(inner_pixels)
                
                # Calcular colores promedio
                avg_border = np.mean(border_pixels, axis=0)
                avg_inner = np.mean(inner_pixels, axis=0)
                
                # Calcular diferencia de color
                color_diff = np.linalg.norm(avg_border - avg_inner)
                
                if color_diff > 30:
                    # Hay marco, estimar grosor
                    # Buscar transición en una línea horizontal del centro
                    middle_row = image[h // 2, :]
                    
                    # Buscar donde cambia el color
                    left_edge = 0
                    right_edge = w - 1
                    
                    # Buscar borde izquierdo (desde la izquierda hacia el centro)
                    for i in range(1, w // 2):
                        if i < len(middle_row):
                            diff = np.linalg.norm(middle_row[i] - avg_inner)
                            if diff < 30:
                                left_edge = i
                                break
                    
                    # Buscar borde derecho (desde la derecha hacia el centro)
                    for i in range(w - 2, w // 2, -1):
                        if i < len(middle_row):
                            diff = np.linalg.norm(middle_row[i] - avg_inner)
                            if diff < 30:
                                right_edge = i
                                break
                    
                    # El grosor estimado
                    outline_thickness = min(left_edge, w - 1 - right_edge)
                    outline_thickness = max(1, outline_thickness)
                    
                    logger.info(f"Marco detectado con grosor: {outline_thickness} px")
                    self.last_outline_thickness = outline_thickness
                    return outline_thickness
                else:
                    logger.info("No se detectó marco (color uniforme)")
                    self.last_outline_thickness = 0
                    return 0
                    
            except Exception as e:
                logger.warning(f"Error en detección de marco: {e}")
            
            # Fallback
            logger.warning("Usando grosor por defecto: 1 px")
            self.last_outline_thickness = 1
            return 1
            
        except Exception as e:
            logger.error(f"Error midiendo marco: {e}")
            return 1
    
    def get_last_measurements(self) -> dict:
        """Retorna las últimas mediciones realizadas"""
        return {
            'block_size': self.last_measured_size,
            'outline_thickness': self.last_outline_thickness
        }