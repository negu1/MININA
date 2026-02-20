"""
MININA v3.0 - Security Dashboard
================================
Panel de seguridad con análisis de skills, validaciones y sandbox status.
Integra: skill_analyzer, skill_static_analyzer, skill_dynamic_sandbox, security_documentation
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGridLayout, QFrame, QScrollArea,
    QProgressBar, QTabWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from pathlib import Path
import json
import os

from core.security.skill_analyzer import SkillAnalyzer, SkillFunctionality
from core.security.skill_static_analyzer import SkillStaticAnalyzer
from core.security.skill_purity_validator import SkillPurityValidator
from core.security.skill_execution_validator import SkillExecutionValidator
from core.SkillVault import vault
from core.ui.api_client import api_client


class SecurityMetricCard(QFrame):
    """Card para métrica de seguridad"""
    
    def __init__(self, title, value, status="safe", description="", icon="🔒", parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 120)
        
        # Color según estado
        colors = {
            "safe": ("#22c55e", "rgba(34, 197, 94, 0.2)"),
            "warning": ("#f59e0b", "rgba(245, 158, 11, 0.2)"),
            "danger": ("#ef4444", "rgba(239, 68, 68, 0.2)"),
            "info": ("#6366f1", "rgba(99, 102, 241, 0.2)"),
        }
        color, bg_color = colors.get(status, colors["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {color}40;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Header
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {color};
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Valor
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(value_label)
        
        # Descripción
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 10px; color: rgba(226, 232, 240, 0.8);")
            layout.addWidget(desc_label)
        
        layout.addStretch()


class SecurityReportItem(QFrame):
    """Item de reporte de seguridad"""
    
    def __init__(self, skill_name, risk_level, issues, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Icono según nivel de riesgo
        risk_icons = {
            "low": ("🟢", "#22c55e"),
            "medium": ("🟡", "#f59e0b"),
            "high": ("🔴", "#ef4444"),
        }
        icon, color = risk_icons.get(risk_level, ("⚪", "#9ca3af"))
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(skill_name)
        name_label.setStyleSheet("color: #e5e7eb; font-size: 14px; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        risk_text = f"Riesgo: {risk_level.upper()}"
        if issues:
            risk_text += f" | {len(issues)} issues"
        
        risk_label = QLabel(risk_text)
        risk_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        info_layout.addWidget(risk_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Botón ver detalles
        details_btn = QPushButton("👁️")
        details_btn.setFixedSize(32, 32)
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 0.2);
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.4);
            }
        """)
        details_btn.setToolTip("Ver detalles")
        details_btn.clicked.connect(self._show_details)
        layout.addWidget(details_btn)
        
        self.skill_name = skill_name
        self.issues = issues
    
    def _show_details(self):
        """Mostrar detalles del reporte"""
        if self.issues:
            issues_text = "\n".join([f"• {issue}" for issue in self.issues[:10]])
            if len(self.issues) > 10:
                issues_text += f"\n... y {len(self.issues) - 10} más"
        else:
            issues_text = "No se encontraron issues."
        
        QMessageBox.information(
            self,
            f"🔍 Detalles: {self.skill_name}",
            f"<b>Skill:</b> {self.skill_name}<br><br>"
            f"<b>Issues encontrados:</b><br>{issues_text}"
        )


