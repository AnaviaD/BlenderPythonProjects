from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QCursor

class ColorPicker(QWidget):
    """
    Widget transparente que cubre toda la pantalla para capturar un clic.
    Emite una señal con las coordenadas donde se hizo clic.
    """
    
    # Señal que se emite cuando el usuario hace clic
    color_selected = pyqtSignal(int, int)  # x, y
    
    def __init__(self):
        super().__init__()
        
        # Configurar ventana sin bordes, transparente y en pantalla completa
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.01)  # Casi transparente (0.01 para que sea clicable)
        self.setCursor(Qt.CrossCursor)  # Cursor de cruz para indicar selección
        self.showFullScreen()
        
        # También capturar clics fuera de la ventana (global)
        self.grabMouse()
        
        # Mensaje en la barra de título (opcional)
        self.setWindowTitle("Haz clic en cualquier lugar para capturar el color")
    
    def mousePressEvent(self, event):
        """Captura el clic del mouse y emite las coordenadas."""
        # Obtener posición global del mouse
        pos = QCursor.pos()
        x, y = pos.x(), pos.y()
        
        # Emitir señal
        self.color_selected.emit(x, y)
        
        # Cerrar el selector
        self.close()
    
    def keyPressEvent(self, event):
        """Permite cancelar con la tecla Escape."""
        if event.key() == Qt.Key_Escape:
            self.close()
    
    def closeEvent(self, event):
        """Liberar el mouse al cerrar."""
        self.releaseMouse()
        event.accept()