import pyautogui
import time
import random
import keyboard  # Necesitas instalar: pip install keyboard
import threading

class ClickExecutor:
    @staticmethod
    def execute_clicks(coordinates, min_delay_ms=150, max_delay_ms=700, click_centers=True, randomize_order=False, click_count=1):
        """
        Ejecuta clics en las coordenadas dadas con retrasos aleatorios.
        
        Args:
            coordinates: Lista de tuplas (x, y) o diccionarios con 'x', 'y', 'width', 'height'
            min_delay_ms: Retraso mínimo entre clics en milisegundos
            max_delay_ms: Retraso máximo entre clics en milisegundos
            click_centers: Si True, usa el centro de los rectángulos; si False, usa las coordenadas tal cual
            randomize_order: Si True, mezcla el orden de los clics
            click_count: Número de clics por coordenada (1 = un clic, 2 = doble clic, etc.)
        """
        # Convertir a lista de (x, y)
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
        
        # Bandera para interrupción
        stop_execution = False
        
        def check_escape():
            nonlocal stop_execution
            keyboard.wait('esc')
            stop_execution = True
            print("\n⏹️ Ejecución interrumpida por Escape")
        
        # Iniciar hilo para escuchar Escape
        escape_thread = threading.Thread(target=check_escape, daemon=True)
        escape_thread.start()
        
        total = len(points) * click_count
        executed = 0
        
        try:
            for idx, (x, y) in enumerate(points):
                if stop_execution:
                    break
                
                # Mover el mouse a la posición
                pyautogui.moveTo(x, y, duration=0.1)
                
                # Realizar clics
                for _ in range(click_count):
                    if stop_execution:
                        break
                    pyautogui.click()
                    time.sleep(0.05)  # pequeño retraso entre clics múltiples
                
                executed += click_count
                
                # Retraso aleatorio entre coordenadas (excepto después del último)
                if idx < len(points) - 1 and not stop_execution:
                    delay_ms = random.randint(min_delay_ms, max_delay_ms)
                    time.sleep(delay_ms / 1000.0)
            
            print(f"✅ Ejecutados {executed} clics en {len(points)} posiciones")
            
        except KeyboardInterrupt:
            print("\n⏹️ Ejecución interrumpida por teclado (Ctrl+C)")
        finally:
            # Liberar recursos si es necesario
            pass
    
    @staticmethod
    def execute_from_squares(squares, min_delay_ms=150, max_delay_ms=700, click_centers=True, randomize_order=False, click_count=1):
        """
        Ejecuta clics a partir de la lista de cuadrados detectados.
        
        Args:
            squares: Lista de diccionarios con 'x', 'y', 'width', 'height'
            Otros parámetros igual que execute_clicks
        """
        ClickExecutor.execute_clicks(
            squares, 
            min_delay_ms, 
            max_delay_ms, 
            click_centers, 
            randomize_order, 
            click_count
        )