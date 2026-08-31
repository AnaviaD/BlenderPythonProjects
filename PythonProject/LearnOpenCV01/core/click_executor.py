import pyautogui
import time
import random
import keyboard as keyboard
import threading
import numpy as np

class ClickExecutor:

    _paused = False  # Variable de clase

    @staticmethod
    def execute_clicks(coordinates, min_delay_ms=1, max_delay_ms=2,
                    click_centers=True, randomize_order=False,
                    click_count=1, mode='click', avg_height=30, avg_width=30):
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
            ClickExecutor._execute_drag_mode(points, min_delay_ms, max_delay_ms, avg_height, avg_width)
        else:
            ClickExecutor._execute_click_mode(points, min_delay_ms, max_delay_ms, click_count)
    


    @staticmethod
    def toggle_pause():
        """Alterna el estado de pausa (sin argumentos)."""
        ClickExecutor._paused = not ClickExecutor._paused
        print(f"{'⏸️ Pausado' if ClickExecutor._paused else '▶️ Reanudado'}")
    
    @classmethod
    def _check_pause(cls):
        """Espera mientras esté en pausa."""
        while cls._paused:
            time.sleep(0.1)



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
                pyautogui.moveTo(x, y, duration=0.001)
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
    def _execute_drag_mode(points, min_delay_ms, max_delay_ms, avg_height=30, avg_width=30):
        """Modo arrastre con pausa y failsafe."""
        # Configurar failsafe
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        
        # Registrar hotkey para pausa
        keyboard.add_hotkey('ctrl+shift+p', ClickExecutor.toggle_pause)
        
        if not points:
            return
        
        # --- 1. Ordenar puntos por fila (Y) y columna (X) ---
        sorted_points = sorted(points, key=lambda p: (p[1], p[0]))
        
        # --- 2. Agrupar por filas usando umbral vertical basado en altura promedio ---
        vertical_threshold = avg_height * 0.6  # 0.6 para ser más tolerante
        vertical_threshold = max(vertical_threshold, 10)
        
        rows = []
        current_row = [sorted_points[0]]
        for p in sorted_points[1:]:
            if abs(p[1] - current_row[-1][1]) < vertical_threshold:
                current_row.append(p)
            else:
                rows.append(current_row)
                current_row = [p]
        rows.append(current_row)
        
        # --- 3. Para cada fila, agrupar horizontalmente basado en el ancho promedio ---
        # Usar el ancho promedio de los targets para definir el umbral
        horizontal_threshold = avg_width * 1.2  # 1.2 para agrupar solo los que están muy cerca
        horizontal_threshold = max(horizontal_threshold, 15)
        
        row_groups = []  # Lista de filas, cada fila tiene una lista de grupos
        for row in rows:
            row.sort(key=lambda p: p[0])  # ordenar por X de izquierda a derecha
            groups_in_row = []
            current_group = [row[0]]
            for p in row[1:]:
                if p[0] - current_group[-1][0] < horizontal_threshold:
                    current_group.append(p)
                else:
                    groups_in_row.append(current_group)
                    current_group = [p]
            if current_group:
                groups_in_row.append(current_group)
            row_groups.append(groups_in_row)
        
        # --- 4. Ejecutar fila por fila, grupo por grupo ---
        try:
            for row_idx, groups_in_row in enumerate(row_groups):
                print(f"\n📐 Fila {row_idx+1} - {len(groups_in_row)} grupos")
                
                for group_idx, group in enumerate(groups_in_row):
                    ClickExecutor._check_pause()
                    if keyboard.is_pressed('esc'):
                        print("\n⏹️ Interrumpido por Escape")
                        break
                    
                    if len(group) == 1:
                        x, y = group[0]
                        pyautogui.moveTo(x, y, duration=0.00005)
                        pyautogui.click()
                        print(f"  🖱️ Click en ({x}, {y})")
                    else:
                        x0, y0 = group[0]
                        pyautogui.moveTo(x0, y0, duration=0.005)
                        print(f"  📌 Grupo de {len(group)} puntos comenzando en ({x0}, {y0})")
                        
                        # Forzar liberación de espacio
                        keyboard.release('space')
                        time.sleep(0.03)
                        
                        # Clic para dar foco
                        pyautogui.click()
                        time.sleep(0.03)
                        
                        # Presionar espacio
                        keyboard.press('space')
                        time.sleep(0.05)
                        
                        # Recorrer los puntos del grupo
                        for x, y in group[1:]:
                            if keyboard.is_pressed('esc'):
                                break
                            pyautogui.moveTo(x, y, duration=0.02)
                            time.sleep(0.01)
                            print(f"    → Movido a ({x}, {y})")
                        
                        # Liberar espacio
                        keyboard.release('space')
                        time.sleep(0.03)
                        print(f"  ✅ Grupo {group_idx+1} completado")
                    
                    # Retraso entre grupos de la misma fila
                    if group_idx < len(groups_in_row) - 1 and not keyboard.is_pressed('esc'):
                        delay = random.randint(min_delay_ms, max_delay_ms) / 100000.0
                        print(f"  ⏳ Esperando {delay:.2f}s")
                        time.sleep(delay)
                
                # Retraso entre filas
                if row_idx < len(row_groups) - 1 and not keyboard.is_pressed('esc'):
                    delay = random.randint(min_delay_ms, max_delay_ms) / 100000.0
                    print(f"\n⏬ Cambiando a fila {row_idx+2}. Esperando {delay:.2f}s")
                    time.sleep(delay)
            
            print(f"\n✅ Ejecutados {sum(len(g) for g in row_groups)} grupos en {len(row_groups)} filas")
        
        
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
                            click_count=1, mode='click', avg_height=30, avg_width=30):
        ClickExecutor.execute_clicks(
            squares, min_delay_ms, max_delay_ms,
            click_centers, randomize_order, click_count, mode,
            avg_height, avg_width
        )