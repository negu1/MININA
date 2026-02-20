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

# Importar managers de APIs para testing
from core.api.asana_manager import AsanaManager
from core.api.slack_manager import SlackManager
from core.api.github_manager import GitHubManager
from core.api.notion_manager import NotionManager
from core.api.discord_manager import DiscordManager
from core.api.dropbox_manager import DropboxManager
from core.api.google_calendar_manager import GoogleCalendarManager
from core.api.google_drive_manager import GoogleDriveManager
from core.api.trello_manager import TrelloManager
from core.api.jira_manager import JiraManager
from core.api.monday_manager import MondayManager
from core.api.hubspot_manager import HubSpotManager
from core.api.mailchimp_manager import MailchimpManager
from core.api.stripe_manager import StripeManager
from core.api.twilio_manager import TwilioManager
from core.api.twitter_manager import TwitterManager
from core.api.zoom_manager import ZoomManager
from core.api.spotify_manager import SpotifyManager
from core.api.email_manager import EmailManager
from core.api.google_search_manager import GoogleSearchManager

import json
import os
import requests


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

            # Persistencia adicional segura para Telegram (para que el launcher arranque el bot)
            if api_id == "telegram":
                try:
                    token = (api_config.get("token") or "").strip()
                    chat_id = (api_config.get("chat_id") or "").strip()
                    if token:
                        os.environ["TELEGRAM_BOT_TOKEN"] = token
                    if chat_id:
                        os.environ["TELEGRAM_ALLOWED_CHAT_ID"] = chat_id

                    from core.llm_extension import credential_store

                    if token:
                        credential_store.set_api_key("telegram_bot_token", token)
                    if chat_id:
                        credential_store.set_api_key("telegram_chat_id", chat_id)
                except Exception:
                    pass
            
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
        """Probar conexión real con la API usando el manager correspondiente"""
        # Extraer credenciales actuales de los inputs
        credentials = {}
        for field in api_data["fields"]:
            input_field = self.api_input_refs.get(field["name"])
            if input_field:
                value = input_field.text().strip()
                if value:
                    credentials[field["name"]] = value
        
        # Verificar que tenemos credenciales
        required_fields = [f["name"] for f in api_data["fields"] if f.get("required", False)]
        missing_fields = [f for f in required_fields if not credentials.get(f)]
        
        if missing_fields:
            QMessageBox.warning(
                self,
                "⚠️ Faltan Credenciales",
                f"Debes completar los campos requeridos:\n\n" +
                "\n".join([f"• {f}" for f in missing_fields]) +
                f"\n\nGuarda la configuración antes de probar."
            )
            return
        
        # Ejecutar test según el tipo de API
        try:
            result = self._execute_api_test(api_id, credentials)
            
            if result.get("success"):
                QMessageBox.information(
                    self,
                    "✅ Conexión Exitosa",
                    f"<b>{api_data['name']}</b>\n\n"
                    f"✅ Conexión verificada correctamente\n"
                    f"{result.get('details', '')}\n\n"
                    f"<i>La API está lista para usar.</i>"
                )
            else:
                QMessageBox.critical(
                    self,
                    "❌ Error de Conexión",
                    f"<b>{api_data['name']}</b>\n\n"
                    f"❌ No se pudo conectar\n"
                    f"<b>Error:</b> {result.get('error', 'Error desconocido')}\n\n"
                    f"<i>Verifica tus credenciales e inténtalo de nuevo.</i>"
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"Error inesperado al probar {api_data['name']}:\n{str(e)}"
            )
    
    def _execute_api_test(self, api_id, credentials):
        """Ejecutar test específico según el tipo de API"""
        testers = {
            # Productivity
            "asana": self._test_asana,
            "notion": self._test_notion,
            "trello": self._test_trello,
            "monday": self._test_monday,
            "jira": self._test_jira,
            # Communication  
            "slack": self._test_slack,
            "discord": self._test_discord,
            "zoom": self._test_zoom,
            "email": self._test_email,
            "twilio": self._test_twilio,
            # Storage
            "dropbox": self._test_dropbox,
            "google_calendar": self._test_google_calendar,
            "google_drive": self._test_google_drive,
            # Development
            "github": self._test_github,
            # Marketing
            "mailchimp": self._test_mailchimp,
            "hubspot": self._test_hubspot,
            # Financial
            "stripe": self._test_stripe,
            # Media
            "twitter": self._test_twitter,
            "spotify": self._test_spotify,
            # Utilities
            "web_search": self._test_web_search,
            # Bots
            "telegram": self._test_telegram,
            "whatsapp": self._test_whatsapp,
            # AI Providers (direct HTTP)
            "openai": self._test_openai,
            "groq": self._test_groq,
            "gemini": self._test_gemini,
            "ollama": self._test_ollama,
            "anthropic": self._test_anthropic,
            "qwen": self._test_qwen,
            "phi4": self._test_phi4,
        }
        
        tester = testers.get(api_id)
        if tester:
            return tester(credentials)
        
        return {"success": False, "error": f"Tester no implementado para {api_id}"}

    def _test_telegram(self, credentials):
        """Test Telegram Bot API connection"""
        try:
            token = (credentials.get("token") or credentials.get("bot_token") or "").strip()
            chat_id = (credentials.get("chat_id") or "").strip()
            if not token:
                return {"success": False, "error": "Se requiere Bot Token"}

            # Endpoint liviano
            resp = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10,
            )

            if resp.status_code != 200:
                return {"success": False, "error": f"Error HTTP {resp.status_code}: {resp.text}"}

            data = resp.json()
            if not data.get("ok"):
                return {"success": False, "error": data.get("description", "Token inválido")}

            bot_info = data.get("result", {})
            bot_name = bot_info.get("first_name", "Bot")
            bot_username = bot_info.get("username", "unknown")

            # Si hay chat_id, intentar enviar mensaje de prueba (para validar chat_id)
            if chat_id:
                send = requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": "✅ MININA: Test de conexión OK"},
                    timeout=10,
                )
                if send.status_code != 200:
                    return {
                        "success": False,
                        "error": f"getMe OK pero sendMessage HTTP {send.status_code}: {send.text}",
                    }
                sj = send.json()
                if not sj.get("ok"):
                    return {
                        "success": False,
                        "error": f"getMe OK pero sendMessage falló: {sj.get('description', 'sin detalle')}",
                    }

            return {
                "success": True,
                "details": f"Telegram OK: {bot_name} (@{bot_username})." + (" Mensaje de prueba enviado." if chat_id else ""),
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Telegram API"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _test_whatsapp(self, credentials):
        """Test WhatsApp Cloud API connection"""
        try:
            # En la UI está como api_key + phone_id
            access_token = (credentials.get("api_key") or credentials.get("access_token") or "").strip()
            phone_id = (credentials.get("phone_id") or credentials.get("phone_number_id") or "").strip()
            if not access_token or not phone_id:
                return {"success": False, "error": "Se requiere API Key/Token y Phone Number ID"}

            headers = {"Authorization": f"Bearer {access_token}"}
            url = f"https://graph.facebook.com/v17.0/{phone_id}/whatsapp_business_profile"
            params = {"fields": "about,description,vertical"}

            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 200:
                return {"success": True, "details": "Conectado a WhatsApp Cloud API. Perfil accesible."}

            return {"success": False, "error": f"Error HTTP {resp.status_code}: {resp.text}"}

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con WhatsApp Cloud API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==========================================================================
    # MÉTODOS DE TESTING ESPECÍFICOS POR API
    # ==========================================================================
    
    def _test_asana(self, credentials):
        """Test Asana API connection"""
        try:
            token = credentials.get("personal_access_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Personal Access Token"}
            
            manager = AsanaManager()
            manager.access_token = token
            
            if manager._test_auth():
                return {"success": True, "details": "Token válido. Acceso confirmado a Asana."}
            else:
                return {"success": False, "error": "Token inválido o expirado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_notion(self, credentials):
        """Test Notion API connection"""
        try:
            token = credentials.get("integration_token")
            if not token:
                return {"success": False, "error": "Se requiere Integration Token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            }
            
            response = requests.get(
                "https://api.notion.com/v1/users",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_count = len(data.get("results", []))
                return {
                    "success": True, 
                    "details": f"Conectado a Notion. {user_count} usuarios encontrados."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu Integration Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Notion API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_trello(self, credentials):
        """Test Trello API connection"""
        try:
            api_key = credentials.get("api_key")
            token = credentials.get("token")
            
            if not api_key or not token:
                return {"success": False, "error": "Se requieren API Key y Token"}
            
            params = {"key": api_key, "token": token}
            
            response = requests.get(
                "https://api.trello.com/1/members/me",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                username = data.get("username", "unknown")
                return {
                    "success": True,
                    "details": f"Conectado como @{username}. API funcionando correctamente."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales inválidas. Verifica API Key y Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Trello API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_monday(self, credentials):
        """Test Monday.com API connection"""
        try:
            token = credentials.get("api_token")
            if not token:
                return {"success": False, "error": "Se requiere API Token"}
            
            headers = {"Authorization": token}
            query = {"query": "query { me { name } }"}
            
            response = requests.post(
                "https://api.monday.com/v2",
                headers=headers,
                json=query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and "me" in data["data"]:
                    name = data["data"]["me"].get("name", "User")
                    return {
                        "success": True,
                        "details": f"Conectado como {name}. API GraphQL funcionando."
                    }
                elif "errors" in data:
                    return {"success": False, "error": data["errors"][0].get("message", "Error desconocido")}
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu API Token."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Monday API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_jira(self, credentials):
        """Test Jira API connection"""
        try:
            email = credentials.get("email")
            token = credentials.get("api_token")
            domain = credentials.get("domain", "")
            
            if not email or not token:
                return {"success": False, "error": "Se requieren Email y API Token"}
            
            base_url = f"https://{domain}.atlassian.net" if domain else "https://atlassian.net"
            
            response = requests.get(
                f"{base_url}/rest/api/3/myself",
                headers={"Accept": "application/json"},
                auth=(email, token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                display_name = data.get("displayName", "User")
                return {
                    "success": True,
                    "details": f"Conectado como {display_name}. Jira API v3 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales inválidas o dominio incorrecto"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Jira API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_slack(self, credentials):
        """Test Slack API connection"""
        try:
            token = credentials.get("bot_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Bot Token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://slack.com/api/auth.test",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    team = data.get("team", "Unknown")
                    user = data.get("user", "Bot")
                    return {
                        "success": True,
                        "details": f"Conectado a workspace '{team}' como {user}."
                    }
                else:
                    error = data.get("error", "Error desconocido")
                    return {"success": False, "error": f"Slack API Error: {error}"}
            else:
                return {"success": False, "error": f"HTTP Error {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Slack API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_discord(self, credentials):
        """Test Discord API connection"""
        try:
            token = credentials.get("bot_token")
            if not token:
                return {"success": False, "error": "Se requiere Bot Token"}
            
            headers = {"Authorization": f"Bot {token}"}
            
            response = requests.get(
                "https://discord.com/api/v10/users/@me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                username = data.get("username", "Bot")
                discriminator = data.get("discriminator", "0000")
                return {
                    "success": True,
                    "details": f"Bot conectado: {username}#{discriminator}"
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Bot Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Discord API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_zoom(self, credentials):
        """Test Zoom API connection"""
        try:
            account_id = credentials.get("account_id")
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            
            if not all([account_id, client_id, client_secret]):
                return {"success": False, "error": "Se requieren Account ID, Client ID y Client Secret"}
            
            auth_str = f"{client_id}:{client_secret}"
            import base64
            auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "account_credentials",
                "account_id": account_id
            }
            
            response = requests.post(
                "https://zoom.us/oauth/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                scope = token_data.get("scope", "unknown")
                return {
                    "success": True,
                    "details": f"OAuth Server-to-Server funcionando. Scope: {scope}"
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales OAuth inválidas"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Zoom API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_email(self, credentials):
        """Test Email SMTP connection"""
        try:
            host = credentials.get("smtp_host")
            port = int(credentials.get("smtp_port", 587))
            username = credentials.get("username")
            password = credentials.get("password")
            
            if not all([host, username, password]):
                return {"success": False, "error": "Se requieren SMTP Host, Username y Password"}
            
            import smtplib
            
            server = smtplib.SMTP(host, port, timeout=10)
            server.starttls()
            server.login(username, password)
            server.quit()
            
            return {
                "success": True,
                "details": f"Conexión SMTP exitosa a {host}:{port}"
            }
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "error": "Autenticación SMTP fallida. Verifica usuario/contraseña."}
        except smtplib.SMTPConnectError:
            return {"success": False, "error": f"No se pudo conectar a {host}:{port}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_twilio(self, credentials):
        """Test Twilio API connection"""
        try:
            account_sid = credentials.get("account_sid")
            auth_token = credentials.get("auth_token")
            
            if not account_sid or not auth_token:
                return {"success": False, "error": "Se requieren Account SID y Auth Token"}
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}.json"
            
            response = requests.get(
                url,
                auth=(account_sid, auth_token),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                friendly_name = data.get("friendly_name", "Account")
                status = data.get("status", "unknown")
                return {
                    "success": True,
                    "details": f"Cuenta: {friendly_name}. Status: {status}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Credenciales Twilio inválidas"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Twilio API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_dropbox(self, credentials):
        """Test Dropbox API connection"""
        try:
            token = credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Access Token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.post(
                "https://api.dropboxapi.com/2/users/get_current_account",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                name = data.get("name", {}).get("display_name", "User")
                email = data.get("email", "unknown")
                return {
                    "success": True,
                    "details": f"Conectado como {name} ({email})."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Access Token inválido o expirado"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Dropbox API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_google_calendar(self, credentials):
        """Test Google Calendar API"""
        return self._test_google_api(credentials, "calendar")
    
    def _test_google_drive(self, credentials):
        """Test Google Drive API"""
        return self._test_google_api(credentials, "drive")
    
    def _test_google_api(self, credentials, service_name):
        """Helper para testear APIs de Google con OAuth2"""
        try:
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            refresh_token = credentials.get("refresh_token")
            
            if not all([client_id, client_secret]):
                return {"success": False, "error": f"Se requieren Client ID y Client Secret para Google {service_name}"}
            
            if not client_id.endswith(".apps.googleusercontent.com"):
                return {"success": False, "error": "Client ID parece inválido. Debe terminar en .apps.googleusercontent.com"}
            
            if refresh_token:
                token_url = "https://oauth2.googleapis.com/token"
                data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
                
                response = requests.post(token_url, data=data, timeout=10)
                
                if response.status_code == 200:
                    token_data = response.json()
                    scopes = token_data.get("scope", "")
                    return {
                        "success": True,
                        "details": f"OAuth2 funcionando. Scopes: {scopes[:100]}..."
                    }
                elif response.status_code == 401:
                    return {"success": False, "error": "Refresh token inválido o expirado"}
                else:
                    return {"success": False, "error": f"Error OAuth: {response.status_code}"}
            else:
                return {
                    "success": True,
                    "details": f"Credenciales formato válido. Para test completo, agrega Refresh Token."
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Google OAuth"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_github(self, credentials):
        """Test GitHub API connection"""
        try:
            token = credentials.get("personal_access_token") or credentials.get("access_token")
            if not token:
                return {"success": False, "error": "Se requiere Personal Access Token"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                login = data.get("login", "user")
                name = data.get("name", login)
                return {
                    "success": True,
                    "details": f"Conectado como {name} (@{login}). API v3 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido. Verifica tu PAT."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con GitHub API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_mailchimp(self, credentials):
        """Test Mailchimp API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            if "-" not in api_key:
                return {"success": False, "error": "API Key inválida. Debe tener formato 'key-dc'"}
            
            dc = api_key.split("-")[-1]
            url = f"https://{dc}.api.mailchimp.com/3.0/"
            
            response = requests.get(
                url,
                auth=("anystring", api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get("account_name", "Account")
                total_subscribers = data.get("total_subscribers", 0)
                return {
                    "success": True,
                    "details": f"Cuenta: {account_name}. Total suscriptores: {total_subscribers}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Mailchimp API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_hubspot(self, credentials):
        """Test HubSpot API connection"""
        try:
            token = credentials.get("access_token") or credentials.get("api_key")
            if not token:
                return {"success": False, "error": "Se requiere Access Token o API Key"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(
                "https://api.hubapi.com/integrations/v1/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                hub_id = data.get("hubId", "unknown")
                app_name = data.get("appName", "Unknown")
                return {
                    "success": True,
                    "details": f"Conectado a Hub {hub_id}. App: {app_name}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con HubSpot API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_stripe(self, credentials):
        """Test Stripe API connection"""
        try:
            secret_key = credentials.get("secret_key") or credentials.get("api_key")
            if not secret_key:
                return {"success": False, "error": "Se requiere Secret Key"}
            
            response = requests.get(
                "https://api.stripe.com/v1/account",
                auth=(secret_key, ""),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get("settings", {}).get("dashboard", {}).get("display_name", "Account")
                charges_enabled = data.get("charges_enabled", False)
                status = "✅ Pagos habilitados" if charges_enabled else "⚠️ Pagos no habilitados"
                return {
                    "success": True,
                    "details": f"Cuenta: {account_name}. {status}."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Secret Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Stripe API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_twitter(self, credentials):
        """Test Twitter/X API connection"""
        try:
            bearer_token = credentials.get("bearer_token")
            
            if not bearer_token:
                return {"success": False, "error": "Se requiere Bearer Token"}
            
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            response = requests.get(
                "https://api.twitter.com/2/users/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                user_data = data.get("data", {})
                username = user_data.get("username", "unknown")
                name = user_data.get("name", username)
                return {
                    "success": True,
                    "details": f"Conectado como @{username} ({name}). API v2 funcionando."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Bearer Token inválido"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Twitter API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_spotify(self, credentials):
        """Test Spotify API connection"""
        try:
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
            
            if not client_id or not client_secret:
                return {"success": False, "error": "Se requieren Client ID y Client Secret"}
            
            auth_str = f"{client_id}:{client_secret}"
            import base64
            auth_b64 = base64.b64encode(auth_str.encode('ascii')).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                expires_in = token_data.get("expires_in", 3600)
                return {
                    "success": True,
                    "details": f"OAuth Client Credentials funcionando. Token válido por {expires_in}s."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "Client ID o Secret inválidos"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Spotify API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_web_search(self, credentials):
        """Test Google Custom Search API"""
        try:
            api_key = credentials.get("api_key")
            cx = credentials.get("cx") or credentials.get("search_engine_id")
            
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            params = {"key": api_key, "q": "test"}
            if cx:
                params["cx"] = cx
            
            response = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                total_results = data.get("searchInformation", {}).get("totalResults", "0")
                return {
                    "success": True,
                    "details": f"API funcionando. Resultados disponibles: {total_results}."
                }
            elif response.status_code == 400:
                return {"success": False, "error": "CX (Search Engine ID) requerido para Custom Search"}
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 403:
                return {"success": False, "error": "API Key sin permisos para Custom Search"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Google Search API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_openai(self, credentials):
        """Test OpenAI API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {
                    "success": True,
                    "details": f"Conectado a OpenAI. {model_count} modelos disponibles."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limit excedido. Revisa tu plan."}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con OpenAI API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_groq(self, credentials):
        """Test Groq API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                model_count = len(data.get("data", []))
                return {
                    "success": True,
                    "details": f"Conectado a Groq. {model_count} modelos disponibles."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Groq API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_gemini(self, credentials):
        """Test Google Gemini API connection"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            response = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "").split("/")[-1] for m in data.get("models", [])]
                gemini_models = [m for m in models if "gemini" in m.lower()]
                return {
                    "success": True,
                    "details": f"Conectado a Gemini. {len(gemini_models)} modelos disponibles."
                }
            elif response.status_code == 400:
                return {"success": False, "error": "API Key inválida"}
            elif response.status_code == 403:
                return {"success": False, "error": "API Key sin acceso a Gemini"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Gemini API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_ollama(self, credentials):
        """Test Ollama local server"""
        try:
            base_url = credentials.get("base_url", "http://localhost:11434")
            
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                model_list = ", ".join(model_names[:3])
                if len(model_names) > 3:
                    model_list += f" y {len(model_names) - 3} más"
                return {
                    "success": True,
                    "details": f"Ollama corriendo en {base_url}. Modelos: {model_list}."
                }
            else:
                return {"success": False, "error": f"Ollama respondió con error {response.status_code}"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": f"No se pudo conectar a Ollama en {base_url}. ¿Está el servidor corriendo?"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Timeout al conectar con Ollama"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_anthropic(self, credentials):
        """Test Anthropic Claude API"""
        try:
            api_key = credentials.get("api_key")
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            # Test con models endpoint
            response = requests.get(
                "https://api.anthropic.com/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                model_names = [m.get("id", "unknown") for m in models[:3]]
                return {
                    "success": True,
                    "details": f"Conectado a Anthropic. {len(models)} modelos disponibles ({', '.join(model_names)}...)"
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Anthropic API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_qwen(self, credentials):
        """Test Alibaba Qwen API"""
        try:
            api_key = credentials.get("api_key")
            base_url = credentials.get("base_url", "https://dashscope.aliyuncs.com")
            
            if not api_key:
                return {"success": False, "error": "Se requiere API Key"}
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Qwen API - list models
            response = requests.get(
                f"{base_url}/api/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "details": f"Conectado a Qwen API en {base_url}. Credenciales válidas."
                }
            elif response.status_code == 401:
                return {"success": False, "error": "API Key inválida o expirada"}
            else:
                # Algunas versiones de Qwen pueden tener diferentes endpoints
                return {
                    "success": True,
                    "details": f"URL accesible. HTTP {response.status_code}. Las credenciales parecen válidas."
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar con Qwen API"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_phi4(self, credentials):
        """Test Microsoft Phi-4 via Azure or Ollama"""
        try:
            api_key = credentials.get("api_key")
            base_url = credentials.get("base_url", "http://localhost:11434")
            
            # Si tiene base_url, asumimos Ollama
            if base_url and "localhost" in base_url:
                response = requests.get(
                    f"{base_url}/api/tags",
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    phi_models = [m for m in models if "phi" in m.get("name", "").lower()]
                    
                    if phi_models:
                        return {
                            "success": True,
                            "details": f"Ollama con {len(phi_models)} modelos Phi disponibles."
                        }
                    else:
                        return {
                            "success": True,
                            "details": "Ollama corriendo. No se encontraron modelos Phi-4 instalados."
                        }
                else:
                    return {"success": False, "error": f"Ollama respondió con error {response.status_code}"}
            
            # Si tiene API key, asumimos Azure
            elif api_key:
                return {
                    "success": True,
                    "details": "Azure API Key configurada. Verificación completa requiere endpoint específico."
                }
            else:
                return {"success": False, "error": "Se requiere base_url (Ollama) o api_key (Azure)"}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "No se pudo conectar. ¿Está Ollama corriendo?"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout al conectar"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
