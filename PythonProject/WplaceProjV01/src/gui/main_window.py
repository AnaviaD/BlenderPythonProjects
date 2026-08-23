"""
Ventana principal de la aplicación - Búsqueda por Color Exacto.
Versión CORREGIDA con nombres consistentes.
"""

import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QMessageBox,
    QApplication, QProgressBar, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from src.core.screen_capture import ScreenCapture
from src.core.color_matcher import ColorMatcher
from src.core.click_executor import ClickExecutor
from src.gui.area_selector import select_area_interactive
from src.utils.logger import logger



class ClickWorker(QThread):
    """Thread para ejecutar clics sin bloquear la GUI"""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, positions, cooldown):
        super().__init__()
        self.positions = positions
        self.cooldown = cooldown
        self.executor = ClickExecutor()
    
    def run(self):
        try:
            self.executor.execute_clicks(self.positions, self.cooldown)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class AnalyzeWorker(QThread):
    """Thread para ejecutar el análisis sin bloquear la GUI"""
    finished = pyqtSignal(list)  # Emite las posiciones encontradas
    error = pyqtSignal(str)
    progress = pyqtSignal(str)   # Para actualizar el estado
    
    def __init__(self, color_matcher, image, selected_area):
        super().__init__()
        self.color_matcher = color_matcher
        self.image = image
        self.selected_area = selected_area
    
    def run(self):
        try:
            self.progress.emit("🔍 Buscando color exacto...")
            
            # Buscar el color exacto (con clustering)
            positions = self.color_matcher.find_exact_color(self.image)
            
            # Ajustar coordenadas al área seleccionada
            offset_x = self.selected_area['left']
            offset_y = self.selected_area['top']
            
            result = [(x + offset_x, y + offset_y) for x, y in positions]
            
            self.progress.emit(f"✅ Encontrados {len(result)} objetivos")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Ventana principal - Búsqueda por Color Exacto"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar componentes
        self.capture = ScreenCapture()
        self.color_matcher = ColorMatcher()
        
        # Variables de estado
        self.target_color = None
        self.selected_area = None
        self.found_positions = []
        self.is_running = False
        self.analyze_worker = None
        self.analysis_timer = None  # ← ESTA LÍNEA DEBE ESTAR
        
        # Configurar UI
        self.setup_ui()
        logger.info("MainWindow inicializada - Modo Color Exacto")




    def on_analysis_progress(self, message: str):
        """Actualiza el progreso del análisis"""
        self.log_info(message)
        self.label_analysis_results.setText(f"🟡 {message}")

    def on_analysis_finished(self, positions: list):
        """Callback cuando el análisis termina exitosamente"""
        # Detener el timer de timeout
        if hasattr(self, 'analysis_timer') and self.analysis_timer:
            self.analysis_timer.stop()
            self.analysis_timer = None
        
        self.found_positions = positions
        
        # Mostrar resultados
        count = len(self.found_positions)
        
        self.label_analysis_results.setText(
            f"✅ Encontrados: {count} objetivos únicos"
        )
        self.label_analysis_results.setStyleSheet(
            "color: #4CAF50; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        
        self.log_success(f"✅ {count} objetivos únicos encontrados")
        
        # Habilitar botones
        self.btn_analyze.setEnabled(True)
        self.btn_select_area.setEnabled(True)
        self.btn_pick_color.setEnabled(True)
        
        # Habilitar ejecución si hay resultados
        self.update_ui_state()
        
        # Mensaje de éxito
        if count > 0:
            QMessageBox.information(
                self,
                "Análisis Completado",
                f"✅ Se encontraron {count} objetivos únicos.\n\n"
                f"Ahora puedes ejecutar los clics."
            )
        else:
            QMessageBox.information(
                self,
                "Análisis Completado",
                f"⚠️ No se encontraron objetivos con el color seleccionado.\n\n"
                f"Verifica que el color sea correcto."
            )


    def on_analysis_error(self, error_msg: str):
        """Callback cuando hay error en el análisis"""
        # Detener el timer de timeout
        if hasattr(self, 'analysis_timer') and self.analysis_timer:
            self.analysis_timer.stop()
            self.analysis_timer = None
        
        self.log_error(f"Error en análisis: {error_msg}")
        self.label_analysis_results.setText("❌ Error en análisis")
        self.label_analysis_results.setStyleSheet(
            "color: #ff4444; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        
        # Habilitar botones
        self.btn_analyze.setEnabled(True)
        self.btn_select_area.setEnabled(True)
        self.btn_pick_color.setEnabled(True)
        
        QMessageBox.critical(self, "Error", f"Error en análisis:\n{error_msg}")


    def on_analysis_timeout(self):
        """Callback cuando el análisis toma demasiado tiempo"""
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.log_warning("⏰ El análisis está tomando mucho tiempo...")
            self.label_analysis_results.setText("⏳ Analizando... (procesando muchos píxeles)")
            
            # Preguntar si cancelar
            reply = QMessageBox.question(
                self,
                "Análisis Lento",
                "El análisis está tomando más de 30 segundos.\n\n"
                "¿Quieres cancelar y continuar con los resultados parciales?\n"
                "Selecciona 'No' para esperar.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.log_info("🛑 Análisis cancelado por el usuario")
                if self.analyze_worker:
                    self.analyze_worker.terminate()
                    self.analyze_worker.wait()
                self.on_analysis_cancelled()
            else:
                # El usuario quiere esperar, reiniciar el timer
                self.analysis_timer = QTimer()
                self.analysis_timer.setSingleShot(True)
                self.analysis_timer.timeout.connect(self.on_analysis_timeout)
                self.analysis_timer.start(30000)  # Otros 30 segundos


    def on_analysis_cancelled(self):
        """Callback cuando el análisis es cancelado"""
        # Limpiar timer
        if hasattr(self, 'analysis_timer') and self.analysis_timer:
            self.analysis_timer.stop()
            self.analysis_timer = None
        
        self.btn_analyze.setEnabled(True)
        self.btn_select_area.setEnabled(True)
        self.btn_pick_color.setEnabled(True)
        self.label_analysis_results.setText("⏹️ Análisis cancelado")
        self.label_analysis_results.setStyleSheet(
            "color: #ff8800; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        self.log_warning("⚠️ Análisis cancelado por el usuario")





    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("Pixel Automator - Búsqueda por Color Exacto")
        self.setFixedSize(600, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # Título
        title = QLabel("🎯 Pixel Automator - Búsqueda por Color Exacto")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        main_layout.addWidget(title)
        
        # ============================================================
        # PASO 1: SELECCIONAR COLOR
        # ============================================================
        group1 = QGroupBox("🎨 Paso 1: Seleccionar Color Objetivo")
        group1_layout = QVBoxLayout(group1)
        
        # Fila 1: Botón + Indicador de color
        row1 = QHBoxLayout()
        
        self.btn_pick_color = QPushButton("🎨 1. Seleccionar Color")
        self.btn_pick_color.clicked.connect(self.select_color)
        self.btn_pick_color.setMinimumHeight(40)
        row1.addWidget(self.btn_pick_color)
        
        # Indicador visual del color
        self.color_indicator = QLabel("      ")
        self.color_indicator.setFixedSize(50, 30)
        self.color_indicator.setStyleSheet("background-color: #cccccc; border: 1px solid #666; border-radius: 3px;")
        row1.addWidget(self.color_indicator)
        
        group1_layout.addLayout(row1)
        
        # Fila 2: Botón de prueba
        row2 = QHBoxLayout()
        
        self.btn_test_color = QPushButton("🧪 Probar Color")
        self.btn_test_color.clicked.connect(self.test_color)
        self.btn_test_color.setEnabled(False)
        row2.addWidget(self.btn_test_color)
        
        group1_layout.addLayout(row2)
        
        # Label de estado del color
        self.label_color_info = QLabel("⏳ Ningún color seleccionado")
        self.label_color_info.setStyleSheet("color: #666; padding: 5px;")
        group1_layout.addWidget(self.label_color_info)
        
        main_layout.addWidget(group1)
        
        # ============================================================
        # PASO 2: SELECCIONAR ÁREA
        # ============================================================
        group2 = QGroupBox("📌 Paso 2: Seleccionar Área de Búsqueda")
        group2_layout = QVBoxLayout(group2)
        
        self.btn_select_area = QPushButton("📌 2. Seleccionar Área")
        self.btn_select_area.clicked.connect(self.select_area)
        self.btn_select_area.setEnabled(False)
        self.btn_select_area.setMinimumHeight(40)
        group2_layout.addWidget(self.btn_select_area)
        
        self.label_area_info = QLabel("⏳ Ningún área seleccionada")
        self.label_area_info.setStyleSheet("color: #666; padding: 5px;")
        group2_layout.addWidget(self.label_area_info)
        
        main_layout.addWidget(group2)
        
        # ============================================================
        # PASO 3: ANALIZAR
        # ============================================================
        group3 = QGroupBox("🔍 Paso 3: Analizar y Buscar Color")
        group3_layout = QVBoxLayout(group3)
        
        self.btn_analyze = QPushButton("🔍 3. Analizar y Buscar")
        self.btn_analyze.clicked.connect(self.analyze_image)
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setMinimumHeight(40)
        group3_layout.addWidget(self.btn_analyze)
        
        self.label_analysis_results = QLabel("⏳ Esperando análisis...")
        self.label_analysis_results.setStyleSheet(
            "color: #666; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        self.label_analysis_results.setWordWrap(True)
        group3_layout.addWidget(self.label_analysis_results)
        
        main_layout.addWidget(group3)
        
        # ============================================================
        # PASO 4: EJECUTAR CLICS
        # ============================================================
        group4 = QGroupBox("🖱️ Paso 4: Ejecutar Clics")
        group4_layout = QVBoxLayout(group4)
        
        self.btn_execute = QPushButton("🖱️ 4. Ejecutar Clics")
        self.btn_execute.clicked.connect(self.execute_clicks)
        self.btn_execute.setEnabled(False)
        self.btn_execute.setMinimumHeight(40)
        self.btn_execute.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        group4_layout.addWidget(self.btn_execute)
        
        self.label_click_status = QLabel("⏳ Esperando análisis...")
        self.label_click_status.setStyleSheet("color: #666; padding: 5px;")
        group4_layout.addWidget(self.label_click_status)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group4_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(group4)
        
        # ============================================================
        # LOG DE ACTIVIDAD
        # ============================================================
        log_group = QGroupBox("📝 Log de Actividad")
        log_layout = QVBoxLayout(log_group)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setStyleSheet("font-family: monospace; font-size: 9pt;")
        log_layout.addWidget(self.info_text)
        
        main_layout.addWidget(log_group)
        
        # ============================================================
        # BOTONES DE ACCIÓN
        # ============================================================
        action_layout = QHBoxLayout()
        
        self.btn_clear = QPushButton("🗑️ Limpiar Todo")
        self.btn_clear.clicked.connect(self.clear_all)
        action_layout.addWidget(self.btn_clear)
        
        btn_exit = QPushButton("❌ Salir")
        btn_exit.clicked.connect(self.close)
        btn_exit.setStyleSheet("background-color: #ff4444; color: white;")
        action_layout.addWidget(btn_exit)
        
        main_layout.addLayout(action_layout)
        
        # Actualizar UI inicial
        self.update_ui_state()
    

    
    def update_ui_state(self):
        """Actualiza el estado de todos los botones"""
        # Estado del color - ¡USAR self.target_color!
        color_selected = self.target_color is not None
        
        # Debug: Mostrar estado del color
        logger.debug(f"🔄 update_ui_state: color_selected={color_selected}, target_color={self.target_color}")
        
        # Actualizar botones según el color
        self.btn_test_color.setEnabled(color_selected)
        self.btn_select_area.setEnabled(color_selected)  # ¡ESTA ES LA LÍNEA CLAVE!
        
        # Estado del área
        area_selected = self.selected_area is not None
        
        # Analizar: necesita color Y área
        self.btn_analyze.setEnabled(color_selected and area_selected)
        
        # Ejecutar: necesita posiciones encontradas
        self.btn_execute.setEnabled(len(self.found_positions) > 0)
        
        # Actualizar labels de estado
        if color_selected:
            hex_color = f"#{self.target_color[0]:02x}{self.target_color[1]:02x}{self.target_color[2]:02x}"
            self.label_color_info.setText(f"✅ Color: RGB{self.target_color} {hex_color}")
            self.label_color_info.setStyleSheet("color: #4CAF50; padding: 5px;")
        else:
            self.label_color_info.setText("⏳ Ningún color seleccionado")
            self.label_color_info.setStyleSheet("color: #666; padding: 5px;")
        
        if area_selected:
            self.label_area_info.setText(f"✅ {self.selected_area['width']}x{self.selected_area['height']} px")
            self.label_area_info.setStyleSheet("color: #4CAF50; padding: 5px;")
        else:
            self.label_area_info.setText("⏳ Ningún área seleccionada")
            self.label_area_info.setStyleSheet("color: #666; padding: 5px;")
        
        if len(self.found_positions) > 0:
            self.label_click_status.setText(f"✅ {len(self.found_positions)} clics listos")
            self.label_click_status.setStyleSheet("color: #4CAF50; padding: 5px;")
        else:
            self.label_click_status.setText("⏳ Esperando análisis...")
            self.label_click_status.setStyleSheet("color: #666; padding: 5px;")


    
    # ============================================================
    # MÉTODOS DE LOG
    # ============================================================
    
    def log_info(self, message: str):
        self.info_text.append(f"ℹ️ {message}")
        logger.info(message)
    
    def log_success(self, message: str):
        self.info_text.append(f"✅ {message}")
        logger.info(message)
    
    def log_error(self, message: str):
        self.info_text.append(f"❌ {message}")
        logger.error(message)
    
    def log_warning(self, message: str):
        self.info_text.append(f"⚠️ {message}")
        logger.warning(message)
    
    # ============================================================
    # MÉTODO: SELECT_COLOR
    # ============================================================
    
    def select_color(self):
        """Selecciona el color objetivo"""
        try:
            self.log_info("🎨 Seleccionando color objetivo...")
            self.btn_pick_color.setEnabled(False)
            
            # Ocultar ventana
            self.hide()
            QApplication.processEvents()
            
            # Seleccionar un área pequeña
            area = select_area_interactive(self)
            
            # Mostrar ventana
            self.show()
            self.raise_()
            
            if area is None:
                self.log_info("Selección de color cancelada")
                self.btn_pick_color.setEnabled(True)
                return
            
            # --- CAPTURAR EL ÁREA ---
            image = self.capture.capture_area(area)
            
            if image is None or image.size == 0:
                self.log_error("No se pudo capturar la imagen")
                self.btn_pick_color.setEnabled(True)
                return
            
            # --- OBTENER EL COLOR ---
            color_rgb = self.color_matcher.get_color_from_area(image, area)
            
            if color_rgb is None:
                self.log_error("No se pudo obtener el color")
                self.btn_pick_color.setEnabled(True)
                return
            
            # --- GUARDAR COLOR CON TAMAÑO DE MUESTRA ---
            # Calcular tamaño aproximado del objeto
            sample_size = min(area['width'], area['height'])
            self.target_color = color_rgb
            self.color_matcher.set_target_color(color_rgb, sample_size)
            
            # --- ACTUALIZAR UI ---
            hex_color = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
            self.color_indicator.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #666; border-radius: 3px;"
            )
            
            # Mostrar información con el tamaño estimado
            self.label_color_info.setText(
                f"✅ Color: RGB{color_rgb} {hex_color} | Tamaño estimado: {sample_size}px"
            )
            self.label_color_info.setStyleSheet("color: #4CAF50; padding: 5px;")
            
            self.log_success(f"✅ Color CAPTURADO: RGB{color_rgb}")
            self.log_success(f"📏 Tamaño de muestra: {sample_size}px (usado para clustering)")
            
            # --- HABILITAR BOTONES ---
            self.btn_pick_color.setEnabled(True)
            self.btn_test_color.setEnabled(True)
            self.btn_select_area.setEnabled(True)
            
            self.update_ui_state()
            
        except Exception as e:
            self.log_error(f"Error seleccionando color: {e}")
            self.btn_pick_color.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Error seleccionando color:\n{str(e)}")


    # ============================================================
    # MÉTODO: TEST_COLOR
    # ============================================================
    
    def test_color(self):
        """Prueba el color capturado mostrando un ejemplo visual"""
        if self.target_color is None:
            self.log_error("Primero debes seleccionar un color")
            return
        
        color_rgb = self.target_color
        hex_color = f"#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}"
        
        # Crear diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Color Capturado")
        dialog.setFixedSize(300, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Mostrar el color
        color_label = QLabel()
        color_label.setFixedSize(200, 100)
        color_label.setStyleSheet(f"background-color: {hex_color}; border: 2px solid #666;")
        color_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(color_label)
        
        # Información del color
        info_label = QLabel(
            f"RGB: {color_rgb}\n"
            f"HEX: {hex_color}\n"
            f"Encontrados: {len(self.found_positions) if self.found_positions else 'Aún no analizado'}"
        )
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Botón cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.exec_()
    
    # ============================================================
    # MÉTODO: SELECT_AREA
    # ============================================================
    
    def select_area(self):
        """Selecciona el área donde buscar el color"""
        try:
            if self.target_color is None:
                self.log_error("Primero debes seleccionar un color")
                return
            
            self.log_info("📌 Seleccionando área de búsqueda...")
            self.btn_select_area.setEnabled(False)
            
            # Ocultar ventana
            self.hide()
            QApplication.processEvents()
            
            # Seleccionar el área
            area = select_area_interactive(self)
            
            # Mostrar ventana
            self.show()
            self.raise_()
            
            if area is None:
                self.log_info("Selección de área cancelada")
                self.btn_select_area.setEnabled(True)
                return
            
            # Guardar área
            self.selected_area = area
            
            self.log_success(f"✅ Área seleccionada: {area['width']}x{area['height']} px")
            
            # Limpiar análisis anterior
            self.found_positions = []
            self.label_analysis_results.setText("⏳ Esperando análisis...")
            
            self.btn_select_area.setEnabled(True)
            self.update_ui_state()
            
        except Exception as e:
            self.log_error(f"Error seleccionando área: {e}")
            self.btn_select_area.setEnabled(True)
            QMessageBox.critical(self, "Error", f"Error seleccionando área:\n{str(e)}")
    
    # ============================================================
    # MÉTODO: ANALYZE_IMAGE
    # ============================================================
    def analyze_image(self):
        """Analiza la imagen buscando el color exacto (en hilo separado)"""
        try:
            if self.target_color is None:
                self.log_error("Primero debes seleccionar un color")
                return
            
            if self.selected_area is None:
                self.log_error("Primero debes seleccionar un área")
                return
            
            self.log_info("🔍 Iniciando análisis...")
            self.btn_analyze.setEnabled(False)
            self.btn_select_area.setEnabled(False)
            self.btn_pick_color.setEnabled(False)
            self.label_analysis_results.setText("🟡 Analizando...")
            
            # Capturar el área
            image = self.capture.capture_area(self.selected_area)
            
            if image is None or image.size == 0:
                self.log_error("No se pudo capturar la imagen")
                self.btn_analyze.setEnabled(True)
                self.btn_select_area.setEnabled(True)
                self.btn_pick_color.setEnabled(True)
                QMessageBox.critical(self, "Error", "No se pudo capturar la imagen")
                return
            
            # --- CREAR WORKER PARA ANÁLISIS ---
            self.analyze_worker = AnalyzeWorker(
                self.color_matcher,
                image,
                self.selected_area
            )
            
            # Conectar señales
            self.analyze_worker.finished.connect(self.on_analysis_finished)
            self.analyze_worker.error.connect(self.on_analysis_error)
            self.analyze_worker.progress.connect(self.on_analysis_progress)
            
            # Iniciar worker
            self.analyze_worker.start()
            
            # --- CREAR TIMER DE SEGURIDAD ---
            # Detener timer anterior si existe
            if hasattr(self, 'analysis_timer') and self.analysis_timer:
                self.analysis_timer.stop()
                self.analysis_timer = None
            
            # Crear nuevo timer
            self.analysis_timer = QTimer()
            self.analysis_timer.setSingleShot(True)
            self.analysis_timer.timeout.connect(self.on_analysis_timeout)
            self.analysis_timer.start(30000)  # 30 segundos
            
            self.log_info("⏳ Analizando en segundo plano...")
            
        except Exception as e:
            self.log_error(f"Error iniciando análisis: {e}")
            self.btn_analyze.setEnabled(True)
            self.btn_select_area.setEnabled(True)
            self.btn_pick_color.setEnabled(True)
            
            # Limpiar timer si existe
            if hasattr(self, 'analysis_timer') and self.analysis_timer:
                self.analysis_timer.stop()
                self.analysis_timer = None
            
            QMessageBox.critical(self, "Error", f"Error iniciando análisis:\n{str(e)}")


    def on_analysis_timeout(self):
        """Callback cuando el análisis toma demasiado tiempo"""
        if self.analyze_worker and self.analyze_worker.isRunning():
            self.log_warning("⏰ El análisis está tomando mucho tiempo...")
            self.label_analysis_results.setText("⏳ Analizando... (procesando muchos píxeles)")
            
            # Preguntar si cancelar
            reply = QMessageBox.question(
                self,
                "Análisis Lento",
                "El análisis está tomando más de 30 segundos.\n\n"
                "¿Quieres cancelar y continuar con los resultados parciales?\n"
                "Selecciona 'No' para esperar.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.log_info("🛑 Análisis cancelado por el usuario")
                self.analyze_worker.terminate()
                self.analyze_worker.wait()
                self.on_analysis_cancelled()

    def on_analysis_cancelled(self):
        """Callback cuando el análisis es cancelado"""
        self.btn_analyze.setEnabled(True)
        self.btn_select_area.setEnabled(True)
        self.btn_pick_color.setEnabled(True)
        self.label_analysis_results.setText("⏹️ Análisis cancelado")
        self.label_analysis_results.setStyleSheet(
            "color: #ff8800; padding: 5px; background-color: #f0f0f0; border-radius: 3px;"
        )
        self.log_warning("⚠️ Análisis cancelado por el usuario")


    # ============================================================
    # MÉTODO: EXECUTE_CLICKS
    # ============================================================
    
    def execute_clicks(self):
        """Ejecuta los clics en las posiciones encontradas"""
        try:
            if not self.found_positions:
                self.log_warning("No hay posiciones para hacer clic")
                return
            
            count = len(self.found_positions)
            time_ms = count * 1.5
            time_sec = time_ms / 1000
            
            # Confirmación
            reply = QMessageBox.question(
                self,
                "Confirmar",
                f"📋 ¿Ejecutar {count} clics?\n\n"
                f"⏱️ Tiempo estimado: {time_sec:.2f} segundos\n"
                f"⚠️ Mueve el mouse a una esquina para detener",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self.log_info(f"🖱️ Ejecutando {count} clics...")
            self.btn_execute.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, count)
            self.progress_bar.setValue(0)
            self.is_running = True
            
            # Crear thread
            self.worker = ClickWorker(self.found_positions, 5.5)
            self.worker.finished.connect(self.on_clicks_finished)
            self.worker.error.connect(self.on_clicks_error)
            self.worker.progress.connect(self.on_clicks_progress)
            self.worker.start()
            
        except Exception as e:
            self.log_error(f"Error ejecutando clics: {e}")
            self.btn_execute.setEnabled(True)
            self.progress_bar.setVisible(False)
            QMessageBox.critical(self, "Error", f"Error ejecutando clics:\n{str(e)}")
    
    # ============================================================
    # CALLBACKS DEL WORKER
    # ============================================================
    
    def on_clicks_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_clicks_finished(self):
        self.is_running = False
        self.btn_execute.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.log_success("✅ Todos los clics ejecutados correctamente")
        self.label_click_status.setText("✅ Completado")
        QMessageBox.information(self, "Completado", "Todos los clics se ejecutaron correctamente")
        self.update_ui_state()
    
    def on_clicks_error(self, error_msg):
        self.is_running = False
        self.btn_execute.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log_error(f"Error en clics: {error_msg}")
        self.label_click_status.setText("❌ Error")
        QMessageBox.critical(self, "Error", f"Error en ejecución:\n{error_msg}")
        self.update_ui_state()
    
    # ============================================================
    # MÉTODO: CLEAR_ALL
    # ============================================================
    
    def clear_all(self):
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Seguro que quieres limpiar todo?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.target_color = None
        self.selected_area = None
        self.found_positions = []
        
        self.color_indicator.setStyleSheet("background-color: #cccccc; border: 1px solid #666; border-radius: 3px;")
        self.progress_bar.setVisible(False)
        
        self.log_info("🗑️ Todo limpiado")
        self.update_ui_state()
    
    # ============================================================
    # MÉTODO: CLOSE_EVENT
    # ============================================================
    
    def closeEvent(self, event):
        if self.is_running:
            reply = QMessageBox.question(
                self,
                "Confirmar salida",
                "¿Seguro que quieres salir? Los clics están en ejecución.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        
        logger.info("Aplicación cerrada")
        event.accept()