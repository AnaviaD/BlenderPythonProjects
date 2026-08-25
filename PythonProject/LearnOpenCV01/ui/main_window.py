import cv2
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, 
                            QFileDialog, QMessageBox, QGroupBox,
                            QSizePolicy)  # ← Importado correctamente
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QCursor

from core.screenshot_capture import ScreenshotCapture
from core.image_processor import ImageProcessor
from utils.image_converter import ImageConverter
from ui.color_picker import ColorPicker

class MainWindow(QMainWindow):
    """
    Ventana principal con dos buffers independientes para imágenes.
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.capture = ScreenshotCapture()
        self.processor = ImageProcessor()
        self.waiting_for_color_pick = False

        # Configurar UI
        self.setWindowTitle("Screenshot Processor - Dual Mode")
        self.setGeometry(100, 100, 900, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # ================================================================
        # FILA 1: Botones y previsualizaciones en horizontal
        # ================================================================
        row1_layout = QHBoxLayout()
        
        # --- Grupo Test (Botón + Label pequeño) ---
        test_group = QWidget()
        test_layout = QVBoxLayout()
        test_layout.setAlignment(Qt.AlignCenter)
        test_layout.setSpacing(5)
        
        self.btn_capture_test = QPushButton("📸 ColorTest")
        self.btn_capture_test.clicked.connect(self.on_capture_test)
        test_layout.addWidget(self.btn_capture_test)
        
        self.image_label_test = QLabel()
        self.image_label_test.setAlignment(Qt.AlignCenter)
        self.image_label_test.setFixedSize(40, 40)
        self.image_label_test.setStyleSheet("""
            QLabel {
                border: 1px solid #999999;
                background-color: #f0f0f0;
            }
        """)
        self.image_label_test.setText("Test")
        test_layout.addWidget(self.image_label_test)
        
        test_group.setLayout(test_layout)
        # ✅ CORREGIDO: Usar QSizePolicy directamente
        test_group.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row1_layout.addWidget(test_group)
        
        # Espaciador entre grupos
        row1_layout.addSpacing(20)
        
        # --- Grupo Canvas (Botón + Label grande) ---
        canvas_group = QWidget()
        canvas_layout = QVBoxLayout()
        canvas_layout.setAlignment(Qt.AlignCenter)
        canvas_layout.setSpacing(5)
        
        self.btn_capture_canvas = QPushButton("📸 Screenshot 2 (Canvas)")
        self.btn_capture_canvas.clicked.connect(self.on_capture_canvas)
        canvas_layout.addWidget(self.btn_capture_canvas)
        
        self.image_label_canvas = QLabel()
        self.image_label_canvas.setAlignment(Qt.AlignCenter)
        self.image_label_canvas.setMinimumSize(600, 400)
        self.image_label_canvas.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                padding: 5px;
            }
        """)
        self.image_label_canvas.setText("Canvas")
        canvas_layout.addWidget(self.image_label_canvas)
        
        canvas_group.setLayout(canvas_layout)
        row1_layout.addWidget(canvas_group)
        
        # Espaciador elástico para empujar botones de acciones a la derecha
        row1_layout.addStretch()
        
        # --- Grupo de Acciones ---
        actions_group = QWidget()
        actions_layout = QVBoxLayout()
        actions_layout.setAlignment(Qt.AlignCenter)
        actions_layout.setSpacing(5)
        
        self.btn_save_test = QPushButton("💾 Guardar Test")
        self.btn_save_test.clicked.connect(lambda: self.on_save("test"))
        actions_layout.addWidget(self.btn_save_test)
        
        self.btn_save_canvas = QPushButton("💾 Guardar Canvas")
        self.btn_save_canvas.clicked.connect(lambda: self.on_save("canvas"))
        actions_layout.addWidget(self.btn_save_canvas)
        
        self.btn_info = QPushButton("ℹ️ Info Imágenes")
        self.btn_info.clicked.connect(self.on_show_info)
        actions_layout.addWidget(self.btn_info)
        
        self.btn_compare = QPushButton("🔍 Comparar")
        self.btn_compare.clicked.connect(self.on_compare)
        actions_layout.addWidget(self.btn_compare)
        
        self.btn_reset = QPushButton("🔄 Resetear Todo")
        self.btn_reset.clicked.connect(self.on_reset_all)
        actions_layout.addWidget(self.btn_reset)
        
        actions_group.setLayout(actions_layout)
        row1_layout.addWidget(actions_group)
        
        main_layout.addLayout(row1_layout)
        
        # --- Barra de estado ---
        self.status_label = QLabel("Listo")
        self.statusBar().addWidget(self.status_label)
    
    # ================================================================
    # MÉTODOS DE ACTUALIZACIÓN DE UI
    # ================================================================

    def update_display_test(self):
        color_bgr = self.processor.get_test_color()
        
        if color_bgr is None:
            self.image_label_test.setText("Test")
            self.image_label_test.setStyleSheet("""
                QLabel {
                    border: 1px solid #999999;
                    background-color: #f0f0f0;
                }
            """)
            return
        
        # Convertir BGR a RGB para Qt
        b, g, r = color_bgr
        color_hex = f"#{r:02x}{g:02x}{b:02x}"
        
        self.image_label_test.setStyleSheet(f"""
            QLabel {{
                border: 1px solid #999999;
                background-color: {color_hex};
            }}
        """)
        self.image_label_test.setText("")  # Limpiar texto    

    
    def update_display_canvas(self):
        """Actualiza el label de canvas con la imagen actual."""
        cv_image = self.processor.get_canvas_pixels()
        
        if cv_image is None:
            self.image_label_canvas.setText("Canvas")
            self.image_label_canvas.setPixmap(QPixmap())
            return
        
        pixmap = ImageConverter.cv_to_qpixmap(cv_image)
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.image_label_canvas.width() - 10,
                self.image_label_canvas.height() - 10,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label_canvas.setPixmap(scaled_pixmap)
            self.image_label_canvas.setText("")
    
    # ================================================================
    # MANEJADORES DE EVENTOS
    # ================================================================

    def on_capture_test(self):
        """
        Activa el modo de selección de color.
        El usuario debe hacer clic en la pantalla para capturar el color.
        """
        self.status_label.setText("Haz clic en cualquier lugar para capturar el color...")
        
        # Crear y mostrar el selector de color
        self.color_picker = ColorPicker()
        self.color_picker.color_selected.connect(self.on_color_picked)
        # Cuando se cierre (por clic o Escape), restaurar estado
        self.color_picker.destroyed.connect(self.on_color_picker_closed) 


    def on_color_picked(self, x, y):
        """Manejador cuando el usuario selecciona un punto en la pantalla."""
        self.status_label.setText(f"Capturando color en ({x}, {y})...")
        
        # Obtener el color en esas coordenadas
        color_bgr = self.capture.get_color_at(x, y, radius=2)
        
        if color_bgr:
            # Guardar en el procesador con coordenadas
            self.processor.set_test_color(color_bgr, (x, y))
            self.update_display_test()
            self.status_label.setText(f"Color capturado en ({x}, {y})")
        else:
            QMessageBox.warning(self, "Error", "No se pudo obtener el color")
            self.status_label.setText("Error al capturar color")


    def on_color_picker_closed(self):
        """Se ejecuta cuando el picker se cierra (por clic o Escape)."""
        # Si no se seleccionó un color (por ejemplo, se cerró con Escape)
        if self.processor.get_test_color() is None:
            self.status_label.setText("Selección cancelada")            


    def eventFilter(self, obj, event):
        if self.waiting_for_color_pick and event.type() == QEvent.MouseButtonPress:
            # Obtener posición global del mouse
            pos = QCursor.pos()
            x, y = pos.x(), pos.y()
            
            # Capturar color
            color_bgr = self.capture.get_color_at(x, y)
            
            if color_bgr:
                self.processor.set_test_color(color_bgr, (x, y))
                self.update_display_test()
                self.status_label.setText(f"Color capturado en ({x}, {y})")
            else:
                self.status_label.setText("Error al capturar color")
            
            # Desactivar modo de espera
            self.waiting_for_color_pick = False
            QApplication.instance().removeEventFilter(self)
            
            # Cambiar cursor de nuevo a normal si lo cambiaste
            QApplication.restoreOverrideCursor()
            
            return True  # Evento procesado
        return super().eventFilter(obj, event)

    
    def on_capture_canvas(self):
        """Captura pantalla y la asigna al buffer canvas."""
        self.status_label.setText("Capturando pantalla para Canvas...")
        
        image = self.capture.capture()
        
        if image is not None:
            self.processor.set_canvas_image(
                image,
                titulo="Screenshot Canvas",
                descripcion="Captura del botón Canvas"
            )
            self.update_display_canvas()
            self.status_label.setText("Screenshot Canvas capturado")
            self.show_image_info("canvas")
        else:
            QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla")
            self.status_label.setText("Error al capturar")

    def on_save(self, image_type="test"):
        if image_type == "test":
            color = self.processor.get_test_color()
            coords = self.processor.get_test_coordenadas()
            if color is None:
                QMessageBox.warning(self, "Aviso", "No hay color para guardar")
                return
            # Guardar en archivo de texto
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Color", "color.txt",
                "Archivo de texto (*.txt)"
            )
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(f"Coordenadas: {coords}\n")
                    f.write(f"Color (BGR): {color}\n")
                    f.write(f"Color (RGB): {color[2]}, {color[1]}, {color[0]}\n")
                    f.write(f"Color HEX: #{color[2]:02x}{color[1]:02x}{color[0]:02x}\n")
                QMessageBox.information(self, "Éxito", f"Color guardado en {file_path}")
        else:
            # Guardar imagen canvas (sin cambios)
            ...    


    
    def on_show_info(self):
        """Muestra información de ambas imágenes."""
        info_test = self.processor.get_image_info("test")
        info_canvas = self.processor.get_image_info("canvas")
        
        message = "=== IMAGEN TEST ===\n"
        if info_test:
            message += f"Título: {info_test['titulo']}\n"
            message += f"Fecha: {info_test['fecha']}\n"
            message += f"Dimensiones: {info_test['dimensiones']}\n"
            message += f"Canales: {info_test['canales']}\n"
            message += f"Memoria: {info_test['memoria']}\n"
        else:
            message += "No hay imagen cargada\n"
        
        message += "\n=== IMAGEN CANVAS ===\n"
        if info_canvas:
            message += f"Título: {info_canvas['titulo']}\n"
            message += f"Fecha: {info_canvas['fecha']}\n"
            message += f"Dimensiones: {info_canvas['dimensiones']}\n"
            message += f"Canales: {info_canvas['canales']}\n"
            message += f"Memoria: {info_canvas['memoria']}\n"
        else:
            message += "No hay imagen cargada\n"
        
        QMessageBox.information(self, "Información de Imágenes", message)
    
    def show_image_info(self, image_type="test"):
        """Muestra información en la barra de estado."""
        info = self.processor.get_image_info(image_type)
        if info:
            self.status_label.setText(
                f"{info['nombre']}: {info['dimensiones']} | "
                f"{info['canales']} canales | {info['memoria']}"
            )
    
    def on_compare(self):
        """Compara las dos imágenes."""
        result = self.processor.compare_images()
        
        if "error" in result:
            QMessageBox.warning(self, "Error de Comparación", result["error"])
            return
        
        message = (
            "=== RESULTADOS DE COMPARACIÓN ===\n\n"
            f"📊 MSE (Error Cuadrático Medio): {result['mse']:.4f}\n"
            f"📈 Similitud: {result['similitud']:.4f} (1.0 = idénticas)\n\n"
            f"📸 Media Test: {result['media_test']:.2f}\n"
            f"📸 Media Canvas: {result['media_canvas']:.2f}\n"
            f"📉 Diferencia de medias: {abs(result['media_test'] - result['media_canvas']):.2f}\n\n"
            "💡 Interpretación:\n"
            f"  • Similitud > 0.9: Muy similares\n"
            f"  • Similitud 0.5-0.9: Algo similares\n"
            f"  • Similitud < 0.5: Muy diferentes"
        )
        
        QMessageBox.information(self, "Comparación de Imágenes", message)
    
    def on_reset_all(self):
        """Limpia ambas imágenes."""
        self.processor.reset_test_image()
        self.processor.reset_canvas_image()
        self.update_display_test()
        self.update_display_canvas()
        self.status_label.setText("Todas las imágenes han sido limpiadas")