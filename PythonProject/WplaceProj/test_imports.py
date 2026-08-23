# test_imports.py
"""
Script para probar todas las importaciones y componentes.
"""

import sys
import traceback

def test_imports():
    """Prueba todas las importaciones del proyecto"""
    
    print("🔍 Probando importaciones...")
    
    try:
        print("  ✅ Importando PyQt5...")
        from PyQt5.QtWidgets import QApplication
    except Exception as e:
        print(f"  ❌ Error importando PyQt5: {e}")
        return False
    
    try:
        print("  ✅ Importando opencv...")
        import cv2
    except Exception as e:
        print(f"  ❌ Error importando opencv: {e}")
        return False
    
    try:
        print("  ✅ Importando numpy...")
        import numpy as np
    except Exception as e:
        print(f"  ❌ Error importando numpy: {e}")
        return False
    
    try:
        print("  ✅ Importando pyautogui...")
        import pyautogui
    except Exception as e:
        print(f"  ❌ Error importando pyautogui: {e}")
        return False
    
    try:
        print("  ✅ Importando mss...")
        import mss
    except Exception as e:
        print(f"  ❌ Error importando mss: {e}")
        return False
    
    try:
        print("  ✅ Importando módulos del proyecto...")
        
        # Importar desde core
        from src.core.pattern_detector import PatternDetector, DetectionParams
        from src.core.screen_capture import ScreenCapture
        from src.core.pixel_analyzer import PixelAnalyzer
        from src.core.click_executor import ClickExecutor
        
        # Importar desde gui
        from src.gui.main_window import MainWindow
        from src.gui.area_selector import AreaSelector, select_area_interactive
        
        # Importar desde utils
        from src.utils.logger import logger
        
        print("     ✅ PatternDetector, DetectionParams")
        print("     ✅ ScreenCapture")
        print("     ✅ PixelAnalyzer")
        print("     ✅ ClickExecutor")
        print("     ✅ MainWindow")
        print("     ✅ AreaSelector")
        print("     ✅ logger")
        
    except Exception as e:
        print(f"  ❌ Error importando módulos del proyecto: {e}")
        print(traceback.format_exc())
        return False
    
    print("✅ Todas las importaciones exitosas!")
    return True

def test_components():
    """Prueba la creación de componentes"""
    
    print("\n🔍 Probando creación de componentes...")
    
    try:
        print("  ✅ Importando DetectionParams...")
        from src.core.pattern_detector import DetectionParams
        params = DetectionParams()
        print(f"     {params}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        print("  ✅ Creando ScreenCapture...")
        from src.core.screen_capture import ScreenCapture
        capture = ScreenCapture()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        print("  ✅ Creando PatternDetector...")
        from src.core.pattern_detector import PatternDetector
        detector = PatternDetector()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        print("  ✅ Creando PixelAnalyzer...")
        from src.core.pixel_analyzer import PixelAnalyzer
        analyzer = PixelAnalyzer()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        print("  ✅ Creando ClickExecutor...")
        from src.core.click_executor import ClickExecutor
        executor = ClickExecutor()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    print("✅ Todos los componentes creados exitosamente!")
    return True

def test_gui():
    """Prueba la creación de la GUI"""
    
    print("\n🔍 Probando GUI...")
    
    try:
        print("  ✅ Creando QApplication...")
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    try:
        print("  ✅ Creando MainWindow...")
        from src.gui.main_window import MainWindow
        window = MainWindow()
        print(f"     Window: {window}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print(traceback.format_exc())
        return False
    
    try:
        print("  ✅ Mostrando MainWindow...")
        window.show()
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    print("✅ GUI creada exitosamente!")
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TEST DE COMPONENTES PIXEL AUTOMATOR")
    print("=" * 50)
    
    # Test 1: Importaciones
    if not test_imports():
        sys.exit(1)
    
    # Test 2: Componentes
    if not test_components():
        sys.exit(1)
    
    # Test 3: GUI (opcional, puede requerir interacción)
    try:
        if not test_gui():
            print("\n⚠️ La GUI no se pudo probar completamente")
        else:
            print("\n✅ TODOS LOS TESTS PASARON!")
            print("\n💡 Presiona Ctrl+C para cerrar la ventana de prueba")
            from PyQt5.QtWidgets import QApplication
            sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\n👋 Prueba finalizada")
        sys.exit(0)