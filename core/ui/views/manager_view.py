"""
MININA v3.0 - Manager View (Capa 4)
Gestión de agentes y pools de recursos
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt


class ManagerView(QWidget):
    """
    Vista de Manager - Gestión de agentes y recursos
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_metrics()
        
    def _setup_ui(self):
        """Configurar interfaz elegante del Manager"""
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
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Pools de agentes, métricas y auto-scaling")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.72);
            margin-bottom: 8px;
        """)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Pools de Agentes
        pools_group = QGroupBox("Pools de Agentes")
        pools_layout = QVBoxLayout(pools_group)
        
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
        
        layout.addWidget(pools_group)
        
        # Tabla de Agentes Activos
        agents_group = QGroupBox("Agentes Activos")
        agents_layout = QVBoxLayout(agents_group)
        
        self.agents_table = QTableWidget()
        self.agents_table.setColumnCount(5)
        self.agents_table.setHorizontalHeaderLabels([
            "ID", "Pool", "Skill", "CPU", "Tiempo"
        ])
        self.agents_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self._load_agents_table()
        
        agents_layout.addWidget(self.agents_table)
        layout.addWidget(agents_group)
        
        # Auto-Scaling
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
        
        layout.addStretch()
        
    def _create_pool_bar(self, name: str, status: str, percentage: int) -> QHBoxLayout:
        """Crear barra de progreso para un pool"""
        layout = QHBoxLayout()
        
        label = QLabel(name)
        label.setFixedWidth(150)
        layout.addWidget(label)
        
        bar = QProgressBar()
        bar.setValue(percentage)
        bar.setTextVisible(True)
        bar.setFormat(status)
        layout.addWidget(bar)
        
        return layout
        
    def _load_agents_table(self):
        """Cargar datos de agentes en la tabla"""
        example_data = [
            ["agent_001", "CPU", "data_analysis", "45%", "5m"],
            ["agent_002", "NETWORK", "web_scraper", "12%", "2m"],
            ["agent_003", "IO", "file_processor", "8%", "10m"],
        ]
        
        self.agents_table.setRowCount(len(example_data))
        for row, data in enumerate(example_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                self.agents_table.setItem(row, col, item)
                
    def _load_metrics(self):
        """Cargar métricas de agentes"""
        pass
