"""
Nuevo Settings View con navegación por categorías de APIs
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QLineEdit,
    QStackedWidget, QGridLayout, QMessageBox, QCheckBox,
    QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from core.ui.views.api_categories_structure import API_CATEGORIES
import json
import os


class CategoryButton(QPushButton):
    """Botón personalizado para categorías de APIs"""
    def __init__(self, icon, name, description, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 120)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Icono
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # Nombre
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)
        
        # Descripción
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 11px;
            color: rgba(226, 232, 240, 0.6);
        """)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Estilo del botón
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(15, 23, 42, 0.6);
                border: 2px solid {color}40;
                border-radius: 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(15, 23, 42, 0.8);
                border: 2px solid {color};
            }}
        """)


class APIItemButton(QPushButton):
    """Botón para una API específica en el listado"""
    def __init__(self, api_id, api_data, is_configured=False, parent=None):
        super().__init__(parent)
        self.api_id = api_id
        self.setFixedHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icono
        icon_label = QLabel(api_data["icon"])
        icon_label.setStyleSheet("font-size: 28px;")
        layout.addWidget(icon_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        name_label = QLabel(api_data["name"])
        name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(api_data["description"])
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.6);
        """)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Indicador de estado
        status = "🟢" if is_configured else "⚪"
        status_label = QLabel(status)
        status_label.setStyleSheet("font-size: 20px;")
        status_label.setToolTip("Configurado" if is_configured else "Sin configurar")
        layout.addWidget(status_label)
        
        # Flecha
        arrow = QLabel("›")
        arrow.setStyleSheet("""
            font-size: 24px;
            color: rgba(226, 232, 240, 0.4);
        """)
        layout.addWidget(arrow)
        
        # Estilo
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(15, 23, 42, 0.4);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(99, 102, 241, 0.4);
            }
        """)


class BackButton(QPushButton):
    """Botón de regreso"""
    def __init__(self, text="← Volver", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 14px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                color: #e5e7eb;
            }
        """)


