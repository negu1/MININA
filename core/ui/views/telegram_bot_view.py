"""
MININA v3.0 - Telegram Bot View
===============================
Panel de control para gestionar el bot de Telegram.
Configuración, notificaciones, logs y estado del bot.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QLineEdit,
    QCheckBox, QComboBox, QTabWidget, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import json
import os
from pathlib import Path


class StatusCard(QFrame):
    """Card de estado del bot"""
    
    def __init__(self, title, value, status="inactive", parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        
        colors = {
            "active": ("#22c55e", "rgba(34, 197, 94, 0.2)"),
            "inactive": ("#ef4444", "rgba(239, 68, 68, 0.2)"),
            "warning": ("#f59e0b", "rgba(245, 158, 11, 0.2)"),
        }
        color, bg_color = colors.get(status, colors["inactive"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {color}40;
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        layout.addStretch()


class TelegramBotView(QWidget):
    """
    Vista de gestión del Bot de Telegram
    Control completo del bot integrado
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config_path = Path("data/telegram_bot_config.json")
        self.bot_running = False
        
        self._setup_ui()
        self._load_config()
        
        # Timer para actualizar estado (se activa solo cuando la vista está visible)
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
    
    def _setup_ui(self):
        """Configurar interfaz del bot"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🚀 Bot de Telegram")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botón iniciar/detener
        self.toggle_btn = QPushButton("▶️ Iniciar Bot")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #22c55e;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a34a;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_bot)
        header_layout.addWidget(self.toggle_btn)
        
        layout.addLayout(header_layout)
        
        # Subtitle
        subtitle = QLabel("Gestiona el bot de Telegram de MININA - Notificaciones y comandos")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.78); font-size: 14px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Cards de estado
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        self.status_card = StatusCard("Estado", "Detenido", "inactive")
        cards_layout.addWidget(self.status_card)
        
        self.users_card = StatusCard("Usuarios", "0", "warning")
        cards_layout.addWidget(self.users_card)
        
        self.messages_card = StatusCard("Mensajes", "0", "active")
        cards_layout.addWidget(self.messages_card)
        
        layout.addLayout(cards_layout)
        
        layout.addSpacing(20)
        
        # Tabs
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
                background-color: #22c55e;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: rgba(34, 197, 94, 0.3);
            }
        """)
        
        # Tab 1: Configuración
        config_tab = self._create_config_tab()
        self.tabs.addTab(config_tab, "⚙️ Configuración")
        
        # Tab 2: Notificaciones
        notif_tab = self._create_notifications_tab()
        self.tabs.addTab(notif_tab, "🔔 Notificaciones")
        
        # Tab 3: Logs
        logs_tab = self._create_logs_tab()
        self.tabs.addTab(logs_tab, "📋 Logs")
        
        # Tab 4: Manual de Uso
        manual_tab = self._create_manual_tab()
        self.tabs.addTab(manual_tab, "📖 Manual")
        
        layout.addWidget(self.tabs, 1)
    
    def _create_config_tab(self):
        """Crear tab de configuración"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Bot Token
        token_group = QGroupBox("Bot Token")
        token_group.setStyleSheet("""
            QGroupBox {
                color: #e5e7eb;
                font-weight: bold;
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        token_layout = QVBoxLayout(token_group)
        
        token_help = QLabel("Obtén el token desde @BotFather en Telegram")
        token_help.setStyleSheet("color: rgba(226, 232, 240, 0.8); font-size: 12px;")
        token_layout.addWidget(token_help)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 41, 59, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 8px;
                padding: 10px;
                color: #e5e7eb;
            }
        """)
        token_layout.addWidget(self.token_input)

        # Chat ID
        chat_help = QLabel("Chat ID (obligatorio para permitir acceso / pruebas)")
        chat_help.setStyleSheet("color: rgba(226, 232, 240, 0.8); font-size: 12px;")
        token_layout.addWidget(chat_help)

        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("123456789")
        self.chat_id_input.setStyleSheet(self.token_input.styleSheet())
        token_layout.addWidget(self.chat_id_input)
        
        # Botón guardar
        save_btn = QPushButton("💾 Guardar Configuración")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        save_btn.clicked.connect(self._save_config)
        token_layout.addWidget(save_btn)
        
        layout.addWidget(token_group)
        
        # Webhook URL
        webhook_group = QGroupBox("Webhook (Opcional)")
        webhook_group.setStyleSheet(token_group.styleSheet())
        
        webhook_layout = QVBoxLayout(webhook_group)
        
        webhook_help = QLabel("URL para recibir actualizaciones vía webhook")
        webhook_help.setStyleSheet("color: rgba(226, 232, 240, 0.8); font-size: 12px;")
        webhook_layout.addWidget(webhook_help)
        
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("https://tudominio.com/webhook (opcional)")
        self.webhook_input.setStyleSheet(self.token_input.styleSheet())
        webhook_layout.addWidget(self.webhook_input)
        
        layout.addWidget(webhook_group)
        
        # Botón probar conexión
        test_btn = QPushButton("🧪 Probar Conexión con Telegram")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(34, 197, 94, 0.2);
                color: #22c55e;
                border: 1px solid #22c55e;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(34, 197, 94, 0.3);
            }
        """)
        test_btn.clicked.connect(self._test_connection)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        
        return tab
    
    def _create_notifications_tab(self):
        """Crear tab de notificaciones"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        header = QLabel("Configuración de Notificaciones")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(header)
        
        desc = QLabel("Elige qué eventos quieres recibir en Telegram")
        desc.setStyleSheet("color: rgba(226, 232, 240, 0.8); font-size: 13px;")
        layout.addWidget(desc)
        
        # Checkboxes de notificaciones
        self.notify_works = QCheckBox("📦 Works completados")
        self.notify_works.setStyleSheet("color: #e5e7eb; font-size: 13px; padding: 8px;")
        self.notify_works.setChecked(True)
        layout.addWidget(self.notify_works)
        
        self.notify_skills = QCheckBox("🔧 Skills ejecutadas")
        self.notify_skills.setStyleSheet("color: #e5e7eb; font-size: 13px; padding: 8px;")
        layout.addWidget(self.notify_skills)
        
        self.notify_errors = QCheckBox("❌ Errores del sistema")
        self.notify_errors.setStyleSheet("color: #e5e7eb; font-size: 13px; padding: 8px;")
        self.notify_errors.setChecked(True)
        layout.addWidget(self.notify_errors)
        
        self.notify_orchestrator = QCheckBox("🎯 Planes del orquestador completados")
        self.notify_orchestrator.setStyleSheet("color: #e5e7eb; font-size: 13px; padding: 8px;")
        layout.addWidget(self.notify_orchestrator)
        
        layout.addSpacing(20)
        
        # Botón guardar
        save_notif_btn = QPushButton("💾 Guardar Preferencias")
        save_notif_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        save_notif_btn.clicked.connect(self._save_notification_prefs)
        layout.addWidget(save_notif_btn)
        
        layout.addStretch()
        
        return tab
    
    def _create_logs_tab(self):
        """Crear tab de logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        
        header = QLabel("Logs del Bot")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #e5e7eb;")
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
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 8px;
                padding: 12px;
                color: #e5e7eb;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.log_viewer)
        
        # Logs iniciales
        self.log_viewer.append("[INFO] Panel de Bot de Telegram iniciado")
        self.log_viewer.append("[INFO] Esperando configuración...")
        
        return tab
    
    def _create_manual_tab(self):
        """Crear tab con el manual de uso del bot de Telegram"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Título del manual
        header = QLabel("📖 Manual de Uso - Bot de Telegram")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #22c55e;")
        layout.addWidget(header)
        
        subtitle = QLabel("Guía completa para usar MININA desde Telegram")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.8); font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # Scroll area para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        manual_widget = QWidget()
        manual_layout = QVBoxLayout(manual_widget)
        manual_layout.setSpacing(20)
        
        # Sección 1: Comandos Básicos
        section1 = self._create_manual_section("🤖 Comandos Básicos", """
