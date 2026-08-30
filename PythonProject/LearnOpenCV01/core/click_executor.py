import pyautogui
import time
import random
import keyboard as keyboard
import threading

class ClickExecutor:
    @staticmethod
    def execute_clicks(coordinates, min_delay_ms=15, max_delay_ms=200, 
                       click_centers=True, randomize_order=False, 
                       click_count=1, mode='click'):
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
                    delay = random.randint(min_delay_ms, max_delay_ms) / 10000000.0
                    time.sleep(delay)
        except KeyboardInterrupt:
            print("\n⏹️ Interrumpido")

    @staticmethod
    def _execute_drag_mode(points, min_delay_ms, max_delay_ms):
        if not points:
            return
        
        # Ordenar puntos por fila (Y) y columna (X)
        sorted_points = sorted(points, key=lambda p: (p[1], p[0]))
        
        # --- 1. Agrupar por filas ---
        rows = []
        current_row = [sorted_points[0]]
        for p in sorted_points[1:]:
            # Si la diferencia en Y es menor que 15 píxeles (ajustable), misma fila
            if abs(p[1] - current_row[-1][1]) < 15:
                current_row.append(p)
            else:
                rows.append(current_row)
                current_row = [p]
        rows.append(current_row)
        
        # --- 2. Calcular umbral dinámico ---
        distances = []
        for row in rows:
            row.sort(key=lambda p: p[0])  # ordenar por X
            for i in range(len(row) - 1):
                dist = row[i+1][0] - row[i][0]
                if dist > 5:  # ignorar distancias muy pequeñas (ruido)
                    distances.append(dist)
        
        if distances:
            median_gap = sorted(distances)[len(distances) // 2]
        else:
            median_gap = 30  # valor por defecto
        
        gap_factor = 1.5  # Ajustable: 1.5 para gaps pequeños, 2.5 para gaps grandes
        threshold = median_gap * gap_factor
        print(f"📊 Distancias: {distances}")
        print(f"📊 Mediana: {median_gap:.1f}px, Umbral: {threshold:.1f}px")
        
        # --- 3. Agrupar por proximidad horizontal ---
        groups = []
        for row in rows:
            row.sort(key=lambda p: p[0])
            current_group = [row[0]]
            for p in row[1:]:
                if p[0] - current_group[-1][0] < threshold:
                    current_group.append(p)
                else:
                    groups.append(current_group)
                    current_group = [p]
            if current_group:
                groups.append(current_group)
        
        # --- 4. Ejecutar arrastre ---
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
                    
                    # Forzar liberación de espacio
                    keyboard.release('space')
                    time.sleep(0.02)
                    
                    # Clic para dar foco
                    pyautogui.click()
                    time.sleep(0.05)
                    
                    # Presionar espacio
                    keyboard.press('space')
                    time.sleep(0.1)
                    
                    # Mover secuencialmente
                    for x, y in group[1:]:
                        if keyboard.is_pressed('esc'):
                            break
                        pyautogui.moveTo(x, y, duration=0.05)
                        time.sleep(0.02)
                        print(f"  → Movido a ({x}, {y})")
                    
                    # Liberar espacio
                    keyboard.release('space')
                    time.sleep(0.05)
                    print(f"✅ Grupo {group_idx+1} completado")
                
                if group_idx < len(groups) - 1 and not keyboard.is_pressed('esc'):
                    delay = random.randint(min_delay_ms, max_delay_ms) / 10000000.0
                    print(f"⏳ Esperando {delay:.2f}s")
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
                            click_count=1, mode='click'):
        """Versión simplificada para usar con lista de cuadrados."""
        ClickExecutor.execute_clicks(
            squares, min_delay_ms, max_delay_ms,
            click_centers, randomize_order, click_count, mode
        )