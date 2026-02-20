"""
MININA v3.0 - Supervisor View (Capa 2)
Centro de alertas y monitoreo
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QTextEdit, QFrame, QScrollArea,
    QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog
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
        
        # Botón de Ayuda
        self.help_btn = QPushButton("❓ Ayuda")
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        self.help_btn.setToolTip("Ver manual del Supervisor")
        self.help_btn.clicked.connect(self._show_help_manual)
        header_layout.addWidget(self.help_btn)
        
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
        """Cargar alertas de ejemplo con colores claros brillantes que resaltan"""
        example_alerts = [
            ("🔴 CRÍTICA", "Loop detectado en skill 'web_scraper'", "2 min ago", "#ff6b6b"),  # Rojo claro brillante
            ("🟡 ADVERTENCIA", "Skill 'reporte_ventas' tomó 10min (est: 5)", "5 min ago", "#ffd93d"),  # Amarillo brillante
            ("🔵 INFO", "Agente agent_001 iniciado correctamente", "10 min ago", "#6bcf7f"),  # Verde menta claro
            ("🔵 INFO", "Pool CPU_INTENSIVE escalado a 6 agentes", "15 min ago", "#4dabf7"),  # Azul cielo brillante
        ]
        
        for level, message, time, color in example_alerts:
            item = QListWidgetItem(f"{level} - {message}\n  {time}")
            item.setData(Qt.UserRole, {"level": level, "message": message, "time": time})
            # Aplicar color CLARO BRILLANTE al texto para que resalte sobre cualquier fondo
            item.setForeground(Qt.transparent)
            item.setData(Qt.UserRole + 1, f"color: {color}; font-weight: bold; font-size: 13px;")
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
        
    def _show_help_manual(self):
        """Mostrar manual de ayuda del Supervisor en ventana horizontal con scroll"""
        
        # Crear ventana de diálogo personalizada
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Manual del Supervisor - MININA v3.0")
        dialog.setFixedSize(800, 500)  # Horizontal: ancho > alto
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Título
        title = QLabel("📖 Manual del Supervisor")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #6366f1;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Área de texto con scroll
        help_text = """
        <h3>🛡️ ¿Qué es el Supervisor?</h3>
        <p>El Supervisor es el <b>centro de control de alertas y monitoreo</b> de MININA. 
        Su función es vigilar todo lo que pasa en el sistema y avisarte cuando algo requiere tu atención.</p>
        
        <h3>🔔 ¿Qué hace?</h3>
        <ul>
        <li><b>Detecta problemas:</b> Identifica cuando una skill falla o tarda demasiado</li>
        <li><b>Monitorea recursos:</b> Controla el uso de CPU, memoria y agentes</li>
        <li><b>Alerta sobre anomalías:</b> Avisa si detecta comportamientos extraños</li>
        <li><b>Registra actividad:</b> Guarda un historial de todo lo que pasa</li>
        </ul>
        
        <h3>📊 Tipos de Alertas</h3>
        <ul>
        <li><span style='color:#ff6b6b'>🔴 CRÍTICA</span> - Problema grave que necesita acción inmediata</li>
        <li><span style='color:#ffd93d'>🟡 ADVERTENCIA</span> - Algo está tardando más de lo normal</li>
        <li><span style='color:#6bcf7f'>🔵 INFO</span> - Información general del sistema</li>
        </ul>
        
        <h3>🔘 ¿Para qué sirven los botones?</h3>
        <ul>
        <li><b>Reconocer:</b> Marcar alerta como "vista" (sigue activa pero sabemos que la viste)</li>
        <li><b>Resolver:</b> Eliminar alerta porque ya solucionaste el problema</li>
        <li><b>Ver Detalles:</b> Mostrar información completa de la alerta seleccionada</li>
        <li><b>Limpiar:</b> Borrar todas las alertas de la lista</li>
        <li><b>Exportar:</b> Guardar los logs en un archivo para revisarlos después</li>
        <li><b>Pausar/Reanudar:</b> Detener o continuar la actualización de logs en tiempo real</li>
        <li><b>Scroll:</b> Bloquear o desbloquear el desplazamiento automático de logs</li>
        </ul>
        
        <h3>📈 Contadores</h3>
        <p>Los números debajo (🔴 0 🟡 0 🔵 0) muestran cuántas alertas hay de cada tipo.</p>
        
        <p style='margin-top:20px;color:#666;'><i>💡 Consejo: Revisa regularmente el Supervisor para mantener el sistema saludable.</i></p>
        """
        
        text_edit = QTextEdit()
        text_edit.setHtml(help_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 15px;
                color: #1f293b;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(text_edit)
        
        # Botón cerrar
        close_btn = QPushButton("✓ Entendido")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
