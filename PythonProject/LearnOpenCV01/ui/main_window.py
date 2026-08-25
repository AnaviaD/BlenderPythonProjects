import cv2
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, 
                            QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from core.screenshot_capture import ScreenshotCapture
from core.image_processor import ImageProcessor
from utils.image_converter import ImageConverter

class MainWindow(QMainWindow):
    """
    Ventana principal con dos paneles para mostrar imágenes lado a lado.
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.capture = ScreenshotCapture()
        self.processor = ImageProcessor()
        
        # Configurar ventana
        self.setWindowTitle("Screenshot Processor - Dual View")
        self.setGeometry(100, 100, 1200, 700)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --- Panel de botones superiores ---
        button_layout = QHBoxLayout()
        
        # Botón para Screenshot 1 (Test)
        self.btn_capture_test = QPushButton("📸 Screenshot 1 (Test)")
        self.btn_capture_test.clicked.connect(self.on_capture_test)
        button_layout.addWidget(self.btn_capture_test)
        
        # Botón para Screenshot 2 (Canvas)
        self.btn_capture_canvas = QPushButton("📸 Screenshot 2 (Canvas)")
        self.btn_capture_canvas.clicked.connect(self.on_capture_canvas)
        button_layout.addWidget(self.btn_capture_canvas)
        
        # Botón para cargar imagen en Test
        self.btn_load_test = QPushButton("📂 Cargar en Test")
        self.btn_load_test.clicked.connect(lambda: self.on_load_image("test"))
        button_layout.addWidget(self.btn_load_test)
        
        # Botón para cargar imagen en Canvas
        self.btn_load_canvas = QPushButton("📂 Cargar en Canvas")
        self.btn_load_canvas.clicked.connect(lambda: self.on_load_image("canvas"))
        button_layout.addWidget(self.btn_load_canvas)
        
        # Botón para guardar (pregunta cuál)
        self.btn_save = QPushButton("💾 Guardar Imagen")
        self.btn_save.clicked.connect(self.on_save)
        button_layout.addWidget(self.btn_save)
        
        # Botón para limpiar ambas
        self.btn_clear_all = QPushButton("🗑️ Limpiar Todo")
        self.btn_clear_all.clicked.connect(self.on_clear_all)
        button_layout.addWidget(self.btn_clear_all)
        
        # Botón de info (muestra info de ambas)
        self.btn_info = QPushButton("ℹ️ Info Imágenes")
        self.btn_info.clicked.connect(self.on_show_info)
        button_layout.addWidget(self.btn_info)
        
        main_layout.addLayout(button_layout)
        
        # --- Panel de visualización dual ---
        display_layout = QHBoxLayout()
        
        # Panel izquierdo: Test
        test_group = QGroupBox("Imagen Test")
        test_layout = QVBoxLayout()
        self.image_label_test = QLabel()
        self.image_label_test.setAlignment(Qt.AlignCenter)
        self.image_label_test.setMinimumSize(40, 30)
        self.image_label_test.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                padding: 10px;
            }
        """)
        self.image_label_test.setText("Imagen Test\n\nPresiona 'Screenshot 1' o 'Cargar en Test'")
        test_layout.addWidget(self.image_label_test)
        test_group.setLayout(test_layout)
        display_layout.addWidget(test_group)
        
        # Panel derecho: Canvas
        canvas_group = QGroupBox("Imagen Canvas")
        canvas_layout = QVBoxLayout()
        self.image_label_canvas = QLabel()
        self.image_label_canvas.setAlignment(Qt.AlignCenter)
        self.image_label_canvas.setMinimumSize(400, 300)
        self.image_label_canvas.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                padding: 10px;
            }
        """)
        self.image_label_canvas.setText("Imagen Canvas\n\nPresiona 'Screenshot 2' o 'Cargar en Canvas'")
        canvas_layout.addWidget(self.image_label_canvas)
        canvas_group.setLayout(canvas_layout)
        display_layout.addWidget(canvas_group)
        
        main_layout.addLayout(display_layout)
        
        # --- Barra de estado ---
        self.status_label = QLabel("Listo")
        self.statusBar().addWidget(self.status_label)
    
    # ================================================================
    # MÉTODOS DE ACTUALIZACIÓN DE UI
    # ================================================================
    
    def update_display_test(self):
        """Actualiza el label de la imagen Test."""
        pixels = self.processor.get_test_pixels()
        if pixels is None:
            self.image_label_test.setText("Imagen Test\n\nPresiona 'Screenshot 1' o 'Cargar en Test'")
            self.image_label_test.setPixmap(QPixmap())
            return
        
        pixmap = ImageConverter.cv_to_qpixmap(pixels)
        if pixmap:
            scaled = pixmap.scaled(
                self.image_label_test.width() - 20,
                self.image_label_test.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label_test.setPixmap(scaled)
            self.image_label_test.setText("")
    
    def update_display_canvas(self):
        """Actualiza el label de la imagen Canvas."""
        pixels = self.processor.get_canvas_pixels()
        if pixels is None:
            self.image_label_canvas.setText("Imagen Canvas\n\nPresiona 'Screenshot 2' o 'Cargar en Canvas'")
            self.image_label_canvas.setPixmap(QPixmap())
            return
        
        pixmap = ImageConverter.cv_to_qpixmap(pixels)
        if pixmap:
            scaled = pixmap.scaled(
                self.image_label_canvas.width() - 20,
                self.image_label_canvas.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label_canvas.setPixmap(scaled)
            self.image_label_canvas.setText("")
    
    # ================================================================
    # MANEJADORES DE EVENTOS
    # ================================================================
    
    def on_capture_test(self):
        """Captura screenshot y lo asigna a Test."""
        self.status_label.setText("Capturando Test...")
        
        image = self.capture.capture()
        if image is not None:
            # Asignar al procesador con metadatos
            self.processor.set_test_image(
                pixels=image,
                titulo="Test Screenshot",
                descripcion="Captura del botón Test"
            )
            self.update_display_test()
            self.status_label.setText("Screenshot Test capturado")
        else:
            QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla")
            self.status_label.setText("Error al capturar Test")
    
    def on_capture_canvas(self):
        """Captura screenshot y lo asigna a Canvas."""
        self.status_label.setText("Capturando Canvas...")
        
        image = self.capture.capture()
        if image is not None:
            # Asignar al procesador con metadatos
            self.processor.set_canvas_image(
                pixels=image,
                titulo="Canvas Screenshot",
                descripcion="Captura del botón Canvas"
            )
            self.update_display_canvas()
            self.status_label.setText("Screenshot Canvas capturado")
        else:
            QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla")
            self.status_label.setText("Error al capturar Canvas")
    
    def on_load_image(self, target):
        """
        Carga una imagen desde disco y la asigna a Test o Canvas.
        
        Args:
            target: 'test' o 'canvas'
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if not file_path:
            return
        
        self.status_label.setText(f"Cargando en {target}...")
        
        image = cv2.imread(file_path)
        if image is None:
            QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
            self.status_label.setText("Error al cargar")
            return
        
        if target == "test":
            self.processor.set_test_image(
                pixels=image,
                titulo="Cargada",
                descripcion=f"Archivo: {file_path}",
                ruta=file_path
            )
            self.update_display_test()
        else:  # canvas
            self.processor.set_canvas_image(
                pixels=image,
                titulo="Cargada",
                descripcion=f"Archivo: {file_path}",
                ruta=file_path
            )
            self.update_display_canvas()
        
        self.status_label.setText(f"Imagen cargada en {target}")
    
    def on_save(self):
        """Guarda la imagen seleccionada (Test o Canvas)."""
        # Verificar si hay al menos una imagen
        has_test = self.processor.get_test_pixels() is not None
        has_canvas = self.processor.get_canvas_pixels() is not None
        
        if not has_test and not has_canvas:
            QMessageBox.warning(self, "Aviso", "No hay imágenes para guardar")
            return
        
        # Preguntar cuál guardar
        if has_test and has_canvas:
            reply = QMessageBox.question(
                self, "Guardar Imagen",
                "¿Qué imagen quieres guardar?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                target = "test"
            elif reply == QMessageBox.No:
                target = "canvas"
            else:
                return
        elif has_test:
            target = "test"
        else:
            target = "canvas"
        
        # Obtener los píxeles
        if target == "test":
            pixels = self.processor.get_test_pixels()
            default_name = "test_screenshot.png"
        else:
            pixels = self.processor.get_canvas_pixels()
            default_name = "canvas_screenshot.png"
        
        # Diálogo para guardar
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Imagen", default_name,
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        
        if file_path:
            cv2.imwrite(file_path, pixels)
            QMessageBox.information(self, "Éxito", f"Imagen guardada en:\n{file_path}")
            self.status_label.setText(f"Imagen guardada: {file_path}")
    
    def on_clear_all(self):
        """Limpia ambas imágenes."""
        self.processor.reset_all()
        self.update_display_test()
        self.update_display_canvas()
        self.status_label.setText("Imágenes limpiadas")
    
    def on_show_info(self):
        """Muestra información de ambas imágenes."""
        test_meta = self.processor.get_test_metadata()
        canvas_meta = self.processor.get_canvas_metadata()
        
        message = ""
        
        # Info de Test
        if test_meta['pixels'] is not None:
            info = self.processor.get_image_info(test_meta['pixels'])
            if info:
                message += "📸 IMAGEN TEST:\n"
                message += f"  Título: {test_meta['titulo']}\n"
                message += f"  Fecha: {test_meta['fecha']}\n"
                message += f"  Dimensiones: {info['dimensions']}\n"
                message += f"  Canales: {info['channels']}\n"
                message += f"  Memoria: {info['memory_size']}\n"
        else:
            message += "📸 IMAGEN TEST: (vacía)\n"
        
        message += "\n" + "-"*40 + "\n"
        
        # Info de Canvas
        if canvas_meta['pixels'] is not None:
            info = self.processor.get_image_info(canvas_meta['pixels'])
            if info:
                message += "🖼️ IMAGEN CANVAS:\n"
                message += f"  Título: {canvas_meta['titulo']}\n"
                message += f"  Fecha: {canvas_meta['fecha']}\n"
                message += f"  Dimensiones: {info['dimensions']}\n"
                message += f"  Canales: {info['channels']}\n"
                message += f"  Memoria: {info['memory_size']}\n"
        else:
            message += "🖼️ IMAGEN CANVAS: (vacía)\n"
        
        QMessageBox.information(self, "Información de Imágenes", message)
    
    # ================================================================
    # MÉTODOS PARA REDIMENSIONAR (opcional, mejora experiencia)
    # ================================================================
    
    def resizeEvent(self, event):
        """Cuando se redimensiona la ventana, actualizar las imágenes."""
        super().resizeEvent(event)
        # Actualizar ambas para que se ajusten al nuevo tamaño
        if self.processor.get_test_pixels() is not None:
            self.update_display_test()
        if self.processor.get_canvas_pixels() is not None:
            self.update_display_canvas()