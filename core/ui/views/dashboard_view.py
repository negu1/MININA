"""
MININA v3.0 - Dashboard View
============================
Vista de resumen del sistema con métricas en tiempo real.
Muestra: skills, APIs, works, estado del sistema, actividades recientes.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGridLayout, QFrame, QScrollArea,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush
import psutil
import json
import os
from datetime import datetime
from pathlib import Path

from core.ui.api_client import api_client
from core.api_registry import get_api_registry


class MetricCard(QFrame):
    """Card visual para mostrar una métrica del sistema"""
    
    def __init__(self, title, value, subtitle="", color="#6366f1", icon="📊", parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 140)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(15, 23, 42, 0.8),
                    stop:1 rgba(15, 23, 42, 0.6));
                border: 1px solid {color}40;
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # Header con icono y título
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: rgba(226, 232, 240, 0.85);
        """)
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)
        
        # Valor principal
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {color};
        """)
        layout.addWidget(self.value_label)
        
        # Subtítulo
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setStyleSheet("""
                font-size: 11px;
                color: rgba(226, 232, 240, 0.78);
            """)
            layout.addWidget(sub_label)
        
        layout.addStretch()
    
    def update_value(self, new_value):
        """Actualizar el valor mostrado"""
        self.value_label.setText(str(new_value))


class StatusIndicator(QFrame):
    """Indicador de estado (online/offline)"""
    
    def __init__(self, name, is_online=True, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)
        
        # Indicador de color
        self.indicator = QLabel("●")
        self.indicator.setStyleSheet(
            f"color: {'#22c55e' if is_online else '#ef4444'}; font-size: 14px;"
        )
        layout.addWidget(self.indicator)
        
        # Nombre
        name_label = QLabel(name)
        name_label.setStyleSheet("color: rgba(226, 232, 240, 0.9); font-size: 13px;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Status text
        self.status_label = QLabel("Online" if is_online else "Offline")
        self.status_label.setStyleSheet(
            f"color: {'#22c55e' if is_online else '#ef4444'}; font-size: 11px;"
        )
        layout.addWidget(self.status_label)
    
    def set_status(self, is_online):
        """Cambiar el estado visual"""
        color = "#22c55e" if is_online else "#ef4444"
        text = "Online" if is_online else "Offline"
        self.indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")


class ActivityItem(QFrame):
    """Item de actividad reciente"""
    
    def __init__(self, icon, message, time_str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.4);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon_label)
        
        # Mensaje
        msg_layout = QVBoxLayout()
        msg_layout.setSpacing(2)
        
        msg_label = QLabel(message)
        msg_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        msg_layout.addWidget(msg_label)
        
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-size: 11px;")
        msg_layout.addWidget(time_label)
        
        layout.addLayout(msg_layout, stretch=1)


class DashboardView(QWidget):
    """
    Dashboard principal de MININA v3.0
    Vista de resumen con métricas en tiempo real
    """
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        # Configurar UI
        self._setup_ui()
        
        # Timer para actualización automática (se activa solo cuando la vista está visible)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_data)
    
    def _setup_ui(self):
        """Configurar interfaz del dashboard"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Dashboard del Sistema")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón refresh
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setStyleSheet("""
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
        refresh_btn.clicked.connect(self._refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Resumen en tiempo real del estado de MININA")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Grid de métricas principales
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        
        self.skills_card = MetricCard(
            "SKILLS", "0", "Activas en el sistema",
            color="#22c55e", icon="🔧"
        )
        metrics_layout.addWidget(self.skills_card)
        
        self.apis_card = MetricCard(
            "APIS CONFIGURADAS", "0", "De 25 disponibles",
            color="#6366f1", icon="🔌"
        )
        metrics_layout.addWidget(self.apis_card)
        
        self.works_card = MetricCard(
            "WORKS GENERADOS", "0", "Archivos en data/works",
            color="#f59e0b", icon="📦"
        )
        metrics_layout.addWidget(self.works_card)
        
        self.system_card = MetricCard(
            "ESTADO", "✅", "Sistema operativo",
            color="#ec4899", icon="⚡"
        )
        metrics_layout.addWidget(self.system_card)
        
        layout.addLayout(metrics_layout)
        
        layout.addSpacing(20)
        
        # Sección inferior: 2 columnas
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Columna izquierda: Estado de componentes
        left_column = QVBoxLayout()
        
        components_title = QLabel("🖥️ Estado de Componentes")
        components_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
            margin-bottom: 12px;
        """)
        left_column.addWidget(components_title)
        
        # Indicadores de estado
        self.indicators = {}
        
        indicators_data = [
            ("SkillVault", True),
            ("Agent Manager", True),
            ("CortexBus", True),
            ("API Registry", True),
            ("Memory Core", True),
            ("System Watchdog", True),
        ]
        
        for name, status in indicators_data:
            indicator = StatusIndicator(name, status)
            self.indicators[name] = indicator
            left_column.addWidget(indicator)
        
        left_column.addStretch()
        
        # Métricas de recursos
        resources_title = QLabel("📈 Recursos del Sistema")
        resources_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
            margin-top: 20px;
            margin-bottom: 12px;
        """)
        left_column.addWidget(resources_title)
        
        # CPU
        cpu_layout = QHBoxLayout()
        cpu_label = QLabel("CPU")
        cpu_label.setStyleSheet("color: rgba(226, 232, 240, 0.7); font-size: 12px;")
        cpu_layout.addWidget(cpu_label)
        
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setValue(0)
        self.cpu_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(15, 23, 42, 0.6);
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #6366f1;
                border-radius: 4px;
            }
        """)
        cpu_layout.addWidget(self.cpu_bar)
        
        self.cpu_label = QLabel("0%")
        self.cpu_label.setStyleSheet("color: #6366f1; font-size: 12px; min-width: 40px;")
        cpu_layout.addWidget(self.cpu_label)
        
        left_column.addLayout(cpu_layout)
        
        # RAM
        ram_layout = QHBoxLayout()
        ram_label = QLabel("RAM")
        ram_label.setStyleSheet("color: rgba(226, 232, 240, 0.7); font-size: 12px;")
        ram_layout.addWidget(ram_label)
        
        self.ram_bar = QProgressBar()
        self.ram_bar.setMaximum(100)
        self.ram_bar.setValue(0)
        self.ram_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(15, 23, 42, 0.6);
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #22c55e;
                border-radius: 4px;
            }
        """)
        ram_layout.addWidget(self.ram_bar)
        
        self.ram_label = QLabel("0%")
        self.ram_label.setStyleSheet("color: #22c55e; font-size: 12px; min-width: 40px;")
        ram_layout.addWidget(self.ram_label)
        
        left_column.addLayout(ram_layout)
        
        # Disco
        disk_layout = QHBoxLayout()
        disk_label = QLabel("Disco")
        disk_label.setStyleSheet("color: rgba(226, 232, 240, 0.7); font-size: 12px;")
        disk_layout.addWidget(disk_label)
        
        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        self.disk_bar.setValue(0)
        self.disk_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(15, 23, 42, 0.6);
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #f59e0b;
                border-radius: 4px;
            }
        """)
        disk_layout.addWidget(self.disk_bar)
        
        self.disk_label = QLabel("0%")
        self.disk_label.setStyleSheet("color: #f59e0b; font-size: 12px; min-width: 40px;")
        disk_layout.addWidget(self.disk_label)
        
        left_column.addLayout(disk_layout)
        
        left_column.addStretch()
        
        bottom_layout.addLayout(left_column, 1)
        
        # Columna derecha: Actividades recientes
        right_column = QVBoxLayout()
        
        activity_title = QLabel("🕐 Actividades Recientes")
        activity_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
            margin-bottom: 12px;
        """)
        right_column.addWidget(activity_title)
        
        # Scroll area para actividades
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        scroll_content = QWidget()
        self.activity_layout = QVBoxLayout(scroll_content)
        self.activity_layout.setSpacing(8)
        self.activity_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        right_column.addWidget(scroll)
        
        bottom_layout.addLayout(right_column, 2)
        
        layout.addLayout(bottom_layout, 1)
    
    def _refresh_data(self):
        """Actualizar todos los datos del dashboard"""
        try:
            # Contar skills
            self._update_skills_count()
            
            # Contar APIs configuradas
            self._update_apis_count()
            
            # Contar works
            self._update_works_count()
            
            # Métricas de sistema
            self._update_system_metrics()
            
            # Indicadores
            self._update_indicators()
            
            # Actividades (simuladas por ahora)
            self._update_activities()
            
        except Exception as e:
            print(f"Error actualizando dashboard: {e}")
    
    def _update_skills_count(self):
        """Actualizar contador de skills"""
        try:
            skills = api_client.get_skills()
            count = len(skills)
            self.skills_card.update_value(str(count))
        except:
            self.skills_card.update_value("0")
    
    def _update_apis_count(self):
        """Actualizar contador de APIs configuradas"""
        try:
            registry = get_api_registry()
            apis = registry.get_all_apis()
            configured = sum(1 for api in apis.values() if api.is_configured)
            self.apis_card.update_value(f"{configured}/{len(apis)}")
        except:
            # Fallback: contar desde archivo
            try:
                config_path = 'data/api_config.json'
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    # Contar APIs configuradas
                    count = 0
                    for cat_data in config.values():
                        if isinstance(cat_data, dict):
                            count += len(cat_data)
                    self.apis_card.update_value(str(count))
                else:
                    self.apis_card.update_value("0")
            except:
                self.apis_card.update_value("0")
    
    def _update_works_count(self):
        """Actualizar contador de works"""
        try:
            works = api_client.get_works()
            count = len(works)
            self.works_card.update_value(str(count))
        except:
            # Fallback: contar archivos
            try:
                works_dir = Path("data/works")
                if works_dir.exists():
                    count = len(list(works_dir.glob("**/*")))
                    self.works_card.update_value(str(count))
                else:
                    self.works_card.update_value("0")
            except:
                self.works_card.update_value("0")
    
    def _update_system_metrics(self):
        """Actualizar métricas de CPU, RAM, disco"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            self.cpu_bar.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # RAM
            ram = psutil.virtual_memory()
            self.ram_bar.setValue(int(ram.percent))
            self.ram_label.setText(f"{ram.percent}%")
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_bar.setValue(int(disk_percent))
            self.disk_label.setText(f"{disk_percent:.1f}%")
            
        except Exception as e:
            print(f"Error obteniendo métricas del sistema: {e}")
    
    def _update_indicators(self):
        """Actualizar indicadores de componentes"""
        try:
            # Verificar health de API client
            is_healthy = api_client.health_check()
            
            # Actualizar indicadores según estado
            self.indicators["SkillVault"].set_status(is_healthy)
            self.indicators["Agent Manager"].set_status(is_healthy)
            self.indicators["CortexBus"].set_status(is_healthy)
            
            # API Registry - verificar si hay APIs configuradas
            try:
                registry = get_api_registry()
                has_apis = len(registry.get_all_apis()) > 0
                self.indicators["API Registry"].set_status(has_apis)
            except:
                self.indicators["API Registry"].set_status(False)
            
            # Memory y Watchdog - asumir ok si core está funcionando
            self.indicators["Memory Core"].set_status(is_healthy)
            self.indicators["System Watchdog"].set_status(is_healthy)
            
        except Exception as e:
            print(f"Error actualizando indicadores: {e}")
    
    def _update_activities(self):
        """Actualizar lista de actividades recientes"""
        # Limpiar actividades actuales (excepto stretch)
        while self.activity_layout.count() > 1:
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Obtener actividades reales del sistema (simuladas por ahora)
        activities = self._get_recent_activities()
        
        for activity in activities:
            item = ActivityItem(
                activity["icon"],
                activity["message"],
                activity["time"]
            )
            self.activity_layout.insertWidget(0, item)
    
    def _get_recent_activities(self):
        """Obtener actividades recientes del sistema"""
        activities = []
        
        try:
            # Verificar skills ejecutadas recientemente
            works_dir = Path("data/works")
            if works_dir.exists():
                # Buscar archivos más recientes
                files = sorted(works_dir.glob("**/*"), key=lambda x: x.stat().st_mtime, reverse=True)[:5]
                for f in files:
                    if f.is_file():
                        mtime = datetime.fromtimestamp(f.stat().st_mtime)
                        time_str = mtime.strftime("%H:%M:%S")
                        activities.append({
                            "icon": "📄",
                            "message": f"Work generado: {f.name}",
                            "time": time_str
                        })
        except:
            pass
        
        # Si no hay actividades, mostrar mensaje de sistema
        if not activities:
            activities = [
                {"icon": "✅", "message": "Sistema iniciado correctamente", "time": "Ahora"},
                {"icon": "🔧", "message": "Dashboard cargado", "time": "Ahora"},
            ]
        
        return activities[:10]  # Máximo 10 actividades
    
    def on_activated(self):
        """Llamado cuando la vista se activa"""
        if not self.refresh_timer.isActive():
            self.refresh_timer.start(8000)
        self._refresh_data()

    def on_deactivated(self):
        """Llamado cuando la vista se desactiva"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()

