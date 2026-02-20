"""
MININA v3.0 - Controller View (Capa 3)
Control de políticas, reglas y permisos
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QCheckBox, QSpinBox,
    QTimeEdit, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTime

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
        """Configurar interfaz elegante del Controlador"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header elegante
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("📜")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        header = QLabel("Controlador")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Reglas, políticas y permisos del sistema")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.72);
            margin-bottom: 8px;
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Reglas Duras
        rules_group = QGroupBox("🔒 Reglas Duras")
        rules_layout = QVBoxLayout(rules_group)

        policy = PolicySettings.get()
        
        # Rate limiting
        rl_row = QHBoxLayout()
        rl_row.addWidget(QLabel("Máx ejecuciones/min por usuario:"))
        self.rate_limit_spin = QSpinBox()
        self.rate_limit_spin.setRange(1, 120)
        self.rate_limit_spin.setValue(policy.rate_limit_per_min)
        self.rate_limit_spin.valueChanged.connect(PolicySettings.set_rate_limit_per_min)
        rl_row.addWidget(self.rate_limit_spin)
        rl_row.addStretch()
        rules_layout.addLayout(rl_row)
        
        # Storage limit
        st_row = QHBoxLayout()
        st_row.addWidget(QLabel("Máx MB archivos generados/día:"))
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(1, 10240)
        self.storage_spin.setValue(policy.storage_mb_per_day)
        self.storage_spin.valueChanged.connect(PolicySettings.set_storage_mb_per_day)
        st_row.addWidget(self.storage_spin)
        st_row.addStretch()
        rules_layout.addLayout(st_row)
        
        # Business hours
        bh_row = QHBoxLayout()
        self.business_hours_check = QCheckBox("Skills sin validar: solo horario laboral")
        self.business_hours_check.setChecked(bool(policy.business_hours_enabled))
        self.business_hours_check.toggled.connect(PolicySettings.set_business_hours_enabled)
        bh_row.addWidget(self.business_hours_check)
        bh_row.addStretch()
        rules_layout.addLayout(bh_row)

        bh_time_row = QHBoxLayout()
        bh_time_row.addWidget(QLabel("Horario:"))

        self.business_start = QTimeEdit()
        self.business_start.setDisplayFormat("HH:mm")
        try:
            start_h, start_m = [int(x) for x in str(policy.business_hours_start).split(":")[:2]]
            self.business_start.setTime(QTime(start_h, start_m))
        except Exception:
            self.business_start.setTime(QTime(9, 0))
        self.business_start.timeChanged.connect(lambda t: PolicySettings.set_business_hours_start(t.toString("HH:mm")))
        bh_time_row.addWidget(self.business_start)

        bh_time_row.addWidget(QLabel("a"))

        self.business_end = QTimeEdit()
        self.business_end.setDisplayFormat("HH:mm")
        try:
            end_h, end_m = [int(x) for x in str(policy.business_hours_end).split(":")[:2]]
            self.business_end.setTime(QTime(end_h, end_m))
        except Exception:
            self.business_end.setTime(QTime(18, 0))
        self.business_end.timeChanged.connect(lambda t: PolicySettings.set_business_hours_end(t.toString("HH:mm")))
        bh_time_row.addWidget(self.business_end)
        bh_time_row.addStretch()
        rules_layout.addLayout(bh_time_row)
        
        # Network skills
        self.network_check = QCheckBox("Skills con network: requieren aprobación manual")
        self.network_check.setChecked(bool(policy.network_requires_approval))
        self.network_check.toggled.connect(PolicySettings.set_network_requires_approval)
        rules_layout.addWidget(self.network_check)
        
        layout.addWidget(rules_group)
        
        # Horarios de Ejecución
        schedules_group = QGroupBox("⏰ Horarios de Ejecución")
        schedules_layout = QVBoxLayout(schedules_group)
        
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(4)
        self.schedules_table.setHorizontalHeaderLabels([
            "Skill", "Días", "Horario", "Estado"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self._load_schedules_table()
        
        schedules_layout.addWidget(self.schedules_table)
        
        # Botones
        sched_buttons = QHBoxLayout()
        self.add_sched_btn = QPushButton("+ Agregar Horario")
        self.add_sched_btn.clicked.connect(self._add_schedule)
        sched_buttons.addWidget(self.add_sched_btn)
        
        self.edit_sched_btn = QPushButton("✏️ Editar")
        self.edit_sched_btn.clicked.connect(self._edit_schedule)
        sched_buttons.addWidget(self.edit_sched_btn)
        
        self.del_sched_btn = QPushButton("🗑️ Eliminar")
        self.del_sched_btn.clicked.connect(self._delete_schedule)
        sched_buttons.addWidget(self.del_sched_btn)
        
        sched_buttons.addStretch()
        schedules_layout.addLayout(sched_buttons)
        
        layout.addWidget(schedules_group)
        
        # Permisos de Usuario
        permissions_group = QGroupBox("👤 Permisos de Usuario")
        perm_layout = QVBoxLayout(permissions_group)
        
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Usuario:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(["admin", "usuario1", "usuario2"])
        user_layout.addWidget(self.user_combo)
        
        user_layout.addWidget(QLabel("Rol:"))
        self.role_label = QLabel("Administrador")
        user_layout.addWidget(self.role_label)
        user_layout.addStretch()
        
        perm_layout.addLayout(user_layout)
        
        # Permisos específicos
        self.can_execute_all = QCheckBox("Puede ejecutar: Todas las skills")
        self.can_execute_all.setChecked(True)
        perm_layout.addWidget(self.can_execute_all)
        
        self.can_create_skills = QCheckBox("Puede crear: Nuevas skills")
        self.can_create_skills.setChecked(True)
        perm_layout.addWidget(self.can_create_skills)
        
        self.can_delete_works = QCheckBox("Puede eliminar: Cualquier work")
        self.can_delete_works.setChecked(True)
        perm_layout.addWidget(self.can_delete_works)
        
        layout.addWidget(permissions_group)

        # Límites UI
        ui_limits_group = QGroupBox("🧰 Límites UI")
        ui_limits_layout = QVBoxLayout(ui_limits_group)

        chat_limit_row = QHBoxLayout()
        chat_limit_row.addWidget(QLabel("Mensajes en chat (máx):"))

        self.chat_limit_spin = QSpinBox()
        self.chat_limit_spin.setRange(5, 200)
        self.chat_limit_spin.setValue(UiSettings.get().chat_history_limit)
        self.chat_limit_spin.valueChanged.connect(UiSettings.set_chat_history_limit)
        chat_limit_row.addWidget(self.chat_limit_spin)
        chat_limit_row.addStretch()

        ui_limits_layout.addLayout(chat_limit_row)
        layout.addWidget(ui_limits_group)
        
        # Botón guardar
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("💾 Guardar Cambios")
        self.save_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.save_btn.clicked.connect(self._save_changes)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        
        layout.addStretch()
        
    def _load_rules(self):
        """Cargar reglas configuradas"""
        pass
        
    def _load_schedules(self):
        """Cargar horarios"""
        pass
        
    def _load_schedules_table(self):
        """Cargar tabla de horarios"""
        example_data = [
            ["reporte_ventas", "Lun-Vie", "09:00", "✅ Activo"],
            ["backup_diario", "Todos", "02:00", "✅ Activo"],
            ["scraper_web", "Lun,Mie,Vie", "10:00,16:00", "⚠️ Pausado"],
        ]
        
        self.schedules_table.setRowCount(len(example_data))
        for row, data in enumerate(example_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                self.schedules_table.setItem(row, col, item)
                
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
            
    def _save_changes(self):
        """Guardar cambios de configuración"""
        pass
