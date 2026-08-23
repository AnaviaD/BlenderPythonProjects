"""
Módulo para ejecutar clics automáticos con cooldown aleatorio.
"""

import pyautogui
import time
import random
from typing import List, Tuple
from src.utils.logger import logger


class ClickExecutor:
    """Ejecuta clics en posiciones específicas con cooldown aleatorio"""
    
    def __init__(self):
        # Configurar seguridad
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.001  # Pausa mínima entre acciones (1ms)
        logger.info("ClickExecutor inicializado")
    
    def execute_clicks(
        self, 
        positions: List[Tuple[int, int]], 
        base_cooldown_ms: float = 15.0,
        random_range: float = 0.5
    ):
        """
        Ejecuta clics en las posiciones dadas con cooldown aleatorio.
        
        Args:
            positions: Lista de coordenadas (x, y)
            base_cooldown_ms: Tiempo base entre clics en milisegundos
            random_range: Rango de aleatoriedad (0.0 = fijo, 0.5 = ±50%)
        """
        if not positions:
            logger.warning("No hay posiciones para hacer clic")
            return
        
        # Calcular rango de aleatoriedad
        min_ms = max(1, base_cooldown_ms * (1 - random_range))
        max_ms = base_cooldown_ms * (1 + random_range)
        
        logger.info(f"🖱️ Iniciando {len(positions)} clics")
        logger.info(f"⚡ Cooldown: {min_ms:.1f}ms - {max_ms:.1f}ms (base: {base_cooldown_ms:.1f}ms)")
        
        try:
            total = len(positions)
            for i, (x, y) in enumerate(positions):
                # Hacer clic
                pyautogui.click(x, y)
                
                # Log cada 100 clics
                if i > 0 and i % 100 == 0:
                    logger.info(f"   Progreso: {i}/{total} clics")
                
                # Generar cooldown aleatorio
                if i < total - 1:  # No esperar después del último clic
                    random_cooldown = random.uniform(min_ms, max_ms)
                    time.sleep(random_cooldown / 1000)  # Convertir a segundos
            
            logger.info(f"✅ Ejecución completada: {total} clics")
            
        except pyautogui.FailSafeException:
            logger.warning("⚠️ FailSafe activado - movimiento del mouse detectado")
            raise
        except KeyboardInterrupt:
            logger.warning("⚠️ Ejecución interrumpida por el usuario")
            raise
        except Exception as e:
            logger.error(f"❌ Error durante ejecución de clics: {e}")
            raise
    
    def execute_clicks_constant(
        self, 
        positions: List[Tuple[int, int]], 
        cooldown_ms: float = 15.0
    ):
        """
        Ejecuta clics con cooldown constante (sin aleatoriedad).
        Útil para pruebas o cuando se necesita precisión.
        """
        if not positions:
            logger.warning("No hay posiciones para hacer clic")
            return
        
        logger.info(f"🖱️ Iniciando {len(positions)} clics (cooldown fijo: {cooldown_ms:.1f}ms)")
        
        try:
            total = len(positions)
            for i, (x, y) in enumerate(positions):
                pyautogui.click(x, y)
                
                if i > 0 and i % 100 == 0:
                    logger.info(f"   Progreso: {i}/{total} clics")
                
                if i < total - 1:
                    time.sleep(cooldown_ms / 1000)
            
            logger.info(f"✅ Ejecución completada: {total} clics")
            
        except pyautogui.FailSafeException:
            logger.warning("⚠️ FailSafe activado")
            raise
        except Exception as e:
            logger.error(f"❌ Error: {e}")
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