<b>/start</b> - Inicia la conversación con el bot y muestra el menú principal
<b>/help</b> - Muestra la ayuda y lista de comandos disponibles
<b>/status</b> - Verifica el estado de MININA y sus componentes
<b>/admin</b> - Acceso al panel de administrador (requiere PIN)
<b>/setadminpin</b> - Configura tu PIN de administrador
        """)
        manual_layout.addWidget(section1)
        
        # Sección 2: Usar Skills
        section2 = self._create_manual_section("🛠️ Usar Skills (Herramientas)", """
<b>Comando básico:</b>
<code>usa skill [nombre_skill] [tarea]</code>

<b>Ejemplos:</b>
• <code>usa skill hola_mundo ejecutar</code> - Ejecuta skill simple
• <code>usa skill pdf_maker crear</code> - Crea un PDF de prueba
• <code>usa skill asana crear_tarea Revisar documento</code> - Crea tarea en Asana

<b>Nota:</b> Algunas skills requieren configurar APIs primero en la UI.
        """)
        manual_layout.addWidget(section2)
        
        # Sección 3: Flujo de Aprobación (Acciones HIGH)
        section3 = self._create_manual_section("🔐 Acciones de Alto Riesgo (HIGH)", """
Cuando una skill tiene permisos peligrosos (ej: <code>fs_write</code> para escribir archivos), 
MININA activa un <b>flujo de doble confirmación</b>:

