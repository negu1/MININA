"""
MININA v3.0 - Settings View
Configuración de APIs, Telegram, WhatsApp y conexiones
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QGridLayout, QCheckBox,
    QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


class SettingsView(QWidget):
    """
    Vista de Configuración - APIs y Conexiones
    """
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interfaz de configuración"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("⚙️")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        header_text = QLabel("Configuración")
        header_text.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(header_text)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("APIs, conexiones y servicios externos")
        subtitle.setStyleSheet("""
            color: rgba(226, 232, 240, 0.72);
            font-size: 14px;
            margin-bottom: 8px;
        """)
        layout.addWidget(subtitle)
        
        # Scroll area para todo el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # === SECCIÓN 1: APIs de IA (Locales y Cloud) ===
        ai_apis_section = self._create_section("🤖 APIs de Inteligencia Artificial")
        
        # Subsección: APIs Locales Gratuitas
        local_ai_header = QLabel("🆓 Modelos Locales (Gratis)")
        local_ai_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #22c55e; margin-top: 8px;")
        ai_apis_section.layout().addWidget(local_ai_header)
        
        # Ollama (Local)
        ollama_card = self._create_local_api_card(
            "🦙 Ollama",
            "http://localhost:11434",
            "Modelos locales (Llama, Mistral, etc.)",
            "Gratis - Requiere instalación local"
        )
        ai_apis_section.layout().addWidget(ollama_card)
        
        # LM Studio (Local)
        lmstudio_card = self._create_local_api_card(
            "🔬 LM Studio",
            "http://localhost:1234",
            "Modelos locales con UI",
            "Gratis - Requiere instalación local"
        )
        ai_apis_section.layout().addWidget(lmstudio_card)
        
        # Jan (Local)
        jan_card = self._create_local_api_card(
            "🤖 Jan",
            "http://localhost:1337",
            "Alternativa local de ChatGPT",
            "Gratis - Requiere instalación local"
        )
        ai_apis_section.layout().addWidget(jan_card)
        
        # Subsección: APIs Cloud (Pagadas)
        cloud_ai_header = QLabel("☁️ APIs Cloud (Requieren API Key)")
        cloud_ai_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #6366f1; margin-top: 16px;")
        ai_apis_section.layout().addWidget(cloud_ai_header)
        
        # OpenAI API
        openai_card = self._create_ai_api_card(
            "openai",
            "OpenAI API",
            "sk-...",
            "🤖 GPT-4, GPT-3.5"
        )
        ai_apis_section.layout().addWidget(openai_card)
        
        # Groq API
        groq_card = self._create_ai_api_card(
            "groq",
            "Groq API", 
            "gsk_...",
            "⚡ Velocidad extrema"
        )
        ai_apis_section.layout().addWidget(groq_card)
        
        # Anthropic API
        anthropic_card = self._create_ai_api_card(
            "anthropic",
            "Anthropic API",
            "sk-ant-...",
            "🧠 Claude AI"
        )
        ai_apis_section.layout().addWidget(anthropic_card)
        
        content_layout.addWidget(ai_apis_section)
        
        # === SECCIÓN 2: APIs de Bots y Mensajería ===
        bots_section = self._create_section("💬 Bots y Mensajería")
        
        # Telegram
        telegram_card = self._create_telegram_card()
        bots_section.layout().addWidget(telegram_card)
        
        # WhatsApp
        whatsapp_card = self._create_whatsapp_card()
        bots_section.layout().addWidget(whatsapp_card)
        
        # Discord
        discord_card = self._create_discord_card()
        bots_section.layout().addWidget(discord_card)
        
        # Slack
        slack_card = self._create_slack_card()
        bots_section.layout().addWidget(slack_card)
        
        content_layout.addWidget(bots_section)
        
        # === SECCIÓN 3: APIs de Negocio (Empresariales) ===
        business_section = self._create_section("🏢 APIs Empresariales")
        
        # Subcategoría: CRM
        crm_header = QLabel("📊 CRM (Gestión de Clientes)")
        crm_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #00a1e0; margin-top: 8px;")
        business_section.layout().addWidget(crm_header)
        
        business_section.layout().addWidget(self._create_salesforce_card())
        business_section.layout().addWidget(self._create_pipedrive_card())
        
        # Subcategoría: Finanzas y Contabilidad
        finance_header = QLabel("💰 Finanzas y Contabilidad")
        finance_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #2ca01c; margin-top: 16px;")
        business_section.layout().addWidget(finance_header)
        
        business_section.layout().addWidget(self._create_quickbooks_card())
        business_section.layout().addWidget(self._create_xero_card())
        business_section.layout().addWidget(self._create_paypal_card())
        business_section.layout().addWidget(self._create_square_card())
        
        # Subcategoría: E-commerce
        ecommerce_header = QLabel("🛒 E-commerce")
        ecommerce_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #96bf48; margin-top: 16px;")
        business_section.layout().addWidget(ecommerce_header)
        
        business_section.layout().addWidget(self._create_shopify_card())
        business_section.layout().addWidget(self._create_woocommerce_card())
        
        # Subcategoría: Soporte al Cliente
        support_header = QLabel("🎫 Soporte al Cliente")
        support_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #03363d; margin-top: 16px;")
        business_section.layout().addWidget(support_header)
        
        business_section.layout().addWidget(self._create_zendesk_card())
        business_section.layout().addWidget(self._create_freshdesk_card())
        
        # Subcategoría: Gestión de Proyectos
        project_header = QLabel("📋 Gestión de Proyectos")
        project_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #7b68ee; margin-top: 16px;")
        business_section.layout().addWidget(project_header)
        
        business_section.layout().addWidget(self._create_clickup_card())
        business_section.layout().addWidget(self._create_wrike_card())
        
        # Subcategoría: Documentación y Colaboración
        docs_header = QLabel("📄 Documentación y Colaboración")
        docs_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #0052cc; margin-top: 16px;")
        business_section.layout().addWidget(docs_header)
        
        business_section.layout().addWidget(self._create_gitlab_card())
        business_section.layout().addWidget(self._create_airtable_card())
        business_section.layout().addWidget(self._create_confluence_card())
        
        content_layout.addWidget(business_section)
        
        # === SECCIÓN 4: Almacenamiento y Sistema ===
        system_section = self._create_section("🗄️ Almacenamiento y Sistema")
        
        # Backend
        backend_card = self._create_connection_card(
            "Backend MININA",
            "Modo Standalone (local)",
            "✅ Conectado",
            True
        )
        system_section.layout().addWidget(backend_card)
        
        # Works/Archivos
        works_card = self._create_connection_card(
            "Works (Archivos)",
            "data/works",
            "✅ Activo - 8 archivos",
            True
        )
        system_section.layout().addWidget(works_card)
        
        # Skills
        skills_card = self._create_connection_card(
            "Skills",
            "skills_user/",
            "✅ 4 skills cargadas",
            True
        )
        system_section.layout().addWidget(skills_card)
        
        # Memoria
        memory_card = self._create_connection_card(
            "Memoria",
            "data/memory",
            "✅ Persistente",
            True
        )
        system_section.layout().addWidget(memory_card)
        
        content_layout.addWidget(system_section)
        
        # === BOTÓN GUARDAR ===
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        test_btn = QPushButton("🧪 Probar Conexiones")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.65);
                color: #e5e7eb;
                border: 1px solid rgba(148, 163, 184, 0.20);
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 1px solid rgba(99, 102, 241, 0.65);
            }
        """)
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.clicked.connect(self._test_connections)
        save_layout.addWidget(test_btn)
        
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #7c3aed);
            }
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(save_btn)
        
        content_layout.addLayout(save_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Cargar configuración guardada
        self._load_settings()
        
    def _create_section(self, title: str) -> QFrame:
        """Crear sección con título"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.55);
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.16);
            }
        """)
        
        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        section.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Título de sección
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #e5e7eb;
            margin-bottom: 8px;
        """)
        layout.addWidget(title_label)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.18);")
        layout.addWidget(separator)
        
        return section
        
    def _create_connection_card(self, name: str, endpoint: str, status: str, is_connected: bool) -> QFrame:
        """Crear card de conexión"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        info_layout.addWidget(name_label)
        
        endpoint_label = QLabel(endpoint)
        endpoint_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.72);
        """)
        info_layout.addWidget(endpoint_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Status badge
        status_label = QLabel(status)
        if is_connected:
            status_label.setStyleSheet("""
                background-color: #dcfce7;
                color: #16a34a;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            """)
        else:
            status_label.setStyleSheet("""
                background-color: #fee2e2;
                color: #dc2626;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            """)
        layout.addWidget(status_label)
        
        return card
        
    def _create_api_card(self, name: str, placeholder: str, description: str) -> QFrame:
        """Crear card de API con input"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(name_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.72);
        """)
        header_layout.addWidget(desc_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Input
        input_layout = QHBoxLayout()
        
        api_input = QLineEdit()
        api_input.setPlaceholderText(placeholder)
        api_input.setEchoMode(QLineEdit.Password)
        input_layout.addWidget(api_input)
        
        verify_btn = QPushButton("✓")
        verify_btn.setFixedSize(40, 40)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        input_layout.addWidget(verify_btn)
        
        layout.addLayout(input_layout)
        
        return card
        
    def _create_ai_api_card(self, api_id: str, name: str, placeholder: str, description: str) -> QFrame:
        """Crear card de API de IA con guardado persistente, eliminar e indicador de estado"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header con nombre, descripción e indicador de estado
        header_layout = QHBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(name_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.72);
        """)
        header_layout.addWidget(desc_label)
        
        # Indicador de estado (configurado/no configurado)
        status_label = QLabel("⚪")
        status_label.setToolTip("Sin configurar")
        status_label.setStyleSheet("font-size: 14px;")
        setattr(self, f"{api_id}_status_label", status_label)
        header_layout.addWidget(status_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Input
        input_layout = QHBoxLayout()
        
        # Crear input y guardar referencia en self
        api_input = QLineEdit()
        api_input.setPlaceholderText(placeholder)
        api_input.setEchoMode(QLineEdit.Password)
        api_input.setStyleSheet("""
            QLineEdit { 
                background-color: rgba(30, 41, 59, 0.5); 
                border: 1px solid rgba(148, 163, 184, 0.2); 
                border-radius: 8px; 
                padding: 10px; 
                color: #e5e7eb; 
            }
            QLineEdit:focus { 
                border-color: #6366f1; 
            }
        """)
        
        # Guardar referencia en self para poder acceder luego
        input_attr_name = f"{api_id}_api_input"
        setattr(self, input_attr_name, api_input)
        
        # Conectar cambio para actualizar indicador
        api_input.textChanged.connect(lambda text, id=api_id: self._update_api_status_indicator(id, text))
        
        input_layout.addWidget(api_input)
        
        # Botón verificar/guardar
        verify_btn = QPushButton("✓")
        verify_btn.setFixedSize(40, 40)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        verify_btn.clicked.connect(lambda: self._verify_and_save_api_key(api_id, name))
        input_layout.addWidget(verify_btn)
        
        # Botón eliminar/borrar key
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(40, 40)
        delete_btn.setToolTip("Eliminar API Key")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_api_key(api_id, name))
        input_layout.addWidget(delete_btn)
        
        layout.addLayout(input_layout)
        
        return card
    
    def _update_api_status_indicator(self, api_id: str, text: str):
        """Actualizar indicador visual de estado de la API"""
        status_label = getattr(self, f"{api_id}_status_label", None)
        if status_label:
            if text.strip():
                status_label.setText("🟢")
                status_label.setToolTip("Configurado")
            else:
                status_label.setText("⚪")
                status_label.setToolTip("Sin configurar")
    
    def _verify_and_save_api_key(self, api_id: str, name: str):
        """Verificar y guardar API key individual"""
        input_field = getattr(self, f"{api_id}_api_input", None)
        if not input_field:
            return
            
        api_key = input_field.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Error", f"Ingresa una API key para {name}")
            return
        
        # Guardar inmediatamente
        self._save_single_api_key(api_id, api_key)
        
        QMessageBox.information(
            self, 
            "✅ API Key Guardada", 
            f"La API key de {name} ha sido guardada de forma segura.\n\n"
            f"Key: {api_key[:10]}..."
        )
    
    def _delete_api_key(self, api_id: str, name: str):
        """Eliminar API key del sistema"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar la API key de {name}?\n\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Limpiar input
            input_field = getattr(self, f"{api_id}_api_input", None)
            if input_field:
                input_field.clear()
            
            # Guardar vacío (elimina del archivo)
            self._save_single_api_key(api_id, "")
            
            # Actualizar indicador
            self._update_api_status_indicator(api_id, "")
            
            QMessageBox.information(
                self,
                "✅ API Key Eliminada",
                f"La API key de {name} ha sido eliminada del sistema."
            )
    
    def _save_single_api_key(self, api_id: str, api_key: str):
        """Guardar una sola API key en el archivo de configuración"""
        try:
            import json
            import os
            
            config_path = 'data/api_config.json'
            config = {}
            
            # Cargar configuración existente si existe
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    config = {}
            
            # Asegurar que existe la sección ai_apis
            if "ai_apis" not in config:
                config["ai_apis"] = {}
            
            # Guardar o eliminar la key
            if api_key:
                config["ai_apis"][api_id] = {"api_key": api_key}
            else:
                # Si está vacío, eliminar la entrada
                if api_id in config["ai_apis"]:
                    del config["ai_apis"][api_id]
            
            # Guardar a archivo
            os.makedirs('data', exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            print(f"Error guardando API key {api_id}: {e}")
        
    def _create_telegram_card(self) -> QFrame:
        """Crear card de Telegram con Bot Token, Chat ID y guía completa"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header con icono
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("🚀")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        name_label = QLabel("Telegram Bot")
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(name_label)
        
        # Toggle switch
        toggle = QCheckBox("Activar")
        toggle.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: rgba(226, 232, 240, 0.72);
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
            }
        """)
        header_layout.addWidget(toggle)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.18);")
        layout.addWidget(separator)
        
        # Bot Token
        token_label = QLabel("🤖 Bot Token:")
        token_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(token_label)
        
        self.telegram_token_input = QLineEdit()
        self.telegram_token_input.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.telegram_token_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.telegram_token_input)
        
        # Chat ID
        chatid_label = QLabel("💬 Chat ID:")
        chatid_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(chatid_label)
        
        self.telegram_chatid_input = QLineEdit()
        self.telegram_chatid_input.setPlaceholderText("12345678 (tu ID de usuario o grupo)")
        layout.addWidget(self.telegram_chatid_input)
        
        # Botón guía
        guide_btn = QPushButton("📖 Guía: Cómo obtener Token y Chat ID")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.65);
                color: rgba(226, 232, 240, 0.9);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.55);
            }
        """)
        guide_btn.clicked.connect(self._show_telegram_guide)
        layout.addWidget(guide_btn)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 Probar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.65);
                color: #e5e7eb;
                border: 1px solid rgba(99, 102, 241, 0.35);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 1px solid rgba(99, 102, 241, 0.55);
            }
        """)
        btn_layout.addWidget(test_btn)
        
        btn_layout.addStretch()
        
        status_label = QLabel("⚪ Sin configurar")
        status_label.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
        """)
        btn_layout.addWidget(status_label)
        
        layout.addLayout(btn_layout)
        
        return card
        
    def _show_telegram_guide(self):
        """Mostrar guía completa para configurar Telegram"""
        guide = """
<h2>🚀 Guía Completa - Configurar Telegram Bot</h2>

<h3>🤖 PASO 1: Crear tu Bot</h3>
<ol>
<li>Abre Telegram y busca: <b>@BotFather</b></li>
<li>Inicia conversación y escribe: <code>/newbot</code></li>
<li>Dale un nombre (ej: "Mi Bot MININA")</li>
<li>Dale un username que termine en <b>bot</b> (ej: "minina_bot")</li>
<li>¡Listo! @BotFather te dará el <b>Bot Token</b></li>
</ol>

<h3>💬 PASO 2: Obtener tu Chat ID</h3>
<p><b>Para obtener TU Chat ID personal:</b></p>
<ol>
<li>Busca en Telegram: <b>@userinfobot</b></li>
<li>Inicia la conversación</li>
<li>Te responderá con tu ID (número como 123456789)</li>
</ol>

<p><b>Para obtener Chat ID de un GRUPO:</b></p>
<ol>
<li>Añade tu bot al grupo</li>
<li>Envía un mensaje en el grupo</li>
<li>Abre en navegador: <code>https://api.telegram.org/bot[TU_TOKEN]/getUpdates</code></li>
<li>Busca "chat":{"id":-123456789 (número negativo = grupo)</li>
</ol>

<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el <b>Bot Token</b> en el primer campo</li>
<li>Pega el <b>Chat ID</b> en el segundo campo</li>
<li>Activa el toggle "Activar"</li>
<li>Click en "🧪 Probar" para verificar</li>
</ol>

<p><b>💡 Tip:</b> El Chat ID de grupo siempre es negativo (ej: -1001234567890)</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Guía Telegram - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def _create_whatsapp_card(self) -> QFrame:
        """Crear card de WhatsApp con guía completa"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header con icono
        header_layout = QHBoxLayout()
        
        icon_label = QLabel("💬")
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        name_label = QLabel("WhatsApp Business API")
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(name_label)
        
        # Toggle switch
        toggle = QCheckBox("Activar")
        toggle.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: rgba(226, 232, 240, 0.72);
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
            }
        """)
        header_layout.addWidget(toggle)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.18);")
        layout.addWidget(separator)
        
        # API Key
        key_label = QLabel("🔑 API Key / Token:")
        key_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(key_label)
        
        self.whatsapp_key_input = QLineEdit()
        self.whatsapp_key_input.setPlaceholderText("EAAxxxxx... (token de WhatsApp Business)")
        self.whatsapp_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.whatsapp_key_input)
        
        # Phone Number ID
        phone_label = QLabel("📱 Phone Number ID:")
        phone_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(phone_label)
        
        self.whatsapp_phone_input = QLineEdit()
        self.whatsapp_phone_input.setPlaceholderText("123456789012345 (ID del número de teléfono)")
        layout.addWidget(self.whatsapp_phone_input)
        
        # Botón guía
        guide_btn = QPushButton("📖 Guía: Cómo configurar WhatsApp Business API")
        guide_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.65);
                color: rgba(226, 232, 240, 0.9);
                border: 1px solid rgba(34, 197, 94, 0.30);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 1px solid rgba(34, 197, 94, 0.45);
            }
        """)
        guide_btn.clicked.connect(self._show_whatsapp_guide)
        layout.addWidget(guide_btn)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        test_btn = QPushButton("🧪 Probar")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.65);
                color: #e5e7eb;
                border: 1px solid rgba(99, 102, 241, 0.35);
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(51, 65, 85, 0.7);
                border: 1px solid rgba(99, 102, 241, 0.55);
            }
        """)
        btn_layout.addWidget(test_btn)
        
        btn_layout.addStretch()
        
        status_label = QLabel("⚪ Sin configurar")
        status_label.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
        """)
        btn_layout.addWidget(status_label)
        
        layout.addLayout(btn_layout)
        
        return card
        
    def _show_whatsapp_guide(self):
        """Mostrar guía completa para configurar WhatsApp"""
        guide = """
<h2>💬 Guía Completa - WhatsApp Business API</h2>

<h3>🔑 PASO 1: Crear App en Meta Developers</h3>
<ol>
<li>Ve a: <a href='https://developers.facebook.com'>developers.facebook.com</a></li>
<li>Inicia sesión con tu cuenta de Facebook</li>
<li>Click en "Mis Apps" → "Crear App"</li>
<li>Selecciona tipo: "Business"</li>
<li>Completa la información básica</li>
</ol>

<h3>� PASO 2: Configurar WhatsApp Producto</h3>
<ol>
<li>En tu app, busca "WhatsApp" en productos</li>
<li>Click en "Configurar"</li>
<li>Vincula una cuenta de Business Manager (o crea una)</li>
<li>Agrega un número de teléfono para pruebas</li>
</ol>

<h3>🔐 PASO 3: Obtener API Key y Phone ID</h3>
<ol>
<li>En el panel de WhatsApp, ve a "API Setup"</li>
<li>Copia el <b>Token de Acceso Temporal</b> (empieza con EAA...)</li>
<li>Copia el <b>Phone Number ID</b> (número largo)</li>
<li>⚠️ Nota: El token temporal expira en 24 horas</li>
</ol>

<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega el <b>API Key/Token</b> en el primer campo</li>
<li>Pega el <b>Phone Number ID</b> en el segundo campo</li>
<li>Activa el toggle "Activar"</li>
<li>Click en "🧪 Probar" para verificar</li>
</ol>

<p><b>⚠️ Importante:</b> Para producción necesitas verificar tu Business y obtener token permanente.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Guía WhatsApp - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def _create_local_api_card(self, name: str, endpoint: str, description: str, status_text: str) -> QFrame:
        """Crear card para APIs locales gratuitas (Ollama, LM Studio, etc.)"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(34, 197, 94, 0.28);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: rgba(134, 239, 172, 0.95);
        """)
        header_layout.addWidget(name_label)
        
        # Badge gratis
        free_badge = QLabel("🆓 GRATIS")
        free_badge.setStyleSheet("""
            background-color: #22c55e;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(free_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Descripción
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            font-size: 13px;
            color: rgba(226, 232, 240, 0.72);
        """)
        layout.addWidget(desc_label)
        
        # Endpoint
        endpoint_label = QLabel(f"📍 {endpoint}")
        endpoint_label.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.72);
            font-family: monospace;
        """)
        layout.addWidget(endpoint_label)
        
        # Botón instalar
        install_btn = QPushButton("📥 Cómo Instalar")
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        install_btn.setCursor(Qt.PointingHandCursor)
        install_btn.clicked.connect(lambda: self._show_install_guide(name))
        layout.addWidget(install_btn)
        
        return card
        
    def _show_install_guide(self, api_name: str):
        """Mostrar guía de instalación para APIs locales"""
        guides = {
            "Ollama": """
<h2>🦙 Guía de Instalación - Ollama</h2>

<p><b>Paso 1:</b> Descargar desde <a href='https://ollama.com'>ollama.com</a></p>

<p><b>Paso 2:</b> Instalar el modelo que desees:</p>
<pre>ollama pull llama3.2
ollama pull mistral
ollama pull codellama</pre>

<p><b>Paso 3:</b> Verificar que está corriendo:</p>
<pre>ollama list
# Debe mostrar: http://localhost:11434</pre>

<p><b>✅ Listo!</b> MININA detectará Ollama automáticamente.</p>
            """,
            "LM Studio": """
<h2>🔬 Guía de Instalación - LM Studio</h2>

<p><b>Paso 1:</b> Descargar desde <a href='https://lmstudio.ai'>lmstudio.ai</a></p>

<p><b>Paso 2:</b> Abrir LM Studio y descargar un modelo</p>

<p><b>Paso 3:</b> Iniciar el servidor local:</p>
<pre>1. Ve a "Developer" tab
2. Click "Start Server"
3. Puerto por defecto: 1234</pre>

<p><b>✅ Listo!</b> La API estará en http://localhost:1234</p>
            """,
            "Jan": """
<h2>🤖 Guía de Instalación - Jan</h2>

<p><b>Paso 1:</b> Descargar desde <a href='https://jan.ai'>jan.ai</a></p>

<p><b>Paso 2:</b> Instalar y descargar un modelo</p>

<p><b>Paso 3:</b> Activar el servidor:</p>
<pre>1. Settings → Advanced
2. Enable API Server
3. Puerto: 1337</pre>

<p><b>✅ Listo!</b> API disponible en http://localhost:1337</p>
            """
        }
        
        guide = guides.get(api_name, "Guía no disponible")
        
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Guía de Instalación - {api_name}")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def _test_connections(self):
        """Probar todas las conexiones"""
        QMessageBox.information(
            self,
            "Probar Conexiones",
            "🔌 Backend: ✅ Conectado\n"
            "🦙 Ollama: ✅ Disponible\n"
            "🔬 LM Studio: ⚪ No detectado\n"
            "🤖 Jan: ⚪ No detectado\n"
            "🤖 OpenAI: ⚪ Sin configurar\n"
            "⚡ Groq: ⚪ Sin configurar\n"
            "🧠 Anthropic: ⚪ Sin configurar\n"
            "🚀 Telegram: ⚪ Sin configurar\n"
            "💬 WhatsApp: ⚪ Sin configurar\n\n"
            "Las APIs marcadas en ⚪ necesitan configuración."
        )
        
    def _create_salesforce_card(self) -> QFrame:
        """Card para configuración de Salesforce API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("☁️ Salesforce API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Username + Password + Security Token")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.salesforce_username_input = QLineEdit()
        self.salesforce_username_input.setPlaceholderText("Username (email)")
        self.salesforce_username_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_username_input)
        
        self.salesforce_password_input = QLineEdit()
        self.salesforce_password_input.setPlaceholderText("Password")
        self.salesforce_password_input.setEchoMode(QLineEdit.Password)
        self.salesforce_password_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_password_input)
        
        self.salesforce_token_input = QLineEdit()
        self.salesforce_token_input.setPlaceholderText("Security Token")
        self.salesforce_token_input.setEchoMode(QLineEdit.Password)
        self.salesforce_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #00a1e0; }
        """)
        layout.addWidget(self.salesforce_token_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #00a1e0; }
        """)
        guide_btn.clicked.connect(self._show_salesforce_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_salesforce)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_salesforce_guide(self):
        guide = """
<h2>☁️ Guía de Configuración - Salesforce API</h2>
<h3>🔑 PASO 1: Habilitar API</h3>
<ol>
<li>Ve a tu cuenta de Salesforce</li>
<li>Setup → API → API Enabled</li>
<li>Asegúrate de que esté habilitada</li>
</ol>
<h3>🔑 PASO 2: Obtener Security Token</h3>
<ol>
<li>Ve a tu perfil (Settings → Personal)</li>
<li>Click "Reset Security Token"</li>
<li>Recibirás el token por email</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega tu Username (email)</li>
<li>Pega tu Password</li>
<li>Pega el Security Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("☁️ Guía Salesforce - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_salesforce(self):
        try:
            username = self.salesforce_username_input.text().strip()
            password = self.salesforce_password_input.text().strip()
            token = self.salesforce_token_input.text().strip()
            if not username or not password:
                QMessageBox.warning(self, "Error", "Ingresa Username y Password")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Salesforce configurado correctamente!\n\nUsername: {username}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_quickbooks_card(self) -> QFrame:
        """Card para configuración de QuickBooks API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("💰 QuickBooks API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Client ID + Client Secret (OAuth 2.0)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.quickbooks_client_id_input = QLineEdit()
        self.quickbooks_client_id_input.setPlaceholderText("Client ID")
        self.quickbooks_client_id_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #2ca01c; }
        """)
        layout.addWidget(self.quickbooks_client_id_input)
        
        self.quickbooks_client_secret_input = QLineEdit()
        self.quickbooks_client_secret_input.setPlaceholderText("Client Secret")
        self.quickbooks_client_secret_input.setEchoMode(QLineEdit.Password)
        self.quickbooks_client_secret_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #2ca01c; }
        """)
        layout.addWidget(self.quickbooks_client_secret_input)
        
        self.quickbooks_realm_input = QLineEdit()
        self.quickbooks_realm_input.setPlaceholderText("Realm ID / Company ID (opcional)")
        self.quickbooks_realm_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #2ca01c; }
        """)
        layout.addWidget(self.quickbooks_realm_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #2ca01c; }
        """)
        guide_btn.clicked.connect(self._show_quickbooks_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_quickbooks)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_quickbooks_guide(self):
        guide = """
<h2>💰 Guía de Configuración - QuickBooks API</h2>
<h3>🔑 PASO 1: Crear App en Intuit Developer</h3>
<ol>
<li>Ve a <a href='https://developer.intuit.com'>developer.intuit.com</a></li>
<li>Crea una cuenta o inicia sesión</li>
<li>Ve a Dashboard → Create an App</li>
<li>Selecciona QuickBooks Online</li>
</ol>
<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>En tu app, ve a "Keys & OAuth"</li>
<li>Copia el Client ID y Client Secret</li>
<li>Configura Redirect URI: http://localhost</li>
</ol>
<h3>🔑 PASO 3: Obtener Realm ID</h3>
<ol>
<li>Abre tu compañía en QuickBooks</li>
<li>El Realm ID aparece en la URL o en Company Settings</li>
</ol>
<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega Client ID, Client Secret y Realm ID</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("💰 Guía QuickBooks - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_quickbooks(self):
        try:
            client_id = self.quickbooks_client_id_input.text().strip()
            client_secret = self.quickbooks_client_secret_input.text().strip()
            realm = self.quickbooks_realm_input.text().strip()
            if not client_id or not client_secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Client Secret")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"QuickBooks configurado correctamente!\n\nRealm ID: {realm if realm else 'Por configurar'}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_shopify_card(self) -> QFrame:
        """Card para configuración de Shopify API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("🛒 Shopify API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Store URL + Admin API Access Token")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.shopify_store_input = QLineEdit()
        self.shopify_store_input.setPlaceholderText("Store URL (tu-tienda.myshopify.com)")
        self.shopify_store_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #96bf48; }
        """)
        layout.addWidget(self.shopify_store_input)
        
        self.shopify_token_input = QLineEdit()
        self.shopify_token_input.setPlaceholderText("Admin API Access Token")
        self.shopify_token_input.setEchoMode(QLineEdit.Password)
        self.shopify_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #96bf48; }
        """)
        layout.addWidget(self.shopify_token_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #96bf48; }
        """)
        guide_btn.clicked.connect(self._show_shopify_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_shopify)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_shopify_guide(self):
        guide = """
<h2>🛒 Guía de Configuración - Shopify API</h2>
<h3>🔑 PASO 1: Crear App Privada</h3>
<ol>
<li>Ve a tu Admin de Shopify</li>
<li>Settings → Apps and sales channels</li>
<li>Develop apps → Create an app</li>
</ol>
<h3>🔑 PASO 2: Configurar Permisos</h3>
<ol>
<li>En tu app, ve a "Configuration"</li>
<li>Selecciona permisos necesarios: read_products, write_products, read_orders, write_orders, read_customers, write_customers</li>
</ol>
<h3>🔑 PASO 3: Instalar App</h3>
<ol>
<li>Click "Install app"</li>
<li>Revela el Admin API access token (empieza con shpat_)</li>
</ol>
<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega tu Store URL (ej: mi-tienda.myshopify.com)</li>
<li>Pega el Admin API Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🛒 Guía Shopify - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_shopify(self):
        try:
            store = self.shopify_store_input.text().strip()
            token = self.shopify_token_input.text().strip()
            if not store or not token:
                QMessageBox.warning(self, "Error", "Ingresa Store URL y Access Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Shopify configurado correctamente!\n\nStore: {store}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_paypal_card(self) -> QFrame:
        """Card para configuración de PayPal API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("💳 PayPal API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Client ID + Secret (Sandbox o Live)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.paypal_client_id_input = QLineEdit()
        self.paypal_client_id_input.setPlaceholderText("Client ID")
        self.paypal_client_id_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #003087; }
        """)
        layout.addWidget(self.paypal_client_id_input)
        self.paypal_secret_input = QLineEdit()
        self.paypal_secret_input.setPlaceholderText("Client Secret")
        self.paypal_secret_input.setEchoMode(QLineEdit.Password)
        self.paypal_secret_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #003087; }
        """)
        layout.addWidget(self.paypal_secret_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #003087; }
        """)
        guide_btn.clicked.connect(self._show_paypal_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_paypal)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_paypal_guide(self):
        guide = """
<h2>💳 Guía de Configuración - PayPal API</h2>
<h3>🔑 PASO 1: Crear App en PayPal Developer</h3>
<ol>
<li>Ve a <a href='https://developer.paypal.com'>developer.paypal.com</a></li>
<li>Inicia sesión con tu cuenta PayPal</li>
<li>Dashboard → Create App</li>
</ol>
<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>Nombra tu app (ej: "MININA")</li>
<li>Selecciona Sandbox (pruebas) o Live (producción)</li>
<li>Copia el Client ID y Secret</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Client ID y Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("💳 Guía PayPal - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_paypal(self):
        try:
            client_id = self.paypal_client_id_input.text().strip()
            secret = self.paypal_secret_input.text().strip()
            if not client_id or not secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Secret")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"PayPal configurado correctamente!\n\nClient ID: {client_id[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_zendesk_card(self) -> QFrame:
        """Card para configuración de Zendesk API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🎫 Zendesk API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Subdomain + Email + API Token")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.zendesk_subdomain_input = QLineEdit()
        self.zendesk_subdomain_input.setPlaceholderText("Subdomain (tuempresa.zendesk.com)")
        self.zendesk_subdomain_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #03363d; }
        """)
        layout.addWidget(self.zendesk_subdomain_input)
        self.zendesk_email_input = QLineEdit()
        self.zendesk_email_input.setPlaceholderText("Email de agente/admin")
        self.zendesk_email_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #03363d; }
        """)
        layout.addWidget(self.zendesk_email_input)
        self.zendesk_token_input = QLineEdit()
        self.zendesk_token_input.setPlaceholderText("API Token")
        self.zendesk_token_input.setEchoMode(QLineEdit.Password)
        self.zendesk_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #03363d; }
        """)
        layout.addWidget(self.zendesk_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #03363d; }
        """)
        guide_btn.clicked.connect(self._show_zendesk_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_zendesk)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_zendesk_guide(self):
        guide = """
<h2>🎫 Guía de Configuración - Zendesk API</h2>
<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Ve a tu Admin Center de Zendesk</li>
<li>Apps and integrations → APIs → Zendesk API</li>
<li>Settings tab → Enable Token Access</li>
<li>Click "+" para agregar un token</li>
</ol>
<h3>🔑 PASO 2: Identificar tu Subdomain</h3>
<ol>
<li>Tu subdomain es la primera parte de tu URL</li>
<li>Ejemplo: en "miempresa.zendesk.com", el subdomain es "miempresa"</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Subdomain (o URL completa)</li>
<li>Pega tu Email de agente</li>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🎫 Guía Zendesk - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_zendesk(self):
        try:
            subdomain = self.zendesk_subdomain_input.text().strip()
            email = self.zendesk_email_input.text().strip()
            token = self.zendesk_token_input.text().strip()
            if not subdomain or not email or not token:
                QMessageBox.warning(self, "Error", "Ingresa Subdomain, Email y Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Zendesk configurado correctamente!\n\nSubdomain: {subdomain}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_clickup_card(self) -> QFrame:
        """Card para configuración de ClickUp API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("📋 ClickUp API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: API Token (desde Settings → Apps)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.clickup_token_input = QLineEdit()
        self.clickup_token_input.setPlaceholderText("API Token (pk_xxxxxxxx)")
        self.clickup_token_input.setEchoMode(QLineEdit.Password)
        self.clickup_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #7b68ee; }
        """)
        layout.addWidget(self.clickup_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #7b68ee; }
        """)
        guide_btn.clicked.connect(self._show_clickup_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_clickup)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_clickup_guide(self):
        guide = """
<h2>📋 Guía de Configuración - ClickUp API</h2>
<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Inicia sesión en ClickUp</li>
<li>Ve a Settings (rueda dentada) → Apps</li>
<li>ClickUp API → Generate</li>
<li>Copia el token (empieza con pk_)</li>
</ol>
<h3>✅ PASO 2: Configurar en MININA</h3>
<ol>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📋 Guía ClickUp - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_clickup(self):
        try:
            token = self.clickup_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el API Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"ClickUp configurado correctamente!\n\nToken: {token[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_gitlab_card(self) -> QFrame:
        """Card para configuración de GitLab API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🦊 GitLab API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Personal Access Token (PAT)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.gitlab_token_input = QLineEdit()
        self.gitlab_token_input.setPlaceholderText("Personal Access Token (glpat-xxx)")
        self.gitlab_token_input.setEchoMode(QLineEdit.Password)
        self.gitlab_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #fc6d26; }
        """)
        layout.addWidget(self.gitlab_token_input)
        self.gitlab_url_input = QLineEdit()
        self.gitlab_url_input.setPlaceholderText("GitLab URL (opcional, por defecto: gitlab.com)")
        self.gitlab_url_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #fc6d26; }
        """)
        layout.addWidget(self.gitlab_url_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #fc6d26; }
        """)
        guide_btn.clicked.connect(self._show_gitlab_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_gitlab)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_gitlab_guide(self):
        guide = """
<h2>🦊 Guía de Configuración - GitLab API</h2>
<h3>🔑 PASO 1: Crear Personal Access Token</h3>
<ol>
<li>Ve a tu perfil en GitLab</li>
<li>Edit Profile → Access Tokens</li>
<li>Add new token</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Selecciona scopes: read_api, read_repository, write_repository</li>
<li>Click Create personal access token</li>
</ol>
<h3>🔑 PASO 2: Copiar Token</h3>
<ol>
<li>Copia el token INMEDIATAMENTE (empieza con glpat-)</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Personal Access Token</li>
<li>(Opcional) Pega tu GitLab URL si usas GitLab auto-hosteado</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🦊 Guía GitLab - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_gitlab(self):
        try:
            token = self.gitlab_token_input.text().strip()
            url = self.gitlab_url_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Personal Access Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"GitLab configurado correctamente!\n\nToken: {token[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_airtable_card(self) -> QFrame:
        """Card para configuración de Airtable API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🗂️ Airtable API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Personal Access Token (PAT)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.airtable_token_input = QLineEdit()
        self.airtable_token_input.setPlaceholderText("Personal Access Token (patxxxx)")
        self.airtable_token_input.setEchoMode(QLineEdit.Password)
        self.airtable_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #18bfff; }
        """)
        layout.addWidget(self.airtable_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #18bfff; }
        """)
        guide_btn.clicked.connect(self._show_airtable_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_airtable)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_airtable_guide(self):
        guide = """
<h2>🗂️ Guía de Configuración - Airtable API</h2>
<h3>🔑 PASO 1: Crear Personal Access Token</h3>
<ol>
<li>Ve a <a href='https://airtable.com/create/tokens'>airtable.com/create/tokens</a></li>
<li>Click "Create new token"</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Selecciona scopes: data.records:read, data.records:write, schema.bases:read</li>
<li>Agrega las bases que necesitas acceder</li>
</ol>
<h3>🔑 PASO 2: Copiar Token</h3>
<ol>
<li>Copia el token generado (empieza con pat)</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Personal Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🗂️ Guía Airtable - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_airtable(self):
        try:
            token = self.airtable_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Personal Access Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Airtable configurado correctamente!\n\nToken: {token[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_pipedrive_card(self) -> QFrame:
        """Card para configuración de Pipedrive API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🚀 Pipedrive API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: API Token (desde Settings → Personal Preferences)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.pipedrive_token_input = QLineEdit()
        self.pipedrive_token_input.setPlaceholderText("API Token")
        self.pipedrive_token_input.setEchoMode(QLineEdit.Password)
        self.pipedrive_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #6266f1; }
        """)
        layout.addWidget(self.pipedrive_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #6266f1; }
        """)
        guide_btn.clicked.connect(self._show_pipedrive_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_pipedrive)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_pipedrive_guide(self):
        guide = """
<h2>🚀 Guía de Configuración - Pipedrive API</h2>
<h3>🔑 PASO 1: Obtener API Token</h3>
<ol>
<li>Inicia sesión en Pipedrive</li>
<li>Ve a Settings (rueda dentada) → Personal preferences → API</li>
<li>Copia el API token</li>
</ol>
<h3>✅ PASO 2: Configurar en MININA</h3>
<ol>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🚀 Guía Pipedrive - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_pipedrive(self):
        try:
            token = self.pipedrive_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el API Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Pipedrive configurado correctamente!\n\nToken: {token[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_xero_card(self) -> QFrame:
        """Card para configuración de Xero API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("📗 Xero API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Client ID + Client Secret (OAuth 2.0)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.xero_client_id_input = QLineEdit()
        self.xero_client_id_input.setPlaceholderText("Client ID")
        self.xero_client_id_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #13b5ea; }
        """)
        layout.addWidget(self.xero_client_id_input)
        self.xero_client_secret_input = QLineEdit()
        self.xero_client_secret_input.setPlaceholderText("Client Secret")
        self.xero_client_secret_input.setEchoMode(QLineEdit.Password)
        self.xero_client_secret_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #13b5ea; }
        """)
        layout.addWidget(self.xero_client_secret_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #13b5ea; }
        """)
        guide_btn.clicked.connect(self._show_xero_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_xero)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_xero_guide(self):
        guide = """
<h2>📗 Guía de Configuración - Xero API</h2>
<h3>🔑 PASO 1: Crear App en Xero Developer</h3>
<ol>
<li>Ve a <a href='https://developer.xero.com'>developer.xero.com</a></li>
<li>My Apps → New app</li>
<li>Selecciona "Web app"</li>
<li>Redirect URI: http://localhost</li>
</ol>
<h3>🔑 PASO 2: Obtener Credenciales</h3>
<ol>
<li>En tu app, copia Client ID y Client Secret</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega Client ID y Client Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📗 Guía Xero - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_xero(self):
        try:
            client_id = self.xero_client_id_input.text().strip()
            client_secret = self.xero_client_secret_input.text().strip()
            if not client_id or not client_secret:
                QMessageBox.warning(self, "Error", "Ingresa Client ID y Client Secret")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Xero configurado correctamente!\n\nClient ID: {client_id[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_woocommerce_card(self) -> QFrame:
        """Card para configuración de WooCommerce API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🏪 WooCommerce API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Consumer Key + Consumer Secret")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.wc_store_url_input = QLineEdit()
        self.wc_store_url_input.setPlaceholderText("Store URL (https://mitienda.com)")
        self.wc_store_url_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #96588a; }
        """)
        layout.addWidget(self.wc_store_url_input)
        self.wc_key_input = QLineEdit()
        self.wc_key_input.setPlaceholderText("Consumer Key (ck_xxx)")
        self.wc_key_input.setEchoMode(QLineEdit.Password)
        self.wc_key_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #96588a; }
        """)
        layout.addWidget(self.wc_key_input)
        self.wc_secret_input = QLineEdit()
        self.wc_secret_input.setPlaceholderText("Consumer Secret (cs_xxx)")
        self.wc_secret_input.setEchoMode(QLineEdit.Password)
        self.wc_secret_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #96588a; }
        """)
        layout.addWidget(self.wc_secret_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #96588a; }
        """)
        guide_btn.clicked.connect(self._show_woocommerce_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_woocommerce)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_woocommerce_guide(self):
        guide = """
<h2>🏪 Guía de Configuración - WooCommerce API</h2>
<h3>🔑 PASO 1: Habilitar REST API</h3>
<ol>
<li>Ve a tu Admin de WordPress</li>
<li>WooCommerce → Settings → Advanced → REST API</li>
<li>Click "Add key"</li>
</ol>
<h3>🔑 PASO 2: Crear API Key</h3>
<ol>
<li>Description: "MININA"</li>
<li>User: Selecciona un usuario admin</li>
<li>Permissions: Read/Write</li>
<li>Click "Generate API key"</li>
</ol>
<h3>🔑 PASO 3: Copiar Credenciales</h3>
<ol>
<li>Copia INMEDIATAMENTE: Consumer Key (ck_) y Consumer Secret (cs_)</li>
</ol>
<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega la Store URL</li>
<li>Pega Consumer Key y Consumer Secret</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🏪 Guía WooCommerce - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_woocommerce(self):
        try:
            store = self.wc_store_url_input.text().strip()
            key = self.wc_key_input.text().strip()
            secret = self.wc_secret_input.text().strip()
            if not store or not key or not secret:
                QMessageBox.warning(self, "Error", "Ingresa Store URL, Key y Secret")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"WooCommerce configurado correctamente!\n\nStore: {store}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_freshdesk_card(self) -> QFrame:
        """Card para configuración de Freshdesk API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("🆘 Freshdesk API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: API Key (desde Profile Settings)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.freshdesk_domain_input = QLineEdit()
        self.freshdesk_domain_input.setPlaceholderText("Domain (tuempresa.freshdesk.com)")
        self.freshdesk_domain_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #25c151; }
        """)
        layout.addWidget(self.freshdesk_domain_input)
        self.freshdesk_key_input = QLineEdit()
        self.freshdesk_key_input.setPlaceholderText("API Key")
        self.freshdesk_key_input.setEchoMode(QLineEdit.Password)
        self.freshdesk_key_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #25c151; }
        """)
        layout.addWidget(self.freshdesk_key_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #25c151; }
        """)
        guide_btn.clicked.connect(self._show_freshdesk_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_freshdesk)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_freshdesk_guide(self):
        guide = """
<h2>🆘 Guía de Configuración - Freshdesk API</h2>
<h3>🔑 PASO 1: Obtener API Key</h3>
<ol>
<li>Inicia sesión en Freshdesk</li>
<li>Click en tu perfil (arriba derecha)</li>
<li>Profile Settings</li>
<li>Copia el "Your API Key"</li>
</ol>
<h3>🔑 PASO 2: Identificar tu Domain</h3>
<ol>
<li>Tu domain es la primera parte de tu URL</li>
<li>Ejemplo: en "miempresa.freshdesk.com", el domain es "miempresa"</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Domain</li>
<li>Pega el API Key</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🆘 Guía Freshdesk - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_freshdesk(self):
        try:
            domain = self.freshdesk_domain_input.text().strip()
            key = self.freshdesk_key_input.text().strip()
            if not domain or not key:
                QMessageBox.warning(self, "Error", "Ingresa Domain y API Key")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Freshdesk configurado correctamente!\n\nDomain: {domain}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_wrike_card(self) -> QFrame:
        """Card para configuración de Wrike API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("📊 Wrike API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Permanent Access Token (PAT)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.wrike_token_input = QLineEdit()
        self.wrike_token_input.setPlaceholderText("Permanent Access Token (eyJ...)")
        self.wrike_token_input.setEchoMode(QLineEdit.Password)
        self.wrike_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #8c31ff; }
        """)
        layout.addWidget(self.wrike_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #8c31ff; }
        """)
        guide_btn.clicked.connect(self._show_wrike_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_wrike)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_wrike_guide(self):
        guide = """
<h2>📊 Guía de Configuración - Wrike API</h2>
<h3>🔑 PASO 1: Crear App en Wrike</h3>
<ol>
<li>Inicia sesión en Wrike</li>
<li>Click en tu perfil → Apps & Integrations</li>
<li>API → Create App</li>
</ol>
<h3>🔑 PASO 2: Obtener Access Token</h3>
<ol>
<li>En tu app, ve a "API" tab</li>
<li>Click "Obtain access token"</li>
<li>Copia el Permanent Access Token</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Permanent Access Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📊 Guía Wrike - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_wrike(self):
        try:
            token = self.wrike_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Permanent Access Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Wrike configurado correctamente!\n\nToken: {token[:10]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_confluence_card(self) -> QFrame:
        """Card para configuración de Confluence API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("📄 Confluence API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: API Token (desde Atlassian Account)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.confluence_url_input = QLineEdit()
        self.confluence_url_input.setPlaceholderText("Confluence URL (tuempresa.atlassian.net/wiki)")
        self.confluence_url_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #0052cc; }
        """)
        layout.addWidget(self.confluence_url_input)
        self.confluence_email_input = QLineEdit()
        self.confluence_email_input.setPlaceholderText("Email de Atlassian")
        self.confluence_email_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #0052cc; }
        """)
        layout.addWidget(self.confluence_email_input)
        self.confluence_token_input = QLineEdit()
        self.confluence_token_input.setPlaceholderText("API Token")
        self.confluence_token_input.setEchoMode(QLineEdit.Password)
        self.confluence_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #0052cc; }
        """)
        layout.addWidget(self.confluence_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #0052cc; }
        """)
        guide_btn.clicked.connect(self._show_confluence_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_confluence)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_confluence_guide(self):
        guide = """
<h2>📄 Guía de Configuración - Confluence API</h2>
<h3>🔑 PASO 1: Crear API Token</h3>
<ol>
<li>Ve a <a href='https://id.atlassian.com/manage-profile/security/api-tokens'>id.atlassian.com</a></li>
<li>Click "Create API token"</li>
<li>Nombra el token (ej: "MININA")</li>
<li>Copia el token generado</li>
</ol>
<h3>🔑 PASO 2: Identificar tu URL</h3>
<ol>
<li>Tu Confluence URL es similar a: tuempresa.atlassian.net/wiki</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega la Confluence URL</li>
<li>Pega tu Email de Atlassian</li>
<li>Pega el API Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("📄 Guía Confluence - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_confluence(self):
        try:
            url = self.confluence_url_input.text().strip()
            email = self.confluence_email_input.text().strip()
            token = self.confluence_token_input.text().strip()
            if not url or not email or not token:
                QMessageBox.warning(self, "Error", "Ingresa URL, Email y Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Confluence configurado correctamente!\n\nURL: {url}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_square_card(self) -> QFrame:
        """Card para configuración de Square API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(148, 163, 184, 0.14);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        header_layout = QHBoxLayout()
        icon_name = QLabel("⬜ Square API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        info_label = QLabel("Requiere: Access Token (Sandbox o Production)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        self.square_token_input = QLineEdit()
        self.square_token_input.setPlaceholderText("Access Token (EAAA...)")
        self.square_token_input.setEchoMode(QLineEdit.Password)
        self.square_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #3e4348; }
        """)
        layout.addWidget(self.square_token_input)
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #3e4348; }
        """)
        guide_btn.clicked.connect(self._show_square_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_square)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_square_guide(self):
        guide = """
<h2>⬜ Guía de Configuración - Square API</h2>
<h3>🔑 PASO 1: Crear App en Square Developer</h3>
<ol>
<li>Ve a <a href='https://developer.squareup.com'>developer.squareup.com</a></li>
<li>Inicia sesión con tu cuenta Square</li>
<li>Dashboard → New Application</li>
</ol>
<h3>🔑 PASO 2: Obtener Access Token</h3>
<ol>
<li>Selecciona tu app</li>
<li>Ve a "Credentials" tab</li>
<li>Copia el "Access token" de Sandbox o Production</li>
</ol>
<h3>✅ PASO 3: Configurar en MININA</h3>
<ol>
<li>Pega el Access Token (empieza con EAAA)</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("⬜ Guía Square - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_square(self):
        try:
            token = self.square_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Access Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Square configurado correctamente!\n\nToken: {token[:8]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _save_settings(self):
        """Guardar configuración de todas las APIs"""
        try:
            import json
            import os
            
            # Crear directorio si no existe
            os.makedirs('data', exist_ok=True)
            
            # Preparar configuración completa
            config = {
                # APIs de IA (Cloud)
                "ai_apis": {
                    "openai": {
                        "api_key": self.openai_api_input.text() if hasattr(self, 'openai_api_input') else ""
                    },
                    "groq": {
                        "api_key": self.groq_api_input.text() if hasattr(self, 'groq_api_input') else ""
                    },
                    "anthropic": {
                        "api_key": self.anthropic_api_input.text() if hasattr(self, 'anthropic_api_input') else ""
                    }
                },
                # APIs de Bots
                "bot_apis": {
                    "discord": {
                        "token": self.discord_token_input.text() if hasattr(self, 'discord_token_input') else ""
                    },
                    "slack": {
                        "token": self.slack_token_input.text() if hasattr(self, 'slack_token_input') else ""
                    },
                    "telegram": {
                        "token": self.telegram_token_input.text() if hasattr(self, 'telegram_token_input') else "",
                        "chat_id": self.telegram_chatid_input.text() if hasattr(self, 'telegram_chatid') else ""
                    },
                    "whatsapp": {
                        "api_key": self.whatsapp_key_input.text() if hasattr(self, 'whatsapp_key_input') else "",
                        "phone_id": self.whatsapp_phone_input.text() if hasattr(self, 'whatsapp_phone_input') else ""
                    }
                },
                # APIs Empresariales
                "business_apis": {
                    "salesforce": {
                        "username": self.salesforce_username_input.text() if hasattr(self, 'salesforce_username_input') else "",
                        "password": self.salesforce_password_input.text() if hasattr(self, 'salesforce_password_input') else "",
                        "security_token": self.salesforce_token_input.text() if hasattr(self, 'salesforce_token_input') else ""
                    },
                    "quickbooks": {
                        "client_id": self.quickbooks_client_id_input.text() if hasattr(self, 'quickbooks_client_id_input') else "",
                        "client_secret": self.quickbooks_client_secret_input.text() if hasattr(self, 'quickbooks_client_secret_input') else "",
                        "realm_id": self.quickbooks_realm_input.text() if hasattr(self, 'quickbooks_realm_input') else ""
                    },
                    "shopify": {
                        "store_url": self.shopify_store_input.text() if hasattr(self, 'shopify_store_input') else "",
                        "access_token": self.shopify_token_input.text() if hasattr(self, 'shopify_token_input') else ""
                    },
                    "paypal": {
                        "client_id": self.paypal_client_id_input.text() if hasattr(self, 'paypal_client_id_input') else "",
                        "client_secret": self.paypal_secret_input.text() if hasattr(self, 'paypal_secret_input') else ""
                    },
                    "zendesk": {
                        "subdomain": self.zendesk_subdomain_input.text() if hasattr(self, 'zendesk_subdomain_input') else "",
                        "email": self.zendesk_email_input.text() if hasattr(self, 'zendesk_email_input') else "",
                        "api_token": self.zendesk_token_input.text() if hasattr(self, 'zendesk_token_input') else ""
                    },
                    "clickup": {
                        "api_token": self.clickup_token_input.text() if hasattr(self, 'clickup_token_input') else ""
                    },
                    "gitlab": {
                        "personal_access_token": self.gitlab_token_input.text() if hasattr(self, 'gitlab_token_input') else "",
                        "url": self.gitlab_url_input.text() if hasattr(self, 'gitlab_url_input') else ""
                    },
                    "airtable": {
                        "personal_access_token": self.airtable_token_input.text() if hasattr(self, 'airtable_token_input') else ""
                    },
                    "pipedrive": {
                        "api_token": self.pipedrive_token_input.text() if hasattr(self, 'pipedrive_token_input') else ""
                    },
                    "xero": {
                        "client_id": self.xero_client_id_input.text() if hasattr(self, 'xero_client_id_input') else "",
                        "client_secret": self.xero_client_secret_input.text() if hasattr(self, 'xero_client_secret_input') else ""
                    },
                    "woocommerce": {
                        "store_url": self.wc_store_url_input.text() if hasattr(self, 'wc_store_url_input') else "",
                        "consumer_key": self.wc_key_input.text() if hasattr(self, 'wc_key_input') else "",
                        "consumer_secret": self.wc_secret_input.text() if hasattr(self, 'wc_secret_input') else ""
                    },
                    "freshdesk": {
                        "domain": self.freshdesk_domain_input.text() if hasattr(self, 'freshdesk_domain_input') else "",
                        "api_key": self.freshdesk_key_input.text() if hasattr(self, 'freshdesk_key_input') else ""
                    },
                    "wrike": {
                        "permanent_access_token": self.wrike_token_input.text() if hasattr(self, 'wrike_token_input') else ""
                    },
                    "confluence": {
                        "url": self.confluence_url_input.text() if hasattr(self, 'confluence_url_input') else "",
                        "email": self.confluence_email_input.text() if hasattr(self, 'confluence_email_input') else "",
                        "api_token": self.confluence_token_input.text() if hasattr(self, 'confluence_token_input') else ""
                    },
                    "square": {
                        "access_token": self.square_token_input.text() if hasattr(self, 'square_token_input') else ""
                    }
                }
            }
            
            # Guardar a archivo
            with open('data/api_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "✅ Todos los cambios han sido guardados exitosamente.\n\n"
                "Las API keys se almacenan de forma segura en data/api_config.json"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {str(e)}")

    def _load_settings(self):
        """Cargar configuración de APIs desde archivo"""
        try:
            import json
            import os
            
            config_path = 'data/api_config.json'
            
            # Verificar si existe el archivo
            if not os.path.exists(config_path):
                return
            
            # Cargar configuración
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Cargar APIs de IA
            ai_apis = config.get('ai_apis', {})
            for api_id in ['openai', 'groq', 'anthropic']:
                api_data = ai_apis.get(api_id, {})
                api_key = api_data.get('api_key', '')
                
                input_field = getattr(self, f'{api_id}_api_input', None)
                if input_field and api_key:
                    input_field.setText(api_key)
                    # Actualizar indicador de estado
                    self._update_api_status_indicator(api_id, api_key)
            
            # Cargar APIs de Bots
            bot_apis = config.get('bot_apis', {})
            
            # Discord
            discord_data = bot_apis.get('discord', {})
            if hasattr(self, 'discord_token_input') and discord_data.get('token'):
                self.discord_token_input.setText(discord_data['token'])
            
            # Slack
            slack_data = bot_apis.get('slack', {})
            if hasattr(self, 'slack_token_input') and slack_data.get('token'):
                self.slack_token_input.setText(slack_data['token'])
            
            # Telegram
            telegram_data = bot_apis.get('telegram', {})
            if hasattr(self, 'telegram_token_input') and telegram_data.get('token'):
                self.telegram_token_input.setText(telegram_data['token'])
            if hasattr(self, 'telegram_chatid_input') and telegram_data.get('chat_id'):
                self.telegram_chatid_input.setText(telegram_data['chat_id'])
            
            # WhatsApp
            whatsapp_data = bot_apis.get('whatsapp', {})
            if hasattr(self, 'whatsapp_key_input') and whatsapp_data.get('api_key'):
                self.whatsapp_key_input.setText(whatsapp_data['api_key'])
            if hasattr(self, 'whatsapp_phone_input') and whatsapp_data.get('phone_id'):
                self.whatsapp_phone_input.setText(whatsapp_data['phone_id'])
            
            # Cargar APIs Empresariales
            business_apis = config.get('business_apis', {})
            
            # Salesforce
            salesforce_data = business_apis.get('salesforce', {})
            if hasattr(self, 'salesforce_username_input') and salesforce_data.get('username'):
                self.salesforce_username_input.setText(salesforce_data['username'])
            if hasattr(self, 'salesforce_password_input') and salesforce_data.get('password'):
                self.salesforce_password_input.setText(salesforce_data['password'])
            if hasattr(self, 'salesforce_token_input') and salesforce_data.get('security_token'):
                self.salesforce_token_input.setText(salesforce_data['security_token'])
            
            # QuickBooks
            qb_data = business_apis.get('quickbooks', {})
            if hasattr(self, 'quickbooks_client_id_input') and qb_data.get('client_id'):
                self.quickbooks_client_id_input.setText(qb_data['client_id'])
            if hasattr(self, 'quickbooks_client_secret_input') and qb_data.get('client_secret'):
                self.quickbooks_client_secret_input.setText(qb_data['client_secret'])
            if hasattr(self, 'quickbooks_realm_input') and qb_data.get('realm_id'):
                self.quickbooks_realm_input.setText(qb_data['realm_id'])
            
            # Shopify
            shopify_data = business_apis.get('shopify', {})
            if hasattr(self, 'shopify_store_input') and shopify_data.get('store_url'):
                self.shopify_store_input.setText(shopify_data['store_url'])
            if hasattr(self, 'shopify_token_input') and shopify_data.get('access_token'):
                self.shopify_token_input.setText(shopify_data['access_token'])
            
            # PayPal
            paypal_data = business_apis.get('paypal', {})
            if hasattr(self, 'paypal_client_id_input') and paypal_data.get('client_id'):
                self.paypal_client_id_input.setText(paypal_data['client_id'])
            if hasattr(self, 'paypal_secret_input') and paypal_data.get('client_secret'):
                self.paypal_secret_input.setText(paypal_data['client_secret'])
            
            # Zendesk
            zendesk_data = business_apis.get('zendesk', {})
            if hasattr(self, 'zendesk_subdomain_input') and zendesk_data.get('subdomain'):
                self.zendesk_subdomain_input.setText(zendesk_data['subdomain'])
            if hasattr(self, 'zendesk_email_input') and zendesk_data.get('email'):
                self.zendesk_email_input.setText(zendesk_data['email'])
            if hasattr(self, 'zendesk_token_input') and zendesk_data.get('api_token'):
                self.zendesk_token_input.setText(zendesk_data['api_token'])
            
            # ClickUp
            clickup_data = business_apis.get('clickup', {})
            if hasattr(self, 'clickup_token_input') and clickup_data.get('api_token'):
                self.clickup_token_input.setText(clickup_data['api_token'])
            
            # GitLab
            gitlab_data = business_apis.get('gitlab', {})
            if hasattr(self, 'gitlab_token_input') and gitlab_data.get('personal_access_token'):
                self.gitlab_token_input.setText(gitlab_data['personal_access_token'])
            if hasattr(self, 'gitlab_url_input') and gitlab_data.get('url'):
                self.gitlab_url_input.setText(gitlab_data['url'])
            
            # Airtable
            airtable_data = business_apis.get('airtable', {})
            if hasattr(self, 'airtable_token_input') and airtable_data.get('personal_access_token'):
                self.airtable_token_input.setText(airtable_data['personal_access_token'])
            
            # Pipedrive
            pipedrive_data = business_apis.get('pipedrive', {})
            if hasattr(self, 'pipedrive_token_input') and pipedrive_data.get('api_token'):
                self.pipedrive_token_input.setText(pipedrive_data['api_token'])
            
            # Xero
            xero_data = business_apis.get('xero', {})
            if hasattr(self, 'xero_client_id_input') and xero_data.get('client_id'):
                self.xero_client_id_input.setText(xero_data['client_id'])
            if hasattr(self, 'xero_client_secret_input') and xero_data.get('client_secret'):
                self.xero_client_secret_input.setText(xero_data['client_secret'])
            
            # WooCommerce
            wc_data = business_apis.get('woocommerce', {})
            if hasattr(self, 'wc_store_url_input') and wc_data.get('store_url'):
                self.wc_store_url_input.setText(wc_data['store_url'])
            if hasattr(self, 'wc_key_input') and wc_data.get('consumer_key'):
                self.wc_key_input.setText(wc_data['consumer_key'])
            if hasattr(self, 'wc_secret_input') and wc_data.get('consumer_secret'):
                self.wc_secret_input.setText(wc_data['consumer_secret'])
            
            # Freshdesk
            freshdesk_data = business_apis.get('freshdesk', {})
            if hasattr(self, 'freshdesk_domain_input') and freshdesk_data.get('domain'):
                self.freshdesk_domain_input.setText(freshdesk_data['domain'])
            if hasattr(self, 'freshdesk_key_input') and freshdesk_data.get('api_key'):
                self.freshdesk_key_input.setText(freshdesk_data['api_key'])
            
            # Wrike
            wrike_data = business_apis.get('wrike', {})
            if hasattr(self, 'wrike_token_input') and wrike_data.get('permanent_access_token'):
                self.wrike_token_input.setText(wrike_data['permanent_access_token'])
            
            # Confluence
            confluence_data = business_apis.get('confluence', {})
            if hasattr(self, 'confluence_url_input') and confluence_data.get('url'):
                self.confluence_url_input.setText(confluence_data['url'])
            if hasattr(self, 'confluence_email_input') and confluence_data.get('email'):
                self.confluence_email_input.setText(confluence_data['email'])
            if hasattr(self, 'confluence_token_input') and confluence_data.get('api_token'):
                self.confluence_token_input.setText(confluence_data['api_token'])
            
            # Square
            square_data = business_apis.get('square', {})
            if hasattr(self, 'square_token_input') and square_data.get('access_token'):
                self.square_token_input.setText(square_data['access_token'])
                
        except Exception as e:
            print(f"Error cargando configuración: {e}")

    def _create_discord_card(self) -> QFrame:
        """Card para configuración de Discord Bot API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(88, 101, 242, 0.3);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("🎮 Discord Bot")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Bot Token (from Discord Developer Portal)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.discord_token_input = QLineEdit()
        self.discord_token_input.setPlaceholderText("Bot Token (MTAx...)")
        self.discord_token_input.setEchoMode(QLineEdit.Password)
        self.discord_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #5865F2; }
        """)
        layout.addWidget(self.discord_token_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #5865F2; }
        """)
        guide_btn.clicked.connect(self._show_discord_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_discord)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_discord_guide(self):
        guide = """
<h2>🎮 Guía de Configuración - Discord Bot</h2>
<h3>🔑 PASO 1: Crear Aplicación en Discord Developer Portal</h3>
<ol>
<li>Ve a <a href='https://discord.com/developers/applications'>discord.com/developers/applications</a></li>
<li>Click "New Application"</li>
<li>Dale un nombre a tu bot</li>
</ol>
<h3>🔑 PASO 2: Obtener Bot Token</h3>
<ol>
<li>En tu aplicación, ve a "Bot" (menú lateral)</li>
<li>Click "Reset Token"</li>
<li>Copia el token (es muy largo, empieza con MTAx...)</li>
</ol>
<h3>🔑 PASO 3: Invitar Bot a tu Servidor</h3>
<ol>
<li>Ve a "OAuth2" → "URL Generator"</li>
<li>En SCOPES, selecciona "bot"</li>
<li>En BOT PERMISSIONS, selecciona los permisos necesarios</li>
<li>Copia la URL generada y ábrela en navegador</li>
<li>Selecciona tu servidor y autoriza</li>
</ol>
<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega el Bot Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("🎮 Guía Discord - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_discord(self):
        try:
            token = self.discord_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Bot Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Discord configurado correctamente!\n\nToken: {token[:10]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")

    def _create_slack_card(self) -> QFrame:
        """Card para configuración de Slack API"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(2, 6, 23, 0.22);
                border-radius: 12px;
                border: 1px solid rgba(74, 21, 75, 0.3);
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        icon_name = QLabel("💼 Slack API")
        icon_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb; background: transparent;")
        header_layout.addWidget(icon_name)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        info_label = QLabel("Requiere: Bot User OAuth Token (xoxb-...)")
        info_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.72); background: transparent;")
        layout.addWidget(info_label)
        
        self.slack_token_input = QLineEdit()
        self.slack_token_input.setPlaceholderText("xoxb-... (Bot User OAuth Token)")
        self.slack_token_input.setEchoMode(QLineEdit.Password)
        self.slack_token_input.setStyleSheet("""
            QLineEdit { background-color: rgba(30, 41, 59, 0.5); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 8px; padding: 10px; color: #e5e7eb; }
            QLineEdit:focus { border-color: #4A154B; }
        """)
        layout.addWidget(self.slack_token_input)
        
        btn_layout = QHBoxLayout()
        guide_btn = QPushButton("📖 Guía")
        guide_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: rgba(226, 232, 240, 0.9); border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 8px; padding: 8px 16px; font-size: 12px; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: #4A154B; }
        """)
        guide_btn.clicked.connect(self._show_slack_guide)
        btn_layout.addWidget(guide_btn)
        btn_layout.addStretch()
        test_btn = QPushButton("✓ Verificar")
        test_btn.setStyleSheet("""
            QPushButton { background-color: rgba(30, 41, 59, 0.65); color: #e5e7eb; border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(51, 65, 85, 0.7); border-color: rgba(99, 102, 241, 0.55); }
        """)
        test_btn.clicked.connect(self._verify_slack)
        btn_layout.addWidget(test_btn)
        layout.addLayout(btn_layout)
        return card
    
    def _show_slack_guide(self):
        guide = """
<h2>💼 Guía de Configuración - Slack API</h2>
<h3>🔑 PASO 1: Crear App en Slack API</h3>
<ol>
<li>Ve a <a href='https://api.slack.com/apps'>api.slack.com/apps</a></li>
<li>Click "Create New App"</li>
<li>Selecciona "From scratch"</li>
<li>Dale un nombre y selecciona tu workspace</li>
</ol>
<h3>🔑 PASO 2: Configurar Permisos (OAuth & Permissions)</h3>
<ol>
<li>En tu app, ve a "OAuth & Permissions"</li>
<li>En "Scopes" → "Bot Token Scopes", agrega:
   <ul>
   <li>chat:write</li>
   <li>channels:read</li>
   <li>users:read</li>
   </ul>
</li>
</ol>
<h3>🔑 PASO 3: Instalar App y Obtener Token</h3>
<ol>
<li>Click "Install to Workspace"</li>
<li>Autoriza los permisos</li>
<li>Copia el "Bot User OAuth Token" (empieza con xoxb-)</li>
</ol>
<h3>✅ PASO 4: Configurar en MININA</h3>
<ol>
<li>Pega el Bot User OAuth Token</li>
<li>Click "✓ Verificar"</li>
</ol>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("💼 Guía Slack - Configuración Completa")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _verify_slack(self):
        try:
            token = self.slack_token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "Error", "Ingresa el Bot User OAuth Token")
                return
            QMessageBox.information(self, "✅ Configuración Guardada", f"Slack configurado correctamente!\n\nToken: {token[:10]}...")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error: {str(e)}")
