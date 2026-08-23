"""
Widget para seleccionar áreas de la pantalla de forma interactiva.
"""

import sys
from PyQt5.QtWidgets import (
    QWidget, QApplication, QDesktopWidget
)
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont

from src.utils.logger import logger


class AreaSelector(QWidget):
    """Widget que permite seleccionar un área arrastrando el mouse"""
    
    area_selected = pyqtSignal(dict)
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurar ventana
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Obtener geometría de la pantalla
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(screen)
        
        # Variables de selección
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_selecting = False
        self.selection_rect = QRect()
        
        # Configurar cursor
        self.setCursor(Qt.CrossCursor)
        self.show_help = True
        
        # Timer para actualización suave
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(50)
        
        logger.debug("AreaSelector inicializado")
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Fondo semitransparente
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRect(self.rect())

        if not self.selection_rect.isNull() and self.selection_rect.width() > 10:
            try:
                # Capturar el color del centro del rectángulo
                center_x = self.selection_rect.center().x()
                center_y = self.selection_rect.center().y()
                
                # Usar QScreen para capturar el píxel
                screen = QApplication.primaryScreen()
                if screen:
                    pixmap = screen.grabWindow(0, center_x-5, center_y-5, 10, 10)
                    image = pixmap.toImage()
                    
                    # Obtener color del centro
                    if image.valid(5, 5):
                        color = QColor(image.pixel(5, 5))
                        
                        # Mostrar el color en la esquina del rectángulo
                        color_hex = f"#{color.red():02x}{color.green():02x}{color.blue():02x}"
                        
                        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
                        painter.drawRoundedRect(
                            self.selection_rect.right() - 60,
                            self.selection_rect.top() - 25,
                            55, 20, 5, 5
                        )
                        
                        painter.setPen(QPen(QColor(255, 255, 255), 1))
                        painter.setFont(QFont("Arial", 8))
                        painter.drawText(
                            self.selection_rect.right() - 55,
                            self.selection_rect.top() - 10,
                            color_hex
                        )
            except Exception as e:
                pass  # Silencioso si falla        
        
        # Dibujar rectángulo de selección
        if not self.selection_rect.isNull() and self.selection_rect.width() > 0:
            # Limpiar el área
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.drawRect(self.selection_rect)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # Borde blanco
            painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.SolidLine))
            painter.drawRect(self.selection_rect)
            
            # Esquinas
            self.draw_corners(painter)
            
            # Dimensiones
            self.draw_dimensions(painter)
        
        # Texto de ayuda
        if self.show_help and not self.is_selecting:
            self.draw_help_text(painter)
    
    def draw_corners(self, painter):
        corner_size = 12
        painter.setPen(QPen(QColor(255, 255, 255), 3, Qt.SolidLine))
        
        # Superior izquierda
        painter.drawLine(
            self.selection_rect.topLeft(),
            self.selection_rect.topLeft() + QPoint(corner_size, 0)
        )
        painter.drawLine(
            self.selection_rect.topLeft(),
            self.selection_rect.topLeft() + QPoint(0, corner_size)
        )
        
        # Superior derecha
        painter.drawLine(
            self.selection_rect.topRight(),
            self.selection_rect.topRight() + QPoint(-corner_size, 0)
        )
        painter.drawLine(
            self.selection_rect.topRight(),
            self.selection_rect.topRight() + QPoint(0, corner_size)
        )
        
        # Inferior izquierda
        painter.drawLine(
            self.selection_rect.bottomLeft(),
            self.selection_rect.bottomLeft() + QPoint(corner_size, 0)
        )
        painter.drawLine(
            self.selection_rect.bottomLeft(),
            self.selection_rect.bottomLeft() + QPoint(0, -corner_size)
        )
        
        # Inferior derecha
        painter.drawLine(
            self.selection_rect.bottomRight(),
            self.selection_rect.bottomRight() + QPoint(-corner_size, 0)
        )
        painter.drawLine(
            self.selection_rect.bottomRight(),
            self.selection_rect.bottomRight() + QPoint(0, -corner_size)
        )
    
    def draw_dimensions(self, painter):
        width = self.selection_rect.width()
        height = self.selection_rect.height()
        
        dim_text = f"📏 {width} × {height} px"
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        text_width = painter.fontMetrics().width(dim_text)
        text_x = self.selection_rect.center().x() - text_width // 2
        text_y = self.selection_rect.bottom() + 25
        
        if text_y > self.height() - 20:
            text_y = self.selection_rect.top() - 20
        
        padding = 8
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(QPen(QColor(0, 0, 0, 180)))
        painter.drawRoundedRect(
            text_x - padding,
            text_y - 18,
            text_width + padding * 2,
            28,
            5, 5
        )
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(text_x, text_y, dim_text)
    
    def draw_help_text(self, painter):
        help_text = "🖱️ Arrastra para seleccionar\n"
        help_text += "⌨️ ESC para cancelar"
        
        painter.setFont(QFont("Arial", 12))
        text_rect = painter.boundingRect(self.rect(), Qt.AlignCenter, help_text)
        
        padding = 20
        from PyQt5.QtCore import QMargins
        bg_rect = text_rect.marginsAdded(QMargins(padding, padding, padding, padding))
        
        painter.setBrush(QBrush(QColor(0, 0, 0, 180)))
        painter.setPen(QPen(QColor(0, 0, 0, 180)))
        painter.drawRoundedRect(bg_rect, 10, 10)
        
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(self.rect(), Qt.AlignCenter, help_text)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_selecting = True
            self.show_help = False
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_point = event.pos()
            self.update_selection_rect()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.end_point = event.pos()
            self.update_selection_rect()
            
            if self.selection_rect.width() > 5 and self.selection_rect.height() > 5:
                self.confirm_selection()
            else:
                self.reset_selection()
            
            self.is_selecting = False
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_selection()
    
    def update_selection_rect(self):
        self.selection_rect = QRect(
            min(self.start_point.x(), self.end_point.x()),
            min(self.start_point.y(), self.end_point.y()),
            abs(self.start_point.x() - self.end_point.x()),
            abs(self.start_point.y() - self.end_point.y())
        )
        self.update()
    
    def reset_selection(self):
        self.selection_rect = QRect()
        self.is_selecting = False
        self.show_help = True
        self.update()
    
    def confirm_selection(self):
        x, y, width, height = self.selection_rect.getRect()
        area_dict = {
            'left': x,
            'top': y,
            'width': width,
            'height': height
        }
        logger.info(f"Área seleccionada: {area_dict}")
        self.area_selected.emit(area_dict)
        self.close()
    
    def cancel_selection(self):
        logger.info("Selección cancelada")
        self.cancelled.emit()
        self.close()
    
    def closeEvent(self, event):
        self.update_timer.stop()
        event.accept()


def select_area_interactive(parent=None) -> dict:
    """Función auxiliar para mostrar el selector de área"""
    logger.info("Iniciando selector de área interactivo")
    
    selector = AreaSelector(parent)
    result = {'area': None, 'cancelled': True}
    
    def on_area_selected(area):
        result['area'] = area
        result['cancelled'] = False
    
    def on_cancelled():
        result['cancelled'] = True
    
    selector.area_selected.connect(on_area_selected)
    selector.cancelled.connect(on_cancelled)
    
    selector.showFullScreen()
    selector.raise_()
    selector.activateWindow()
    
    while selector.isVisible():
        QApplication.processEvents()
    
    selector.deleteLater()
    
    if result['cancelled']:
        return None
    return result['area']