<b>Paso 1:</b> Aparece un mensaje con botones ✅ Confirmar / ❌ Cancelar
<b>Paso 2:</b> Después de confirmar, el bot pide tu PIN de administrador
<b>Paso 3:</b> Solo si el PIN es correcto, se ejecuta la acción

<b>Ejemplo:</b>
1. Escribes: <code>usa skill mi_pdf crear</code>
2. Bot muestra: "⚠️ Acción de riesgo alto - Ejecutar skill: mi_pdf"
3. Presionas ✅ Confirmar
4. Bot pide: "🔐 Escribe tu PIN para continuar"
5. Ingresas tu PIN (4-6 dígitos)
6. Si es correcto: se ejecuta y te envía el resultado

<b>¿Por qué?</b> Esto evita que un mensaje accidental o una inyección de prompt 
ejecute acciones peligrosas sin tu consentimiento explícito.
        """)
        manual_layout.addWidget(section3)
        
        # Sección 4: Crear Nuevas Skills
        section4 = self._create_manual_section("➕ Crear Nuevas Skills", """
<b>Comando:</b>
<code>/builder</code>

<b>Flujo del asistente:</b>
1. El bot te guía paso a paso para crear una skill
2. Pregunta: nombre, descripción, qué hace, parámetros necesarios
3. Pregunta: si necesita escribir archivos (fs_write = HIGH risk)
4. Genera automáticamente el archivo skill.py y manifest.json
5. La skill queda lista para usar inmediatamente

<b>Tip:</b> Usa /builder cuando quieras extender MININA sin programar manualmente.
        """)
        manual_layout.addWidget(section4)
        
        # Sección 5: Gestión y Admin
        section5 = self._create_manual_section("⚙️ Gestión y Administración", """
<b>Configurar PIN por primera vez:</b>
1. En la UI, ve a Configuración → Telegram Bot
2. Guarda tu Token y Chat ID
3. En Telegram, escribe: <code>/setadminpin</code>
4. Sigue las instrucciones para crear tu PIN seguro

<b>Ver estado del sistema:</b>
<code>/admin</code> - Panel de control (requiere PIN)

<b>Chat ID:</b>
Para obtener tu Chat ID, habla con @userinfobot en Telegram.
        """)
        manual_layout.addWidget(section5)
        
        # Sección 6: Seguridad Importante
        section6 = self._create_manual_section("🛡️ Notas de Seguridad", """
• <b>Tu PIN nunca se guarda en texto plano</b> - usa hash con salt (PBKDF2)
• <b>Tu PIN no va a ninguna API</b> - solo se verifica localmente
• <b>Tus credenciales están encriptadas</b> - no en .env expuesto
• <b>Cada ejecución usa agentes efímeros</b> - nacen, trabajan y mueren
• <b>Sandbox aislado</b> - las skills no pueden tocar tu sistema principal

<b>Golden rule:</b> Si algo no está en el manifest de la skill, la skill no lo puede hacer.
        """)
        manual_layout.addWidget(section6)
        
        # Sección 7: Ejemplos Prácticos
        section7 = self._create_manual_section("💡 Ejemplos Prácticos", """
<b>1. Generar un reporte PDF:</b>
<code>usa skill reporte_pdf generar</code>
→ Aprobación HIGH → PIN → PDF enviado

<b>2. Crear tarea en Asana:</b>
<code>usa skill asana crear_tarea "Comprar suministros"</code>
→ Ejecuta directamente (MEDIUM risk)

<b>3. Buscar en Google:</b>
<code>usa skill serpapi buscar "últimas noticias IA"</code>
→ Resultados en el chat

