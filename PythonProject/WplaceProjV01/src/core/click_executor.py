"""
Módulo para ejecutar clics automáticos.
"""

import pyautogui
import time
from typing import List, Tuple
from src.utils.logger import logger

class ClickExecutor:
    """Ejecuta clics en posiciones específicas"""
    
    def __init__(self):
        # Configurar seguridad
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.0015  # 1.5ms entre acciones
        logger.info("ClickExecutor inicializado")
    
    def execute_clicks(self, positions: List[Tuple[int, int]], cooldown_ms: float = 1.5):
        """
        Ejecuta clics en las posiciones dadas.
        
        Args:
            positions: Lista de coordenadas (x, y)
            cooldown_ms: Tiempo entre clics en milisegundos
        """
        if not positions:
            logger.warning("No hay posiciones para hacer clic")
            return
        
        logger.info(f"Iniciando ejecución de {len(positions)} clics")
        
        try:
            for i, (x, y) in enumerate(positions):
                # Hacer clic
                pyautogui.click(x, y)
                
                # Log cada 100 clics para no saturar
                if i % 100 == 0:
                    logger.debug(f"Progreso: {i+1}/{len(positions)} clics")
                
                # Cooldown en segundos
                if cooldown_ms > 0:
                    time.sleep(cooldown_ms / 1000)
            
            logger.info(f"Ejecución completada: {len(positions)} clics")
            
        except pyautogui.FailSafeException:
            logger.warning("FailSafe activado - movimiento del mouse detectado")
            raise
        except Exception as e:
            logger.error(f"Error durante ejecución de clics: {e}")
            raise
    
    def test_click(self, x: int, y: int):
        """Prueba un solo clic (para debugging)"""
        try:
            pyautogui.click(x, y)
            logger.info(f"Clic de prueba en ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Error en clic de prueba: {e}")
            return False