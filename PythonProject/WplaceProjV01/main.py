#!/usr/bin/env python3
"""
Pixel Automator - Aplicación para detectar y hacer clic en píxeles anidados.
"""

import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

from src.gui.main_window import MainWindow
from src.utils.logger import logger

def main():
    """Punto de entrada principal"""
    try:
        logger.info("=== INICIANDO PIXEL AUTOMATOR ===")
        
        # Crear aplicación
        app = QApplication(sys.argv)
        logger.info("QApplication creada")
        
        # Crear ventana principal
        window = MainWindow()
        logger.info("Ventana principal creada")
        
        # Mostrar ventana
        window.show()
        logger.info("Ventana mostrada")
        
        # Ejecutar aplicación
        sys.exit(app.exec_())
        
    except Exception as e:
        error_msg = f"Error fatal: {e}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        
        # Intentar mostrar mensaje de error en GUI si es posible
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error Fatal")
            msg.setText("Ha ocurrido un error al iniciar la aplicación")
            msg.setInformativeText(str(e))
            msg.setDetailedText(traceback.format_exc())
            msg.exec_()
        except:
            print(f"ERROR: {e}")
            print(traceback.format_exc())
        
        sys.exit(1)

if __name__ == "__main__":
    main()