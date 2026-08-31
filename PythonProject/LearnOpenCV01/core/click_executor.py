import pyautogui
import time
import random
import keyboard as keyboard
import threading
import numpy as np

class ClickExecutor:
    @staticmethod
    def execute_clicks(coordinates, min_delay_ms=15, max_delay_ms=200, 
                   click_centers=True, randomize_order=False, 
                   click_count=1, mode='click', avg_height=30):
        """
        Ejecuta clics o arrastres en las coordenadas.
        
        Args:
            mode: 'click' para clics individuales, 'drag' para arrastre con espacio
        """
        # Convertir a lista de puntos (x, y)
        points = []
        for coord in coordinates:
            if isinstance(coord, dict):
                if click_centers and 'width' in coord and 'height' in coord:
                    x = coord['x'] + coord['width'] // 2
                    y = coord['y'] + coord['height'] // 2
                elif 'centro' in coord:
                    x, y = coord['centro']
                else:
                    x, y = coord.get('x', 0), coord.get('y', 0)
            else:
                x, y = coord
            points.append((x, y))
        
        if randomize_order:
            random.shuffle(points)
        
        if mode == 'drag':
            ClickExecutor._execute_drag_mode(points, min_delay_ms, max_delay_ms)
        else:
            ClickExecutor._execute_click_mode(points, min_delay_ms, max_delay_ms, click_count)
    
    @staticmethod
    def _execute_click_mode(points, min_delay_ms, max_delay_ms, click_count):
        """Modo clics individuales (funcionalidad existente)."""
        stop_execution = False
        def check_escape():
            nonlocal stop_execution
            keyboard.wait('esc')
            stop_execution = True
            print("\n⏹️ Ejecución interrumpida por Escape")
        
        escape_thread = threading.Thread(target=check_escape, daemon=True)
        escape_thread.start()
        
        try:
            for idx, (x, y) in enumerate(points):
                if stop_execution:
                    break
                pyautogui.moveTo(x, y, duration=0.1)
                for _ in range(click_count):
                    if stop_execution:
                        break
                    pyautogui.click()
                    time.sleep(0.05)
                if idx < len(points) - 1 and not stop_execution:
                    delay = random.randint(min_delay_ms, max_delay_ms) / 100000.0
                    time.sleep(delay)
        except KeyboardInterrupt:
            print("\n⏹️ Interrumpido")

    @staticmethod
    def _execute_drag_mode(points, min_delay_ms, max_delay_ms, avg_height=30):
        if not points:
            return
        
        # --- 1. Ordenar todos los puntos por Y (fila) y X (columna) ---
        sorted_points = sorted(points, key=lambda p: (p[1], p[0]))
        
        # --- 2. Agrupar por filas usando un umbral vertical fijo basado en avg_height ---
        vertical_threshold = avg_height * 0.5  # Factor ajustable (0.5 = mitad de la altura)
        vertical_threshold = max(vertical_threshold, 10)  # mínimo 10 px
        
        rows = []
        current_row = [sorted_points[0]]
        for p in sorted_points[1:]:
            if abs(p[1] - current_row[-1][1]) < vertical_threshold:
                current_row.append(p)
            else:
                rows.append(current_row)
                current_row = [p]
        rows.append(current_row)
        
        # --- 3. Para cada fila, agrupar horizontalmente ---
        # Calcular umbral horizontal dinámico (basado en distancias entre puntos consecutivos)
        all_h_dists = []
        for row in rows:
            row.sort(key=lambda p: p[0])  # ordenar por X
            for i in range(len(row) - 1):
                dist = row[i+1][0] - row[i][0]
                if dist > 2:
                    all_h_dists.append(dist)
        
        if all_h_dists:
            # Ordenar distancias y tomar el percentil 75 (para ignorar gaps grandes)
            sorted_dists = sorted(all_h_dists)
            # Tomar el valor en el percentil 75 (3/4 de los datos)
            percentile_75 = sorted_dists[int(len(sorted_dists) * 0.75)]
            median_h_gap = sorted_dists[len(sorted_dists) // 2]  # mediana
            # Usar el menor entre la mediana y el percentil 75 (para ser conservador)
            typical_gap = min(median_h_gap, percentile_75)
            # Umbral = typical_gap * 1.2 (factor más pequeño)
            horizontal_threshold = min(typical_gap * 1.2, max(typical_gap + 15, 35))
        else:
            horizontal_threshold = 30
        
        gap_factor = 1.2
        max_threshold = 80
        horizontal_threshold = min(median_h_gap * gap_factor, max_threshold)
        horizontal_threshold = max(horizontal_threshold, 15)
        
        # --- 4. Formar grupos horizontales dentro de cada fila ---
        groups = []
        for row in rows:
            row.sort(key=lambda p: p[0])  # asegurar orden de izquierda a derecha
            current_group = [row[0]]
            for p in row[1:]:
                if p[0] - current_group[-1][0] < horizontal_threshold:
                    current_group.append(p)
                else:
                    groups.append(current_group)
                    current_group = [p]
            if current_group:
                groups.append(current_group)
        
        # --- 5. Reordenar grupos para que el recorrido sea por filas (Y) y luego por X ---
        # groups ya está en orden de fila superior a inferior (porque rows está ordenado por Y),
        # pero si hay alguna inconsistencia, forzamos el orden.
        groups.sort(key=lambda g: (g[0][1], g[0][0]))  # Y primero, luego X
        
        # --- 6. Ejecutar arrastre ---
        try:
            for group_idx, group in enumerate(groups):
                if keyboard.is_pressed('esc'):
                    print("\n⏹️ Interrumpido por Escape")
                    break
                
                if len(group) == 1:
                    x, y = group[0]
                    pyautogui.moveTo(x, y, duration=0.1)
                    pyautogui.click()
                    print(f"🖱️ Click en ({x}, {y})")
                else:
                    x0, y0 = group[0]
                    pyautogui.moveTo(x0, y0, duration=0.1)
                    print(f"📌 Grupo de {len(group)} puntos comenzando en ({x0}, {y0})")
                    
                    # Forzar liberación de espacio antes de iniciar el grupo
                    keyboard.release('space')
                    time.sleep(0.005)
                    
                    pyautogui.click()
                    time.sleep(0.005)
                    
                    keyboard.press('space')
                    time.sleep(0.001)
                    
                    for x, y in group[1:]:
                        if keyboard.is_pressed('esc'):
                            break
                        pyautogui.moveTo(x, y, duration=0.005)
                        time.sleep(0.02)
                        print(f"  → Movido a ({x}, {y})")
                    
                    keyboard.release('space')
                    time.sleep(0.1)
                    print(f"✅ Grupo {group_idx+1} completado")
                
                # Retraso entre grupos
                if group_idx < len(groups) - 1 and not keyboard.is_pressed('esc'):
                    delay = random.randint(min_delay_ms, max_delay_ms) / 100000.0
                    print(f"⏳ Esperando {delay:.2f}s antes del siguiente grupo")
                    time.sleep(delay)
            
            print(f"✅ Ejecutados {len(groups)} grupos")
        except KeyboardInterrupt:
            print("\n⏹️ Interrumpido")
            keyboard.release('space')
        except Exception as e:
            print(f"❌ Error: {e}")
            keyboard.release('space')
            raise

    @staticmethod
    def execute_from_squares(squares, min_delay_ms=15, max_delay_ms=200, 
                        click_centers=True, randomize_order=False, 
                        click_count=1, mode='click', avg_height=30):
        """Versión simplificada para usar con lista de cuadrados."""
        ClickExecutor.execute_clicks(
            squares, min_delay_ms, max_delay_ms,
            click_centers, randomize_order, click_count, mode, avg_height
        )