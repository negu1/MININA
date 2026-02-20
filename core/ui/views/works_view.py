"""
MININA v3.0 - Works View (UI Local)
Vista de archivos generados - INTEGRACIÓN REAL CON BACKEND
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, 
    QFileDialog, QMessageBox, QComboBox,
    QSplitter, QFrame, QTextEdit, QScrollArea
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage
from pathlib import Path
import shutil

# INTEGRACIÓN: Importar API client y category names
from core.ui.api_client import api_client
from core.file_manager import works_manager, CATEGORY_NAMES


class WorksView(QWidget):
    """
    Vista de Works - Archivos generados por skills
    INTEGRADO CON BACKEND FASTAPI
    """
    
    def __init__(self):
        super().__init__()
        self.current_category = "all"
        self.current_work = None
        self.works_data = {}  # Cache de works
        self._setup_ui()
        self._load_works_from_api()  # Cargar desde API
        
    def _setup_ui(self):
        """Configurar interfaz elegante de Works"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Panel izquierdo
        left_panel = self._create_left_panel()
        layout.addWidget(left_panel, 2)
        
        # Panel derecho
        right_panel = self._create_right_panel()
        layout.addWidget(right_panel, 3)
        
    def _create_left_panel(self) -> QWidget:
        """Crear panel izquierdo con filtros y lista - Estilo moderno"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.55);
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.16);
            }
        """)
        
        # Sombra
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
        
        icon_label = QLabel("📦")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        header_text = QLabel("Works")
        header_text.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(header_text)
        header_layout.addStretch()
        
        self.connection_label = QLabel("🟡")
        self.connection_label.setStyleSheet("font-size: 12px;")
        self.connection_label.setToolTip("Conectando...")
        header_layout.addWidget(self.connection_label)
        
        layout.addLayout(header_layout)
        
        # Subtítulo
        subtitle = QLabel("Archivos generados por los skills")
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
        
        # Filtros
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Categoría:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas", "all")
        for cat_id, cat_name in CATEGORY_NAMES.items():
            self.category_combo.addItem(cat_name, cat_id)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_combo)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Refrescar desde servidor")
        self.refresh_btn.clicked.connect(self._load_works_from_api)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Lista de archivos
        self.works_list = QListWidget()
        self.works_list.setMinimumWidth(400)
        self.works_list.itemClicked.connect(self._on_work_selected)
        layout.addWidget(self.works_list)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("💾 Descargar")
        self.download_btn.clicked.connect(self._download_selected_api)
        self.download_btn.setEnabled(False)
        buttons_layout.addWidget(self.download_btn)
        
        self.open_location_btn = QPushButton("📂 Abrir Ubicación")
        self.open_location_btn.clicked.connect(self._open_location_api)
        self.open_location_btn.setEnabled(False)
        buttons_layout.addWidget(self.open_location_btn)
        
        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.clicked.connect(self._delete_selected_api)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """Crear panel derecho de preview"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_header = QLabel("👁️ Vista Previa")
        self.preview_header.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.preview_header)
        
        self.file_info = QLabel("Selecciona un archivo para ver detalles")
        self.file_info.setStyleSheet("color: #666; font-size: 12px;")
        self.file_info.setWordWrap(True)
        layout.addWidget(self.file_info)
        layout.addSpacing(10)
        
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setFrameShape(QFrame.StyledPanel)
        
        self.preview_content = QLabel("No hay archivo seleccionado")
        self.preview_content.setAlignment(Qt.AlignCenter)
        self.preview_content.setMinimumHeight(300)
        
        self.preview_area.setWidget(self.preview_content)
        layout.addWidget(self.preview_area)
        
        return panel
        
    def _load_works_from_api(self):
        """INTEGRACIÓN REAL: Cargar works desde API backend"""
        self.connection_label.setText("🟡 Cargando...")
        self.works_list.clear()
        self.works_data = {}
        
        # Verificar conexión
        if not api_client.health_check():
            self.connection_label.setText("🔴 Sin conexión al servidor (puerto 8897)")
            self._load_works_fallback()  # Fallback a modo offline
            return
        
        # Cargar desde API
        works = api_client.get_works(
            category=self.current_category if self.current_category != "all" else None
        )
        
        if not works:
            self.connection_label.setText("🟢 Conectado - Sin archivos")
            return
            
        self.connection_label.setText(f"🟢 Conectado - {len(works)} archivos")
        
        for work in works:
            self.works_data[work['id']] = work
            
            item = QListWidgetItem()
            item.setData(Qt.UserRole, work['id'])
            
            size_mb = work['size'] / 1024 / 1024
            text = f"{work['original_name']}\n"
            text += f"  {size_mb:.2f} MB | {work['skill_name']} | {work['created_at'][:16]}"
            
            item.setText(text)
            self.works_list.addItem(item)
            
    def _load_works_fallback(self):
        """Fallback: Cargar desde file_manager local si API no disponible"""
        works = works_manager.get_all_works(
            category=self.current_category if self.current_category != "all" else None
        )
        
        for work in works:
            self.works_data[work['id']] = work
            
            item = QListWidgetItem()
            item.setData(Qt.UserRole, work['id'])
            
            size_mb = work['size'] / 1024 / 1024
            text = f"{work['original_name']}\n"
            text += f"  {size_mb:.2f} MB | {work['skill_name']} | {work['created_at'][:16]}"
            
            item.setText(text)
            self.works_list.addItem(item)
        
    def _on_category_changed(self, index):
        """Cambiar categoría filtrada"""
        self.current_category = self.category_combo.currentData()
        self._load_works_from_api()
        
    def _on_work_selected(self, item: QListWidgetItem):
        """Manejar selección de trabajo"""
        work_id = item.data(Qt.UserRole)
        work = self.works_data.get(work_id)
        
        if not work:
            return
            
        self.current_work = work
        
        # Habilitar botones
        self.download_btn.setEnabled(True)
        self.open_location_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        
        # Mostrar info
        size_mb = work['size'] / 1024 / 1024
        info = f"""
        <b>Nombre:</b> {work['original_name']}<br>
        <b>Categoría:</b> {CATEGORY_NAMES.get(work['category'], work['category'])}<br>
        <b>Tamaño:</b> {size_mb:.2f} MB<br>
        <b>Skill:</b> {work['skill_name']}<br>
        <b>Creado:</b> {work['created_at']}<br>
        <b>ID:</b> {work['id']}
        """
        self.file_info.setText(info)
        
        # Preview básico (sin archivo local)
        ext = Path(work['original_name']).suffix.lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            self.preview_content.setText("🖼️ Imagen - Use 'Descargar' para ver")
        elif ext == '.pdf':
            self.preview_content.setText("📄 PDF - Use 'Descargar' para ver")
        elif ext in ['.csv', '.txt', '.json', '.py']:
            self.preview_content.setText("📄 Archivo de texto - Use 'Descargar' para ver")
        else:
            self.preview_content.setText(f"📁 {ext.upper()} - Use 'Descargar' para abrir")
        
    def _download_selected_api(self):
        """INTEGRACIÓN REAL: Descargar desde API"""
        if not self.current_work:
            return
            
        work = self.current_work
        
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo",
            str(Path.home() / "Downloads" / work['original_name']),
            "All Files (*.*)"
        )
        
        if not destination:
            return
            
        # Intentar descargar desde API
        if api_client.health_check():
            success = api_client.download_work(work['id'], Path(destination))
            if success:
                QMessageBox.information(self, "Éxito", f"Archivo descargado:\n{destination}")
                return
        
        # Fallback: copiar desde sistema de archivos local
        file_path = works_manager.get_file_path(work['id'])
        
        if file_path and file_path.exists():
            try:
                shutil.copy2(str(file_path), destination)
                QMessageBox.information(self, "Éxito", f"Archivo guardado:\n{destination}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo descargar:\n{str(e)}")
        else:
            QMessageBox.critical(self, "Error", "Archivo no encontrado en servidor ni local")
            
    def _open_location_api(self):
        """Abrir ubicación del archivo"""
        if not self.current_work:
            return
            
        # Fallback a sistema local
        file_path = works_manager.get_file_path(self.current_work['id'])
        
        if file_path and file_path.exists():
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))
        else:
            QMessageBox.information(self, "Info", "Ubicación solo disponible para archivos locales")
            
    def _delete_selected_api(self):
        """INTEGRACIÓN REAL: Eliminar vía API"""
        if not self.current_work:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar permanentemente '{self.current_work['original_name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.Yes:
            # Intentar eliminar vía API
            success = False
            if api_client.health_check():
                success = api_client.delete_work(self.current_work['id'])
            
            # Fallback a eliminación local
            if not success:
                success = works_manager.delete_work(self.current_work['id'])
            
            if success:
                self._load_works_from_api()
                self.current_work = None
                self.download_btn.setEnabled(False)
                self.open_location_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.file_info.setText("Selecciona un archivo para ver detalles")
                self.preview_content.setText("No hay archivo seleccionado")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el archivo")
