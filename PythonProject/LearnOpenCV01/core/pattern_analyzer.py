import cv2
import numpy as np
from collections import Counter

class PatternAnalyzer:
    """Análisis de patrones con detección robusta de cuadrados por color y tamaño."""

    @staticmethod
    def detect_target_squares(image, target_color_bgr, area_tolerance=0.15, hue_tolerance=30, sat_tolerance=80, val_tolerance=150):
        """
        Detecta cuadrados que coinciden con el color objetivo y tienen área predominante.
        """
        if image is None or target_color_bgr is None:
            return None, []

        # --- 1. Convertir a HSV ---
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[target_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        # --- 2. Crear máscara (con manejo especial para grises) ---
        if s < 30:  # Target gris: rango completo de H, usar solo S y V
            val_tolerance = 150  # Sobrescribir el valor por defecto
            lower_h, upper_h = 0, 179
            lower_s = np.clip(s - sat_tolerance, 0, 255)
            upper_s = np.clip(s + sat_tolerance, 0, 255)
            lower_v = np.clip(v - val_tolerance, 0, 255)
            upper_v = np.clip(v + val_tolerance, 0, 255)
        else:  # Target con color: usar tolerancias normales
            lower_h = np.clip(h - hue_tolerance, 0, 179)
            upper_h = np.clip(h + hue_tolerance, 0, 179)
            lower_s = np.clip(s - sat_tolerance, 0, 255)
            upper_s = np.clip(s + sat_tolerance, 0, 255)
            lower_v = np.clip(v - val_tolerance, 0, 255)
            upper_v = np.clip(v + val_tolerance, 0, 255)

        lower = np.array([lower_h, lower_s, lower_v])
        upper = np.array([upper_h, upper_s, upper_v])
        mask = cv2.inRange(img_hsv, lower, upper)

        # --- 3. Encontrar contornos en la máscara ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- 4. Filtrar por forma (cuadrados) y guardar áreas ---
        candidate_squares = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 10:  # ignorar ruido
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0
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

        # --- 5. Calcular área predominante (moda) ---
        areas = [sq['area'] for sq in candidate_squares]
        rounded_areas = [round(a / 5) * 5 for a in areas]
        area_counts = Counter(rounded_areas)
        most_common_area = area_counts.most_common(1)[0][0]
        min_area = most_common_area * (1 - area_tolerance)
        max_area = most_common_area * (1 + area_tolerance)

        # --- 6. Filtrar por área ---
        filtered_by_area = []
        for sq in candidate_squares:
            if min_area <= sq['area'] <= max_area:
                filtered_by_area.append(sq)

        # --- 7. Aplicar filtro de color central (NUEVO) ---
        detected_squares = PatternAnalyzer.apply_center_color_filter(
            filtered_by_area,
            target_color_bgr,
            image,  # ← IMAGEN PASADA AQUÍ
            center_ratio=0.5,
            hue_tolerance=15,
            sat_tolerance=40,
            val_tolerance=40
        )

        if s < 30:  # s es la saturación del target
            extra_squares = PatternAnalyzer._detect_gray_squares(image, target_color_bgr)  # ← Pasar target_color_bgr
            detected_squares = PatternAnalyzer._merge_squares(detected_squares, extra_squares)

        if detected_squares:
            areas = [sq['area'] for sq in detected_squares]
            median_area = np.median(areas)
            detected_squares = [sq for sq in detected_squares if sq['area'] < median_area * 2.0]

        # --- 8. Dibujar resultados en la imagen ---
        img_copy = image.copy()
        for sq in detected_squares:
            x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # --- 9. (Opcional) Dibujar líneas de separación entre grupos ---
        if len(detected_squares) > 1:
            sorted_sq = sorted(detected_squares, key=lambda s: (s['y'], s['x']))
            # Puedes agregar lógica para dibujar líneas rojas aquí si lo deseas

        return img_copy, detected_squares

    @staticmethod
    def apply_center_color_filter(candidates, target_color_bgr, image, center_ratio=0.5, hue_tolerance=15, sat_tolerance=40, val_tolerance=40):
        """
        Filtra candidatos verificando que el color en el centro del cuadrado coincida con el objetivo.
        """
        if not candidates or target_color_bgr is None or image is None:
            return []

        # Convertir target a HSV
        target_hsv = cv2.cvtColor(np.uint8([[target_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h_target, s_target, v_target = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        s_target = target_hsv[1]
        if s_target < 30:
            # Para grises, usar tolerancia relativa en V (20% del valor)
            val_tolerance = int(v_target * 0.2) + 20  # al menos 20

        # Convertir imagen a HSV una sola vez
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        filtered = []
        for sq in candidates:
            x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']

            # Calcular región central
            center_w = max(1, int(w * center_ratio))
            center_h = max(1, int(h * center_ratio))
            offset_x = (w - center_w) // 2
            offset_y = (h - center_h) // 2
            cx = x + offset_x
            cy = y + offset_y

            # Extraer región central de la imagen HSV
            roi = img_hsv[cy:cy+center_h, cx:cx+center_w]
            if roi.size == 0:
                continue

            # Calcular promedio de H, S, V en la región central
            h_mean = int(np.mean(roi[:, :, 0]))
            s_mean = int(np.mean(roi[:, :, 1]))
            v_mean = int(np.mean(roi[:, :, 2]))

            # Comparar con el target
            if (abs(h_mean - h_target) <= hue_tolerance and
                abs(s_mean - s_target) <= sat_tolerance and
                abs(v_mean - v_target) <= val_tolerance):
                filtered.append(sq)

        return filtered


    @staticmethod
    def _detect_gray_squares(image, target_color_bgr):
        """
        Detección de grises usando bordes (Canny) para fondos difíciles (blanco/negro).
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Aplicar desenfoque para reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # Detectar bordes
        edges = cv2.Canny(blurred, 30, 100)
        # Cerrar huecos en bordes
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Convertir target a HSV para filtro de color
        target_hsv = cv2.cvtColor(np.uint8([[target_color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h_target, s_target, v_target = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        extra_squares = []
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
                    # Verificar color central (con tolerancia más amplia para grises)
                    center_w = max(1, int(w * 0.5))
                    center_h = max(1, int(h * 0.5))
                    cx = x + (w - center_w) // 2
                    cy = y + (h - center_h) // 2
                    roi = img_hsv[cy:cy+center_h, cx:cx+center_w]
                    if roi.size == 0:
                        continue
                    h_mean = int(np.mean(roi[:, :, 0]))
                    s_mean = int(np.mean(roi[:, :, 1]))
                    v_mean = int(np.mean(roi[:, :, 2]))
                    # Tolerancias amplias para grises
                    if (abs(h_mean - h_target) <= 15 and
                        abs(s_mean - s_target) <= 60 and  # más tolerancia en S
                        abs(v_mean - v_target) <= 80):    # más tolerancia en V
                        extra_squares.append({
                            'x': x, 'y': y, 'width': w, 'height': h,
                            'area': area, 'aspect_ratio': aspect_ratio
                        })
        return extra_squares





    @staticmethod
    def _merge_squares(squares1, squares2, distance_threshold=5):
        """Fusiona dos listas de cuadrados eliminando duplicados por proximidad."""
        merged = list(squares1)
        for sq2 in squares2:
            duplicate = False
            cx2, cy2 = sq2['x'] + sq2['width']//2, sq2['y'] + sq2['height']//2
            for sq1 in squares1:
                cx1, cy1 = sq1['x'] + sq1['width']//2, sq1['y'] + sq1['height']//2
                if abs(cx2 - cx1) < distance_threshold and abs(cy2 - cy1) < distance_threshold:
                    duplicate = True
                    break
            if not duplicate:
                merged.append(sq2)
        return merged