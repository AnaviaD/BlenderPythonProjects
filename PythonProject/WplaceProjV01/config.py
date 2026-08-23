"""
Configuración de parámetros de detección.
"""

from src.core.pattern_detector import DetectionParams

# Parámetros de detección (ajusta estos valores según tu necesidad)
DETECTION_PARAMS = DetectionParams(
    # Para detección de contornos
    canny_threshold1=50,
    canny_threshold2=150,
    
    # Para detección de píxeles anidados
    nested_radius_min=2,       # Radio mínimo del píxel interior
    nested_radius_max=8,       # Radio máximo del píxel interior
    nested_color_tolerance=20,  # Tolerancia de color
    
    # Para detección de contornos
    outline_thickness=1,
    outline_color_tolerance=30,
    
    # Para píxeles normales
    normal_min_size=3,
    normal_max_size=20,
    
    # Umbrales de confianza
    confidence_threshold=0.7
)

# Si quieres probar diferentes configuraciones, crea variantes:
DETECTION_PARAMS_STRICT = DetectionParams(
    nested_radius_min=2,
    nested_radius_max=5,
    nested_color_tolerance=10,
    confidence_threshold=0.9
)

DETECTION_PARAMS_LOOSE = DetectionParams(
    nested_radius_min=1,
    nested_radius_max=15,
    nested_color_tolerance=50,
    confidence_threshold=0.5
)