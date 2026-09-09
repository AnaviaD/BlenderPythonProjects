import cv2
import numpy as np
from collections import Counter

class PatternAnalyzer:
    @staticmethod
    def detect_target_squares(image, primary_color, color_list=None, area_tolerance=0.15, hue_tolerance=30, sat_tolerance=80, val_tolerance=80):
        """
        Detecta cuadrados que coinciden con el color primario o con la lista de colores.
        Prioriza el color primario.
        
        Args:
            image: Imagen en BGR
            primary_color: Color primario en BGR
            color_list: Lista de colores adicionales en BGR (cada uno es una tupla)
            area_tolerance: Tolerancia para el área
            hue_tolerance: Tolerancia H
            sat_tolerance: Tolerancia S
            val_tolerance: Tolerancia V
        
        Returns:
            tuple: (imagen_con_dibujos, lista_diccionarios)
        """
        if image is None or primary_color is None:
            return None, []
        
        if color_list is None:
            color_list = []
        
        # 1. Recolectar candidatos de todos los colores
        all_candidates = []
        colors_to_analyze = [primary_color] + color_list
        # El primario debe ser el primero para priorizarlo después
        for color in colors_to_analyze:
            candidates = PatternAnalyzer._detect_candidates_for_color(image, color, hue_tolerance, sat_tolerance, val_tolerance)
            # Añadir información del color a cada candidato
            for c in candidates:
                c['color'] = color
            all_candidates.extend(candidates)
        
        if not all_candidates:
            return image.copy(), []
        
        # 2. Calcular área predominante global (moda)
        areas = [c['area'] for c in all_candidates]
        rounded_areas = [round(a / 5) * 5 for a in areas]
        area_counts = Counter(rounded_areas)
        most_common_area = area_counts.most_common(1)[0][0]
        min_area = most_common_area * (1 - area_tolerance)
        max_area = most_common_area * (1 + area_tolerance)
        
        # 3. Filtrar por área y eliminar duplicados
        candidates_filtered = []
        # Primero, los del color primario
        primary_candidates = [c for c in all_candidates if np.array_equal(c['color'], primary_color) and min_area <= c['area'] <= max_area]
        # Luego, los demás colores (que no estén ya cubiertos por el primario)
        other_candidates = [c for c in all_candidates if not np.array_equal(c['color'], primary_color) and min_area <= c['area'] <= max_area]
        
        # Fusionar: para cada cuadrado, si hay uno del primario en la misma posición, nos quedamos con ese
        # Usamos un umbral de distancia para considerar la misma posición (5 píxeles)
        final_squares = []
        used_positions = set()
        
        # Primero agregar primarios
        for c in primary_candidates:
            center = (c['x'] + c['width']//2, c['y'] + c['height']//2)
            # Verificar si ya hay un cuadrado en esa posición (de otro primario o de otros)
            # Como los primarios son únicos, no debería haber duplicados entre ellos, pero por si acaso
            duplicate = False
            for used in used_positions:
                if abs(center[0] - used[0]) < 5 and abs(center[1] - used[1]) < 5:
                    duplicate = True
                    break
            if not duplicate:
                final_squares.append({
                    'x': c['x'],
                    'y': c['y'],
                    'width': c['width'],
                    'height': c['height'],
                    'area': c['area'],
                    'aspect_ratio': c['aspect_ratio'],
                    'centro': center,
                    'color': c['color'],  # Guardamos el color original
                    'color_type': 'primary'
                })
                used_positions.add(center)
        
        # Luego agregar otros colores (solo si no están en la misma posición que un primario)
        for c in other_candidates:
            center = (c['x'] + c['width']//2, c['y'] + c['height']//2)
            duplicate = False
            for used in used_positions:
                if abs(center[0] - used[0]) < 5 and abs(center[1] - used[1]) < 5:
                    duplicate = True
                    break
            if not duplicate:
                final_squares.append({
                    'x': c['x'],
                    'y': c['y'],
                    'width': c['width'],
                    'height': c['height'],
                    'area': c['area'],
                    'aspect_ratio': c['aspect_ratio'],
                    'centro': center,
                    'color': c['color'],
                    'color_type': 'secondary'
                })
                used_positions.add(center)
        
        # 4. Dibujar en la imagen
        img_copy = image.copy()
        for sq in final_squares:
            x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']
            if sq['color_type'] == 'primary':
                color = (0, 255, 0)  # Verde
            else:
                color = (255, 0, 0)  # Azul
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 2)
        
        return img_copy, final_squares

    @staticmethod
    def _detect_candidates_for_color(image, color_bgr, hue_tolerance, sat_tolerance, val_tolerance):
        """
        Detecta candidatos a cuadrados para un color específico (sin filtrar por área).
        Devuelve lista de diccionarios con x, y, width, height, area, aspect_ratio.
        """
        # Convertir a HSV
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])
        
        # Crear máscara (con manejo especial para grises)
        if s < 30:
            lower_h, upper_h = 0, 179
            lower_s = np.clip(s - sat_tolerance, 0, 255)
            upper_s = np.clip(s + sat_tolerance, 0, 255)
            lower_v = np.clip(v - val_tolerance, 0, 255)
            upper_v = np.clip(v + val_tolerance, 0, 255)
        else:
            lower_h = np.clip(h - hue_tolerance, 0, 179)
            upper_h = np.clip(h + hue_tolerance, 0, 179)
            lower_s = np.clip(s - sat_tolerance, 0, 255)
            upper_s = np.clip(s + sat_tolerance, 0, 255)
            lower_v = np.clip(v - val_tolerance, 0, 255)
            upper_v = np.clip(v + val_tolerance, 0, 255)
        
        lower = np.array([lower_h, lower_s, lower_v])
        upper = np.array([upper_h, upper_s, upper_v])
        mask = cv2.inRange(img_hsv, lower, upper)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 10:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0
                if 0.8 <= aspect_ratio <= 1.2:
                    candidates.append({
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'area': area,
                        'aspect_ratio': aspect_ratio,
                        'contour': cnt
                    })
        return candidates