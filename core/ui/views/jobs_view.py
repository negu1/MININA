"""
MININA v3.0 - JobsView: Panel de Trabajos/Rutinas Guardadas
Vista para activar trabajos pre-configurados del orquestador
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QLineEdit, QComboBox,
    QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

from core.saved_jobs import get_saved_jobs_manager, SavedJob, JobStatus, JobType


class JobCard(QFrame):
    """Card visual para un trabajo guardado"""
    
    activate_clicked = pyqtSignal(str)  # job_id
    edit_clicked = pyqtSignal(str)        # job_id
    
    def __init__(self, job: SavedJob, parent=None):
        super().__init__(parent)
        self.job = job
        self.job_id = job.job_id
        self._setup_ui()
    
    def _setup_ui(self):
        self.setStyleSheet(f"""
            JobCard {{
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid {self.job.color}40;
                border-radius: 12px;
                padding: 16px;
            }}
            JobCard:hover {{
                background-color: rgba(30, 41, 59, 0.95);
                border: 1px solid {self.job.color}80;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header con icono y nombre
        header = QHBoxLayout()
        
        icon_label = QLabel(self.job.icon)
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background-color: {self.job.color}20;
            border-radius: 10px;
            padding: 8px;
        """)
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        header.addWidget(icon_label)
        
        # Nombre y tipo
        name_layout = QVBoxLayout()
        name_layout.setSpacing(4)
        
        name_label = QLabel(self.job.name)
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #f1f5f9;
        """)
        name_layout.addWidget(name_label)
        
        type_label = QLabel(f"📁 {self.job.job_type.value.title()} | 🔄 {'Recurrente' if self.job.is_recurring else 'Una vez'}")
        type_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        name_layout.addWidget(type_label)
        
        header.addLayout(name_layout, stretch=1)
        
        # Badge de estado
        status_color = "#22c55e" if self.job.status == JobStatus.ACTIVE else "#6b7280"
        status_text = "🟢 Activo" if self.job.status == JobStatus.ACTIVE else "⚪ Archivado"
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            font-size: 10px;
            font-weight: bold;
            color: {status_color};
            background-color: {status_color}20;
            border-radius: 6px;
            padding: 4px 8px;
        """)
        header.addWidget(status_label)
        
        layout.addLayout(header)
        
        # Descripción
        desc_label = QLabel(self.job.description)
        desc_label.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Objetivo
        obj_label = QLabel(f"🎯 {self.job.objective[:80]}..." if len(self.job.objective) > 80 else f"🎯 {self.job.objective}")
        obj_label.setStyleSheet("font-size: 11px; color: #94a3b8; font-style: italic;")
        obj_label.setWordWrap(True)
        layout.addWidget(obj_label)
        
        # Tags
        if self.job.tags:
            tags_layout = QHBoxLayout()
            tags_layout.setSpacing(6)
            for tag in self.job.tags[:4]:
                tag_label = QLabel(f"#{tag}")
                tag_label.setStyleSheet("""
                    font-size: 10px;
                    color: #64748b;
                    background-color: rgba(51, 65, 85, 0.5);
                    border-radius: 4px;
                    padding: 2px 6px;
                """)
                tags_layout.addWidget(tag_label)
            tags_layout.addStretch()
            layout.addLayout(tags_layout)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        
        if self.job.execution_count > 0:
            exec_label = QLabel(f"▶️ {self.job.execution_count} ejecuciones")
            exec_label.setStyleSheet("font-size: 11px; color: #64748b;")
            stats_layout.addWidget(exec_label)
            
            if self.job.last_executed:
                last_label = QLabel(f"• Última: {self.job.last_executed[:10]}")
                last_label.setStyleSheet("font-size: 11px; color: #64748b;")
                stats_layout.addWidget(last_label)
        else:
            exec_label = QLabel("⏳ Sin ejecutar aún")
            exec_label.setStyleSheet("font-size: 11px; color: #64748b;")
            stats_layout.addWidget(exec_label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Botón ACTIVAR (principal)
        self.activate_btn = QPushButton("🚀 ACTIVAR TRABAJO")
        self.activate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.job.color};
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {self.job.color}DD;
            }}
            QPushButton:pressed {{
                background-color: {self.job.color}BB;
            }}
            QPushButton:disabled {{
                background-color: #475569;
                color: #94a3b8;
            }}
        """)
        self.activate_btn.setCursor(Qt.PointingHandCursor)
        self.activate_btn.clicked.connect(lambda: self.activate_clicked.emit(self.job_id))
        if self.job.status != JobStatus.ACTIVE:
            self.activate_btn.setEnabled(False)
            self.activate_btn.setText("⚪ ARCHIVADO")
        buttons_layout.addWidget(self.activate_btn)
        
        # Botón Editar
        edit_btn = QPushButton("⚙️ Editar")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                font-size: 12px;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: rgba(148, 163, 184, 0.1);
                border-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.job_id))
        buttons_layout.addWidget(edit_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)


