"""
Sistema de logging simple para el proyecto.
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str = "pixel_automator") -> logging.Logger:
    """Configura y retorna un logger con formato consistente"""
    
    # Crear directorio de logs si no existe
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nombre del archivo con fecha
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Formato consistente
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo (siempre guarda todo)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler para consola (solo info y errores)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger global para usar en toda la aplicación
logger = setup_logger()