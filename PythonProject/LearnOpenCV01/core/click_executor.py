import pyautogui
import time
import random
import keyboard as keyboard
import threading
import numpy as np

class ClickExecutor:

    _paused = False

    @staticmethod
    def execute_clicks(coordinates, min_delay_ms=1, max_delay_ms=2,
                    click_centers=True, randomize_order=False,
                    click_count=1, mode='click', avg_height=30, avg_width=30):
        points = []
        point_to_color = {}
        for coord in coordinates:
            if isinstance(coord, dict):
                if click_centers and 'width' in coord and 'height' in coord:
                    x = coord['x'] + coord['width'] // 2
                    y = coord['y'] + coord['height'] // 2
                elif 'centro' in coord:
                    x, y = coord['centro']
                else:
                    x, y = coord.get('x', 0), coord.get('y', 0)
                color = coord.get('color', None)
            else:
                x, y = coord
                color = None
            points.append((x, y))
            point_to_color[(x, y)] = color

        if randomize_order:
            random.shuffle(points)

        if mode == 'drag':
            ClickExecutor._execute_drag_mode(
                points, min_delay_ms, max_delay_ms, avg_height, avg_width,
                point_to_color
            )
        else:
            ClickExecutor._execute_click_mode(
                points, min_delay_ms, max_delay_ms, click_count,
                point_to_color
            )

    @staticmethod
    def toggle_pause():
        ClickExecutor._paused = not ClickExecutor._paused
        print(f"{'⏸️ Pausado' if ClickExecutor._paused else '▶️ Reanudado'}")

    @classmethod
    def _check_pause(cls):
        while cls._paused:
            time.sleep(0.1)

    # ================================================================
    # MODO CLICK (con verificación de color)
    # ================================================================
    @staticmethod
    def _execute_click_mode(points, min_delay_ms, max_delay_ms, click_count, point_to_color):
        stop_execution = False
        def check_escape():
            nonlocal stop_execution
            keyboard.wait('esc')
            stop_execution = True
            print("\n⏹️ Ejecución interrumpida por Escape")

        escape_thread = threading.Thread(target=check_escape, daemon=True)
        escape_thread.start()

        previous_color = None

        try:
            for idx, (x, y) in enumerate(points):
                if stop_execution:
                    break

                current_color = point_to_color.get((x, y))

                # 1. Posicionarse en el target
                pyautogui.moveTo(x, y, duration=0.001)

                # 2. Click central si es el primero o si cambió el color
                is_first = (idx == 0)
                color_changed = (previous_color is not None and current_color is not None
                                and current_color != previous_color)
                if is_first or color_changed:
                    print(f"🎯 Click central en ({x}, {y}) [primero={is_first}, cambio={color_changed}]")
                    pyautogui.click(button='middle')
                    time.sleep(0.05)

                # 3. Ejecutar la acción normal
                for _ in range(click_count):
                    if stop_execution:
                        break
                    pyautogui.click()
                    time.sleep(0.05)

                if idx < len(points) - 1 and not stop_execution:
                    delay = random.randint(min_delay_ms, max_delay_ms) / 100000.0
                    time.sleep(delay)

                previous_color = current_color

        except KeyboardInterrupt:
            print("\n⏹️ Interrumpido")

    # ================================================================
    # MODO DRAG (con verificación de color ANTES del space)
    # ================================================================
    @staticmethod
    def _execute_drag_mode(points, min_delay_ms, max_delay_ms, avg_height=30, avg_width=30,
                        point_to_color=None):
        if point_to_color is None:
            point_to_color = {}

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01
        keyboard.add_hotkey('ctrl+shift+p', ClickExecutor.toggle_pause)

        if not points:
            return

        # --- Agrupamiento (SIN CAMBIOS) ---
        sorted_points = sorted(points, key=lambda p: (p[1], p[0]))

        vertical_threshold = max(avg_height * 0.6, 10)
        rows = []
        current_row = [sorted_points[0]]
        for p in sorted_points[1:]:
            if abs(p[1] - current_row[-1][1]) < vertical_threshold:
                current_row.append(p)
            else:
                rows.append(current_row)
                current_row = [p]
        rows.append(current_row)

        horizontal_threshold = max(avg_width * 1.2, 15)
        row_groups = []
        for row in rows:
            row.sort(key=lambda p: p[0])
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

        # --- Ejecución con verificación de color ---
        previous_color = None
        is_first_group = True

        try:
            for row_idx, groups_in_row in enumerate(row_groups):
                print(f"\n📐 Fila {row_idx+1} - {len(groups_in_row)} grupos")

                for group_idx, group in enumerate(groups_in_row):
                    ClickExecutor._check_pause()
                    if keyboard.is_pressed('esc'):
                        print("\n⏹️ Interrumpido por Escape")
                        break

                    # 1. Posicionarse en el primer punto del grupo
                    x0, y0 = group[0]
                    pyautogui.moveTo(x0, y0, duration=0.005)

                    # 2. Obtener color del primer punto del grupo
                    current_color = point_to_color.get((x0, y0))

                    # 3. Click central si es el primero o si cambió el color
                    color_changed = (previous_color is not None and current_color is not None
                                    and current_color != previous_color)
                    if is_first_group or color_changed:
                        print(f"🎯 Click central en ({x0}, {y0}) [primero={is_first_group}, cambio={color_changed}]")
                        pyautogui.click(button='middle')
                        time.sleep(0.05)

                    # 4. Ejecutar el grupo (SIN CAMBIOS)
                    if len(group) == 1:
                        pyautogui.click()
                        print(f"  🖱️ Click en ({x0}, {y0})")
                    else:
                        print(f"  📌 Grupo de {len(group)} puntos comenzando en ({x0}, {y0})")

                        keyboard.release('space')
                        time.sleep(0.03)

                        pyautogui.click()  # click de foco (normal)
                        time.sleep(0.03)

                        keyboard.press('space')
                        time.sleep(0.05)

                        for x, y in group[1:]:
                            if keyboard.is_pressed('esc'):
                                break
                            pyautogui.moveTo(x, y, duration=0.02)
                            time.sleep(0.01)
                            print(f"    → Movido a ({x}, {y})")

                        keyboard.release('space')
                        time.sleep(0.03)
                        print(f"  ✅ Grupo {group_idx+1} completado")

                    previous_color = current_color
                    is_first_group = False

                    # Retraso entre grupos
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