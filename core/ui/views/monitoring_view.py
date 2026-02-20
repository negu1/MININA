"""
MININA v3.0 - System Monitoring View
====================================
Vista avanzada de monitoreo del sistema con gráficos en tiempo real.
Muestra: CPU, RAM, Disco, Red, Procesos, Logs del sistema.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGridLayout, QFrame, QScrollArea,
    QProgressBar, QTabWidget, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient
import psutil
import time
from datetime import datetime
from collections import deque


class ResourceGraph(QFrame):
    """Widget de gráfico de recursos en tiempo real"""
    
    def __init__(self, title, color="#6366f1", max_points=60, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 150)
        self.setMaximumHeight(180)
        
        self.title = title
        self.color = QColor(color)
        self.max_points = max_points
        self.data = deque([0] * max_points, maxlen=max_points)
        self.current_value = 0
        
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {color};
        """)
        header.addWidget(title_label)
        
        header.addStretch()
        
        self.value_label = QLabel("0%")
        self.value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {color};
        """)
        header.addWidget(self.value_label)
        
        layout.addLayout(header)
        
        layout.addStretch()
    
    def add_value(self, value):
        """Agregar nuevo valor al gráfico"""
        self.data.append(value)
        self.current_value = value
        self.value_label.setText(f"{value:.1f}%")
        self.update()
    
    def paintEvent(self, event):
        """Dibujar gráfico"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Área del gráfico
        graph_rect = QRect(12, 45, self.width() - 24, self.height() - 60)
        
        # Fondo del gráfico
        painter.fillRect(graph_rect, QColor(15, 23, 42, 100))
        
        # Dibujar líneas de grid
        pen = QPen(QColor(255, 255, 255, 30))
        pen.setWidth(1)
        painter.setPen(pen)
        
        for i in range(5):
            y = graph_rect.top() + (graph_rect.height() * i / 4)
            painter.drawLine(graph_rect.left(), int(y), graph_rect.right(), int(y))
        
        # Dibujar área bajo la curva
        if len(self.data) > 1:
            gradient = QLinearGradient(graph_rect.topLeft(), graph_rect.bottomLeft())
            gradient.setColorAt(0, QColor(self.color.red(), self.color.green(), self.color.blue(), 100))
            gradient.setColorAt(1, QColor(self.color.red(), self.color.green(), self.color.blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            
            points = []
            x_step = graph_rect.width() / (self.max_points - 1)
            
            for i, value in enumerate(self.data):
                x = graph_rect.left() + (i * x_step)
                y = graph_rect.bottom() - (value / 100 * graph_rect.height())
                points.append((x, y))
            
            # Crear path para el área
            if points:
                path = QPainter()
                # Simplificado: dibujar línea
                painter.setPen(QPen(self.color, 2))
                painter.setBrush(Qt.NoBrush)
                
                for i in range(len(points) - 1):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.end()


class ProcessTable(QTableWidget):
    """Tabla de procesos del sistema"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["PID", "Nombre", "CPU %", "RAM MB", "Estado"])
        
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setMaximumHeight(300)
        
        self.setStyleSheet("""
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
                font-size: 11px;
            }
            QTableWidget::item {
                color: #e5e7eb;
                padding: 6px;
                font-size: 12px;
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.4);
            }
        """)


class LogViewer(QTextEdit):
    """Visor de logs en tiempo real"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(250)
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
    
    def add_log(self, level, message):
        """Agregar entrada de log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "INFO": "#22c55e",
            "WARN": "#f59e0b",
            "ERROR": "#ef4444",
            "DEBUG": "#6366f1"
        }
        
        color = colors.get(level, "#e5e7eb")
        
        html = f'<span style="color: rgba(226,232,240,0.5)">[{timestamp}]</span> '
        html += f'<span style="color: {color}">{level}</span>: {message}<br>'
        
        self.insertHtml(html)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        
        # Limitar líneas
        if self.document().blockCount() > 500:
            cursor = self.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()


class SystemMonitoringView(QWidget):
    """
    Vista de Monitoreo del Sistema - Dashboard avanzado de recursos
    """
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        # Historial de datos para gráficos
        self.cpu_history = deque([0] * 60, maxlen=60)
        self.ram_history = deque([0] * 60, maxlen=60)
        
        self._setup_ui()

        # Timers (se activan solo cuando la vista está visible)
        self.fast_timer = QTimer(self)
        self.fast_timer.timeout.connect(self._update_fast)

        self.heavy_timer = QTimer(self)
        self.heavy_timer.timeout.connect(self._update_heavy)
    
    def _setup_ui(self):
        """Configurar interfaz de monitoreo"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📈 Monitoreo del Sistema")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Indicador de actualización
        self.update_indicator = QLabel("● Live")
        self.update_indicator.setStyleSheet("color: #22c55e; font-size: 12px;")
        header_layout.addWidget(self.update_indicator)
        
        # Botón pausar/reanudar
        self.pause_btn = QPushButton("⏸️ Pausar")
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 0.2);
                color: #e5e7eb;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.4);
            }
        """)
        self.pause_btn.clicked.connect(self._toggle_monitoring)
        header_layout.addWidget(self.pause_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Monitoreo en tiempo real de recursos y procesos")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Gráficos principales
        graphs_layout = QHBoxLayout()
        graphs_layout.setSpacing(16)
        
        # CPU Graph
        self.cpu_graph = ResourceGraph("Uso de CPU", color="#6366f1")
        graphs_layout.addWidget(self.cpu_graph, 1)
        
        # RAM Graph
        self.ram_graph = ResourceGraph("Uso de RAM", color="#22c55e")
        graphs_layout.addWidget(self.ram_graph, 1)
        
        # Disco info
        disk_frame = QFrame()
        disk_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 12px;
            }
        """)
        disk_layout = QVBoxLayout(disk_frame)
        disk_layout.setContentsMargins(16, 16, 16, 16)
        
        disk_title = QLabel("💾 Almacenamiento")
        disk_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f59e0b;")
        disk_layout.addWidget(disk_title)
        
        self.disk_info = QLabel("Cargando...")
        self.disk_info.setStyleSheet("color: #e5e7eb; font-size: 12px;")
        disk_layout.addWidget(self.disk_info)
        
        self.disk_bar = QProgressBar()
        self.disk_bar.setMaximum(100)
        self.disk_bar.setValue(0)
        self.disk_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(15, 23, 42, 0.8);
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #f59e0b;
                border-radius: 4px;
            }
        """)
        disk_layout.addWidget(self.disk_bar)
        
        disk_layout.addStretch()
        graphs_layout.addWidget(disk_frame, 1)
        
        layout.addLayout(graphs_layout)
        
        layout.addSpacing(20)
        
        # Tabs inferiores
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
        
        # Tab 1: Procesos
        processes_tab = self._create_processes_tab()
        self.tabs.addTab(processes_tab, "⚙️ Procesos")
        
        # Tab 2: Red
        network_tab = self._create_network_tab()
        self.tabs.addTab(network_tab, "🌐 Red")
        
        # Tab 3: Logs
        logs_tab = self._create_logs_tab()
        self.tabs.addTab(logs_tab, "📋 Logs del Sistema")
        
        # Tab 4: Hardware
        hardware_tab = self._create_hardware_tab()
        self.tabs.addTab(hardware_tab, "🖥️ Hardware")
        
        layout.addWidget(self.tabs, 1)
    
    def _create_processes_tab(self):
        """Crear tab de procesos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Procesos del Sistema")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        self.process_table = ProcessTable()
        layout.addWidget(self.process_table)
        
        return tab
    
    def _create_network_tab(self):
        """Crear tab de red"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Estado de la Red")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        # Info de red
        self.network_info = QLabel("Cargando información de red...")
        self.network_info.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        layout.addWidget(self.network_info)
        
        layout.addStretch()
        
        return tab
    
    def _create_logs_tab(self):
        """Crear tab de logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        
        header = QLabel("Logs del Sistema")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Limpiar")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }
        """)
        clear_btn.clicked.connect(self._clear_logs)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer)
        
        # Agregar logs iniciales
        self.log_viewer.add_log("INFO", "System Monitoring iniciado")
        self.log_viewer.add_log("INFO", "Monitoreo de recursos activado")
        
        return tab
    
    def _create_hardware_tab(self):
        """Crear tab de hardware"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header = QLabel("Información del Hardware")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        self.hardware_info = QLabel("Cargando...")
        self.hardware_info.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        self.hardware_info.setWordWrap(True)
        layout.addWidget(self.hardware_info)
        
        layout.addStretch()
        
        return tab
    
    def _update_fast(self):
        """Actualizar métricas rápidas (bajo costo)"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=None)
            self.cpu_graph.add_value(cpu_percent)
            
            # RAM
            ram = psutil.virtual_memory()
            self.ram_graph.add_value(ram.percent)
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.disk_bar.setValue(int(disk_percent))
            
            disk_gb_used = disk.used / (1024**3)
            disk_gb_total = disk.total / (1024**3)
            self.disk_info.setText(
                f"Usado: {disk_gb_used:.1f} GB / Total: {disk_gb_total:.1f} GB ({disk_percent:.1f}%)"
            )
            
            # Log periódico
            if cpu_percent > 80:
                self.log_viewer.add_log("WARN", f"Uso de CPU alto: {cpu_percent:.1f}%")
            if ram.percent > 85:
                self.log_viewer.add_log("WARN", f"Uso de RAM alto: {ram.percent:.1f}%")
                
        except Exception as e:
            self.log_viewer.add_log("ERROR", f"Error en monitoreo: {str(e)}")

    def _update_heavy(self):
        """Actualizar métricas pesadas (procesos/red/hardware)"""
        try:
            self._update_processes()
            self._update_network()
            self._update_hardware()
        except Exception:
            pass
    
    def _update_processes(self):
        """Actualizar tabla de procesos"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
                try:
                    info = proc.info
                    if info['cpu_percent'] is not None and info['cpu_percent'] > 0:
                        processes.append(info)
                except:
                    pass
            
            # Ordenar por uso de CPU
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            # Mostrar top 20
            self.process_table.setRowCount(min(len(processes), 20))
            
            for i, proc in enumerate(processes[:20]):
                self.process_table.setItem(i, 0, QTableWidgetItem(str(proc['pid'])))
                self.process_table.setItem(i, 1, QTableWidgetItem(str(proc['name'])[:30]))
                self.process_table.setItem(i, 2, QTableWidgetItem(f"{proc['cpu_percent']:.1f}%"))
                
                ram_mb = proc['memory_info'].rss / (1024**2) if proc['memory_info'] else 0
                self.process_table.setItem(i, 3, QTableWidgetItem(f"{ram_mb:.1f}"))
                self.process_table.setItem(i, 4, QTableWidgetItem(str(proc['status'])))
                
        except Exception as e:
            pass  # Silenciar errores de procesos
    
    def _update_network(self):
        """Actualizar info de red"""
        try:
            net_io = psutil.net_io_counters()
            
            sent_mb = net_io.bytes_sent / (1024**2)
            recv_mb = net_io.bytes_recv / (1024**2)
            
            info_text = f"""
            <b>Estadísticas de Red:</b><br>
            <b>Datos enviados:</b> {sent_mb:.2f} MB<br>
            <b>Datos recibidos:</b> {recv_mb:.2f} MB<br>
            <b>Paquetes enviados:</b> {net_io.packets_sent:,}<br>
            <b>Paquetes recibidos:</b> {net_io.packets_recv:,}<br>
            <b>Errores entrada:</b> {net_io.errin}<br>
            <b>Errores salida:</b> {net_io.errout}<br>
            <b>Drops entrada:</b> {net_io.dropin}<br>
            <b>Drops salida:</b> {net_io.dropout}
            """
            
            self.network_info.setText(info_text)
            
        except Exception as e:
            self.network_info.setText(f"Error obteniendo info de red: {e}")
    
    def _update_hardware(self):
        """Actualizar info de hardware"""
        try:
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            info_text = f"""
            <b>CPU:</b><br>
            Núcleos físicos: {psutil.cpu_count(logical=False)}<br>
            Núcleos lógicos: {cpu_count}<br>
            Frecuencia: {cpu_freq.current:.0f} MHz (min: {cpu_freq.min:.0f}, max: {cpu_freq.max:.0f})<br><br>
            
            <b>Memoria:</b><br>
            Total: {psutil.virtual_memory().total / (1024**3):.2f} GB<br><br>
            
            <b>Disco:</b><br>
            Particiones: {len(psutil.disk_partitions())}<br>
            """
            
            self.hardware_info.setText(info_text)
            
        except Exception as e:
            self.hardware_info.setText(f"Error: {e}")
    
    def _toggle_monitoring(self):
        """Pausar/reanudar monitoreo"""
        if self.fast_timer.isActive() or self.heavy_timer.isActive():
            if self.fast_timer.isActive():
                self.fast_timer.stop()
            if self.heavy_timer.isActive():
                self.heavy_timer.stop()
            self.pause_btn.setText("▶️ Reanudar")
            self.update_indicator.setText("● Pausado")
            self.update_indicator.setStyleSheet("color: #ef4444; font-size: 12px;")
            self.log_viewer.add_log("INFO", "Monitoreo pausado")
        else:
            self.fast_timer.start(1000)
            self.heavy_timer.start(4000)
            self.pause_btn.setText("⏸️ Pausar")
            self.update_indicator.setText("● Live")
            self.update_indicator.setStyleSheet("color: #22c55e; font-size: 12px;")
            self.log_viewer.add_log("INFO", "Monitoreo reanudado")
    
    def _clear_logs(self):
        """Limpiar logs"""
        self.log_viewer.clear()
        self.log_viewer.add_log("INFO", "Logs limpiados")
    
    def on_activated(self):
        """Llamado cuando la vista se activa"""
        if not self.fast_timer.isActive():
            self.fast_timer.start(1000)
        if not self.heavy_timer.isActive():
            self.heavy_timer.start(4000)
        self._update_fast()

    def on_deactivated(self):
        """Llamado cuando la vista se desactiva"""
        if self.fast_timer.isActive():
            self.fast_timer.stop()
        if self.heavy_timer.isActive():
            self.heavy_timer.stop()

