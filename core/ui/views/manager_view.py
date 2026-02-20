"""
MININA v3.0 - Manager View (Capa 4)
Gestión de agentes y pools de recursos
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ManagerView(QWidget):
    """
    Vista de Manager - Gestión de agentes y recursos
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_metrics()
        
    def _setup_ui(self):
        """Configurar interfaz elegante del Manager - Layout horizontal"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header elegante
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("⚡")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        header = QLabel("Gestión de Agentes")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
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
        self.help_btn.setToolTip("Ver manual de Gestión de Agentes")
        self.help_btn.clicked.connect(self._show_help_manual)
        header_layout.addWidget(self.help_btn)
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Pools de agentes, métricas y auto-scaling")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.72);
            margin-bottom: 8px;
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # === LAYOUT PRINCIPAL HORIZONTAL ===
        # Agentes Activos (IZQUIERDA - más espacio) | Pools (DERECHA - compacto)
        main_split = QHBoxLayout()
        main_split.setSpacing(24)
        
        # === PANEL IZQUIERDO: Agentes Activos (70% del espacio) ===
        left_panel = self._create_agents_panel()
        main_split.addWidget(left_panel, 7)  # 70% del espacio
        
        # === PANEL DERECHO: Pools de Agentes (30% del espacio) ===
        right_panel = self._create_pools_panel()
        main_split.addWidget(right_panel, 3)  # 30% del espacio
        
        layout.addLayout(main_split, 1)  # Expande para ocupar espacio restante
        
        # Auto-Scaling abajo
        scaling_layout = QHBoxLayout()
        scaling_layout.addWidget(QLabel("Auto-Scaling:"))
        
        self.scaling_btn = QPushButton("✅ Activado")
        self.scaling_btn.setCheckable(True)
        self.scaling_btn.setChecked(True)
        scaling_layout.addWidget(self.scaling_btn)
        
        scaling_layout.addWidget(QLabel("Umbral:"))
        self.threshold_label = QLabel("10 tareas en cola")
        scaling_layout.addWidget(self.threshold_label)
        
        scaling_layout.addStretch()
        layout.addLayout(scaling_layout)
        
    def _create_agents_panel(self) -> QWidget:
        """Crear panel izquierdo con tabla de Agentes Activos"""
        agents_group = QGroupBox("🤖 Agentes Activos")
        agents_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1e293b;
                border: 2px solid #6366f1;
                border-radius: 12px;
                padding: 16px;
                background-color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                color: #6366f1;
                background-color: #e2e8f0;
                border-radius: 4px;
            }
        """)
        agents_layout = QVBoxLayout(agents_group)
        agents_layout.setSpacing(12)
        
        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(5)
        self.agents_table.setHorizontalHeaderLabels([
            "ID del Agente", "Tipo Pool", "Skill Ejecutando", "Uso CPU", "Tiempo Activo"
        ])
        self.agents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.agents_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Configurar altura de filas para mostrar contenido completo
        self.agents_table.verticalHeader().setDefaultSectionSize(48)
        self.agents_table.verticalHeader().setMinimumSectionSize(48)
        self.agents_table.setWordWrap(True)
        self.agents_table.setShowGrid(False)
        self.agents_table.setAlternatingRowColors(True)
        
        # Estilos modernos para la tabla con fondo gris plateado suave
        self.agents_table.setStyleSheet("""
            QTableWidget {
                background-color: #e2e8f0;
                border: 1px solid #94a3b8;
                border-radius: 8px;
                gridline-color: #94a3b8;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #cbd5e1;
                border-right: 1px solid #cbd5e1;
                font-size: 13px;
                color: #1e293b;
                background-color: #f1f5f9;
            }
            QTableWidget::item:alternate {
                background-color: #e2e8f0;
            }
            QTableWidget::item:selected {
                background-color: #c4b5fd;
                color: #1e1b4b;
                border-left: 4px solid #7c3aed;
                border-bottom: 1px solid #7c3aed;
            }
            QHeaderView::section {
                background-color: #cbd5e1;
                color: #334155;
                padding: 14px 16px;
                border: none;
                border-bottom: 2px solid #64748b;
                border-right: 1px solid #94a3b8;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
        """)
        
        self._load_agents_table()
        
        agents_layout.addWidget(self.agents_table)
        return agents_group
        
    def _create_pools_panel(self) -> QWidget:
        """Crear panel derecho con Pools de Agentes (compacto vertical)"""
        pools_group = QGroupBox("📊 Pools de Agentes")
        pools_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #1e293b;
                border: 2px solid #8b5cf6;
                border-radius: 12px;
                padding: 16px;
                background-color: #e2e8f0;
                min-width: 280px;
                max-width: 320px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                color: #8b5cf6;
                background-color: #e2e8f0;
                border-radius: 4px;
            }
        """)
        pools_layout = QVBoxLayout(pools_group)
        pools_layout.setSpacing(12)
        pools_layout.setContentsMargins(12, 20, 12, 12)
        
        # CPU Intensive
        self.cpu_bar = self._create_pool_bar("🔴 CPU_INTENSIVE", "3/4 activos", 75)
        pools_layout.addLayout(self.cpu_bar)
        
        # IO Intensive
        self.io_bar = self._create_pool_bar("🟢 IO_INTENSIVE", "2/8 activos", 25)
        pools_layout.addLayout(self.io_bar)
        
        # Network
        self.network_bar = self._create_pool_bar("🟡 NETWORK", "5/10 activos", 50)
        pools_layout.addLayout(self.network_bar)
        
        # General
        self.general_bar = self._create_pool_bar("🔵 GENERAL", "1/6 activos", 17)
        pools_layout.addLayout(self.general_bar)
        
        pools_layout.addStretch()
        return pools_group
        
    def _create_pool_bar(self, name: str, status: str, percentage: int) -> QHBoxLayout:
        """Crear barra de progreso compacta para un pool"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 4, 0, 4)
        
        label = QLabel(name)
        label.setFixedWidth(120)
        label.setStyleSheet("color: #1f2937; font-weight: 500; font-size: 13px;")
        layout.addWidget(label)
        
        bar = QProgressBar()
        bar.setValue(percentage)
        bar.setTextVisible(True)
        bar.setFormat(status)
        bar.setFixedHeight(20)
        bar.setStyleSheet("""
            QProgressBar {
                background-color: #e5e7eb;
                border-radius: 10px;
                text-align: center;
                color: #1f2937;
                font-weight: bold;
                font-size: 11px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 10px;
            }
        """)
        layout.addWidget(bar)
        
        return layout
        
    def _load_agents_table(self):
        """Cargar datos de agentes en la tabla con estilos modernos"""
        example_data = [
            ["agent_001", "CPU_INTENSIVE", "data_analysis", "45%", "5m"],
            ["agent_002", "NETWORK", "web_scraper", "12%", "2m"],
            ["agent_003", "IO_INTENSIVE", "file_processor", "8%", "10m"],
        ]
        
        # Colores para cada tipo de pool
        pool_colors = {
            "CPU_INTENSIVE": ("#ef4444", "#fee2e2"),  # Rojo
            "IO_INTENSIVE": ("#10b981", "#d1fae5"),   # Verde
            "NETWORK": ("#f59e0b", "#fef3c7"),        # Amarillo
            "GENERAL": ("#3b82f6", "#dbeafe"),        # Azul
        }
        
        # Colores para CPU
        def get_cpu_color(cpu_str):
            cpu_val = int(cpu_str.replace("%", ""))
            if cpu_val >= 70:
                return ("#ef4444", "#fee2e2")  # Rojo - alto
            elif cpu_val >= 40:
                return ("#f59e0b", "#fef3c7")  # Amarillo - medio
            else:
                return ("#10b981", "#d1fae5")  # Verde - bajo
        
        self.agents_table.setRowCount(len(example_data))
        for row, data in enumerate(example_data):
            agent_id, pool, skill, cpu, time = data
            
            # ID del Agente con icono
            id_item = QTableWidgetItem(f"🔹 {agent_id}")
            id_item.setFont(QFont("Segoe UI", 12, QFont.Bold))
            self.agents_table.setItem(row, 0, id_item)
            
            # Tipo Pool con badge de color
            pool_item = QTableWidgetItem(pool)
            text_color, bg_color = pool_colors.get(pool, ("#6b7280", "#f3f4f6"))
            pool_item.setForeground(Qt.transparent)
            pool_item.setData(Qt.UserRole + 1, f"""
                color: {text_color}; 
                background-color: {bg_color};
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 11px;
            """)
            self.agents_table.setItem(row, 1, pool_item)
            
            # Skill ejecutando
            skill_item = QTableWidgetItem(f"⚙️ {skill}")
            skill_item.setForeground(Qt.transparent)
            skill_item.setData(Qt.UserRole + 1, "color: #6366f1; font-weight: 500;")
            self.agents_table.setItem(row, 2, skill_item)
            
            # Uso CPU con indicador de color
            cpu_item = QTableWidgetItem(cpu)
            text_color, bg_color = get_cpu_color(cpu)
            cpu_item.setForeground(Qt.transparent)
            cpu_item.setData(Qt.UserRole + 1, f"""
                color: {text_color}; 
                background-color: {bg_color};
                padding: 4px 10px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            """)
            self.agents_table.setItem(row, 3, cpu_item)
            
            # Tiempo activo
            time_item = QTableWidgetItem(f"⏱️ {time}")
            time_item.setForeground(Qt.transparent)
            time_item.setData(Qt.UserRole + 1, "color: #6b7280; font-size: 12px;")
            self.agents_table.setItem(row, 4, time_item)
                
    def _load_metrics(self):
        """Cargar métricas de agentes"""
        pass
        
    def _show_help_manual(self):
        """Mostrar manual de ayuda de Gestión de Agentes"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Manual de Gestión de Agentes - MININA v3.0")
        dialog.setFixedSize(800, 500)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("📖 Manual de Gestión de Agentes")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #6366f1;
            background: transparent;
        """)
        layout.addWidget(title)
        
        help_text = """
        <h3>⚡ ¿Qué es la Gestión de Agentes?</h3>
        <p>Es el <b>centro de control de los agentes</b> de MININA. Aquí ves qué agentes están trabajando,
        en qué están ocupados y cómo está el uso de recursos.</p>
        
        <h3>🤖 Agentes Activos (Panel Izquierdo)</h3>
        <p>Muestra todos los agentes que están trabajando ahora mismo:</p>
        <ul>
        <li><b>🔹 ID del Agente:</b> Identificador único del agente</li>
        <li><b>Tipo Pool:</b> Qué tipo de trabajo hace (CPU, IO, Network, General)</li>
        <li><b>Skill Ejecutando:</b> Qué skill está corriendo ahora</li>
        <li><b>Uso CPU:</b> Cuánto procesador está usando (verde=bajo, amarillo=medio, rojo=alto)</li>
        <li><b>Tiempo Activo:</b> Cuánto tiempo lleva trabajando</li>
        </ul>
        
        <h3>📊 Pools de Agentes (Panel Derecho)</h3>
        <p>Barras de progreso que muestran cuántos agentes de cada tipo están ocupados:</p>
        <ul>
        <li><b>🔴 CPU_INTENSIVE:</b> Agentes para cálculos pesados (análisis, procesamiento)</li>
        <li><b>🟢 IO_INTENSIVE:</b> Agentes para lectura/escritura de archivos</li>
        <li><b>🟡 NETWORK:</b> Agentes para descargas, APIs, web scraping</li>
        <li><b>🔵 GENERAL:</b> Agentes para tareas variadas simples</li>
        </ul>
        
        <h3>🔄 Auto-Scaling</h3>
        <p>Sistema automático que ajusta la cantidad de agentes según la carga de trabajo.
        Si hay muchas tareas en cola, se crean más agentes automáticamente.</p>
        
        <h3>🎨 Códigos de Color</h3>
        <ul>
        <li><span style='color:#ef4444'>🔴 Rojo</span> - CPU alto / Pool CPU</li>
        <li><span style='color:#10b981'>🟢 Verde</span> - CPU bajo / Pool IO</li>
        <li><span style='color:#f59e0b'>🟡 Amarillo</span> - CPU medio / Pool Network</li>
        <li><span style='color:#3b82f6'>🔵 Azul</span> - Pool General</li>
        </ul>
        
        <p style='margin-top:20px;color:#666;'><i>💡 Consejo: Si ves muchos agentes en rojo, el sistema está muy cargado.</i></p>
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