class SettingsViewV2(QWidget):
    """Nueva vista de Settings con navegación por categorías"""
    
    def __init__(self, api_client=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.config_path = 'data/api_config.json'
        self.current_category = None
        self.current_api = None
        
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self):
        """Configurar interfaz principal"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stack de pantallas
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Pantalla 1: Selección de categoría
        self.category_screen = self._create_category_screen()
        self.stack.addWidget(self.category_screen)
        
        # Pantalla 2: Listado de APIs en categoría
        self.api_list_screen = self._create_api_list_screen()
        self.stack.addWidget(self.api_list_screen)
        
        # Pantalla 3: Configuración de API específica
        self.api_config_screen = self._create_api_config_screen()
        self.stack.addWidget(self.api_config_screen)
        
        # Mostrar pantalla de categorías primero
        self.stack.setCurrentIndex(0)
    
    def _create_category_screen(self):
        """Crear pantalla de selección de categoría"""
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
            }
        """)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0f172a;
            }
        """)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("⚙️ Configuración de APIs")
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Selecciona una categoría para configurar las APIs")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.6);
            margin-bottom: 16px;
        """)
        layout.addWidget(subtitle)
        
        # Grid de categorías
        grid = QGridLayout()
        grid.setSpacing(20)
        
        row = 0
        col = 0
        for cat_id, cat_data in API_CATEGORIES.items():
            btn = CategoryButton(
                cat_data["name"].split()[0],  # Icono
                " ".join(cat_data["name"].split()[1:]),  # Nombre sin icono
                cat_data["description"],
                cat_data["color"]
            )
            btn.clicked.connect(lambda checked, cid=cat_id: self._show_api_list(cid))
            grid.addWidget(btn, row, col)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        layout.addLayout(grid)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(screen)
        main_layout.addWidget(scroll)
        
        return screen
    
    def _create_api_list_screen(self):
        """Crear pantalla de listado de APIs"""
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
            }
        """)
        
        self.api_list_layout = QVBoxLayout(screen)
        self.api_list_layout.setContentsMargins(40, 40, 40, 40)
        self.api_list_layout.setSpacing(20)
        
        # Se llenará dinámicamente cuando se seleccione una categoría
        return screen
    
    def _create_api_config_screen(self):
        """Crear pantalla de configuración de API"""
        screen = QFrame()
        screen.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
            }
        """)
        
        self.api_config_layout = QVBoxLayout(screen)
        self.api_config_layout.setContentsMargins(40, 40, 40, 40)
        self.api_config_layout.setSpacing(20)
        
        # Se llenará dinámicamente cuando se seleccione una API
        return screen
    
    def _show_api_list(self, category_id):
        """Mostrar listado de APIs de una categoría"""
        self.current_category = category_id
        cat_data = API_CATEGORIES[category_id]
        
        # Limpiar layout anterior
        while self.api_list_layout.count():
            item = self.api_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Header con botón de regreso
        header_layout = QHBoxLayout()
        
        back_btn = BackButton()
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        self.api_list_layout.addLayout(header_layout)
        
        # Título de categoría
        title = QLabel(cat_data["name"])
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {cat_data["color"]};
        """)
        self.api_list_layout.addWidget(title)
        
        # Descripción
        desc = QLabel(cat_data["description"])
        desc.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.6);
            margin-bottom: 20px;
        """)
        self.api_list_layout.addWidget(desc)
        
        # Listado de APIs
        if "subcategories" in cat_data:
            # Categoría con subcategorías (Business)
            for sub_id, sub_data in cat_data["subcategories"].items():
                sub_label = QLabel(sub_data["name"])
                sub_label.setStyleSheet("""
                    font-size: 14px;
                    font-weight: bold;
                    color: #94a3b8;
                    margin-top: 16px;
                    margin-bottom: 8px;
                """)
                self.api_list_layout.addWidget(sub_label)
                
                for api_id, api_data in sub_data["apis"].items():
                    is_configured = self._is_api_configured(api_id, api_data)
                    btn = APIItemButton(api_id, api_data, is_configured)
                    btn.clicked.connect(lambda checked, aid=api_id, ad=api_data: self._show_api_config(aid, ad))
                    self.api_list_layout.addWidget(btn)
        else:
            # Categoría simple
            for api_id, api_data in cat_data["apis"].items():
                is_configured = self._is_api_configured(api_id, api_data)
                btn = APIItemButton(api_id, api_data, is_configured)
                btn.clicked.connect(lambda checked, aid=api_id, ad=api_data: self._show_api_config(aid, ad))
                self.api_list_layout.addWidget(btn)
        
        self.api_list_layout.addStretch()
        
        # Mostrar pantalla
        self.stack.setCurrentIndex(1)
    
    def _show_api_config(self, api_id, api_data):
        """Mostrar pantalla de configuración de una API"""
        self.current_api = api_id
        
        # Limpiar layout anterior
        while self.api_config_layout.count():
            item = self.api_config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Limpiar referencias de inputs anteriores
        self.api_input_refs = {}
        
        # Header con botón de regreso
        header_layout = QHBoxLayout()
        
        back_btn = BackButton()
        back_btn.clicked.connect(lambda: self._show_api_list(self.current_category))
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        self.api_config_layout.addLayout(header_layout)
        
        # Icono y nombre
        title_layout = QHBoxLayout()
        title_layout.setSpacing(12)
        
        icon = QLabel(api_data["icon"])
        icon.setStyleSheet("font-size: 48px;")
        title_layout.addWidget(icon)
        
        name_layout = QVBoxLayout()
        name_layout.setSpacing(4)
        
        name = QLabel(api_data["name"])
        name.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        name_layout.addWidget(name)
        
        desc = QLabel(api_data["description"])
        desc.setStyleSheet("""
            font-size: 14px;
            color: rgba(226, 232, 240, 0.6);
        """)
        name_layout.addWidget(desc)
        
        title_layout.addLayout(name_layout)
        title_layout.addStretch()
        
        self.api_config_layout.addLayout(title_layout)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.2);")
        self.api_config_layout.addWidget(separator)
        
        # Formulario de configuración
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 16px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)
        
        # Campos de configuración
        for field in api_data["fields"]:
            field_label = QLabel(field["label"])
            field_label.setStyleSheet("""
                font-size: 13px;
                font-weight: bold;
                color: #e5e7eb;
            """)
            form_layout.addWidget(field_label)
            
            input_field = QLineEdit()
            input_field.setPlaceholderText(field.get("placeholder", ""))
            
            if field["type"] == "password":
                input_field.setEchoMode(QLineEdit.Password)
            
            # Cargar valor guardado si existe
            saved_value = self._get_saved_api_value(api_id, field["name"])
            if saved_value:
                input_field.setText(saved_value)
            
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: rgba(30, 41, 59, 0.8);
                    border: 1px solid rgba(148, 163, 184, 0.2);
                    border-radius: 8px;
                    padding: 12px;
                    color: #e5e7eb;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border-color: #6366f1;
                }
            """)
            
            form_layout.addWidget(input_field)
            self.api_input_refs[field["name"]] = input_field
        
        self.api_config_layout.addWidget(form_frame)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Botón de prueba
        test_btn = QPushButton("🧪 Probar Conexión")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.8);
                color: #e5e7eb;
                border: 1px solid rgba(99, 102, 241, 0.4);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.8);
            }
        """)
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(lambda: self._test_api_connection(api_id, api_data))
        buttons_layout.addWidget(test_btn)
        
        buttons_layout.addStretch()
        
        # Botón de eliminar
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self._delete_api_config(api_id, api_data))
        buttons_layout.addWidget(delete_btn)
        
        # Botón de guardar
        save_btn = QPushButton("💾 Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(lambda: self._save_api_config(api_id, api_data))
        buttons_layout.addWidget(save_btn)
        
        self.api_config_layout.addLayout(buttons_layout)
        self.api_config_layout.addStretch()
        
        # Mostrar pantalla
        self.stack.setCurrentIndex(2)
    
    def _is_api_configured(self, api_id, api_data):
        """Verificar si una API está configurada"""
        if not os.path.exists(self.config_path):
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Buscar en todas las categorías
            for cat_key, cat_data in API_CATEGORIES.items():
                if "subcategories" in cat_data:
                    for sub_id, sub_data in cat_data["subcategories"].items():
                        if api_id in sub_data.get("apis", {}):
                            section = config.get(cat_key, {})
                            api_config = section.get(api_id, {})
                            return any(api_config.get(field["name"]) for field in api_data["fields"])
                else:
                    if api_id in cat_data.get("apis", {}):
                        section = config.get(cat_key, {})
                        api_config = section.get(api_id, {})
                        return any(api_config.get(field["name"]) for field in api_data["fields"])
            
            return False
        except:
            return False
    
    def _get_saved_api_value(self, api_id, field_name):
        """Obtener valor guardado de un campo de API"""
        if not os.path.exists(self.config_path):
            return None
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Buscar en todas las categorías
            for cat_key, cat_data in API_CATEGORIES.items():
                if "subcategories" in cat_data:
                    for sub_id, sub_data in cat_data["subcategories"].items():
                        if api_id in sub_data.get("apis", {}):
                            return config.get(cat_key, {}).get(api_id, {}).get(field_name)
                else:
                    if api_id in cat_data.get("apis", {}):
                        return config.get(cat_key, {}).get(api_id, {}).get(field_name)
            
            return None
        except:
            return None
    
    def _save_api_config(self, api_id, api_data):
        """Guardar configuración de una API"""
        try:
            # Cargar config existente
            config = {}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            
            # Preparar datos de la API
            api_config = {}
            for field in api_data["fields"]:
                input_field = self.api_input_refs.get(field["name"])
                if input_field:
                    api_config[field["name"]] = input_field.text()
            
            # Encontrar la categoría correcta
            for cat_key, cat_data in API_CATEGORIES.items():
                if "subcategories" in cat_data:
                    for sub_id, sub_data in cat_data["subcategories"].items():
                        if api_id in sub_data.get("apis", {}):
                            if cat_key not in config:
                                config[cat_key] = {}
                            config[cat_key][api_id] = api_config
                            break
                else:
                    if api_id in cat_data.get("apis", {}):
                        if cat_key not in config:
                            config[cat_key] = {}
                        config[cat_key][api_id] = api_config
                        break
            
            # Guardar
            os.makedirs('data', exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(self, "✅ Guardado", f"Configuración de {api_data['name']} guardada exitosamente")
            
            # Notificar al orquestador del cambio
            self._notify_orchestrator_api_change(api_id, api_config)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al guardar: {str(e)}")
    
    def _delete_api_config(self, api_id, api_data):
        """Eliminar configuración de una API"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la configuración de {api_data['name']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Cargar config existente
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        config = json.load(f)
                    
                    # Encontrar y eliminar la API
                    for cat_key in list(config.keys()):
                        if api_id in config[cat_key]:
                            del config[cat_key][api_id]
                            break
                    
                    # Guardar
                    with open(self.config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    # Limpiar inputs
                    for field in api_data["fields"]:
                        input_field = self.api_input_refs.get(field["name"])
                        if input_field:
                            input_field.clear()
                    
                    QMessageBox.information(self, "✅ Eliminado", f"Configuración de {api_data['name']} eliminada")
                    
                    # Notificar al orquestador
                    self._notify_orchestrator_api_change(api_id, None)
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"Error al eliminar: {str(e)}")
    
    def _test_api_connection(self, api_id, api_data):
        """Probar conexión con la API"""
        QMessageBox.information(
            self,
            "🧪 Probar Conexión",
            f"Prueba de conexión para {api_data['name']}\n\n"
            "Esta función verificará que las credenciales sean válidas.\n"
            "(Implementación pendiente según cada API)"
        )
    
    def _notify_orchestrator_api_change(self, api_id, config):
        """Notificar al orquestador sobre cambios en APIs"""
        # Esta función se conectará con el orchestrator_agent
        # para que sepa qué APIs están disponibles
        if self.api_client:
            try:
                self.api_client.notify_api_change(api_id, config)
            except:
                pass
    
    def _load_config(self):
        """Cargar configuración existente"""
        # La carga se hace dinámicamente en cada pantalla
        pass
    
    def get_configured_apis(self):
        """Obtener diccionario de APIs configuradas (para el orquestador)"""
        if not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