class JobsView(QWidget):
    """
    Vista principal de Trabajos/Rutinas Guardadas
    Panel para activar trabajos pre-configurados del orquestador
    """
    
    job_activated = pyqtSignal(dict)  # Señal cuando se activa un trabajo
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.jobs_manager = get_saved_jobs_manager()
        self._setup_ui()
        self._load_jobs()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🚀 Trabajos y Rutinas")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #f8fafc;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Estadísticas rápidas
        self.stats_label = QLabel("Cargando...")
        self.stats_label.setStyleSheet("""
            font-size: 13px;
            color: #94a3b8;
            background-color: rgba(30, 41, 59, 0.6);
            border-radius: 8px;
            padding: 8px 16px;
        """)
        header_layout.addWidget(self.stats_label)
        
        # Botón Nuevo Trabajo
        new_btn = QPushButton("➕ Nuevo Trabajo")
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 8px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._create_new_job)
        header_layout.addWidget(new_btn)
        
        layout.addLayout(header_layout)
        
        # Descripción
        desc = QLabel("Activa trabajos pre-configurados que ya funcionan bien. Cada trabajo contiene un plan optimizado para el orquestador.")
        desc.setStyleSheet("font-size: 14px; color: #94a3b8;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Barra de filtros
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(12)
        
        # Buscador
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar trabajos...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #f1f5f9;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """)
        self.search_input.textChanged.connect(self._filter_jobs)
        filters_layout.addWidget(self.search_input, stretch=2)
        
        # Filtro por tipo
        self.type_filter = QComboBox()
        self.type_filter.addItem("📋 Todos los tipos", "all")
        for job_type in self.jobs_manager.get_job_types():
            self.type_filter.addItem(f"{job_type['icon']} {job_type['name']}", job_type['id'])
        self.type_filter.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f1f5f9;
                font-size: 13px;
                min-width: 180px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f1f5f9;
                selection-background-color: #6366f1;
            }
        """)
        self.type_filter.currentIndexChanged.connect(self._filter_jobs)
        filters_layout.addWidget(self.type_filter)
        
        # Filtro por estado
        self.status_filter = QComboBox()
        self.status_filter.addItem("🌐 Todos", "all")
        self.status_filter.addItem("🟢 Activos", "active")
        self.status_filter.addItem("⚪ Archivados", "archived")
        self.status_filter.setStyleSheet(self.type_filter.styleSheet())
        self.status_filter.currentIndexChanged.connect(self._filter_jobs)
        filters_layout.addWidget(self.status_filter)
        
        layout.addLayout(filters_layout)
        
        # Scroll area para cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(30, 41, 59, 0.5);
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #475569;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #64748b;
            }
        """)
        
        scroll_content = QWidget()
        self.jobs_layout = QGridLayout(scroll_content)
        self.jobs_layout.setSpacing(16)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.setColumnStretch(0, 1)
        self.jobs_layout.setColumnStretch(1, 1)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, stretch=1)
    
    def _load_jobs(self):
        """Cargar y mostrar todos los trabajos"""
        # Limpiar layout actual
        while self.jobs_layout.count():
            item = self.jobs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Cargar trabajos
        jobs = self.jobs_manager.get_all_jobs()
        
        # Mostrar cards
        for i, job in enumerate(jobs):
            row = i // 2
            col = i % 2
            card = JobCard(job)
            card.activate_clicked.connect(self._on_activate_job)
            card.edit_clicked.connect(self._on_edit_job)
            self.jobs_layout.addWidget(card, row, col)
        
        # Actualizar estadísticas
        self._update_stats()
    
    def _update_stats(self):
        """Actualizar estadísticas en el header"""
        stats = self.jobs_manager.get_stats()
        text = f"📦 {stats['total']} trabajos | 🟢 {stats['active']} activos | ▶️ {stats['total_executions']} ejecuciones"
        self.stats_label.setText(text)
    
    def _filter_jobs(self):
        """Filtrar trabajos según búsqueda y filtros"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentData()
        status_filter = self.status_filter.currentData()
        
        # Obtener trabajos filtrados
        jobs = self.jobs_manager.get_all_jobs()
        
        filtered = []
        for job in jobs:
            # Filtro de búsqueda
            if search_text:
                if not (search_text in job.name.lower() or 
                        search_text in job.description.lower() or
                        any(search_text in tag.lower() for tag in job.tags)):
                    continue
            
            # Filtro de tipo
            if type_filter != "all":
                if job.job_type.value != type_filter:
                    continue
            
            # Filtro de estado
            if status_filter != "all":
                if job.status.value != status_filter:
                    continue
            
            filtered.append(job)
        
        # Limpiar y recargar
        while self.jobs_layout.count():
            item = self.jobs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, job in enumerate(filtered):
            row = i // 2
            col = i % 2
            card = JobCard(job)
            card.activate_clicked.connect(self._on_activate_job)
            card.edit_clicked.connect(self._on_edit_job)
            self.jobs_layout.addWidget(card, row, col)
    
    def _on_activate_job(self, job_id: str):
        """Activar un trabajo"""
        job_data = self.jobs_manager.activate_job(job_id)
        if job_data:
            # Emitir señal para que main_window lo maneje
            self.job_activated.emit(job_data)
            
            # Mostrar confirmación
            QMessageBox.information(
                self,
                "🚀 Trabajo Activado",
                f"El trabajo '{job_data['name']}' ha sido activado.\n\n"
                f"Objetivo: {job_data['objective'][:80]}...\n\n"
                f"Ve al Orquestador para ver el plan generado."
            )
            
            self._update_stats()
    
    def _on_edit_job(self, job_id: str):
        """Editar un trabajo"""
        job = self.jobs_manager.get_job(job_id)
        if job:
            QMessageBox.information(
                self,
                "⚙️ Editar Trabajo",
                f"Función de edición para '{job.name}' en desarrollo.\n\n"
                f"Podrás modificar:\n"
                f"• Nombre y descripción\n"
                f"• Frecuencia de ejecución\n"
                f"• Notificaciones\n"
                f"• Tags y categorías"
            )
    
    def _create_new_job(self):
        """Crear nuevo trabajo"""
        QMessageBox.information(
            self,
            "➕ Nuevo Trabajo",
            "Para crear un nuevo trabajo:\n\n"
            "1. Ve al Orquestador\n"
            "2. Configura tu objetivo y plan\n"
            "3. Cuando el plan esté listo, selecciona 'Guardar como Rutina'\n\n"
            "El trabajo aparecerá aquí para activarlo rápidamente."
        )
    
    def refresh(self):
        """Refrescar la vista"""
        self._load_jobs()
