import cv2
import numpy as np
from collections import Counter

class PatternAnalyzer:
    """Análisis de patrones con detección robusta de cuadrados por color y tamaño."""
    
    @staticmethod
    def detect_target_squares(image, target_color_bgr, area_tolerance=0.15, hue_tolerance=30, sat_tolerance=80, val_tolerance=80):
        """
        Detecta cuadrados que coinciden con el color objetivo y tienen área predominante.
        
        Args:
            image: Imagen en BGR
            target_color_bgr: Color objetivo en BGR (tupla)
            area_tolerance: Tolerancia relativa para el área (0.2 = 20%)
            hue_tolerance: Tolerancia para el canal H (0-180)
            sat_tolerance: Tolerancia para el canal S
            val_tolerance: Tolerancia para el canal V
        
        Returns:
            tuple: (imagen_con_dibujos, lista_diccionarios)
        """
        if image is None or target_color_bgr is None:
            return None, []
        
        # 1. Convertir a HSV
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[target_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h = int(target_hsv[0])
        s = int(target_hsv[1])
        v = int(target_hsv[2])

        # Usar np.clip para acotar los rangos de forma segura
        lower_h = np.clip(h - hue_tolerance, 0, 179)
        lower_s = np.clip(s - sat_tolerance, 0, 255)
        lower_v = np.clip(v - val_tolerance, 0, 255)

        upper_h = np.clip(h + hue_tolerance, 0, 179)
        upper_s = np.clip(s + sat_tolerance, 0, 255)
        upper_v = np.clip(v + val_tolerance, 0, 255)

        lower = np.array([lower_h, lower_s, lower_v])
        upper = np.array([upper_h, upper_s, upper_v])
        mask = cv2.inRange(img_hsv, lower, upper)
        
        # 3. Encontrar contornos en la máscara
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 4. Filtrar por forma (cuadrados) y guardar áreas
        candidate_squares = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 10:  # ignorar ruido
                continue
            
            # Aproximar polígono
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            
            if len(approx) == 4:
                # Obtener rectángulo delimitador
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0
                # Cuadrado si relación entre 0.8 y 1.2 (tolerancia)
                if 0.8 <= aspect_ratio <= 1.2:
                    candidate_squares.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'contour': cnt
                    })
        
        if not candidate_squares:
            return image.copy(), []
        
        # 5. Calcular área predominante (moda)
        areas = [sq['area'] for sq in candidate_squares]
        # Redondear áreas al múltiplo de 5 para agrupar
        rounded_areas = [round(a / 5) * 5 for a in areas]
        area_counts = Counter(rounded_areas)
        most_common_area = area_counts.most_common(1)[0][0]
        
        # Rango de área aceptable
        min_area = most_common_area * (1 - area_tolerance)
        max_area = most_common_area * (1 + area_tolerance)
        
        # 6. Filtrar cuadrados por área y obtener los definitivos
        detected_squares = []
        img_copy = image.copy()
        for sq in candidate_squares:
            if min_area <= sq['area'] <= max_area:
                # Dibujar en verde
                x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']
                cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Añadir información
                detected_squares.append({
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h,
                    'area': sq['area'],
                    'aspect_ratio': sq['aspect_ratio'],
                    'centro': (x + w//2, y + h//2)
                })
                
        if len(detected_squares) > 1:
            # Ordenar por Y y X
            sorted_sq = sorted(detected_squares, key=lambda s: (s['y'], s['x']))
            # Agrupar por fila y calcular gaps
            # ... (similar a la lógica de agrupamiento)
            # Dibujar líneas rojas en los gaps
        
        return img_copy, detected_squares