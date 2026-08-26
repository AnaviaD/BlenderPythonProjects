import cv2
import numpy as np

class PatternAnalyzer:
    """
    Clase para analizar patrones en imágenes.
    Actualmente: detección de formas cuadradas/rectangulares.
    """
    
    @staticmethod
    def detect_squares(image, min_area=100, max_area=None, aspect_ratio_tolerance=0.2):
        """
        Detecta formas cuadradas/rectangulares en la imagen.
        
        Args:
            image: Imagen en formato OpenCV (BGR)
            min_area: Área mínima para considerar un cuadrado
            max_area: Área máxima (None = sin límite)
            aspect_ratio_tolerance: Tolerancia para relación de aspecto (1.0 = cuadrado perfecto)
        
        Returns:
            tuple: (imagen_con_dibujos, lista_de_cuadrados)
                - imagen_con_dibujos: Imagen con rectángulos dibujados en verde
                - lista_de_cuadrados: Lista de diccionarios con info de cada cuadrado
        """
        if image is None:
            return None, []
        
        # Hacer una copia para no modificar la original
        img_copy = image.copy()
        gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
        
        # Aplicar desenfoque para reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detección de bordes con Canny
        edges = cv2.Canny(blurred, 50, 150)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_squares = []
        
        for contour in contours:
            # Calcular área
            area = cv2.contourArea(contour)
            if area < min_area:
                continue
            if max_area and area > max_area:
                continue
            
            # Aproximar polígono
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Si tiene 4 vértices, es un candidato a cuadrado/rectángulo
            if len(approx) == 4:
                # Calcular la relación de aspecto (ancho/alto)
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0
                
                # Verificar si es aproximadamente cuadrado (aspect_ratio cercano a 1)
                if abs(aspect_ratio - 1.0) <= aspect_ratio_tolerance:
                    # Dibujar el rectángulo en la imagen
                    cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Guardar información
                    detected_squares.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'centro': (x + w//2, y + h//2)
                    })
        
        return img_copy, detected_squares
    
    @staticmethod
    def analyze_with_color_reference(canvas_image, test_color, color_tolerance=30):
        """
        Analiza la imagen canvas buscando cuadrados que coincidan con el color de test.
        
        Args:
            canvas_image: Imagen canvas (BGR)
            test_color: Color en formato BGR (tupla de 3 enteros)
            color_tolerance: Tolerancia para comparar colores
        
        Returns:
            tuple: (imagen_con_dibujos, lista_de_resultados)
        """
        if canvas_image is None or test_color is None:
            return None, []
        
        # Primero detectar cuadrados
        img_with_squares, squares = PatternAnalyzer.detect_squares(canvas_image)
        
        if not squares:
            return img_with_squares, []
        
        # Filtrar cuadrados por color
        matched_squares = []
        for square in squares:
            x, y, w, h = square['x'], square['y'], square['width'], square['height']
            # Extraer la región del cuadrado
            roi = canvas_image[y:y+h, x:x+w]
            # Calcular color promedio de la región
            avg_color = np.mean(roi, axis=(0, 1))
            avg_color = tuple(int(c) for c in avg_color)
            
            # Comparar con el color de test
            if PatternAnalyzer._colors_match(test_color, avg_color, color_tolerance):
                # Dibujar en otro color (por ejemplo, azul) para resaltar los que coinciden
                cv2.rectangle(img_with_squares, (x, y), (x + w, y + h), (255, 0, 0), 3)
                matched_squares.append({
                    **square,
                    'color_promedio': avg_color,
                    'coincidencia': True
                })
            else:
                # Los que no coinciden los dejamos en verde
                matched_squares.append({
                    **square,
                    'color_promedio': avg_color,
                    'coincidencia': False
                })
        
        return img_with_squares, matched_squares
    
    @staticmethod
    def _colors_match(color1, color2, tolerance):
        """Compara dos colores BGR con tolerancia."""
        if len(color1) != 3 or len(color2) != 3:
            return False
        b1, g1, r1 = color1
        b2, g2, r2 = color2
        diff = abs(b1 - b2) + abs(g1 - g2) + abs(r1 - r2)
        return diff <= tolerance * 3  # Tolerancia por canal