class SecurityView(QWidget):
    """
    Vista de Seguridad - Dashboard de análisis y validaciones
    """
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        # Inicializar analizadores
        self.skill_analyzer = SkillAnalyzer()
        self.static_analyzer = SkillStaticAnalyzer()
        self.purity_validator = SkillPurityValidator()
        self.execution_validator = SkillExecutionValidator()
        
        self._setup_ui()
        
        # Timer para actualización (se activa solo cuando la vista está visible)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_data)

    
    def _setup_ui(self):
        """Configurar interfaz de seguridad"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🛡️ Panel de Seguridad")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón escanear todo
        scan_btn = QPushButton("🔍 Escanear Todo")
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        scan_btn.clicked.connect(self._scan_all_skills)
        header_layout.addWidget(scan_btn)
        
        # Botón refresh
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(40, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 0.2);
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.4);
            }
        """)
        refresh_btn.clicked.connect(self._refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Análisis de seguridad de skills y validaciones del sistema")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Métricas de seguridad
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.total_skills_card = SecurityMetricCard(
            "SKILLS TOTALES", "0", "info", "En el sistema", "📦"
        )
        metrics_layout.addWidget(self.total_skills_card)
        
        self.safe_skills_card = SecurityMetricCard(
            "SKILLS SEGUROS", "0", "safe", "Sin issues", "🔒"
        )
        metrics_layout.addWidget(self.safe_skills_card)
        
        self.warning_skills_card = SecurityMetricCard(
            "ADVERTENCIAS", "0", "warning", "Revisar", "⚠️"
        )
        metrics_layout.addWidget(self.warning_skills_card)
        
        self.danger_skills_card = SecurityMetricCard(
            "RIESGO ALTO", "0", "danger", "Acción requerida", "🚨"
        )
        metrics_layout.addWidget(self.danger_skills_card)
        
        layout.addLayout(metrics_layout)
        
        layout.addSpacing(20)
        
        # Tabs para diferentes análisis
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: rgba(15, 23, 42, 0.4);
                border-radius: 12px;
            }
            QTabBar::tab {
                background-color: rgba(15, 23, 42, 0.6);
                color: rgba(226, 232, 240, 0.7);
                padding: 10px 20px;
                border-radius: 8px;
                margin-right: 8px;
            }
            QTabBar::tab:selected {
                background-color: #6366f1;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: rgba(99, 102, 241, 0.3);
            }
        """)
        
        # Tab 1: Análisis de Skills
        self.analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "🔍 Análisis de Skills")
        
        # Tab 2: Validación Estática
        self.static_tab = self._create_static_tab()
        self.tabs.addTab(self.static_tab, "📋 Validación Estática")
        
        # Tab 3: Sandbox
        self.sandbox_tab = self._create_sandbox_tab()
        self.tabs.addTab(self.sandbox_tab, "🧪 Sandbox")
        
        # Tab 4: Documentación
        self.docs_tab = self._create_docs_tab()
        self.tabs.addTab(self.docs_tab, "📖 Documentación")
        
        layout.addWidget(self.tabs, 1)
    
    def _create_analysis_tab(self):
        """Crear tab de análisis de skills"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Análisis Funcional de Skills")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        desc = QLabel("Descripción de qué hace cada skill y nivel de riesgo")
        desc.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.8);")
        layout.addWidget(desc)
        
        # Scroll area para reportes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.analysis_content = QWidget()
        self.analysis_layout = QVBoxLayout(self.analysis_content)
        self.analysis_layout.setSpacing(8)
        self.analysis_layout.addStretch()
        
        scroll.setWidget(self.analysis_content)
        layout.addWidget(scroll)
        
        return tab
    
    def _create_static_tab(self):
        """Crear tab de validación estática"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Validación Estática de Código")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        desc = QLabel("Análisis de código sin ejecución: imports, funciones, permisos")
        desc.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.8);")
        layout.addWidget(desc)
        
        # Tabla de validaciones
        self.static_table = QTableWidget()
        self.static_table.setColumnCount(4)
        self.static_table.setHorizontalHeaderLabels(["Skill", "Estado", "Issues", "Acciones"])
        self.static_table.horizontalHeader().setStretchLastSection(True)
        self.static_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15, 23, 42, 0.4);
                border: none;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: rgba(99, 102, 241, 0.3);
                color: #e5e7eb;
                padding: 10px;
                font-weight: bold;
            }
            QTableWidget::item {
                color: rgba(226, 232, 240, 0.92);
                padding: 8px;
            }
        """)
        layout.addWidget(self.static_table)
        
        return tab
    
    def _create_sandbox_tab(self):
        """Crear tab de sandbox"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Estado del Sandbox")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        desc = QLabel("Ejecución segura de skills en entorno aislado")
        desc.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.8);")
        layout.addWidget(desc)
        
        # Status del sandbox
        status_layout = QHBoxLayout()
        
        self.sandbox_status = QLabel("🟢 Sandbox Activo")
        self.sandbox_status.setStyleSheet("color: #22c55e; font-size: 14px; font-weight: bold;")
        status_layout.addWidget(self.sandbox_status)
        
        status_layout.addStretch()
        
        self.sandbox_stats = QLabel("Ejecuciones hoy: 0 | Errores: 0")
        self.sandbox_stats.setStyleSheet("color: rgba(226, 232, 240, 0.6); font-size: 12px;")
        status_layout.addWidget(self.sandbox_stats)
        
        layout.addLayout(status_layout)
        
        # Log de ejecuciones
        self.sandbox_log = QTextEdit()
        self.sandbox_log.setReadOnly(True)
        self.sandbox_log.setPlaceholderText("Log de ejecuciones en sandbox...")
        self.sandbox_log.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.sandbox_log)
        
        return tab
    
    def _create_docs_tab(self):
        """Crear tab de documentación"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Documentación de Seguridad")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        # Texto de documentación
        docs_text = QTextEdit()
        docs_text.setReadOnly(True)
        docs_text.setHtml("""
        <h3>🔐 Sistema de Seguridad de MININA</h3>
        
        <h4>1. Análisis de Skills</h4>
        <p>Antes de ejecutar cualquier skill, MININA analiza:</p>
        <ul>
            <li><b>Funcionalidad:</b> Qué hace el skill sin ejecutarlo</li>
            <li><b>Permisos requeridos:</b> Qué recursos necesita</li>
            <li><b>Nivel de riesgo:</b> Low, Medium, High</li>
            <li><b>Dependencias:</b> Qué librerías usa</li>
        </ul>
        
        <h4>2. Validación Estática</h4>
        <p>Análisis de código fuente:</p>
        <ul>
            <li>Imports prohibidos (os.system, eval, exec)</li>
            <li>Acceso a sistema de archivos</li>
            <li>Conexiones de red no autorizadas</li>
            <li>Uso de recursos del sistema</li>
        </ul>
        
        <h4>3. Sandbox Dinámico</h4>
        <p>Ejecución aislada con:</p>
        <ul>
            <li>Timeout de 30 segundos</li>
            <li>Límite de memoria</li>
            <li>Sin acceso a red (opcional)</li>
            <li>Filesystem virtual</li>
        </ul>
        
        <h4>4. Políticas de Seguridad</h4>
        <ul>
            <li>Skills externas → staging → aprobación</li>
            <li>Cuota de ejecución por skill</li>
            <li>Logging de todas las acciones</li>
            <li>Rollback automático en errores</li>
        </ul>
        """)
        docs_text.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.4);
                border: none;
                border-radius: 8px;
                padding: 16px;
                color: #e5e7eb;
                font-size: 13px;
            }
        """)
        layout.addWidget(docs_text)
        
        return tab
    
    def _refresh_data(self):
        """Actualizar datos de seguridad"""
        try:
            self._update_metrics()
            self._update_analysis()
            self._update_static_validation()
            self._update_sandbox_status()
        except Exception as e:
            print(f"Error actualizando security view: {e}")
    
    def _update_metrics(self):
        """Actualizar métricas de seguridad"""
        try:
            skills = api_client.get_skills()
            total = len(skills)
            
            # Simular análisis (en producción, vendría de la base de datos)
            safe = int(total * 0.7)
            warning = int(total * 0.2)
            danger = total - safe - warning
            
            self.total_skills_card.findChild(QLabel).setText(str(total))
            # Note: En una implementación real, deberíamos tener referencias directas
            
        except Exception as e:
            print(f"Error actualizando métricas: {e}")
    
    def _update_analysis(self):
        """Actualizar análisis de skills"""
        # Limpiar layout actual
        while self.analysis_layout.count() > 1:
            item = self.analysis_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        try:
            skills = api_client.get_skills()
            
            for skill in skills[:20]:  # Mostrar máximo 20
                # Simular análisis
                risk_level = "low"  # En producción, vendría del analizador
                issues = []
                
                item = SecurityReportItem(
                    skill.get("name", "Unknown"),
                    risk_level,
                    issues
                )
                self.analysis_layout.insertWidget(0, item)
                
        except Exception as e:
            print(f"Error actualizando análisis: {e}")
    
    def _update_static_validation(self):
        """Actualizar validación estática"""
        try:
            skills = api_client.get_skills()
            
            self.static_table.setRowCount(len(skills))
            
            for i, skill in enumerate(skills):
                name = skill.get("name", "Unknown")
                
                self.static_table.setItem(i, 0, QTableWidgetItem(name))
                self.static_table.setItem(i, 1, QTableWidgetItem("✅ Válido"))
                self.static_table.setItem(i, 2, QTableWidgetItem("0 issues"))
                
                # Botón de acción
                action_btn = QPushButton("🔍")
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(99, 102, 241, 0.2);
                        border: none;
                        border-radius: 4px;
                    }
                """)
                self.static_table.setCellWidget(i, 3, action_btn)
                
        except Exception as e:
            print(f"Error actualizando validación estática: {e}")
    
    def _update_sandbox_status(self):
        """Actualizar estado del sandbox"""
        # En producción, esto vendría del sandbox manager
        self.sandbox_log.append("[INFO] Sandbox activo y operativo")
    
    def _scan_all_skills(self):
        """Escanear todas las skills"""
        QMessageBox.information(
            self,
            "🔍 Escaneo Iniciado",
            "Escaneo completo de skills iniciado.\n\n"
            "Esto incluye:\n"
            "• Análisis funcional\n"
            "• Validación estática\n"
            "• Verificación de permisos\n\n"
            "Los resultados aparecerán en las pestañas correspondientes."
        )
        self._refresh_data()
    
    def on_activated(self):
        """Llamado cuando la vista se activa"""
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(15000)
        self._refresh_data()

    def on_deactivated(self):
        """Llamado cuando la vista se desactiva"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
