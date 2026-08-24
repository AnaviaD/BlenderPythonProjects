from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, 
                            QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from core.screenshot_capture import ScreenshotCapture
from core.image_processor import ImageProcessor
import cv2
import os

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self):
        """Constructor de la ventana principal."""
        super().__init__()
        
        # Inicializar componentes
        self.screenshot_capture = ScreenshotCapture()
        self.image_processor = ImageProcessor()
        self.current_image = None
        
        # Configurar la ventana
        self.setWindowTitle("Screenshot Processor")
        self.setGeometry(100, 100, 800, 600)  # x, y, width, height
        
        # Crear la interfaz
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura todos los elementos de la interfaz."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal (vertical)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # --- Botones de control ---
        button_layout = QHBoxLayout()
        
        self.btn_capture = QPushButton("📸 Tomar Screenshot")
        self.btn_capture.clicked.connect(self.on_capture_clicked)
        button_layout.addWidget(self.btn_capture)
        
        self.btn_load = QPushButton("📂 Cargar Imagen")
        self.btn_load.clicked.connect(self.on_load_clicked)
        button_layout.addWidget(self.btn_load)
        
        self.btn_save = QPushButton("💾 Guardar Imagen")
        self.btn_save.clicked.connect(self.on_save_clicked)
        button_layout.addWidget(self.btn_save)
        
        self.btn_reset = QPushButton("🔄 Resetear")
        self.btn_reset.clicked.connect(self.on_reset_clicked)
        button_layout.addWidget(self.btn_reset)
        
        main_layout.addLayout(button_layout)
        
        # --- Panel de procesamiento ---
        processor_layout = QHBoxLayout()
        
        # Grupo de efectos
        effects_group = QGroupBox("Efectos")
        effects_layout = QVBoxLayout()
        
        self.btn_grayscale = QPushButton("Escala de Grises")
        self.btn_grayscale.clicked.connect(lambda: self.apply_effect("grayscale"))
        effects_layout.addWidget(self.btn_grayscale)
        
        self.btn_blur = QPushButton("Desenfocar")
        self.btn_blur.clicked.connect(lambda: self.apply_effect("blur"))
        effects_layout.addWidget(self.btn_blur)
        
        self.btn_edges = QPushButton("Detectar Bordes")
        self.btn_edges.clicked.connect(lambda: self.apply_effect("edges"))
        effects_layout.addWidget(self.btn_edges)
        
        self.btn_negative = QPushButton("Negativo")
        self.btn_negative.clicked.connect(lambda: self.apply_effect("negative"))
        effects_layout.addWidget(self.btn_negative)
        
        self.btn_sepia = QPushButton("Sepia")
        self.btn_sepia.clicked.connect(lambda: self.apply_effect("sepia"))
        effects_layout.addWidget(self.btn_sepia)
        
        self.btn_cartoon = QPushButton("Cartoon")
        self.btn_cartoon.clicked.connect(lambda: self.apply_effect("cartoon"))
        effects_layout.addWidget(self.btn_cartoon)
        
        effects_group.setLayout(effects_layout)
        processor_layout.addWidget(effects_group)
        
        # --- Área de visualización de imagen ---
        display_group = QGroupBox("Vista Previa")
        display_layout = QVBoxLayout()
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("""
            border: 2px solid #cccccc;
            background-color: #f0f0f0;
        """)
        self.image_label.setText("No hay imagen cargada")
        display_layout.addWidget(self.image_label)
        
        display_group.setLayout(display_layout)
        processor_layout.addWidget(display_group)
        
        main_layout.addLayout(processor_layout)
        
        # --- Barra de estado ---
        self.status_label = QLabel("Listo")
        self.statusBar().addWidget(self.status_label)
        
    def display_image(self, cv_image):
        """Muestra una imagen de OpenCV en el QLabel."""
        if cv_image is None:
            self.image_label.setText("No hay imagen para mostrar")
            return
            
        try:
            # Convertir OpenCV (BGR) a QPixmap
            if len(cv_image.shape) == 2:  # Imagen en escala de grises
                height, width = cv_image.shape
                bytes_per_line = width
                qt_image = QImage(cv_image.data, width, height, 
                                bytes_per_line, QImage.Format_Grayscale8)
            else:  # Imagen a color (BGR)
                height, width, channel = cv_image.shape
                bytes_per_line = 3 * width
                # Convertir BGR a RGB
                rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
                qt_image = QImage(rgb_image.data, width, height, 
                                bytes_per_line, QImage.Format_RGB888)
            
            # Escalar para ajustarse al label manteniendo aspecto
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.image_label.width() - 10,
                self.image_label.height() - 10,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("")  # Limpiar texto de placeholder
            
        except Exception as e:
            self.image_label.setText(f"Error al mostrar imagen: {str(e)}")
    
    def on_capture_clicked(self):
        """Manejador del botón de captura de pantalla."""
        try:
            self.status_label.setText("Capturando pantalla...")
            # Capturar la pantalla
            img = self.screenshot_capture.capture_fullscreen()
            
            if img is not None:
                self.current_image = img
                self.display_image(img)
                self.status_label.setText("Screenshot capturado exitosamente")
            else:
                QMessageBox.warning(self, "Error", 
                                   "No se pudo capturar la pantalla")
                self.status_label.setText("Error al capturar")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al capturar: {str(e)}")
            self.status_label.setText("Error en captura")
    
    def on_load_clicked(self):
        """Manejador del botón de cargar imagen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen", "", 
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            try:
                self.status_label.setText(f"Cargando {os.path.basename(file_path)}...")
                img = cv2.imread(file_path)
                if img is not None:
                    self.current_image = img
                    self.display_image(img)
                    self.status_label.setText("Imagen cargada exitosamente")
                else:
                    QMessageBox.warning(self, "Error", 
                                      "No se pudo cargar la imagen")
                    self.status_label.setText("Error al cargar")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error: {str(e)}")
                self.status_label.setText("Error en carga")
    
    def on_save_clicked(self):
        """Manejador del botón de guardar imagen."""
        if self.current_image is None:
            QMessageBox.warning(self, "Aviso", 
                              "No hay imagen para guardar")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Imagen", "screenshot.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        
        if file_path:
            try:
                cv2.imwrite(file_path, self.current_image)
                QMessageBox.information(self, "Éxito", 
                                      f"Imagen guardada en:\n{file_path}")
                self.status_label.setText(f"Imagen guardada en {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")
                self.status_label.setText("Error al guardar")
    
    def on_reset_clicked(self):
        """Restablece la imagen a la original (última captura o cargada)."""
        if self.screenshot_capture.last_screenshot is not None:
            self.current_image = self.screenshot_capture.last_screenshot.copy()
            self.display_image(self.current_image)
            self.status_label.setText("Imagen restablecida")
        else:
            self.image_label.setText("No hay imagen para restablecer")
            self.status_label.setText("Sin imagen original")
    
    def apply_effect(self, effect_type):
        """Aplica un efecto a la imagen actual."""
        if self.current_image is None:
            QMessageBox.warning(self, "Aviso", 
                              "Primero carga o captura una imagen")
            return
            
        try:
            self.status_label.setText(f"Aplicando efecto: {effect_type}...")
            
            if effect_type == "grayscale":
                result = self.image_processor.to_grayscale(self.current_image)
            elif effect_type == "blur":
                result = self.image_processor.apply_blur(self.current_image)
            elif effect_type == "edges":
                result = self.image_processor.detect_edges(self.current_image)
            elif effect_type in ["negative", "sepia", "cartoon"]:
                result = self.image_processor.apply_effect(self.current_image, effect_type)
            else:
                result = self.current_image
            
            if result is not None:
                self.current_image = result
                self.display_image(result)
                self.status_label.setText(f"Efecto '{effect_type}' aplicado")
            else:
                self.status_label.setText(f"Error al aplicar '{effect_type}'")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al aplicar efecto: {str(e)}")
            self.status_label.setText("Error en efecto")