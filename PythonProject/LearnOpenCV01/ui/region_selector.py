from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QCursor

class RegionSelector(QWidget):
    """
    Widget transparente que cubre toda la pantalla para seleccionar un área.
    Emite una señal con las coordenadas (x, y, ancho, alto) al soltar el mouse.
    """
    
    region_selected = pyqtSignal(int, int, int, int)  # x, y, w, h
    
    def __init__(self):
        super().__init__()
        
        # Configurar ventana sin bordes, transparente y en pantalla completa
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.01)  # Casi transparente (0.01 para que sea clicable)
        self.setCursor(Qt.CrossCursor)  # Cursor de cruz
        self.showFullScreen()
        
        # Variables de selección
        self.start_point = None
        self.end_point = None
        self.is_dragging = False
        
        # Capturar eventos de mouse globales
        self.grabMouse()
    
    def mousePressEvent(self, event):
        """Inicia la selección al presionar el mouse."""
        self.start_point = QCursor.pos()
        self.end_point = self.start_point
        self.is_dragging = True
        self.update()  # Redibujar
    
    def mouseMoveEvent(self, event):
        """Actualiza el rectángulo al mover el mouse."""
        if self.is_dragging:
            self.end_point = QCursor.pos()
            self.update()  # Redibujar
    
    def mouseReleaseEvent(self, event):
        """Finaliza la selección y emite las coordenadas."""
        if self.is_dragging:
            self.is_dragging = False
            self.end_point = QCursor.pos()
            
            # Calcular rectángulo desde start_point hasta end_point
            x = min(self.start_point.x(), self.end_point.x())
            y = min(self.start_point.y(), self.end_point.y())
            w = abs(self.start_point.x() - self.end_point.x())
            h = abs(self.start_point.y() - self.end_point.y())
            
            # Solo emitir si el área es significativa (mínimo 5x5)
            if w > 5 and h > 5:
                self.region_selected.emit(x, y, w, h)
            else:
                # Si es muy pequeño, cancelar selección
                self.region_selected.emit(0, 0, 0, 0)  # Área inválida
            
            self.close()
    
    def keyPressEvent(self, event):
        """Permite cancelar con Escape (opcional, pero no lo prohibimos)."""
        if event.key() == Qt.Key_Escape:
            self.close()
    
    def paintEvent(self, event):
        """Dibuja el rectángulo de selección."""
        if not self.is_dragging or self.start_point is None or self.end_point is None:
            return
        
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))  # Borde rojo de 2px
        
        # Dibujar rectángulo
        x = min(self.start_point.x(), self.end_point.x())
        y = min(self.start_point.y(), self.end_point.y())
        w = abs(self.start_point.x() - self.end_point.x())
        h = abs(self.start_point.y() - self.end_point.y())
        painter.drawRect(x, y, w, h)
    
    def closeEvent(self, event):
        """Liberar el mouse al cerrar."""
        self.releaseMouse()
        event.accept()