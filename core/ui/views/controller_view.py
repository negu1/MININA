"""
MININA v3.0 - Controller View (Capa 3) - Modernizado
Control de políticas, reglas y permisos con fondo plateado
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QCheckBox, QSpinBox,
    QTimeEdit, QComboBox, QTextEdit, QFrame,
    QMessageBox, QDialog
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QFont

from core.ui.ui_settings import UiSettings
from core.ui.policy_settings import PolicySettings


class ControllerView(QWidget):
    """
    Vista del Controlador - Reglas y Políticas
    Configuración de horarios, permisos y reglas duras
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_rules()
        self._load_schedules()
        
    def _setup_ui(self):
        """Configurar interfaz moderna del Controlador - Fondo plateado"""
        # Layout principal con fondo plateado
        self.setStyleSheet("""
            QWidget {
                background-color: #e2e8f0;
                color: #1e293b;
            }
            QLabel {
                color: #1e293b;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header elegante con título brillante
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("📜")
        icon_label.setStyleSheet("font-size: 32px; background: transparent;")
        header_layout.addWidget(icon_label)
        
        header = QLabel("Controlador")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #6366f1;
            background: transparent;
        """)
        header_layout.addWidget(header)
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
        self.help_btn.setToolTip("Ver manual del Controlador")
        self.help_btn.clicked.connect(self._show_help_manual)
        header_layout.addWidget(self.help_btn)
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Reglas, políticas y permisos del sistema")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
            background: transparent;
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # === LAYOUT PRINCIPAL HORIZONTAL ===
        main_split = QHBoxLayout()
        main_split.setSpacing(24)
        
        # === IZQUIERDA: Reglas Duras (compacto vertical) ===
        left_panel = self._create_rules_panel()
        main_split.addWidget(left_panel, 3)
        
        # === DERECHA: Horarios de Ejecución (más espacio) ===
        right_panel = self._create_schedules_panel()
        main_split.addWidget(right_panel, 5)
        
        layout.addLayout(main_split, 1)
        
        # === ABAJO: Permisos desplegable ===
        permissions_section = self._create_permissions_collapsible()
        layout.addWidget(permissions_section)
        
        # Botón guardar
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.save_btn.clicked.connect(self._save_changes)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        
    def _create_rules_panel(self) -> QWidget:
        """Panel de Reglas Duras - Vertical compacto"""
        rules_group = QGroupBox("🔒 Reglas Duras")
        rules_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1e293b;
                border: 2px solid #ef4444;
                border-radius: 12px;
                padding: 16px;
                background-color: #f1f5f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                color: #ef4444;
                background-color: #fee2e2;
                border-radius: 6px;
            }
        """)
        
        policy = PolicySettings.get()
        rules_layout = QVBoxLayout(rules_group)
        rules_layout.setSpacing(12)
        
        # Rate limiting - Vertical
        rate_label = QLabel("⚡ Máx ejecuciones/min:")
        rate_label.setStyleSheet("color: #475569; font-weight: 500; background: transparent;")
        rules_layout.addWidget(rate_label)
        
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 120)
        self.rate_limit_spin.setValue(policy.rate_limit_per_min)
        self.rate_limit_spin.valueChanged.connect(PolicySettings.set_rate_limit_per_min)
        self.rate_limit_spin.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
                color: #1e293b;
                font-weight: bold;
            }
        """)
        rules_layout.addWidget(self.rate_limit_spin)
        
        # Storage limit - Vertical
        storage_label = QLabel("💾 Máx MB archivos/día:")
        storage_label.setStyleSheet("color: #475569; font-weight: 500; background: transparent;")
        rules_layout.addWidget(storage_label)
        
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(1, 10240)
        self.storage_spin.setValue(policy.storage_mb_per_day)
        self.storage_spin.valueChanged.connect(PolicySettings.set_storage_mb_per_day)
        self.storage_spin.setStyleSheet("""
            QSpinBox {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
                color: #1e293b;
                font-weight: bold;
            }
        """)
        rules_layout.addWidget(self.storage_spin)
        
        # Business hours - Vertical
        self.business_hours_check = QCheckBox("🕐 Solo horario laboral")
        self.business_hours_check.setChecked(bool(policy.business_hours_enabled))
        self.business_hours_check.toggled.connect(PolicySettings.set_business_hours_enabled)
        self.business_hours_check.setStyleSheet("""
            QCheckBox {
                color: #475569;
                font-weight: 500;
                background: transparent;
            }
        """)
        rules_layout.addWidget(self.business_hours_check)
        
        # Horario específico
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)
        
        time_label = QLabel("De:")
        time_label.setStyleSheet("color: #64748b; background: transparent;")
        time_layout.addWidget(time_label)
        
        self.business_start = QTimeEdit()
        self.business_start.setDisplayFormat("HH:mm")
        try:
            start_h, start_m = [int(x) for x in str(policy.business_hours_start).split(":")[:2]]
            self.business_start.setTime(QTime(start_h, start_m))
        except Exception:
            self.business_start.setTime(QTime(9, 0))
        self.business_start.timeChanged.connect(lambda t: PolicySettings.set_business_hours_start(t.toString("HH:mm")))
        self.business_start.setStyleSheet("""
            QTimeEdit {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
                color: #1e293b;
            }
        """)
        time_layout.addWidget(self.business_start)
        
        time_to_label = QLabel("a:")
        time_to_label.setStyleSheet("color: #64748b; background: transparent;")
        time_layout.addWidget(time_to_label)
        
        self.business_end = QTimeEdit()
        self.business_end.setDisplayFormat("HH:mm")
        try:
            end_h, end_m = [int(x) for x in str(policy.business_hours_end).split(":")[:2]]
            self.business_end.setTime(QTime(end_h, end_m))
        except Exception:
            self.business_end.setTime(QTime(18, 0))
        self.business_end.timeChanged.connect(lambda t: PolicySettings.set_business_hours_end(t.toString("HH:mm")))
        self.business_end.setStyleSheet("""
            QTimeEdit {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
                color: #1e293b;
            }
        """)
        time_layout.addWidget(self.business_end)
        time_layout.addStretch()
        
        rules_layout.addLayout(time_layout)
        
        # Network skills
        self.network_check = QCheckBox("🌐 Skills network: requieren aprobación")
        self.network_check.setChecked(bool(policy.network_requires_approval))
        self.network_check.toggled.connect(PolicySettings.set_network_requires_approval)
        self.network_check.setStyleSheet("""
            QCheckBox {
                color: #475569;
                font-weight: 500;
                background: transparent;
            }
        """)
        rules_layout.addWidget(self.network_check)
        
        rules_layout.addStretch()
        return rules_group
        
    def _create_schedules_panel(self) -> QWidget:
        """Panel de Horarios de Ejecución - Más espacio, estilo moderno"""
        schedules_group = QGroupBox("⏰ Horarios de Ejecución")
        schedules_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1e293b;
                border: 2px solid #f59e0b;
                border-radius: 12px;
                padding: 16px;
                background-color: #f1f5f9;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                color: #f59e0b;
                background-color: #fef3c7;
                border-radius: 6px;
            }
        """)
        
        schedules_layout = QVBoxLayout(schedules_group)
        schedules_layout.setSpacing(12)
        
        # Tabla moderna
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(4)
        self.schedules_table.setHorizontalHeaderLabels([
            "🤖 Skill", "📅 Días", "⏰ Horario", "📊 Estado"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedules_table.verticalHeader().setDefaultSectionSize(44)
        self.schedules_table.verticalHeader().setMinimumSectionSize(44)
        self.schedules_table.setWordWrap(True)
        
        # Estilos modernos de tabla
        self.schedules_table.setStyleSheet("""
            QTableWidget {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                gridline-color: #cbd5e1;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 13px;
                color: #334155;
                background-color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #f1f5f9;
            }
            QTableWidget::item:selected {
                background-color: #ddd6fe;
                color: #5b21b6;
                border-left: 3px solid #8b5cf6;
            }
            QHeaderView::section {
                background-color: #e2e8f0;
                color: #475569;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #94a3b8;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        
        self._load_schedules_table()
        schedules_layout.addWidget(self.schedules_table)
        
        # Botones modernos
        sched_buttons = QHBoxLayout()
        sched_buttons.setSpacing(12)
        
        self.add_sched_btn = QPushButton("➕ Agregar")
        self.add_sched_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.add_sched_btn.clicked.connect(self._add_schedule)
        sched_buttons.addWidget(self.add_sched_btn)
        
        self.edit_sched_btn = QPushButton("✏️ Editar")
        self.edit_sched_btn.setStyleSheet("""
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
        self.edit_sched_btn.clicked.connect(self._edit_schedule)
        sched_buttons.addWidget(self.edit_sched_btn)
        
        self.del_sched_btn = QPushButton("🗑️ Eliminar")
        self.del_sched_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.del_sched_btn.clicked.connect(self._delete_schedule)
        sched_buttons.addWidget(self.del_sched_btn)
        
        sched_buttons.addStretch()
        schedules_layout.addLayout(sched_buttons)
        
        return schedules_group
        
    def _create_permissions_collapsible(self) -> QWidget:
        """Panel de Permisos desplegable (collapsible)"""
        container = QFrame()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)
        
        # Botón de encabezado desplegable
        self.perm_toggle_btn = QPushButton("👤 Permisos de Usuario ▼")
        self.perm_toggle_btn.setCheckable(True)
        self.perm_toggle_btn.setChecked(False)  # Inicia colapsado
        self.perm_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:checked {
                background-color: #6d28d9;
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }
        """)
        self.perm_toggle_btn.clicked.connect(self._toggle_permissions)
        container_layout.addWidget(self.perm_toggle_btn)
        
        # Contenido desplegable
        self.perm_content = QFrame()
        self.perm_content.setVisible(False)  # Inicia oculto
        self.perm_content.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 2px solid #8b5cf6;
                border-top: none;
                border-radius: 0 0 10px 10px;
                padding: 16px;
            }
        """)
        
        perm_layout = QVBoxLayout(self.perm_content)
        perm_layout.setSpacing(12)
        
        # Usuario y Rol
        user_layout = QHBoxLayout()
        user_layout.setSpacing(16)
        
        user_label = QLabel("👤 Usuario:")
        user_label.setStyleSheet("color: #475569; font-weight: bold; background: transparent;")
        user_layout.addWidget(user_label)
        
        self.user_combo = QComboBox()
        self.user_combo.addItems(["admin", "usuario1", "usuario2"])
        self.user_combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px 12px;
                color: #1e293b;
                min-width: 120px;
            }
        """)
        user_layout.addWidget(self.user_combo)
        
        role_label = QLabel("🏷️ Rol:")
        role_label.setStyleSheet("color: #475569; font-weight: bold; background: transparent;")
        user_layout.addWidget(role_label)
        
        self.role_label = QLabel("Administrador")
        self.role_label.setStyleSheet("""
            color: #6366f1;
            font-weight: bold;
            background-color: #e0e7ff;
            padding: 6px 12px;
            border-radius: 6px;
        """)
        user_layout.addWidget(self.role_label)
        user_layout.addStretch()
        
        perm_layout.addLayout(user_layout)
        
        # Separador
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet("background-color: #cbd5e1;")
        perm_layout.addWidget(sep)
        
        # Permisos específicos
        perms_title = QLabel("🔐 Permisos Específicos:")
        perms_title.setStyleSheet("color: #475569; font-weight: bold; background: transparent;")
        perm_layout.addWidget(perms_title)
        
        self.can_execute_all = QCheckBox("✅ Ejecutar todas las skills")
        self.can_execute_all.setChecked(True)
        self.can_execute_all.setStyleSheet("""
            QCheckBox {
                color: #059669;
                font-weight: 500;
                background: transparent;
            }
        """)
        perm_layout.addWidget(self.can_execute_all)
        
        self.can_create_skills = QCheckBox("✅ Crear nuevas skills")
        self.can_create_skills.setChecked(True)
        self.can_create_skills.setStyleSheet("""
            QCheckBox {
                color: #059669;
                font-weight: 500;
                background: transparent;
            }
        """)
        perm_layout.addWidget(self.can_create_skills)
        
        self.can_delete_works = QCheckBox("✅ Eliminar cualquier work")
        self.can_delete_works.setChecked(True)
        self.can_delete_works.setStyleSheet("""
            QCheckBox {
                color: #059669;
                font-weight: 500;
                background: transparent;
            }
        """)
        perm_layout.addWidget(self.can_delete_works)
        
        container_layout.addWidget(self.perm_content)
        
        return container
        
    def _toggle_permissions(self):
        """Mostrar/ocultar panel de permisos"""
        is_visible = self.perm_content.isVisible()
        self.perm_content.setVisible(not is_visible)
        
        # Cambiar icono de flecha
        if is_visible:
            self.perm_toggle_btn.setText("👤 Permisos de Usuario ▼")
        else:
            self.perm_toggle_btn.setText("👤 Permisos de Usuario ▲")
        
    def _load_rules(self):
        """Cargar reglas configuradas"""
        pass
        
    def _load_schedules(self):
        """Cargar horarios"""
        pass
        
    def _load_schedules_table(self):
        """Cargar tabla de horarios con colores brillantes"""
        example_data = [
            ["reporte_ventas", "Lun-Vie", "09:00", "✅ Activo"],
            ["backup_diario", "Todos", "02:00", "✅ Activo"],
            ["scraper_web", "Lun,Mie,Vie", "10:00,16:00", "⚠️ Pausado"],
        ]
        
        self.schedules_table.setRowCount(len(example_data))
        for row, data in enumerate(example_data):
            skill, days, time, status = data
            
            # Skill
            skill_item = QTableWidgetItem(skill)
            skill_item.setForeground(Qt.transparent)
            skill_item.setData(Qt.UserRole + 1, "color: #6366f1; font-weight: bold;")
            self.schedules_table.setItem(row, 0, skill_item)
            
            # Días
            days_item = QTableWidgetItem(days)
            days_item.setForeground(Qt.transparent)
            days_item.setData(Qt.UserRole + 1, "color: #475569;")
            self.schedules_table.setItem(row, 1, days_item)
            
            # Horario
            time_item = QTableWidgetItem(time)
            time_item.setForeground(Qt.transparent)
            time_item.setData(Qt.UserRole + 1, "color: #f59e0b; font-weight: 500;")
            self.schedules_table.setItem(row, 2, time_item)
            
            # Estado con color
            status_item = QTableWidgetItem(status)
            status_color = "#059669" if "Activo" in status else "#dc2626"
            status_item.setForeground(Qt.transparent)
            status_item.setData(Qt.UserRole + 1, f"color: {status_color}; font-weight: bold;")
            self.schedules_table.setItem(row, 3, status_item)
                
    def _add_schedule(self):
        """Agregar nuevo horario"""
        pass
        
    def _edit_schedule(self):
        """Editar horario seleccionado"""
        pass
        
    def _delete_schedule(self):
        """Eliminar horario seleccionado"""
        current_row = self.schedules_table.currentRow()
        if current_row >= 0:
            self.schedules_table.removeRow(current_row)
            
    def _show_help_manual(self):
        """Mostrar manual de ayuda del Controlador en ventana horizontal con scroll"""
        
        # Crear ventana de diálogo personalizada
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Manual del Controlador - MININA v3.0")
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
        title = QLabel("📖 Manual del Controlador")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #6366f1;
            background: transparent;
        """)
        layout.addWidget(title)
        
        # Área de texto con scroll
        help_text = """
        <h3>📜 ¿Qué es el Controlador?</h3>
        <p>El Controlador es la <b>capa de seguridad y políticas</b> de MININA. 
        Aquí defines las reglas que todos los agentes y skills deben seguir.</p>
        
        <h3>🔒 Reglas Duras (Panel Izquierdo)</h3>
        <p>Reglas de seguridad estrictas que protegen el sistema:</p>
        <ul>
        <li><b>⚡ Máx ejecuciones/min:</b> Cuántas skills puede ejecutar un usuario por minuto (anti-spam)</li>
        <li><b>💾 Máx MB archivos/día:</b> Límite de almacenamiento para archivos generados</li>
        <li><b>🕐 Solo horario laboral:</b> Skills sin validar solo funcionan en horario de oficina</li>
        <li><b>🌐 Skills network:</b> Skills que usan internet requieren aprobación manual</li>
        </ul>
        
        <h3>⏰ Horarios de Ejecución (Panel Derecho)</h3>
        <p>Programa skills para que se ejecuten automáticamente en días y horarios específicos.</p>
        <ul>
        <li><b>🤖 Skill:</b> Nombre de la skill a programar</li>
        <li><b>📅 Días:</b> Cuándo debe ejecutarse (Lun-Vie, Todos, etc.)</li>
        <li><b>⏰ Horario:</b> A qué hora exacta (formato 24h)</li>
        <li><b>📊 Estado:</b> Activo o Pausado</li>
        </ul>
        
        <h3>🔘 Botones de Horarios</h3>
        <ul>
        <li><b>➕ Agregar:</b> Crear nuevo horario programado</li>
        <li><b>✏️ Editar:</b> Modificar horario seleccionado</li>
        <li><b>🗑️ Eliminar:</b> Borrar horario seleccionado</li>
        </ul>
        
        <h3>👤 Permisos de Usuario (Panel Desplegable)</h3>
        <p>Haz clic en el botón violeta para ver los permisos. Define qué puede hacer cada usuario:</p>
        <ul>
        <li><b>✅ Ejecutar todas las skills:</b> Puede correr cualquier skill</li>
        <li><b>✅ Crear nuevas skills:</b> Puede añadir skills al sistema</li>
        <li><b>✅ Eliminar cualquier work:</b> Puede borrar archivos generados</li>
        </ul>
        
        <h3>🎯 ¿Cuándo usar cada regla?</h3>
        <ul>
        <li><b>Rate limiting:</b> Cuando múltiples usuarios usan el sistema</li>
        <li><b>Storage limit:</b> Para evitar llenar el disco con archivos</li>
        <li><b>Horario laboral:</b> Para skills de prueba que no deben correr 24/7</li>
        <li><b>Network approval:</b> Para skills que descargan o suben datos externos</li>
        </ul>
        
        <h3>⚠️ Importante</h3>
        <p>Las <b>Reglas Duras</b> se aplican automáticamente y no se pueden saltar.
        Los cambios guardados son inmediatos.</p>
        
        <p style='margin-top:20px;color:#666;'><i>💡 Consejo: Empezá con reglas permisivas y ajustalas según necesites.</i></p>
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
            
    def _save_changes(self):
        """Guardar cambios de configuración"""
        pass
