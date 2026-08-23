# src/core/screen_capture.py

import mss
import numpy as np
from src.utils.logger import logger

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
        logger.info("ScreenCapture inicializado")

    # En src/core/screen_capture.py

    def capture_area(self, area: dict) -> np.ndarray:
        """
        Captura un área específica de la pantalla y devuelve la imagen RECORTADA.
        """
        try:
            # Validar área
            if not area or 'left' not in area or 'top' not in area or 'width' not in area or 'height' not in area:
                logger.error("Área inválida: faltan coordenadas")
                return np.array([])
            
            # Validar dimensiones
            if area['width'] <= 0 or area['height'] <= 0:
                logger.error(f"Dimensiones inválidas: {area}")
                return np.array([])
            
            logger.debug(f"Capturando área: {area}")
            
            # Crear monitor para mss
            monitor = {
                'left': area['left'],
                'top': area['top'],
                'width': area['width'],
                'height': area['height']
            }
            
            # Capturar
            screenshot = self.sct.grab(monitor)
            
            # Convertir a numpy array
            img = np.array(screenshot)
            
            # Verificar que la captura no esté vacía
            if img.size == 0:
                logger.error("Captura vacía")
                return np.array([])
            
            # Convertir BGRA a BGR (eliminar canal alfa)
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            
            logger.info(f"✅ Área capturada: {img.shape} (BGR)")
            return img
            
        except Exception as e:
            logger.error(f"Error capturando área: {e}")
            return np.array([])