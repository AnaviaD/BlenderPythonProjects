import cv2
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, 
                            QFileDialog, QMessageBox, QGroupBox,
                            QSizePolicy)  # ← Importado correctamente
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from core.screenshot_capture import ScreenshotCapture
from core.image_processor import ImageProcessor
from utils.image_converter import ImageConverter

class MainWindow(QMainWindow):
    """
    Ventana principal con dos buffers independientes para imágenes.
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.capture = ScreenshotCapture()
        self.processor = ImageProcessor()
        
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
        
        self.btn_capture_test = QPushButton("📸 Screenshot 1 (Test)")
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
        self.image_label_canvas.setMinimumSize(300, 200)
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
        """Actualiza el label de test con la imagen actual."""
        cv_image = self.processor.get_test_pixels()
        
        if cv_image is None:
            self.image_label_test.setText("Test")
            self.image_label_test.setPixmap(QPixmap())
            return
        
        pixmap = ImageConverter.cv_to_qpixmap(cv_image)
        if pixmap:
            scaled_pixmap = pixmap.scaled(
                self.image_label_test.width() - 4,
                self.image_label_test.height() - 4,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label_test.setPixmap(scaled_pixmap)
            self.image_label_test.setText("")
    
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
        """Captura pantalla y la asigna al buffer test."""
        self.status_label.setText("Capturando pantalla para Test...")
        
        image = self.capture.capture()
        
        if image is not None:
            self.processor.set_test_image(
                image, 
                titulo="Screenshot Test",
                descripcion="Captura del botón Test"
            )
            self.update_display_test()
            self.status_label.setText("Screenshot Test capturado")
            self.show_image_info("test")
        else:
            QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla")
            self.status_label.setText("Error al capturar")
    
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
        """Guarda la imagen especificada."""
        if image_type == "test":
            cv_image = self.processor.get_test_pixels()
            default_name = "test_image.png"
        else:
            cv_image = self.processor.get_canvas_pixels()
            default_name = "canvas_image.png"
        
        if cv_image is None:
            QMessageBox.warning(self, "Aviso", f"No hay imagen {image_type} para guardar")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Guardar Imagen {image_type}",
            default_name,
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        
        if file_path:
            cv2.imwrite(file_path, cv_image)
            QMessageBox.information(self, "Éxito", f"Imagen guardada en:\n{file_path}")
            self.status_label.setText(f"Imagen {image_type} guardada")
    
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