<b>4. Enviar email:</b>
<code>usa skill email_sender enviar destino@email.com "Asunto"</code>
→ Email enviado (requiere configurar SMTP primero)
        """)
        manual_layout.addWidget(section7)
        
        # Footer
        footer = QLabel("✅ MININA v3.0 - Sistema de Automatización Segura")
        footer.setStyleSheet("color: rgba(226, 232, 240, 0.6); font-size: 11px; margin-top: 20px;")
        manual_layout.addWidget(footer)
        
        manual_layout.addStretch()
        
        scroll.setWidget(manual_widget)
        layout.addWidget(scroll)
        
        return tab
    
    def _create_manual_section(self, title, content):
        """Crear una sección del manual con título y contenido HTML"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 12px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        
        # Título de sección
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 15px;
            font-weight: bold;
            color: #22c55e;
            border: none;
            background: transparent;
        """)
        layout.addWidget(title_label)
        
        # Contenido
        content_label = QLabel(content)
        content_label.setStyleSheet("""
            color: #e5e7eb;
            font-size: 13px;
            line-height: 1.6;
            border: none;
            background: transparent;
        """)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        content_label.setOpenExternalLinks(True)
        layout.addWidget(content_label)
        
        return section
    
    def _load_config(self):
        """Cargar configuración desde archivo"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                self.token_input.setText(config.get("token", ""))
                if hasattr(self, "chat_id_input"):
                    self.chat_id_input.setText(config.get("chat_id", ""))
                self.webhook_input.setText(config.get("webhook_url", ""))
                
                # Cargar preferencias de notificaciones
                notif_prefs = config.get("notifications", {})
                self.notify_works.setChecked(notif_prefs.get("works", True))
                self.notify_skills.setChecked(notif_prefs.get("skills", False))
                self.notify_errors.setChecked(notif_prefs.get("errors", True))
                self.notify_orchestrator.setChecked(notif_prefs.get("orchestrator", False))
                
                self.log_viewer.append("[INFO] Configuración cargada")
        except Exception as e:
            self.log_viewer.append(f"[ERROR] Error cargando configuración: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            config = {
                "token": self.token_input.text(),
                "chat_id": self.chat_id_input.text().strip() if hasattr(self, "chat_id_input") else "",
                "webhook_url": self.webhook_input.text(),
                "notifications": {
                    "works": self.notify_works.isChecked(),
                    "skills": self.notify_skills.isChecked(),
                    "errors": self.notify_errors.isChecked(),
                    "orchestrator": self.notify_orchestrator.isChecked()
                }
            }

            token = (config.get("token") or "").strip()
            chat_id = (config.get("chat_id") or "").strip()
            if token:
                os.environ["TELEGRAM_BOT_TOKEN"] = token
            if chat_id:
                os.environ["TELEGRAM_ALLOWED_CHAT_ID"] = chat_id

            try:
                from core.llm_extension import credential_store

                if token:
                    credential_store.set_api_key("telegram_bot_token", token)
                if chat_id:
                    credential_store.set_api_key("telegram_chat_id", chat_id)
            except Exception:
                pass
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_viewer.append("[INFO] Configuración guardada exitosamente")
            QMessageBox.information(self, "✅ Éxito", "Configuración guardada")
            
        except Exception as e:
            self.log_viewer.append(f"[ERROR] Error guardando configuración: {e}")
            QMessageBox.critical(self, "❌ Error", f"No se pudo guardar: {e}")
    
    def _save_notification_prefs(self):
        """Guardar preferencias de notificaciones"""
        self._save_config()
        QMessageBox.information(self, "✅ Éxito", "Preferencias de notificaciones guardadas")
    
    def _toggle_bot(self):
        """Iniciar o detener el bot"""
        if not self.bot_running:
            # Iniciar bot
            token = self.token_input.text().strip()
            if not token:
                QMessageBox.warning(self, "⚠️ Token requerido", "Ingresa el Bot Token primero")
                return
            
            self.bot_running = True
            self.toggle_btn.setText("⏹️ Detener Bot")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """)
            
            self.status_card.findChild(QLabel, "Estado").setText("Activo")
            self.log_viewer.append("[INFO] Bot iniciado")
            
        else:
            # Detener bot
            self.bot_running = False
            self.toggle_btn.setText("▶️ Iniciar Bot")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
            
            self.status_card.findChild(QLabel, "Estado").setText("Detenido")
            self.log_viewer.append("[INFO] Bot detenido")
    
    def _test_connection(self):
        """Probar conexión con Telegram"""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(self, "⚠️ Token requerido", "Ingresa el Bot Token primero")
            return

        chat_id = ""
        try:
            chat_id = self.chat_id_input.text().strip()
        except Exception:
            chat_id = ""
        
        self.log_viewer.append("[INFO] Probando conexión con Telegram...")
        
        try:
            import requests

            token_hint = token[:6] + "..." + token[-4:] if len(token) > 12 else "(corto)"
            self.log_viewer.append(f"[DEBUG] Endpoint: /getMe (token={token_hint})")
            
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10
            )

            if response.status_code != 200:
                body_preview = (response.text or "").strip()
                if len(body_preview) > 500:
                    body_preview = body_preview[:500] + "..."
                self.log_viewer.append(f"[ERROR] HTTP {response.status_code} en getMe")
                if body_preview:
                    self.log_viewer.append(f"[ERROR] Respuesta: {body_preview}")
                QMessageBox.critical(self, "❌ Error", f"Telegram HTTP {response.status_code}. Revisa logs para detalles.")
                return
            
            data = {}
            try:
                data = response.json()
            except Exception:
                body_preview = (response.text or "").strip()
                if len(body_preview) > 500:
                    body_preview = body_preview[:500] + "..."
                self.log_viewer.append("[ERROR] getMe devolvió JSON inválido")
                if body_preview:
                    self.log_viewer.append(f"[ERROR] Respuesta: {body_preview}")
                QMessageBox.critical(self, "❌ Error", "Respuesta inválida de Telegram. Revisa logs.")
                return

            if not data.get("ok"):
                error = data.get("description") or data.get("error") or "Error desconocido"
                self.log_viewer.append(f"[ERROR] Telegram getMe: {error}")
                QMessageBox.critical(self, "❌ Error", str(error))
                return

            bot_info = data.get("result", {})
            bot_name = bot_info.get("first_name", "Bot")
            bot_username = bot_info.get("username", "unknown")
            self.log_viewer.append(f"[INFO] ✅ getMe OK")
            self.log_viewer.append(f"[INFO] Bot: {bot_name} (@{bot_username})")

            if chat_id:
                self.log_viewer.append("[DEBUG] Endpoint: /sendMessage (mensaje de prueba)")
                try:
                    test_resp = requests.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": "✅ MININA: Conexión Telegram OK"},
                        timeout=10,
                    )
                    if test_resp.status_code == 200:
                        try:
                            tj = test_resp.json()
                        except Exception:
                            tj = {}
                        if tj.get("ok"):
                            self.log_viewer.append("[INFO] ✅ Mensaje de prueba enviado")
                        else:
                            self.log_viewer.append(f"[WARN] sendMessage falló: {tj.get('description', 'sin detalle')}")
                    else:
                        body_preview = (test_resp.text or "").strip()
                        if len(body_preview) > 500:
                            body_preview = body_preview[:500] + "..."
                        self.log_viewer.append(f"[WARN] sendMessage HTTP {test_resp.status_code}")
                        if body_preview:
                            self.log_viewer.append(f"[WARN] Respuesta: {body_preview}")
                except requests.exceptions.RequestException as e:
                    self.log_viewer.append(f"[WARN] sendMessage exception: {type(e).__name__}: {e}")
            else:
                self.log_viewer.append("[WARN] No se configuró Chat ID: no se envía mensaje de prueba")

            QMessageBox.information(
                self,
                "✅ Conexión Exitosa",
                f"Bot conectado: {bot_name}\n@{bot_username}"
            )
                
        except Exception as e:
            try:
                import requests
                if isinstance(e, requests.exceptions.RequestException):
                    self.log_viewer.append(f"[ERROR] requests: {type(e).__name__}: {e}")
                else:
                    self.log_viewer.append(f"[ERROR] {type(e).__name__}: {e}")
            except Exception:
                self.log_viewer.append(f"[ERROR] {type(e).__name__}: {e}")
            QMessageBox.critical(self, "❌ Error", "Error de conexión. Revisa la pestaña Logs para detalles.")
    
    def _update_status(self):
        """Actualizar estado del bot"""
        # En producción, esto consultaría el estado real del bot
        pass
    
    def _clear_logs(self):
        """Limpiar logs"""
        self.log_viewer.clear()
        self.log_viewer.append("[INFO] Logs limpiados")
    
    def on_activated(self):
        """Llamado cuando la vista se activa"""
        if not self.status_timer.isActive():
            self.status_timer.start(8000)
        self._update_status()

    def on_deactivated(self):
        """Llamado cuando la vista se desactiva"""
        if self.status_timer.isActive():
            self.status_timer.stop()
