"""
MININA v3.0 - MainWindow (Diseño Elegante)
Ventana principal con tema moderno y logo de gato
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from core.ui.views.orchestrator_view import OrchestratorView
from core.ui.views.supervisor_view import SupervisorView
from core.ui.views.controller_view_v2 import ControllerViewV2
from core.ui.views.manager_view import ManagerView
from core.ui.views.works_view import WorksView
from core.ui.views.jobs_view import JobsView
from core.ui.views.skills_view import SkillsView
from core.ui.views.settings_view_v2 import SettingsViewV2
from core.ui.views.external_skills_view import ExternalSkillsEvaluatorView


class MainWindow(QMainWindow):
    """Ventana principal de MININA v3.0 - Diseño Elegante"""
    
    # Colores del tema moderno
    PRIMARY_COLOR = "#6366f1"
    SECONDARY_COLOR = "#8b5cf6"
    ACCENT_COLOR = "#ec4899"
    NAV_BG = "#1e293b"
    TEXT_LIGHT = "#f1f5f9"
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MININA v3.0 - Sistema Inteligente 🐱")
        self.setMinimumSize(1400, 900)
        
        # Aplicar estilos
        self._apply_styles()
        
        # Configurar UI
        self._setup_ui()
        self._setup_navigation()
        self._setup_tray_icon()
        
    def _apply_styles(self):
        """Aplicar estilos CSS modernos elegantes"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #0b1220;
            }}

            QWidget {{
                color: #e5e7eb;
                font-family: Inter, Segoe UI, Arial;
                font-size: 13px;
            }}

            QLabel {{
                color: #e5e7eb;
            }}

            QToolTip {{
                background-color: #111827;
                color: #e5e7eb;
                border: 1px solid rgba(99, 102, 241, 0.55);
                padding: 6px 10px;
                border-radius: 10px;
            }}

            QFrame {{
                background: transparent;
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 6px 2px 6px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(148, 163, 184, 0.35);
                min-height: 24px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(148, 163, 184, 0.55);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}

            QLineEdit, QTextEdit {{
                background-color: #ffffff;
                border: 2px solid #6366f1;
                border-radius: 8px;
                padding: 10px 12px;
                color: #1f2937;
                font-size: 14px;
                selection-background-color: #6366f1;
                selection-color: #ffffff;
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid #4f46e5;
                background-color: #ffffff;
            }}
            QLineEdit::placeholder, QTextEdit::placeholder {{
                color: #6b7280;
            }}

            QComboBox {{
                background-color: #ffffff;
                border: 2px solid #6366f1;
                border-radius: 8px;
                padding: 8px 12px;
                color: #1f2937;
                font-size: 14px;
                min-height: 24px;
            }}
            QComboBox:hover {{
                border: 2px solid #4f46e5;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #ffffff;
                color: #1f2937;
                selection-background-color: #6366f1;
                selection-color: #ffffff;
                border: 2px solid #6366f1;
                outline: 0;
                padding: 4px;
            }}

            QPushButton {{
                background-color: #6366f1;
                border: 2px solid #4f46e5;
                padding: 10px 18px;
                border-radius: 10px;
                font-weight: bold;
                color: #ffffff;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #4f46e5;
                border: 2px solid #4338ca;
            }}
            QPushButton:pressed {{
                background-color: #4338ca;
            }}
            QPushButton:disabled {{
                background-color: #9ca3af;
                color: #6b7280;
                border: 2px solid #9ca3af;
            }}

            QGroupBox {{
                background-color: #ffffff;
                border: 2px solid #6366f1;
                border-radius: 12px;
                margin-top: 16px;
                padding: 16px;
                color: #1f2937;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 4px 12px;
                color: #6366f1;
                font-weight: bold;
                font-size: 14px;
                background-color: #ffffff;
                border-radius: 4px;
            }}

            QTableWidget {{
                background-color: #ffffff;
                border: 2px solid #6366f1;
                border-radius: 12px;
                gridline-color: #e5e7eb;
                selection-background-color: #6366f1;
                selection-color: #ffffff;
                color: #1f2937;
                font-size: 13px;
                alternate-background-color: #f3f4f6;
            }}
            QTableWidget::item {{
                padding: 12px 8px;
                border-bottom: 1px solid #e5e7eb;
                min-height: 40px;
            }}
            QTableWidget::item:selected {{
                background-color: #6366f1;
                color: #ffffff;
            }}
            QTableWidget QHeaderView::section {{
                background-color: #6366f1;
                color: #ffffff;
                padding: 12px 8px;
                border: none;
                font-weight: bold;
                font-size: 13px;
                min-height: 44px;
            }}

            QListWidget {{
                background-color: #ffffff;
                border: 2px solid #6366f1;
                border-radius: 12px;
                padding: 8px;
                color: #1f2937;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 4px;
                color: #1f2937;
            }}
            QListWidget::item:selected {{
                background-color: #6366f1;
                color: #ffffff;
            }}
            QListWidget::item:hover {{
                background-color: #e0e7ff;
            }}
            QListWidget::item:selected:hover {{
                background-color: #4f46e5;
            }}
            
            #navigationRail {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self.NAV_BG},
                    stop:1 #0f172a);
                border: none;
            }}
            
            QPushButton#nav_orchestrator, QPushButton#nav_manager,
            QPushButton#nav_supervisor, QPushButton#nav_controller,
            QPushButton#nav_jobs, QPushButton#nav_works, QPushButton#nav_skills,
            QPushButton#nav_external_skills, QPushButton#nav_settings {{
                background-color: transparent;
                border: 2px solid transparent;
                border-radius: 16px;
                font-size: 28px;
                padding: 8px;
            }}
            
            QPushButton#nav_orchestrator:hover, QPushButton#nav_manager:hover,
            QPushButton#nav_supervisor:hover, QPushButton#nav_controller:hover,
            QPushButton#nav_jobs:hover, QPushButton#nav_works:hover, QPushButton#nav_skills:hover,
            QPushButton#nav_external_skills:hover, QPushButton#nav_settings:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border: 2px solid {self.PRIMARY_COLOR};
            }}
            
            QPushButton#nav_orchestrator:checked, QPushButton#nav_manager:checked,
            QPushButton#nav_supervisor:checked, QPushButton#nav_controller:checked,
            QPushButton#nav_jobs:checked, QPushButton#nav_works:checked, QPushButton#nav_skills:checked,
            QPushButton#nav_external_skills:checked, QPushButton#nav_settings:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.PRIMARY_COLOR},
                    stop:1 {self.SECONDARY_COLOR});
                border: 2px solid {self.ACCENT_COLOR};
            }}
        """)
        
    def _setup_ui(self):
        """Configurar interfaz principal"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Navigation Rail (barra lateral)
        self.nav_rail = self._create_navigation_rail()
        main_layout.addWidget(self.nav_rail)
        
        # Área de contenido
        self.content_area = self._create_content_area()
        main_layout.addWidget(self.content_area, 1)
        
    def _create_navigation_rail(self) -> QFrame:
        """Crear barra de navegación lateral elegante con logo de gato"""
        rail = QFrame()
        rail.setObjectName("navigationRail")
        rail.setFixedWidth(90)
        
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(12, 24, 12, 24)
        layout.setSpacing(10)
        
        # Logo de Gato 🐱 en contenedor elegante
        logo_container = QFrame()
        logo_container.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {self.PRIMARY_COLOR},
                stop:0.5 {self.SECONDARY_COLOR},
                stop:1 {self.ACCENT_COLOR});
            border-radius: 20px;
        """)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(8, 12, 8, 12)
        
        logo_label = QLabel("🐱")
        logo_label.setStyleSheet("font-size: 36px; background: transparent;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        # Nombre MININA
        app_name = QLabel("MININA")
        app_name.setStyleSheet(f"""
            color: {self.TEXT_LIGHT};
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 2px;
            background: transparent;
        """)
        app_name.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(app_name)
        
        layout.addWidget(logo_container)
        layout.addSpacing(25)
        
        # Separador decorativo
        separator = QFrame()
        separator.setFixedHeight(2)
        separator.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.5 {self.PRIMARY_COLOR},
                stop:1 transparent);
            border: none;
        """)
        layout.addWidget(separator)
        layout.addSpacing(20)
        
        # Botones de navegación con iconos modernos
        self.nav_buttons = {}
        nav_items = [
            ("orchestrator", "🎯", "Orquestador"),
            ("manager", "⚡", "Agentes"),
            ("supervisor", "🛡️", "Alertas"),
            ("controller", "📜", "Reglas"),
            ("jobs", "🚀", "Trabajos"),
            ("works", "📦", "Works"),
            ("skills", "🔧", "Skills"),
            ("external_skills", "🧪", "Skills Externas"),
            ("settings", "⚙️", "Configuración"),
        ]
        
        for view_id, icon, tooltip in nav_items:
            btn = QPushButton(f"{icon}")
            btn.setObjectName(f"nav_{view_id}")
            btn.setFixedSize(66, 66)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, vid=view_id: self._on_nav_clicked(vid))
            
            self.nav_buttons[view_id] = btn
            layout.addWidget(btn, alignment=Qt.AlignCenter)
            
        layout.addSpacing(15)
        
        # Separador antes del botón de refresh
        separator_refresh = QFrame()
        separator_refresh.setFixedHeight(2)
        separator_refresh.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.5 {self.PRIMARY_COLOR},
                stop:1 transparent);
            border: none;
        """)
        layout.addWidget(separator_refresh)
        
        layout.addSpacing(10)
        
        # Botón de actualización global
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setObjectName("nav_refresh")
        self.refresh_btn.setFixedSize(50, 50)
        self.refresh_btn.setToolTip("Actualizar todas las vistas")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton#nav_refresh {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 2px solid {self.PRIMARY_COLOR};
                border-radius: 25px;
                color: {self.TEXT_LIGHT};
                font-size: 20px;
            }}
            QPushButton#nav_refresh:hover {{
                background-color: rgba(99, 102, 241, 0.3);
                border: 2px solid {self.ACCENT_COLOR};
            }}
            QPushButton#nav_refresh:pressed {{
                background-color: rgba(99, 102, 241, 0.5);
            }}
        """)
        self.refresh_btn.clicked.connect(self._refresh_all_views)
        layout.addWidget(self.refresh_btn, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        
        return rail
        
    def _create_content_area(self) -> QStackedWidget:
        """Crear área de contenido con vistas apiladas"""
        stack = QStackedWidget()
        stack.setObjectName("contentStack")
        
        # Crear y añadir vistas
        self.views = {
            "orchestrator": OrchestratorView(),
            "manager": ManagerView(),
            "supervisor": SupervisorView(),
            "controller": ControllerViewV2(),
            "jobs": JobsView(),
            "works": WorksView(),
            "skills": SkillsView(),
            "external_skills": ExternalSkillsEvaluatorView(),
            "settings": SettingsViewV2(),
        }
        
        for view in self.views.values():
            stack.addWidget(view)
            
        # Mostrar orquestador por defecto
        self._current_view = "orchestrator"
        self.nav_buttons["orchestrator"].setChecked(True)
        
        return stack
        
    def _on_nav_clicked(self, view_id: str):
        """Manejar click en navegación"""
        # Desmarcar botón anterior
        if self._current_view in self.nav_buttons:
            self.nav_buttons[self._current_view].setChecked(False)
            
        # Marcar nuevo botón
        self.nav_buttons[view_id].setChecked(True)
        self._current_view = view_id
        
        # Cambiar vista
        view = self.views[view_id]
        self.content_area.setCurrentWidget(view)

        try:
            if hasattr(view, "on_activated"):
                view.on_activated()
        except Exception:
            pass

    def navigate_to(self, view_id: str):
        """Navegar a una vista por id (API pública para otras vistas)."""
        if view_id in self.views:
            self._on_nav_clicked(view_id)

    def get_view(self, view_id: str):
        """Obtener instancia de una vista por id."""
        return self.views.get(view_id)

    def _refresh_all_views(self):
        """Actualizar/recargar todas las vistas del sistema."""
        from PyQt5.QtWidgets import QApplication
        
        # Cambiar cursor a espera
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            # Recargar cada vista si tiene método de refresh
            refresh_methods = {
                "orchestrator": lambda v: v.on_activated() if hasattr(v, "on_activated") else None,
                "manager": lambda v: v.on_activated() if hasattr(v, "on_activated") else None,
                "supervisor": lambda v: v.on_activated() if hasattr(v, "on_activated") else None,
                "controller": lambda v: self._refresh_controller_view(v),
                "works": lambda v: v.on_activated() if hasattr(v, "on_activated") else None,
                "skills": lambda v: self._refresh_skills_view(v),
                "settings": lambda v: v.on_activated() if hasattr(v, "on_activated") else None,
            }
            
            for view_id, view in self.views.items():
                try:
                    if view_id in refresh_methods:
                        refresh_methods[view_id](view)
                except Exception as e:
                    print(f"Error actualizando {view_id}: {e}")
            
            # Forzar actualización visual
            self.content_area.update()
            
        finally:
            QApplication.restoreOverrideCursor()
    
    def _refresh_controller_view(self, view):
        """Refrescar vista de Controller (recargar policy settings)"""
        from core.ui.policy_settings import PolicySettings
        try:
            PolicySettings.load()
            # Actualizar valores en UI si es posible
            if hasattr(view, 'chat_limit_spin'):
                view.chat_limit_spin.setValue(PolicySettings.get().chat_history_limit)
            if hasattr(view, 'rate_limit_spin'):
                view.rate_limit_spin.setValue(PolicySettings.get().rate_limit_per_min)
            if hasattr(view, 'storage_spin'):
                view.storage_spin.setValue(PolicySettings.get().storage_mb_per_day)
        except Exception as e:
            print(f"Error refrescando controller: {e}")
    
    def _refresh_skills_view(self, view):
        """Refrescar vista de Skills (recargar lista de skills)"""
        try:
            if hasattr(view, '_load_skills_from_api'):
                view._load_skills_from_api()
            if hasattr(view, 'on_activated'):
                view.on_activated()
        except Exception as e:
            print(f"Error refrescando skills: {e}")
        
    def _setup_navigation(self):
        """Configurar navegación entre vistas"""
        # La navegación se configura automáticamente en _create_navigation_rail
        pass
        
    def _setup_tray_icon(self):
        """Configurar icono en system tray con logo de gato"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Menú del tray estilizado
        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.NAV_BG};
                color: {self.TEXT_LIGHT};
                border: 1px solid {self.PRIMARY_COLOR};
                border-radius: 8px;
                padding: 8px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {self.PRIMARY_COLOR};
            }}
        """)
        
        show_action = tray_menu.addAction("🐱 Mostrar MININA")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("👋 Salir")
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("🐱 MININA v3.0 - Sistema Inteligente")
        self.tray_icon.show()
