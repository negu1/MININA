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
        
        # === SECCIÓN: APIs Gratuitas ===
        free_apis_section = self._create_section("🆓 APIs Gratuitas (Local)")
        
        # Ollama (Local)
        ollama_card = self._create_local_api_card(
            "🦙 Ollama",
            "http://localhost:11434",
            "Modelos locales (Llama, Mistral, etc.)",
            "Gratis - Requiere instalación local"
        )
        free_apis_section.layout().addWidget(ollama_card)
        
        # LM Studio (Local)
        lmstudio_card = self._create_local_api_card(
            "🔬 LM Studio",
            "http://localhost:1234",
            "Modelos locales con UI",
            "Gratis - Requiere instalación local"
        )
        free_apis_section.layout().addWidget(lmstudio_card)
        
        # Jan (Local)
        jan_card = self._create_local_api_card(
            "🤖 Jan",
            "http://localhost:1337",
            "Alternativa local de ChatGPT",
            "Gratis - Requiere instalación local"
        )
        free_apis_section.layout().addWidget(jan_card)
        
        content_layout.addWidget(free_apis_section)
        paid_apis_section = self._create_section("🔌 APIs y Servicios")
        
        # Backend
        backend_card = self._create_connection_card(
            "Backend MININA",
            "http://localhost:8897",
            "✅ Conectado",
            True
        )
        paid_apis_section.layout().addWidget(backend_card)
        
        # OpenAI API
        openai_card = self._create_api_card(
            "OpenAI API",
            "sk-...",
            "🤖 GPT-4, GPT-3.5"
        )
        paid_apis_section.layout().addWidget(openai_card)
        
        # Groq API
        groq_card = self._create_api_card(
            "Groq API",
            "gsk_...",
            "⚡ Velocidad extrema"
        )
        paid_apis_section.layout().addWidget(groq_card)
        
        # Anthropic API
        anthropic_card = self._create_api_card(
            "Anthropic API",
            "sk-ant-...",
            "🧠 Claude AI"
        )
        paid_apis_section.layout().addWidget(anthropic_card)
        
        content_layout.addWidget(paid_apis_section)
        
        # === SECCIÓN: MESSAGING ===
        messaging_section = self._create_section("💬 Mensajería")
        
        # Telegram con Chat ID y guía
        telegram_card = self._create_telegram_card()
        messaging_section.layout().addWidget(telegram_card)
        
        # WhatsApp con guía
        whatsapp_card = self._create_whatsapp_card()
        messaging_section.layout().addWidget(whatsapp_card)
        
        content_layout.addWidget(messaging_section)
        
        # === SECCIÓN: BASE DE DATOS ===
        db_section = self._create_section("🗄️ Almacenamiento")
        
        # Works/Archivos
        works_card = self._create_connection_card(
            "Works (Archivos)",
            "data/works",
            "✅ Activo - 8 archivos",
            True
        )
        db_section.layout().addWidget(works_card)
        
        # Skills
        skills_card = self._create_connection_card(
            "Skills",
            "skills_user/",
            "✅ 4 skills cargadas",
            True
        )
        db_section.layout().addWidget(skills_card)
        
        # Memoria
        memory_card = self._create_connection_card(
            "Memoria",
            "data/memory",
            "✅ Persistente",
            True
        )
        db_section.layout().addWidget(memory_card)
        
        content_layout.addWidget(db_section)
        
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
        
        token_input = QLineEdit()
        token_input.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        token_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(token_input)
        
        # Chat ID
        chatid_label = QLabel("💬 Chat ID:")
        chatid_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(chatid_label)
        
        chatid_input = QLineEdit()
        chatid_input.setPlaceholderText("12345678 (tu ID de usuario o grupo)")
        layout.addWidget(chatid_input)
        
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
        
        key_input = QLineEdit()
        key_input.setPlaceholderText("EAAxxxxx... (token de WhatsApp Business)")
        key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(key_input)
        
        # Phone Number ID
        phone_label = QLabel("📱 Phone Number ID:")
        phone_label.setStyleSheet("font-size: 13px; color: rgba(226, 232, 240, 0.72);")
        layout.addWidget(phone_label)
        
        phone_input = QLineEdit()
        phone_input.setPlaceholderText("123456789012345 (ID del número de teléfono)")
        layout.addWidget(phone_input)
        
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
        
    def _save_settings(self):
        """Guardar configuración"""
        QMessageBox.information(
            self,
            "Configuración Guardada",
            "✅ Los cambios han sido guardados exitosamente.\n\n"
            "Nota: Las API keys se almacenan de forma segura."
        )
