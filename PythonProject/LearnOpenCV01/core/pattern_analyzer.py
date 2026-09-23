import cv2
import numpy as np
import os
from datetime import datetime


class PatternAnalyzer:

    DIAGNOSTIC_FOLDER = r"C:\Users\Alberto\Pictures\wplace\Program"
    
    @staticmethod
    def detect_target_squares(image, primary_color, color_list=None,
                            hue_tolerance=30, sat_tolerance=80, val_tolerance=80,
                            min_extent=0.75, min_area=8,
                            area_tolerance_upper=0.20,   # ← nuevo
                            area_tolerance_lower=0.25,   # ← nuevo
                            dim_tolerance=0.12,          # ← nuevo
                            grid_pos_tolerance=2,
                            diagnostic=False):
        """
        Pipeline combinado con diagnóstico opcional.
        Si diagnostic=True, guarda imágenes intermedias en DIAGNOSTIC_FOLDER.
        """
        if image is None or primary_color is None:
            return None, []

        if color_list is None:
            color_list = []

        # --- Preparar carpeta de diagnóstico ---
        diag_dir = None
        if diagnostic:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            diag_dir = os.path.join(PatternAnalyzer.DIAGNOSTIC_FOLDER, timestamp)
            os.makedirs(diag_dir, exist_ok=True)
            print(f"\n🔍 Diagnóstico activo. Guardando en: {diag_dir}")

            cv2.imwrite(os.path.join(diag_dir, "01_original.png"), image)

        # ============================================================
        # FASE 1: Multi-pasada por color
        # ============================================================
        all_colors = [primary_color] + color_list
        pass_configs = [
            (8,  25, 25, 'pass1', 0),
            (15, 50, 50, 'pass2', 1),
            (25, 75, 75, 'pass3', 2),
        ]

        all_candidates = []
        # Para diagnóstico: guardar máscaras combinadas por pasada
        masks_by_pass = {0: None, 1: None, 2: None, 'acrom': None}

        for color in all_colors:
            # Determinar si el color es acromático
            target_hsv_temp = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
            s_target = int(target_hsv_temp[1])

            if s_target < 40:
                # ← ACROMÁTICO: usar filtro A (V-only)
                mask, cands = PatternAnalyzer._detect_achromatic(
                    image, color, min_extent, min_area
                )
                if mask is not None:
                    if diagnostic:
                        # Guardar máscara acumulada para acromáticos
                        if masks_by_pass.get('acrom') is None:
                            masks_by_pass['acrom'] = mask.copy()
                        else:
                            masks_by_pass['acrom'] = cv2.bitwise_or(
                                masks_by_pass['acrom'], mask
                            )
                    for c in cands:
                        c['color'] = tuple(color)
                        c['source'] = 'achromatic'
                        c['priority'] = 0   # misma prioridad que pass1
                    all_candidates.extend(cands)
            else:
                # ← SATURADO: usar HSV multi-pasada (como antes)
                for (h_tol, s_tol, v_tol, source, priority) in pass_configs:
                    mask, cands = PatternAnalyzer._detect_by_color_with_mask(
                        image, color, h_tol, s_tol, v_tol, min_extent, min_area
                    )
                    if diagnostic:
                        if masks_by_pass[priority] is None:
                            masks_by_pass[priority] = mask.copy()
                        else:
                            masks_by_pass[priority] = cv2.bitwise_or(
                                masks_by_pass[priority], mask
                            )
                    for c in cands:
                        c['color'] = tuple(color)
                        c['source'] = source
                        c['priority'] = priority
                    all_candidates.extend(cands)

        # Guardar máscaras combinadas por pasada
        if diagnostic:
            for p, mask in masks_by_pass.items():
                if mask is not None:
                    name = f"02_mask_{p}_all_colors.png" if isinstance(p, str) else f"02_mask_pass{p+1}_all_colors.png"
                    cv2.imwrite(os.path.join(diag_dir, name), mask)

        # Guardar imagen con candidatos por fuente ANTES de deduplicar
        if diagnostic:
            img_sources = image.copy()
            for c in all_candidates:
                color_rect = {
                    'pass1': (0, 255, 0),        # verde
                    'pass2': (0, 255, 255),      # amarillo
                    'pass3': (0, 165, 255),      # naranja
                    'achromatic': (255, 0, 0),   # azul
                }.get(c['source'], (255, 0, 255))
                cv2.rectangle(img_sources,
                              (c['x'], c['y']),
                              (c['x'] + c['width'], c['y'] + c['height']),
                              color_rect, 1)
            cv2.imwrite(os.path.join(diag_dir, "03_candidates_by_source.png"), img_sources)

        if not all_candidates:
            if diagnostic:
                PatternAnalyzer._write_stats(diag_dir, {
                    'total_candidates_raw': 0,
                    'after_dedup': 0,
                    'after_grid': 0,
                    'after_area_filter': 0,
                    'final': 0,
                })
            return image.copy(), []

        # ============================================================
        # FASE 2: Deduplicación con prioridad
        # ============================================================
        deduped = PatternAnalyzer._deduplicate_with_priority(all_candidates, threshold=3)

        # ============================================================
        # FASE 3: Grid completion
        # ============================================================
        completed = PatternAnalyzer._grid_completion(image, deduped, grid_pos_tolerance)

        if diagnostic:
            img_grid = image.copy()
            for c in completed:
                if c.get('source') == 'grid':
                    color_rect = (255, 0, 255)  # magenta
                else:
                    color_rect = (0, 255, 0)
                cv2.rectangle(img_grid,
                              (c['x'], c['y']),
                              (c['x'] + c['width'], c['y'] + c['height']),
                              color_rect, 1)
            cv2.imwrite(os.path.join(diag_dir, "04_after_grid_completion.png"), img_grid)

        # ============================================================
        # FASE 4: Filtro de área estricto
        # ============================================================
        area_before = len(completed)

        if len(completed) > 3:
            # --- Filtro D: dimensiones W y H ---
            widths = [c['width'] for c in completed]
            heights = [c['height'] for c in completed]
            median_w = float(np.median(widths))
            median_h = float(np.median(heights))

            tol_w = max(median_w * dim_tolerance, 2)
            tol_h = max(median_h * dim_tolerance, 2)

            after_dim = [c for c in completed
                        if abs(c['width'] - median_w) <= tol_w
                        and abs(c['height'] - median_h) <= tol_h]

            if diagnostic:
                print(f"\n📏 Filtro D (dimensiones):")
                print(f"   mediana W: {median_w:.1f}, tolerancia: ±{tol_w:.1f}")
                print(f"   mediana H: {median_h:.1f}, tolerancia: ±{tol_h:.1f}")
                print(f"   antes: {len(completed)}, después: {len(after_dim)}")

            completed = after_dim

            # --- Filtro B: área asimétrica ---
            if len(completed) > 3:
                areas = [c['area'] for c in completed]
                median_area = float(np.median(areas))
                min_a = median_area * (1 - area_tolerance_lower)
                max_a = median_area * (1 + area_tolerance_upper)

                after_area = [c for c in completed if min_a <= c['area'] <= max_a]

                if diagnostic:
                    print(f"\n📐 Filtro B (área asimétrica):")
                    print(f"   mediana área: {median_area:.1f}")
                    print(f"   rango: [{min_a:.1f}, {max_a:.1f}]")
                    print(f"   antes: {len(completed)}, después: {len(after_area)}")

                completed = after_area

        # ============================================================
        # FASE 5: Clasificación de color en LAB
        # ============================================================
        img_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        primary_lab = cv2.cvtColor(np.uint8([[primary_color]]), cv2.COLOR_BGR2LAB)[0][0]
        colors_lab = [
            (color, cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2LAB)[0][0])
            for color in color_list
        ]

        for c in completed:
            center_lab = PatternAnalyzer._get_center_color_lab(img_lab, c)
            dist_primary = PatternAnalyzer._color_distance(center_lab, primary_lab)

            best_color = tuple(primary_color)
            best_dist = dist_primary
            best_type = 'primary'

            for color_bgr, color_lab in colors_lab:
                d = PatternAnalyzer._color_distance(center_lab, color_lab)
                if d < best_dist:
                    best_dist = d
                    best_color = tuple(color_bgr)
                    best_type = 'secondary'

            c['color'] = best_color
            c['color_type'] = best_type
            c['color_distance'] = float(best_dist)
            c['centro'] = (c['x'] + c['width'] // 2, c['y'] + c['height'] // 2)

        # ============================================================
        # FASE 6: Deduplicación final + ordenamiento
        # ============================================================
        final_squares = PatternAnalyzer._deduplicate_final(completed, threshold=3)
        final_squares.sort(key=lambda c: (c['y'], c['x']))

        # ============================================================
        # DIBUJAR Y GUARDAR
        # ============================================================
        img_copy = image.copy()
        for sq in final_squares:
            x, y, w, h = sq['x'], sq['y'], sq['width'], sq['height']
            color = (0, 255, 0) if sq['color_type'] == 'primary' else (255, 0, 0)
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), color, 1)

        if diagnostic:
            cv2.imwrite(os.path.join(diag_dir, "06_final_result.png"), img_copy)

            # Estadísticas por pasada
            stats = {
                'total_candidates_raw': len(all_candidates),
                'after_dedup': len(deduped),
                'after_grid': area_before,
                'after_area_filter': len(completed),
                'final': len(final_squares),
                'by_source': {
                    'pass1': sum(1 for c in all_candidates if c.get('source') == 'pass1'),
                    'pass2': sum(1 for c in all_candidates if c.get('source') == 'pass2'),
                    'pass3': sum(1 for c in all_candidates if c.get('source') == 'pass3'),
                    'achromatic': sum(1 for c in all_candidates if c.get('source') == 'achromatic'),
                    'grid': sum(1 for c in final_squares if c.get('source') == 'grid'),
                },
                'by_color_type': {
                    'primary': sum(1 for c in final_squares if c['color_type'] == 'primary'),
                    'secondary': sum(1 for c in final_squares if c['color_type'] == 'secondary'),
                }
            }
            PatternAnalyzer._write_stats(diag_dir, stats)
            print(f"✅ Diagnóstico guardado. Total detectado: {len(final_squares)}")
            print(f"   pass1: {stats['by_source']['pass1']} | "
                  f"pass2: {stats['by_source']['pass2']} | "
                  f"pass3: {stats['by_source']['pass3']} | "
                  f"grid: {stats['by_source']['grid']}")

        return img_copy, final_squares



    
    # ================================================================
    # DETECCIÓN POR COLOR (devuelve también la máscara)
    # ================================================================
    @staticmethod
    def _detect_by_color_with_mask(image, color_bgr, hue_tol, sat_tol, val_tol,
                                    min_extent, min_area):
        """Igual que _detect_by_color pero devuelve la máscara."""
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
        candidates = PatternAnalyzer._filter_contours(contours, min_extent, min_area)
        return mask, candidates



    # ================================================================
    # GUARDAR ESTADÍSTICAS
    # ================================================================
    @staticmethod
    def _write_stats(diag_dir, stats):
        path = os.path.join(diag_dir, "stats.txt")
        with open(path, 'w', encoding='utf-8') as f:
            for key, value in stats.items():
                if isinstance(value, dict):
                    f.write(f"{key}:\n")
                    for k2, v2 in value.items():
                        f.write(f"  {k2}: {v2}\n")
                else:
                    f.write(f"{key}: {value}\n")


    # ================================================================
    # DETECCIÓN POR COLOR (una pasada)
    # ================================================================
    @staticmethod
    def _detect_by_color(image, color_bgr, hue_tol, sat_tol, val_tol, min_extent, min_area):
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        target_hsv = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(target_hsv[0]), int(target_hsv[1]), int(target_hsv[2])

        if s < 30:  # gris: usar rango completo de H
            lower = np.array([0, max(0, s - sat_tol), max(0, v - val_tol)])
            upper = np.array([179, min(255, s + sat_tol), min(255, v + val_tol)])
        else:
            lower = np.array([max(0, h - hue_tol), max(0, s - sat_tol), max(0, v - val_tol)])
            upper = np.array([min(179, h + hue_tol), min(255, s + sat_tol), min(255, v + val_tol)])

        mask = cv2.inRange(img_hsv, lower, upper)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return PatternAnalyzer._filter_contours(contours, min_extent, min_area, min_solidity=0.85)

    # ================================================================
    # FILTRO DE CONTORNOS → CANDIDATOS
    # ================================================================
    @staticmethod
    def _filter_contours(contours, min_extent, min_area, min_solidity=0.85):
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

            # ← NUEVO: calcular solidez (área / área del casco convexo)
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area <= 0:
                continue
            solidity = area / hull_area
            if solidity < min_solidity:
                continue

            candidates.append({
                'x': int(x), 'y': int(y),
                'width': int(w), 'height': int(h),
                'area': float(area),
                'aspect_ratio': float(aspect_ratio),
                'extent': float(extent),
            })
        return candidates

    # ================================================================
    # DEDUPLICACIÓN CON PRIORIDAD (pass1 > pass2 > pass3 > grid)
    # ================================================================
    @staticmethod
    def _deduplicate_with_priority(candidates, threshold=3):
        # Ordenar por prioridad (menor = mejor)
        sorted_c = sorted(candidates, key=lambda c: (c['priority'], c['area'] * -1))
        unique = []
        for c in sorted_c:
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

    @staticmethod
    def _deduplicate_final(candidates, threshold=3):
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
    # GRID COMPLETION
    # ================================================================
    @staticmethod
    def _grid_completion(image, candidates, pos_tolerance=2):
        """
        Rellena huecos aprovechando la regularidad de la cuadrícula.
        Trabaja por filas y por runs horizontales dentro de cada fila.
        """
        if len(candidates) < 3:
            return candidates

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        sorted_c = sorted(candidates, key=lambda c: (c['y'], c['x']))

        # Altura mediana → umbral para agrupar por fila
        heights = [c['height'] for c in sorted_c]
        median_h = float(np.median(heights))
        row_threshold = max(median_h * 0.5, 3)

        # Agrupar por filas
        rows = []
        current_row = [sorted_c[0]]
        for c in sorted_c[1:]:
            prev = current_row[-1]
            if abs(c['y'] - prev['y']) <= row_threshold:
                current_row.append(c)
            else:
                rows.append(current_row)
                current_row = [c]
        rows.append(current_row)

        new_candidates = list(candidates)

        # Ancho mediano (para verificar posición)
        widths = [c['width'] for c in sorted_c]
        median_w = int(np.median(widths))

        for row in rows:
            row.sort(key=lambda c: c['x'])
            if len(row) < 2:
                continue

            # Calcular gaps dentro de la fila
            gaps = [row[i + 1]['x'] - row[i]['x'] for i in range(len(row) - 1)]
            gaps = [g for g in gaps if g > 3]
            if not gaps:
                continue

            median_gap = float(np.median(gaps))
            run_threshold = median_gap * 1.5

            # Detectar runs
            runs = []
            current_run = [row[0]]
            for i in range(1, len(row)):
                gap = row[i]['x'] - current_run[-1]['x']
                if gap <= run_threshold:
                    current_run.append(row[i])
                else:
                    runs.append(current_run)
                    current_run = [row[i]]
            runs.append(current_run)

            # Extender cada run
            for run in runs:
                if len(run) < 2:
                    continue

                run_gaps = [run[i + 1]['x'] - run[i]['x'] for i in range(len(run) - 1)]
                run_gaps = [g for g in run_gaps if g > 3]
                if not run_gaps:
                    continue

                dX = int(np.median(run_gaps))
                if dX < 3:
                    continue

                y_med = int(np.median([c['y'] for c in run]))
                h_med = int(np.median([c['height'] for c in run]))

                # Extender a la derecha
                last_x = run[-1]['x']
                next_x = last_x + dX
                for _ in range(200):  # límite para evitar loops
                    if PatternAnalyzer._target_exists_at(
                            gray, next_x, y_med, median_w, median_h, pos_tolerance):
                        new_c = PatternAnalyzer._make_grid_candidate(
                            next_x, y_med, median_w, median_h, run[0]['color'])
                        new_candidates.append(new_c)
                        next_x += dX
                    else:
                        break

                # Extender a la izquierda
                first_x = run[0]['x']
                prev_x = first_x - dX
                for _ in range(200):
                    if prev_x < 0:
                        break
                    if PatternAnalyzer._target_exists_at(
                            gray, prev_x, y_med, median_w, median_h, pos_tolerance):
                        new_c = PatternAnalyzer._make_grid_candidate(
                            prev_x, y_med, median_w, median_h, run[0]['color'])
                        new_candidates.append(new_c)
                        prev_x -= dX
                    else:
                        break

        return new_candidates

    @staticmethod
    def _make_grid_candidate(x, y, w, h, color):
        return {
            'x': int(x), 'y': int(y),
            'width': int(w), 'height': int(h),
            'area': float(w * h),
            'aspect_ratio': 1.0,
            'extent': 0.95,
            'color': color,
            'source': 'grid',
            'priority': 3,
        }

    @staticmethod
    def _detect_achromatic(image, color_bgr, min_extent, min_area):
        """
        Detecta targets acromáticos (blancos, negros, grises).
        Usa V-only con tolerancias adaptativas al brillo del target.
        
        Retorna (mask, candidates) o (None, []) si el color no es acromático.
        """
        target_hsv = cv2.cvtColor(np.uint8([[color_bgr]]), cv2.COLOR_BGR2HSV)[0][0]
        s_target = int(target_hsv[1])
        v_target = int(target_hsv[2])

        # Solo para targets acromáticos
        if s_target >= 40:
            return None, []

        # Tolerancias adaptativas según brillo
        if v_target > 220:      # blanco
            v_tol = 20
        elif v_target < 30:     # negro
            v_tol = 20
        else:                   # gris
            v_tol = 30

        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        s_channel = img_hsv[:, :, 1]
        v_channel = img_hsv[:, :, 2]

        # Máscara: S bajo Y V en rango
        v_min = max(0, v_target - v_tol)
        v_max = min(255, v_target + v_tol)

        mask_s = cv2.inRange(s_channel, 0, 40)
        mask_v = cv2.inRange(v_channel, v_min, v_max)
        mask = cv2.bitwise_and(mask_s, mask_v)

        # Morfología
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = PatternAnalyzer._filter_contours(contours, min_extent, min_area)
        return mask, candidates





    @staticmethod
    def _target_exists_at(gray, x, y, w, h, pos_tolerance=2):
        # ← Convertir a int para asegurar slices válidas
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        pos_tolerance = int(pos_tolerance)
        
        margin = max(3, int(min(w, h) * 0.2))
        x0 = max(0, x - margin)
        y0 = max(0, y - margin)
        x1 = min(gray.shape[1], x + w + margin)
        y1 = min(gray.shape[0], y + h + margin)
        
        if x1 - x0 < 5 or y1 - y0 < 5:
            return False
        
        patch = gray[y0:y1, x0:x1]

        # Canny con umbrales bajos
        edges = cv2.Canny(patch, 30, 80)
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 4:
                continue
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) != 4:
                continue
            bx, by, bw, bh = cv2.boundingRect(approx)
            aspect = bw / bh if bh > 0 else 0
            if not (0.75 <= aspect <= 1.25):
                continue
            rect_area = bw * bh
            extent = area / rect_area if rect_area > 0 else 0
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area <= 0:
                continue
            solidity = area / hull_area
            if solidity < 0.85:
                continue
            if extent < 0.7:
                continue
            # Verificar que esté centrado cerca de la posición esperada
            # (el centro del contorno encontrado, trasladado al sistema global)
            cnt_cx = bx + bw // 2 + x0
            cnt_cy = by + bh // 2 + y0
            expected_cx = x + w // 2
            expected_cy = y + h // 2
            if (abs(cnt_cx - expected_cx) <= pos_tolerance + 2 and
                    abs(cnt_cy - expected_cy) <= pos_tolerance + 2):
                return True

        return False

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