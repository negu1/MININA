"""
MININA v3.0 - External Skills Evaluator View
UI para probar y evaluar skills externas en el Skills Studio
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTextEdit, QFrame, QScrollArea, QGridLayout,
    QMessageBox, QSplitter, QProgressBar, QGroupBox, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from core.SkillVault import vault
from core.security.skill_static_analyzer import SkillStaticAnalyzer
from core.security.skill_dynamic_sandbox import SkillDynamicSandbox
from core.security.skill_analyzer import SkillAnalyzer
from core.SkillSafetyGate import SafetyReport, SkillSafetyGate


class ExternalSkillEvaluationWorker(QThread):
    """Worker thread para evaluación de skills sin bloquear UI"""
    
    progress = pyqtSignal(str)
    static_analysis_done = pyqtSignal(dict)
    dynamic_test_done = pyqtSignal(dict)
    functional_analysis_done = pyqtSignal(dict)
    safety_validation_done = pyqtSignal(dict)
    finished_all = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, skill_path: Path, extracted_dir: Path):
        super().__init__()
        self.skill_path = skill_path
        self.extracted_dir = extracted_dir
        self.results = {}
        
    def run(self):
        try:
            # 1. Análisis de seguridad estático
            self.progress.emit("🔍 Analizando código estáticamente...")
            analyzer = SkillStaticAnalyzer()
            static_result = analyzer.analyze_directory(self.extracted_dir)
            self.results['static'] = static_result.to_dict()
            self.static_analysis_done.emit(static_result.to_dict())
            
            # 2. Análisis funcional
            self.progress.emit("📋 Analizando qué hace esta skill...")
            func_analyzer = SkillAnalyzer()
            func_result = func_analyzer.analyze_directory(self.extracted_dir)
            self.results['functional'] = func_result.to_dict()
            self.functional_analysis_done.emit(func_result.to_dict())
            
            # 3. Validación de seguridad completa
            self.progress.emit("🛡️ Validando seguridad...")
            gate = SkillSafetyGate()
            safety_result = gate.validate_extracted_dir(self.extracted_dir)
            self.results['safety'] = {
                'ok': safety_result.ok,
                'skill_id': safety_result.skill_id,
                'name': safety_result.name,
                'reasons': safety_result.reasons,
                'permissions': safety_result.permissions,
            }
            self.safety_validation_done.emit(self.results['safety'])
            
            # 4. Prueba dinámica en sandbox (solo si pasó seguridad)
            if safety_result.ok and static_result.is_safe:
                self.progress.emit("🧪 Probando en sandbox aislado...")
                sandbox = SkillDynamicSandbox()
                dynamic_result = sandbox.test_skill(
                    self.extracted_dir,
                    test_context={"test_mode": True, "skill_path": str(self.extracted_dir)}
                )
                self.results['dynamic'] = dynamic_result.to_dict()
                self.dynamic_test_done.emit(dynamic_result.to_dict())
            else:
                self.results['dynamic'] = {'skipped': True, 'reason': 'No pasó validación de seguridad'}
                self.dynamic_test_done.emit(self.results['dynamic'])
            
            self.progress.emit("✅ Evaluación completada")
            self.finished_all.emit(self.results)
            
        except Exception as e:
            self.error.emit(str(e))


class ExternalSkillsEvaluatorView(QWidget):
    """
    Vista para evaluar skills externas en el Skills Studio.
    Permite subir, analizar y aprobar/rechazar skills ajenas a MININA.
    """
    
    def __init__(self):
        super().__init__()
        self.current_skill_path: Optional[Path] = None
        self.current_extracted_dir: Optional[Path] = None
        self.evaluation_results: dict = {}
        self._worker: Optional[ExternalSkillEvaluationWorker] = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interfaz de evaluación"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Panel izquierdo: Upload y controles
        left_panel = self._create_left_panel()
        layout.addWidget(left_panel, 1)
        
        # Panel derecho: Resultados
        right_panel = self._create_right_panel()
        layout.addWidget(right_panel, 2)
        
        self.setAcceptDrops(True)
        
    def _create_left_panel(self) -> QFrame:
        """Crear panel izquierdo con upload y controles"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-radius: 12px;
                border: 2px solid #e2e8f0;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("📦 Evaluador de Skills Externas")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)
        
        # Descripción
        desc = QLabel(
            "Evalúa skills descargadas antes de usarlas en MININA.\n"
            "El sistema verifica seguridad, funcionalidad y riesgos."
        )
        desc.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        # Área de drop
        self.drop_area = QFrame()
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #e0e7ff;
                border: 3px dashed #6366f1;
                border-radius: 10px;
                min-height: 150px;
            }
        """)
        drop_layout = QVBoxLayout(self.drop_area)
        drop_label = QLabel("📁 Arrastra un ZIP aquí\no haz clic para seleccionar")
        drop_label.setAlignment(Qt.AlignCenter)
        drop_label.setStyleSheet("""
            color: #6366f1;
            font-size: 14px;
            font-weight: bold;
            background: transparent;
            border: none;
        """)
        drop_layout.addWidget(drop_label)
        self.drop_area.mousePressEvent = self._on_drop_area_clicked
        layout.addWidget(self.drop_area)
        
        # Botón seleccionar archivo
        self.select_btn = QPushButton("📂 Seleccionar archivo ZIP")
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
            }
        """)
        self.select_btn.clicked.connect(self._select_zip_file)
        layout.addWidget(self.select_btn)
        
        # Información del archivo
        self.file_info_label = QLabel("Ningún archivo seleccionado")
        self.file_info_label.setStyleSheet("""
            color: #64748b;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        self.file_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_info_label)
        
        layout.addSpacing(20)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 5px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Estado
        self.status_label = QLabel("Esperando archivo...")
        self.status_label.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addSpacing(20)
        
        # Botones de acción
        action_group = QGroupBox("Acciones")
        action_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        action_layout = QVBoxLayout(action_group)
        
        self.analyze_btn = QPushButton("🔍 Iniciar Evaluación")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
            }
        """)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.clicked.connect(self._start_evaluation)
        action_layout.addWidget(self.analyze_btn)
        
        self.approve_btn = QPushButton("✅ Aprobar y Instalar")
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
            }
        """)
        self.approve_btn.setEnabled(False)
        self.approve_btn.clicked.connect(self._approve_skill)
        action_layout.addWidget(self.approve_btn)
        
        self.reject_btn = QPushButton("❌ Rechazar y Eliminar")
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:disabled {
                background-color: #cbd5e1;
            }
        """)
        self.reject_btn.setEnabled(False)
        self.reject_btn.clicked.connect(self._reject_skill)
        action_layout.addWidget(self.reject_btn)
        
        layout.addWidget(action_group)
        
        layout.addStretch()
        
        return panel
    
    def _create_right_panel(self) -> QFrame:
        """Crear panel derecho con resultados"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
                border: 2px solid #e2e8f0;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("📊 Resultados de Evaluación")
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1e293b;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title)
        
        # Scroll area para resultados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(15)
        self.results_layout.setAlignment(Qt.AlignTop)
        
        # Placeholder
        placeholder = QLabel(
            "Los resultados de la evaluación aparecerán aquí\n"
            "una vez que completes el análisis."
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #94a3b8;
            font-size: 14px;
            background: transparent;
            border: none;
            padding: 50px;
        """)
        self.results_layout.addWidget(placeholder)
        
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll)
        
        return panel
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Permitir drag de archivos"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().endswith('.zip') for url in urls):
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Manejar drop de archivos"""
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.endswith('.zip'):
                self._load_zip_file(Path(file_path))
                break
    
    def _on_drop_area_clicked(self, event):
        """Click en área de drop"""
        self._select_zip_file()
    
    def _select_zip_file(self):
        """Abrir diálogo para seleccionar ZIP"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Skill Externa (ZIP)",
            "",
            "Archivos ZIP (*.zip)"
        )
        if file_path:
            self._load_zip_file(Path(file_path))
    
    def _load_zip_file(self, zip_path: Path):
        """Cargar archivo ZIP"""
        if not zip_path.exists():
            QMessageBox.warning(self, "Error", "El archivo no existe")
            return
        
        # Copiar a staging externo
        self.current_skill_path = vault.stage_external_zip(zip_path).zip_path
        
        # Extraer para análisis
        import zipfile
        import tempfile
        
        self.current_extracted_dir = Path(tempfile.mkdtemp(prefix="skill_eval_"))
        
        try:
            with zipfile.ZipFile(self.current_skill_path, 'r') as zf:
                zf.extractall(self.current_extracted_dir)
            
            # Actualizar UI
            self.file_info_label.setText(
                f"📦 {zip_path.name}\n"
                f"📁 Extraído en: {self.current_extracted_dir.name}"
            )
            self.status_label.setText("✅ Listo para evaluar")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.analyze_btn.setEnabled(True)
            self.drop_area.setStyleSheet("""
                QFrame {
                    background-color: #d1fae5;
                    border: 3px solid #10b981;
                    border-radius: 10px;
                    min-height: 150px;
                }
            """)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error extrayendo ZIP: {str(e)}")
    
    def _start_evaluation(self):
        """Iniciar evaluación completa"""
        if not self.current_extracted_dir:
            QMessageBox.warning(self, "Error", "No hay skill cargada")
            return
        
        self.analyze_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        
        # Limpiar resultados previos
        self._clear_results()
        
        # Iniciar worker
        self._worker = ExternalSkillEvaluationWorker(
            self.current_skill_path,
            self.current_extracted_dir
        )
        self._worker.progress.connect(self._on_evaluation_progress)
        self._worker.static_analysis_done.connect(self._on_static_analysis)
        self._worker.functional_analysis_done.connect(self._on_functional_analysis)
        self._worker.safety_validation_done.connect(self._on_safety_validation)
        self._worker.dynamic_test_done.connect(self._on_dynamic_test)
        self._worker.finished_all.connect(self._on_evaluation_finished)
        self._worker.error.connect(self._on_evaluation_error)
        self._worker.start()
    
    def _clear_results(self):
        """Limpiar resultados previos"""
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _on_evaluation_progress(self, message: str):
        """Actualizar progreso"""
        self.status_label.setText(message)
    
    def _on_static_analysis(self, result: dict):
        """Mostrar resultado de análisis estático"""
        widget = self._create_result_card(
            "🔍 Análisis Estático de Seguridad",
            result['is_safe'],
            result.get('errors', []),
            result.get('warnings', []),
            f"Permisos detectados: {', '.join(result.get('permissions_required', [])) or 'Ninguno'}"
        )
        self.results_layout.addWidget(widget)
    
    def _on_functional_analysis(self, result: dict):
        """Mostrar análisis funcional"""
        operations = result.get('operations', [])
        ops_text = '\n'.join([f"• {op.get('description', 'Operación')}" for op in operations[:5]])
        
        widget = self._create_result_card(
            "📋 Análisis Funcional",
            True,
            [],
            [],
            f"""
            <b>Nombre:</b> {result.get('name', 'Unknown')}<br>
            <b>Propósito:</b> {result.get('purpose', 'No especificado')}<br>
            <b>Nivel de riesgo:</b> {result.get('risk_level', 'unknown').upper()}<br>
            <b>Operaciones:</b><br>{ops_text or 'No detectadas'}
            """
        )
        self.results_layout.addWidget(widget)
    
    def _on_safety_validation(self, result: dict):
        """Mostrar validación de seguridad"""
        widget = self._create_result_card(
            "🛡️ Validación de Seguridad (Safety Gate)",
            result.get('ok', False),
            result.get('reasons', []),
            [],
            f"Skill ID: {result.get('skill_id', 'unknown')} | Permisos: {', '.join(result.get('permissions', []))}"
        )
        self.results_layout.addWidget(widget)
    
    def _on_dynamic_test(self, result: dict):
        """Mostrar resultado de prueba dinámica"""
        if result.get('skipped'):
            widget = self._create_result_card(
                "🧪 Prueba en Sandbox",
                None,  # Neutral
                [],
                [f"Saltado: {result.get('reason', 'No especificado')}"],
                ""
            )
        else:
            widget = self._create_result_card(
                "🧪 Prueba en Sandbox",
                result.get('success', False),
                result.get('errors', []),
                result.get('warnings', []),
                f"Tiempo: {result.get('execution_time_ms', 0)}ms"
            )
        self.results_layout.addWidget(widget)
    
    def _on_evaluation_finished(self, results: dict):
        """Evaluación completada"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        
        # Determinar si es seguro aprobar
        static_ok = results.get('static', {}).get('is_safe', False)
        safety_ok = results.get('safety', {}).get('ok', False)
        dynamic = results.get('dynamic', {})
        dynamic_ok = dynamic.get('success', False) if not dynamic.get('skipped') else True
        
        if static_ok and safety_ok and dynamic_ok:
            self.status_label.setText("✅ Skill verificada - Lista para aprobar")
            self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.approve_btn.setEnabled(True)
        else:
            self.status_label.setText("⚠️ Skill tiene problemas - Revisar rechazo")
            self.status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")
        
        self.reject_btn.setEnabled(True)
        self.evaluation_results = results
    
    def _on_evaluation_error(self, error: str):
        """Error en evaluación"""
        self.progress_bar.setVisible(False)
        self.analyze_btn.setEnabled(True)
        self.status_label.setText(f"❌ Error: {error}")
        self.status_label.setStyleSheet("color: #ef4444;")
        QMessageBox.critical(self, "Error de Evaluación", error)
    
    def _create_result_card(self, title: str, is_safe: Optional[bool], errors: list, warnings: list, details: str) -> QFrame:
        """Crear tarjeta de resultado"""
        card = QFrame()
        
        # Color según estado
        if is_safe is True:
            border_color = "#10b981"
            bg_color = "#ecfdf5"
        elif is_safe is False:
            border_color = "#ef4444"
            bg_color = "#fef2f2"
        else:
            border_color = "#f59e0b"
            bg_color = "#fffbeb"
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {border_color};
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)
        
        # Detalles
        if details:
            details_label = QLabel(details)
            details_label.setStyleSheet("""
                font-size: 12px;
                color: #1e293b;
                background: transparent;
                border: none;
            """)
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
        
        # Errores
        if errors:
            errors_text = "<br>".join([f"❌ {e}" for e in errors[:3]])
            errors_label = QLabel(errors_text)
            errors_label.setStyleSheet("""
                color: #ef4444;
                font-size: 12px;
                background: transparent;
                border: none;
            """)
            errors_label.setWordWrap(True)
            layout.addWidget(errors_label)
        
        # Warnings
        if warnings:
            warnings_text = "<br>".join([f"⚠️ {w}" for w in warnings[:3]])
            warnings_label = QLabel(warnings_text)
            warnings_label.setStyleSheet("""
                color: #f59e0b;
                font-size: 12px;
                background: transparent;
                border: none;
            """)
            warnings_label.setWordWrap(True)
            layout.addWidget(warnings_label)
        
        return card
    
    def _approve_skill(self):
        """Aprobar e instalar skill"""
        if not self.current_skill_path:
            return
        
        # Extraer skill_id del nombre del archivo
        skill_id = self.current_skill_path.stem.replace("ext_", "").split("_")[0]
        
        result = vault.approve_external_skill(skill_id)
        
        if result.get('success'):
            QMessageBox.information(
                self,
                "✅ Skill Aprobada",
                f"Skill instalada correctamente:\n{result.get('message', '')}"
            )
            self._reset_ui()
        else:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"No se pudo aprobar:\n{result.get('error', 'Error desconocido')}"
            )
    
    def _reject_skill(self):
        """Rechazar y eliminar skill"""
        if not self.current_skill_path:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Rechazo",
            "¿Estás seguro de rechazar esta skill?\nSe moverá a cuarentena.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Mover a cuarentena manual
            if self.current_extracted_dir and self.current_extracted_dir.exists():
                # Crear reporte de rechazo
                from core.SkillSafetyGate import SafetyReport
                report = SafetyReport(
                    ok=False,
                    skill_id=self.current_skill_path.stem,
                    name=self.current_skill_path.stem,
                    version="1.0",
                    permissions=[],
                    reasons=["Rechazo manual por usuario"]
                )
                vault._quarantine_external(self.current_skill_path, report)
            
            QMessageBox.information(self, "Rechazada", "Skill movida a cuarentena")
            self._reset_ui()
    
    def _reset_ui(self):
        """Resetear UI a estado inicial"""
        self.current_skill_path = None
        self.current_extracted_dir = None
        self.evaluation_results = {}
        
        self.file_info_label.setText("Ningún archivo seleccionado")
        self.status_label.setText("Esperando archivo...")
        self.status_label.setStyleSheet("color: #64748b;")
        
        self.analyze_btn.setEnabled(False)
        self.approve_btn.setEnabled(False)
        self.reject_btn.setEnabled(False)
        
        self.drop_area.setStyleSheet("""
            QFrame {
                background-color: #e0e7ff;
                border: 3px dashed #6366f1;
                border-radius: 10px;
                min-height: 150px;
            }
        """)
        
        self._clear_results()
        placeholder = QLabel(
            "Los resultados de la evaluación aparecerán aquí\n"
            "una vez que completes el análisis."
        )
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("""
            color: #94a3b8;
            font-size: 14px;
            background: transparent;
            border: none;
            padding: 50px;
        """)
        self.results_layout.addWidget(placeholder)
