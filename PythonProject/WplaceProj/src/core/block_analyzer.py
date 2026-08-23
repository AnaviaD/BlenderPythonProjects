"""
Módulo para analizar bloques y encontrar los más pequeños automáticamente.
"""

import numpy as np
import cv2
import time
from typing import List, Tuple, Optional, Dict
from collections import Counter

from src.models.pixel_data import Block, BlockType, MatrixAnalysisResult
from src.utils.logger import logger


class BlockAnalyzer:
    """
    Analiza imágenes y encuentra automáticamente los bloques más pequeños.
    """
    
    def __init__(self):
        self.last_result: Optional[MatrixAnalysisResult] = None
        logger.info("BlockAnalyzer inicializado - Modo automático")
    
    def analyze_matrix(self, image: np.ndarray, area: dict) -> MatrixAnalysisResult:
        """
        Analiza la imagen y encuentra automáticamente los bloques más pequeños.
        
        Args:
            image: Imagen YA RECORTADA del área seleccionada
            area: Área seleccionada (para coordenadas absolutas)
            
        Returns:
            MatrixAnalysisResult con los bloques detectados
        """
        start_time = time.time()
        
        logger.info("🔍 Iniciando análisis automático...")
        
        # Validar imagen
        if image is None or image.size == 0:
            logger.error("Imagen vacía")
            raise ValueError("La imagen está vacía")
        
        # 1. Detectar todos los bloques de colores en la imagen
        blocks = self._detect_all_blocks(image, area)
        
        if not blocks:
            logger.warning("No se detectaron bloques en la imagen")
            return self._create_empty_result(area, 0)
        
        # 2. Encontrar el tamaño mínimo entre todos los bloques
        block_sizes = [b.size for b in blocks]
        size_counter = Counter(block_sizes)
        min_size = min(block_sizes)
        
        logger.info(f"📊 Tamaños encontrados: {dict(size_counter)}")
        logger.info(f"✅ Tamaño mínimo detectado: {min_size} px")
        
        # 3. Filtrar solo los bloques del tamaño mínimo
        min_blocks = [b for b in blocks if b.size == min_size]
        
        # 4. Clasificar los bloques
        all_blocks = []
        nested_blocks = []
        normal_blocks = []
        outlined_blocks = []
        
        for block in blocks:
            # Clasificar por tamaño
            if block.size == min_size:
                # Es el más pequeño → Tipo C (Anidado)
                block.block_type = BlockType.NESTED
                block.confidence = 0.95
                nested_blocks.append(block)
            elif block.size < min_size * 2:
                # Tamaño intermedio → Tipo B (Marco)
                block.block_type = BlockType.OUTLINED
                block.confidence = 0.85
                outlined_blocks.append(block)
            else:
                # Tamaño grande → Tipo A (Normal)
                block.block_type = BlockType.NORMAL
                block.confidence = 0.75
                normal_blocks.append(block)
            
            all_blocks.append(block)
        
        # 5. Crear resultado
        result = MatrixAnalysisResult(
            block_size=min_size,  # Usamos el mínimo como referencia
            outline_thickness=0,
            matrix_rows=0,
            matrix_cols=0,
            total_blocks=len(all_blocks),
            normal_count=len(normal_blocks),
            outlined_count=len(outlined_blocks),
            nested_count=len(nested_blocks),
            all_blocks=all_blocks,
            nested_blocks=nested_blocks,
            processing_time=time.time() - start_time
        )
        
        self.last_result = result
        
        # Log detallado
        logger.info(f"✅ Análisis completado:")
        logger.info(f"  • Total bloques: {len(all_blocks)}")
        logger.info(f"  • Tamaño mínimo: {min_size} px")
        logger.info(f"  • 🟥 Anidados (más pequeños): {len(nested_blocks)}")
        logger.info(f"  • 🟨 Con marco: {len(outlined_blocks)}")
        logger.info(f"  • 🟦 Normales: {len(normal_blocks)}")
        
        return result
    
    def _detect_all_blocks(self, image: np.ndarray, area: dict) -> List[Block]:
        """
        Detecta TODOS los bloques de colores en la imagen.
        """
        blocks = []
        
        try:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detectar bordes para encontrar contornos
            edges = cv2.Canny(gray, 30, 100)
            
            # Encontrar contornos
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                logger.warning("No se encontraron contornos en la imagen")
                return blocks
            
            # Obtener offset del área
            offset_x = area.get('left', 0)
            offset_y = area.get('top', 0)
            
            # Procesar cada contorno
            for contour in contours:
                # Obtener rectángulo delimitador
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filtrar contornos muy pequeños o muy grandes (ruido)
                if w < 3 or h < 3 or w > 200 or h > 200:
                    continue
                
                # El bloque debe ser aproximadamente cuadrado
                aspect_ratio = w / h if h > 0 else 1
                if aspect_ratio < 0.7 or aspect_ratio > 1.3:
                    continue
                
                # Tamaño del bloque (promedio)
                block_size = (w + h) // 2
                
                # Calcular centro
                center_x = offset_x + x + w // 2
                center_y = offset_y + y + h // 2
                
                # Extraer el bloque de la imagen original
                block_region = image[y:y+h, x:x+w]
                
                # Obtener color promedio del bloque
                if block_region.size > 0:
                    color = np.mean(block_region, axis=(0, 1)).astype(int).tolist()
                else:
                    color = [128, 128, 128]
                
                # Crear bloque (tipo temporal, se clasificará después)
                block = Block(
                    row=0,
                    col=0,
                    block_type=BlockType.NORMAL,  # Temporal
                    color=tuple(color),
                    center_x=center_x,
                    center_y=center_y,
                    size=block_size,
                    confidence=0.5,
                    metadata={
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'area': w * h
                    }
                )
                blocks.append(block)
            
            logger.info(f"🔍 Detectados {len(blocks)} bloques potenciales")
            
        except Exception as e:
            logger.error(f"Error detectando bloques: {e}")
        
        return blocks
    
    def _create_empty_result(self, area: dict, min_size: int) -> MatrixAnalysisResult:
        """Crea un resultado vacío cuando no se detectan bloques"""
        return MatrixAnalysisResult(
            block_size=min_size or 1,
            outline_thickness=0,
            matrix_rows=0,
            matrix_cols=0,
            total_blocks=0,
            normal_count=0,
            outlined_count=0,
            nested_count=0,
            all_blocks=[],
            nested_blocks=[],
            processing_time=0
        )
    
    def get_last_result(self) -> Optional[MatrixAnalysisResult]:
        """Retorna el último resultado del análisis"""
        return self.last_result