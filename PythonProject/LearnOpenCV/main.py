import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Función principal de la aplicación."""
    # Crear la aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Screenshot Processor")
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()