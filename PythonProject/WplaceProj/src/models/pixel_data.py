"""
Modelos de datos para el análisis de bloques de píxeles.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional, List
import numpy as np

class BlockType(Enum):
    """Tipos de bloques en la matriz"""
    NORMAL = "normal"          # Color sólido uniforme
    OUTLINED = "outlined"      # Con marco de diferente color
    NESTED = "nested"          # Pixel dentro de pixel (punto interior)

@dataclass
class Block:
    """
    Representa un bloque en la matriz de colores.
    Cada bloque es una celda que puede ser de diferentes tipos.
    """
    # Posición en la matriz (fila/columna)
    row: int
    col: int
    
    # Tipo de bloque
    block_type: BlockType
    
    # Color del bloque (RGB)
    color: Tuple[int, int, int]
    
    # Posición exacta en píxeles reales (para clics)
    center_x: int
    center_y: int
    
    # Tamaño del bloque en píxeles reales
    size: int
    
    # Metadatos adicionales
    confidence: float = 0.0
    metadata: Optional[dict] = None
    
    def __str__(self):
        return f"Block({self.row},{self.col}) [{self.block_type.value}] at ({self.center_x},{self.center_y})"

@dataclass
class MatrixAnalysisResult:
    """
    Resultado completo del análisis de la matriz.
    """
    # Parámetros usados
    block_size: int                    # Tamaño de cada bloque en píxeles
    outline_thickness: int              # Grosor del marco en píxeles
    
    # Dimensiones de la matriz
    matrix_rows: int
    matrix_cols: int
    total_blocks: int
    
    # Conteos por tipo
    normal_count: int
    outlined_count: int
    nested_count: int
    
    # Todos los bloques analizados
    all_blocks: List[Block]
    
    # Solo bloques anidados (para clics)
    nested_blocks: List[Block]
    
    # Tiempo de procesamiento
    processing_time: float
    
    def get_summary(self) -> str:
        """Retorna un resumen legible del análisis"""
        return (
            f"📊 Resumen de Análisis de Matriz:\n"
            f"  • Matriz: {self.matrix_rows} x {self.matrix_cols} bloques\n"
            f"  • Total: {self.total_blocks} bloques\n"
            f"  • Tamaño de bloque: {self.block_size}x{self.block_size} px\n"
            f"  • 🟦 Normales: {self.normal_count}\n"
            f"  • 🟨 Con marco: {self.outlined_count}\n"
            f"  • 🟥 Anidados: {self.nested_count}\n"
            f"  • 🎯 Posiciones para clic: {len(self.nested_blocks)}\n"
            f"  • ⏱️ Tiempo: {self.processing_time:.3f}s"
        )
    
    def get_nested_positions(self) -> List[Tuple[int, int]]:
        """Retorna las posiciones (x, y) de los bloques anidados"""
        return [(b.center_x, b.center_y) for b in self.nested_blocks]