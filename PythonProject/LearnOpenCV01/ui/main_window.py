import cv2
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, 
                            QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from core.screenshot_capture import ScreenshotCapture
from core.image_processor import ImageProcessor
from utils.image_converter import ImageConverter

class MainWindow(QMainWindow):
    """
    Ventana principal - SOLO SE ENCARGA DE LA UI.
    No contiene lógica de procesamiento de imágenes.
    """
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes (capa de lógica)
        self.capture = ScreenshotCapture()
        self.processor = ImageProcessor()
        
        # Configurar UI
        self.setWindowTitle("Screenshot Processor")
        self.setGeometry(100, 100, 800, 600)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --- Panel de botones ---
        button_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("📸 Tomar Screenshot")
        self.btn_capture.clicked.connect(self.on_capture)
        button_layout.addWidget(self.btn_capture)
        
        self.btn_load = QPushButton("📂 Cargar Imagen")
        self.btn_load.clicked.connect(self.on_load)
        button_layout.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("💾 Guardar Imagen")
        self.btn_save.clicked.connect(self.on_save)
        button_layout.addWidget(self.btn_save)
        
        self.btn_reset = QPushButton("🔄 Restablecer")
        self.btn_reset.clicked.connect(self.on_reset)
        button_layout.addWidget(self.btn_reset)
        
        # Botón para mostrar info de la imagen (ejemplo de uso del procesador)
        self.btn_info = QPushButton("ℹ️ Info Imagen")
        self.btn_info.clicked.connect(self.on_show_info)
        button_layout.addWidget(self.btn_info)
        
        main_layout.addLayout(button_layout)
        
        # --- Área de visualización ---
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f0f0f0;
                padding: 10px;
            }
        """)
        self.image_label.setText("No hay imagen cargada")
        main_layout.addWidget(self.image_label)
        
        # --- Barra de estado ---
        self.status_label = QLabel("Listo")
        self.statusBar().addWidget(self.status_label)
    
    def update_display(self):
        """Actualiza la visualización con la imagen actual del procesador."""
        cv_image = self.processor.get_current_image()
        
        if cv_image is None:
            self.image_label.setText("No hay imagen cargada")
            self.image_label.setPixmap(QPixmap())
            return
        
        # Convertir a QPixmap y mostrar
        pixmap = ImageConverter.cv_to_qpixmap(cv_image)
        
        if pixmap:
            # Escalar para ajustarse al label
            scaled_pixmap = pixmap.scaled(
                self.image_label.width() - 20,
                self.image_label.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")
    
    # ================================================================
    # MANEJADORES DE EVENTOS DE UI
    # Estos métodos conectan la UI con la lógica
    # ================================================================
    
    def on_capture(self):
        """Manejador del botón Capturar."""
        self.status_label.setText("Capturando pantalla...")
        
        # 1. Capturar pantalla (capa de captura)
        image = self.capture.capture()
        
        if image is not None:
            # 2. Pasar la imagen al procesador (📍 ¡AQUÍ EMPIEZA EL ANÁLISIS!)
            self.processor.set_image(image)
            
            # 3. Mostrar en UI
            self.update_display()
            self.status_label.setText("Screenshot capturado y listo para procesar")
            
            # 4. ✅ Mostrar información básica (ya usando el procesador)
            self.show_image_info()
        else:
            QMessageBox.warning(self, "Error", "No se pudo capturar la pantalla")
            self.status_label.setText("Error al capturar")
    
    def on_load(self):
        """Manejador del botón Cargar."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.status_label.setText(f"Cargando {file_path}...")
            
            # 1. Cargar imagen con OpenCV
            image = cv2.imread(file_path)
            
            if image is not None:
                # 2. Pasar al procesador (📍 ¡AQUÍ EMPIEZA EL ANÁLISIS!)
                self.processor.set_image(image)
                
                # 3. Mostrar en UI
                self.update_display()
                self.status_label.setText(f"Imagen cargada: {file_path}")
                
                # 4. ✅ Mostrar información
                self.show_image_info()
            else:
                QMessageBox.warning(self, "Error", "No se pudo cargar la imagen")
                self.status_label.setText("Error al cargar")
    
    def on_save(self):
        """Manejador del botón Guardar."""
        cv_image = self.processor.get_current_image()
        
        if cv_image is None:
            QMessageBox.warning(self, "Aviso", "No hay imagen para guardar")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Imagen", "screenshot.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        
        if file_path:
            cv2.imwrite(file_path, cv_image)
            QMessageBox.information(self, "Éxito", f"Imagen guardada en:\n{file_path}")
            self.status_label.setText(f"Imagen guardada: {file_path}")
    
    def on_reset(self):
        """Manejador del botón Restablecer."""
        self.processor.reset_to_original()
        self.update_display()
        self.status_label.setText("Imagen restablecida a la original")
    
    def on_show_info(self):
        """Manejador del botón Info - DEMOSTRACIÓN DEL PROCESADOR."""
        self.show_image_info()
    
    def show_image_info(self):
        """
        📍 DEMOSTRACIÓN DE USO DEL PROCESADOR
        Muestra información de la imagen usando el ImageProcessor.
        """
        info = self.processor.get_image_info()
        
        if info:
            message = (
                f"📐 Dimensiones: {info['dimensions']}\n"
                f"🎨 Canales: {info['channels']}\n"
                f"📦 Tipo de dato: {info['dtype']}\n"
                f"🔢 Píxeles totales: {info['total_pixels']:,}\n"
                f"💾 Memoria: {info['memory_size']}"
            )
            
            # También calcular estadísticas
            stats = self.processor.calculate_statistics()
            if stats:
                message += f"\n\n📊 Estadísticas:\n"
                message += f"  Media: {stats['mean']:.2f}\n"
                message += f"  Desviación: {stats['std']:.2f}\n"
                message += f"  Mínimo: {stats['min']:.0f}\n"
                message += f"  Máximo: {stats['max']:.0f}"
            
            QMessageBox.information(self, "Información de la Imagen", message)
        else:
            QMessageBox.warning(self, "Aviso", "No hay imagen cargada")