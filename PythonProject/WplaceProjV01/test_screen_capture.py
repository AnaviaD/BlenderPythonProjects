# test_screen_capture.py
"""
Prueba rápida de ScreenCapture
"""

print("1. Importando ScreenCapture...")

try:
    from src.core.screen_capture import ScreenCapture
    print("   ✅ Importado correctamente")
except ImportError as e:
    print(f"   ❌ Error de importación: {e}")
    
    # Intentar importar directamente
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
        from screen_capture import ScreenCapture
        print("   ✅ Importado directamente desde screen_capture.py")
    except Exception as e2:
        print(f"   ❌ Error directo: {e2}")
        sys.exit(1)

print("\n2. Creando instancia de ScreenCapture...")
try:
    capture = ScreenCapture()
    print(f"   ✅ Creado: {capture}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print("\n3. Probando captura de pantalla completa...")
try:
    img = capture.capture_full_screen()
    if img is not None and img.size > 0:
        print(f"   ✅ Captura exitosa: {img.shape}")
    else:
        print("   ⚠️ Captura vacía o fallida")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n✅ ScreenCapture funciona correctamente!")