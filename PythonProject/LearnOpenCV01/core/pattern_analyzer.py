import cv2
import numpy as np
from collections import Counter

class PatternAnalyzer:
    """
    Detección en 4 etapas:
    1. Detectar todos los cuadrados candidatos (por forma Y por color).
    2. Eliminar duplicados.
    3. Filtrar por tamaño (los targets son el tamaño más frecuente).
    4. Clasificar color con LAB (primary vs secondary).
    """

    @staticmethod
    def detect_target_squares(image, primary_color, color_list=None,
                              hue_tolerance=30, sat_tolerance=80, val_tolerance=80,
                              min_extent=0.75, min_area=8, size_tolerance=0.15):
        if image is None or primary_color is None:
            return None, []
        if color_list is None:
            color_list = []

        # ============================================================
        # FILTRO 1: Detección por forma (Canny) + por color (HSV)
        # ============================================================
        all_candidates = []

        # Método A: por forma (Canny)
        all_candidates.extend(
            PatternAnalyzer._detect_by_shape(image, min_extent, min_area)
        )

        # Método B: por color (HSV mask) para cada color del catálogo
        all_colors = [primary_color] + color_list
        for color in all_colors:
            all_candidates.extend(
                PatternAnalyzer._detect_by_color(
                    image, color, hue_tolerance, sat_tolerance,
                    val_tolerance, min_extent, min_area
                )
            )

        if not all_candidates:
            return image.copy(), []

        # ============================================================
        # FILTRO 2: Eliminar duplicados
        # ============================================================
        candidates = PatternAnalyzer._deduplicate(all_candidates, threshold=3)

        if not candidates:
            return image.copy(), []

        # ============================================================
        # FILTRO 3: Filtrar por tamaño (los targets son el tamaño más común)
        # ============================================================
        areas = [c['area'] for c in candidates]
        rounded = [round(a / 5) * 5 for a in areas]
        counts = Counter(rounded)
        mode_area = counts.most_common(1)[0][0]

        min_a = mode_area * (1 - size_tolerance)
        max_a = mode_area * (1 + size_tolerance)

        candidates = [c for c in candidates if min_a <= c['area'] <= max_a]

        if not candidates:
            return image.copy(), []

        # ============================================================
        # FILTRO 4: Clasificación de color en LAB
        # ============================================================
        img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        primary_lab = cv2.cvtColor(np.uint8([[primary_color]]), cv2.COLOR_BGR2LAB)[0][0]
        colors_lab = [
            (color, cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2LAB)[0][0])
            for color in color_list
        ]

        final_squares = []
        for c in candidates:
            center_lab = PatternAnalyzer._get_center_color_lab(img_lab, c)
            dist_primary = PatternAnalyzer._color_distance(center_lab, primary_lab)

            best_color = primary_color
            best_dist = dist_primary
            best_type = 'primary'

            for color_bgr, color_lab in colors_lab:
                d = PatternAnalyzer._color_distance(center_lab, color_lab)
                if d < best_dist:
                    best_dist = d
                    best_color = color_bgr
                    best_type = 'secondary'

            c['color'] = best_color
            c['color_type'] = best_type
            c['color_distance'] = float(best_dist)
            c['centro'] = (c['x'] + c['width'] // 2, c['y'] + c['height'] // 2)
            final_squares.append(c)

        # ============================================================
        # DIBUJAR
        # ============================================================
        img_copy = image.copy()
        for sq in final_squares:
            x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']
            color = (0, 255, 0) if sq['color_type'] == 'primary' else (255, 0, 0)
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 1)

        return img_copy, final_squares

    # ================================================================
    # MÉTODOS DE DETECCIÓN
    # ================================================================
    @staticmethod
    def _detect_by_shape(image, min_extent, min_area):
        """Detección por bordes Canny."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 20, 60)
        kernel = np.ones((3, 3), np.uint8)
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return PatternAnalyzer._filter_contours(contours, min_extent, min_area)

    @staticmethod
    def _detect_by_color(image, color_bgr, hue_tol, sat_tol, val_tol, min_extent, min_area):
        """Detección por máscara HSV."""
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        if s < 30:
            lower = np.array([0, max(0, s - sat_tol), max(0, v - val_tol)])
            upper = np.array([179, min(255, s + sat_tol), min(255, v + val_tol)])
        else:
            lower = np.array([max(0, h - hue_tol), max(0, s - sat_tol), max(0, v - val_tol)])
            upper = np.array([min(179, h + hue_tol), min(255, s + sat_tol), min(255, v + val_tol)])

        mask = cv2.inRange(img_hsv, lower, upper)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return PatternAnalyzer._filter_contours(contours, min_extent, min_area)

    # ================================================================
    # FILTROS COMUNES
    # ================================================================
    @staticmethod
    def _filter_contours(contours, min_extent, min_area):
        """Filtra contornos que parecen cuadrados sólidos."""
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

            if len(approx) != 4:
                continue

            x, y, w, h = cv2.boundingRect(approx)
            if w < 3 or h < 3:
                continue

            aspect_ratio = w / h
            if not (0.8 <= aspect_ratio <= 1.2):
                continue

            rect_area = w * h
            extent = area / rect_area if rect_area > 0 else 0
            if extent < min_extent:
                continue

            candidates.append({
                'x': int(x), 'y': int(y),
                'width': int(w), 'height': int(h),
                'area': float(area),
                'aspect_ratio': float(aspect_ratio),
                'extent': float(extent)
            })
        return candidates

    @staticmethod
    def _deduplicate(candidates, threshold=3):
        """Elimina candidatos con el mismo centro."""
        unique = []
        for c in candidates:
            cx = c['x'] + c['width'] // 2
            cy = c['y'] + c['height'] // 2
            duplicate = False
            for u in unique:
                ux = u['x'] + u['width'] // 2
                uy = u['y'] + u['height'] // 2
                if abs(cx - ux) < threshold and abs(cy - uy) < threshold:
                    duplicate = True
                    break
            if not duplicate:
                unique.append(c)
        return unique

    # ================================================================
    # UTILIDADES DE COLOR (LAB)
    # ================================================================
    @staticmethod
    def _get_center_color_lab(img_lab, square, center_ratio=0.5):
        x, y, w, h = square['x'], square['y'], square['width'], square['height']
        cw = max(1, int(w * center_ratio))
        ch = max(1, int(h * center_ratio))
        cx = x + (w - cw) // 2
        cy = y + (h - ch) // 2
        roi = img_lab[cy:cy + ch, cx:cx + cw]
        if roi.size == 0:
            return np.array([0.0, 0.0, 0.0])
        return np.mean(roi, axis=(0, 1))

    @staticmethod
    def _color_distance(lab1, lab2):
        return float(np.linalg.norm(np.array(lab1) - np.array(lab2)))