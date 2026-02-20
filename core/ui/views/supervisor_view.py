"""
MININA v3.0 - Supervisor View (Capa 2)
Centro de alertas y monitoreo
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit, QFrame, QScrollArea,
    QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class SupervisorView(QWidget):
    """
    Vista del Supervisor - Centro de alertas
    Monitoreo de ejecuciones y detección de anomalías
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_alerts()
        self._load_logs()
        
    def _setup_ui(self):
        """Configurar interfaz elegante del Supervisor"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Panel izquierdo: Alertas
        left_panel = self._create_alerts_panel()
        layout.addWidget(left_panel, 1)
        
        # Panel derecho: Logs
        right_panel = self._create_logs_panel()
        layout.addWidget(right_panel, 1)
        
    def _create_alerts_panel(self) -> QWidget:
        """Crear panel de alertas - Estilo moderno"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.55);
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.16);
            }
        """)
        
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        panel.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header elegante
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🛡️")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        header_text = QLabel("Supervisor")
        header_text.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(header_text)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Centro de alertas y monitoreo")
        subtitle.setStyleSheet("""
            color: rgba(226, 232, 240, 0.72);
            font-size: 14px;
            margin-bottom: 8px;
        """)
        layout.addWidget(subtitle)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.18);")
        layout.addWidget(separator)
        
        # Filtros de alertas
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Nivel:"))
        
        self.alert_filter = QComboBox()
        self.alert_filter.addItems(["Todos", "Crítico", "Advertencia", "Info"])
        filter_layout.addWidget(self.alert_filter)
        filter_layout.addStretch()
        
        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.clicked.connect(self._clear_alerts)
        filter_layout.addWidget(self.clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Lista de alertas
        self.alerts_list = QListWidget()
        self.alerts_list.setMinimumWidth(400)
        layout.addWidget(self.alerts_list)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        
        self.ack_btn = QPushButton("✓ Reconocer")
        self.ack_btn.clicked.connect(self._acknowledge_alert)
        actions_layout.addWidget(self.ack_btn)
        
        self.resolve_btn = QPushButton("✓ Resolver")
        self.resolve_btn.clicked.connect(self._resolve_alert)
        actions_layout.addWidget(self.resolve_btn)
        
        self.details_btn = QPushButton("Ver Detalles")
        self.details_btn.clicked.connect(self._show_alert_details)
        actions_layout.addWidget(self.details_btn)
        
        layout.addLayout(actions_layout)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        self.critical_count = QLabel("🔴 0")
        self.warning_count = QLabel("🟡 0")
        self.info_count = QLabel("🔵 0")
        stats_layout.addWidget(QLabel("Alertas:"))
        stats_layout.addWidget(self.critical_count)
        stats_layout.addWidget(self.warning_count)
        stats_layout.addWidget(self.info_count)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        return panel
        
    def _create_logs_panel(self) -> QWidget:
        """Crear panel de logs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel("📋 Logs de Ejecución")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)
        
        subtitle = QLabel("Registro en tiempo real de actividad del sistema")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Filtros de logs
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Nivel:"))
        
        self.log_filter = QComboBox()
        self.log_filter.addItems(["Todos", "ERROR", "WARN", "INFO", "DEBUG"])
        filter_layout.addWidget(self.log_filter)
        filter_layout.addStretch()
        
        self.export_btn = QPushButton("📥 Exportar")
        self.export_btn.clicked.connect(self._export_logs)
        filter_layout.addWidget(self.export_btn)
        
        layout.addLayout(filter_layout)
        
        # Área de logs
        self.logs_area = QTextEdit()
        self.logs_area.setReadOnly(True)
        self.logs_area.setFont(QFont("Consolas", 10))
        self.logs_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.logs_area)
        
        # Control de logs
        control_layout = QHBoxLayout()
        
        self.pause_btn = QPushButton("⏸️ Pausar")
        self.pause_btn.setCheckable(True)
        self.pause_btn.clicked.connect(self._pause_logs)
        control_layout.addWidget(self.pause_btn)
        
        self.clear_logs_btn = QPushButton("🗑️ Limpiar")
        self.clear_logs_btn.clicked.connect(self._clear_logs)
        control_layout.addWidget(self.clear_logs_btn)
        
        self.scroll_lock_btn = QPushButton("🔒 Scroll")
        self.scroll_lock_btn.setCheckable(True)
        self.scroll_lock_btn.setChecked(True)
        control_layout.addWidget(self.scroll_lock_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        return panel
        
    def _load_alerts(self):
        """Cargar alertas de ejemplo"""
        example_alerts = [
            ("🔴 CRÍTICA", "Loop detectado en skill 'web_scraper'", "2 min ago"),
            ("🟡 ADVERTENCIA", "Skill 'reporte_ventas' tomó 10min (est: 5)", "5 min ago"),
            ("🔵 INFO", "Agente agent_001 iniciado correctamente", "10 min ago"),
            ("🔵 INFO", "Pool CPU_INTENSIVE escalado a 6 agentes", "15 min ago"),
        ]
        
        for level, message, time in example_alerts:
            item = QListWidgetItem(f"{level} - {message}\n  {time}")
            item.setData(Qt.UserRole, {"level": level, "message": message, "time": time})
            self.alerts_list.addItem(item)
            
    def _load_logs(self):
        """Cargar logs de ejemplo"""
        example_logs = [
            "[2024-02-19 10:15:32] INFO: skill_database iniciado",
            "[2024-02-19 10:15:34] INFO: skill_database completado (2s)",
            "[2024-02-19 10:15:35] WARN: skill_analysis tardando más de lo esperado",
            "[2024-02-19 10:15:40] INFO: skill_analysis completado (8s)",
            "[2024-02-19 10:15:41] ERROR: skill_reporte no pudo generar archivo",
            "[2024-02-19 10:15:45] INFO: Retrying skill_reporte (intento 2/3)",
            "[2024-02-19 10:16:00] INFO: skill_reporte completado con éxito",
        ]
        
        for log in example_logs:
            self.logs_area.append(log)
            
    def _clear_alerts(self):
        """Limpiar todas las alertas"""
        self.alerts_list.clear()
        self.critical_count.setText("🔴 0")
        self.warning_count.setText("🟡 0")
        self.info_count.setText("🔵 0")
        
    def _acknowledge_alert(self):
        """Reconocer alerta seleccionada"""
        current = self.alerts_list.currentItem()
        if current:
            # TODO: Marcar como reconocida
            pass
            
    def _resolve_alert(self):
        """Resolver alerta seleccionada"""
        current = self.alerts_list.currentItem()
        if current:
            row = self.alerts_list.row(current)
            self.alerts_list.takeItem(row)
            
    def _show_alert_details(self):
        """Mostrar detalles de alerta"""
        current = self.alerts_list.currentItem()
        if current:
            data = current.data(Qt.UserRole)
            # TODO: Mostrar diálogo con detalles
            pass
            
    def _export_logs(self):
        """Exportar logs a archivo"""
        # TODO: Implementar exportación
        pass
        
    def _pause_logs(self):
        """Pausar/reanudar actualización de logs"""
        if self.pause_btn.isChecked():
            self.pause_btn.setText("▶️ Reanudar")
        else:
            self.pause_btn.setText("⏸️ Pausar")
            
    def _clear_logs(self):
        """Limpiar área de logs"""
        self.logs_area.clear()
