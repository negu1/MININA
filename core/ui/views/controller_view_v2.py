"""
Nuevo Controller View con navegación por categorías de reglas/políticas
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QStackedWidget,
    QGridLayout, QCheckBox, QSpinBox, QLineEdit,
    QComboBox, QSlider, QMessageBox, QTextEdit,
    QTabWidget, QGroupBox, QFormLayout, QListWidget,
    QListWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.universal_policy import (
    get_policy_engine, UniversalRule, RuleType, 
    ComparisonOp, RuleCondition, RuleAction, JobProfile
)
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import json


class RuleCategoryCard(QPushButton):
    """Card para categoría de reglas"""
    def __init__(self, category_id: str, name: str, icon: str, 
                 description: str, count: int, color: str, parent=None):
        super().__init__(parent)
        self.category_id = category_id
        self.setFixedSize(260, 140)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Header con icono y contador
        header = QHBoxLayout()
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 32px; color: {color};")
        header.addWidget(icon_label)
        
        header.addStretch()
        
        count_badge = QLabel(str(count))
        count_badge.setStyleSheet(f"""
            background-color: {color}40;
            color: {color};
            border-radius: 12px;
            padding: 4px 12px;
            font-size: 13px;
            font-weight: bold;
        """)
        header.addWidget(count_badge)
        
        layout.addLayout(header)
        
        # Nombre
        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        layout.addWidget(name_label)
        
        # Descripción
        desc = QLabel(description)
        desc.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.6);
        """)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Estilo
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(15, 23, 42, 0.6);
                border: 2px solid {color}30;
                border-radius: 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba(15, 23, 42, 0.8);
                border: 2px solid {color};
            }}
        """)


class RuleItemWidget(QFrame):
    """Widget para mostrar una regla en la lista"""
    clicked = pyqtSignal(str)  # Emite rule_id
    
    def __init__(self, rule: UniversalRule, is_enabled: bool, parent=None):
        super().__init__(parent)
        self.rule_id = rule.id
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Indicador de estado
        status = "🟢" if is_enabled else "⚪"
        status_label = QLabel(status)
        status_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(status_label)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name = QLabel(f"{rule.name}")
        name.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        info_layout.addWidget(name)
        
        desc = QLabel(rule.description)
        desc.setStyleSheet("""
            font-size: 12px;
            color: rgba(226, 232, 240, 0.6);
        """)
        info_layout.addWidget(desc)
        
        # Tags
        tags_layout = QHBoxLayout()
        tags_layout.setSpacing(6)
        
        type_tag = QLabel(f"📋 {rule.type.value}")
        type_tag.setStyleSheet("""
            background-color: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 10px;
        """)
        tags_layout.addWidget(type_tag)
        
        if rule.applies_to:
            scope_tag = QLabel(f"🎯 {len(rule.applies_to)} tipos")
            scope_tag.setStyleSheet("""
                background-color: rgba(34, 197, 94, 0.2);
                color: #4ade80;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
            """)
            tags_layout.addWidget(scope_tag)
        
        tags_layout.addStretch()
        info_layout.addLayout(tags_layout)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Flecha
        arrow = QLabel("›")
        arrow.setStyleSheet("""
            font-size: 24px;
            color: rgba(226, 232, 240, 0.4);
        """)
        layout.addWidget(arrow)
        
        # Estilo
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.4);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(99, 102, 241, 0.3);
            }
        """)
    
    def mousePressEvent(self, event):
        self.clicked.emit(self.rule_id)


class JobProfileCard(QFrame):
    """Card para perfil de trabajo"""
    def __init__(self, profile: JobProfile, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.5);
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        
        icon = QLabel(profile.name.split()[0])  # Emoji
        icon.setStyleSheet("font-size: 24px;")
        header.addWidget(icon)
        
        name = QLabel(" ".join(profile.name.split()[1:]))
        name.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        header.addWidget(name)
        
        header.addStretch()
        
        # Risk badge
        risk_colors = {0: "#22c55e", 30: "#22c55e", 50: "#f59e0b", 70: "#ef4444", 90: "#dc2626"}
        risk_color = risk_colors.get(min([k for k in risk_colors.keys() if k >= profile.base_risk_level]), "#f59e0b")
        risk_badge = QLabel(f"Riesgo: {profile.base_risk_level}")
        risk_badge.setStyleSheet(f"""
            background-color: {risk_color}30;
            color: {risk_color};
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        header.addWidget(risk_badge)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel(profile.description)
        desc.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.6);")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Stats
        stats = QHBoxLayout()
        
        rules_count = len(profile.default_rules)
        apis_count = len(profile.typical_apis)
        
        stats_label = QLabel(f"📋 {rules_count} reglas | 🔌 {apis_count} APIs típicas")
        stats_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        stats.addWidget(stats_label)
        
        stats.addStretch()
        layout.addLayout(stats)


class ControllerViewV2(QWidget):
    """
    Nueva vista del Controlador con navegación por categorías
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.policy_engine = get_policy_engine()
        self.current_category = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stack de pantallas
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Pantalla 1: Dashboard de categorías
        self.dashboard_screen = self._create_dashboard()
        self.stack.addWidget(self.dashboard_screen)
        
        # Pantalla 2: Lista de reglas de categoría
        self.rules_list_screen = self._create_rules_list_screen()
        self.stack.addWidget(self.rules_list_screen)
        
        # Pantalla 3: Editor de regla
        self.rule_editor_screen = self._create_rule_editor()
        self.stack.addWidget(self.rule_editor_screen)
        
        # Pantalla 4: Perfiles de trabajo
        self.profiles_screen = self._create_profiles_screen()
        self.stack.addWidget(self.profiles_screen)
        
        # Mostrar dashboard
        self.stack.setCurrentIndex(0)
    
    def _create_dashboard(self):
        """Crear pantalla principal con categorías"""
        screen = QFrame()
        screen.setStyleSheet("background-color: #0f172a;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("🎛️ Controlador de Políticas")
        header.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #e5e7eb;
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Gestiona reglas universales aplicables a todos los trabajos")
        subtitle.setStyleSheet("font-size: 14px; color: rgba(226, 232, 240, 0.6);")
        layout.addWidget(subtitle)
        
        # Stats rápidos
        stats_layout = QHBoxLayout()
        
        total_rules = len(self.policy_engine.rules)
        enabled_rules = sum(1 for r in self.policy_engine.rules.values() if r.enabled)
        
        stats = [
            ("📋 Reglas Activas", str(enabled_rules), "#6366f1"),
            ("🔒 Reglas Totales", str(total_rules), "#94a3b8"),
            ("👤 Perfiles", str(len(self.policy_engine.job_profiles)), "#22c55e"),
        ]
        
        for label, value, color in stats:
            stat_frame = QFrame()
            stat_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(15, 23, 42, 0.6);
                    border: 1px solid {color}40;
                    border-radius: 12px;
                    padding: 16px;
                }}
            """)
            stat_layout = QVBoxLayout(stat_frame)
            
            val_label = QLabel(value)
            val_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
            stat_layout.addWidget(val_label)
            
            lab_label = QLabel(label)
            lab_label.setStyleSheet("font-size: 12px; color: rgba(226, 232, 240, 0.6);")
            stat_layout.addWidget(lab_label)
            
            stats_layout.addWidget(stat_frame)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Separador
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(148, 163, 184, 0.2);")
        layout.addWidget(separator)
        
        # Grid de categorías
        categories = [
            ("system", "🖥️ Sistema", "Reglas de recursos y rendimiento", "#6366f1"),
            ("security", "🔒 Seguridad", "Protección y permisos", "#ef4444"),
            ("time", "🕐 Tiempo", "Horarios y ventanas", "#f59e0b"),
            ("financial", "💰 Financiero", "Costos y límites", "#22c55e"),
            ("compliance", "📋 Compliance", "Normativas y auditoría", "#8b5cf6"),
            ("custom", "⚙️ Personalizado", "Reglas específicas", "#94a3b8"),
        ]
        
        cats_title = QLabel("📁 Categorías de Reglas")
        cats_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(cats_title)
        
        grid = QGridLayout()
        grid.setSpacing(16)
        
        for i, (cat_id, name, desc, color) in enumerate(categories):
            # Contar reglas en esta categoría
            count = sum(1 for r in self.policy_engine.rules.values() 
                       if r.category == cat_id and r.enabled)
            
            card = RuleCategoryCard(cat_id, name, name.split()[0], desc, count, color)
            card.clicked.connect(lambda checked, cid=cat_id: self._show_category_rules(cid))
            grid.addWidget(card, i // 3, i % 3)
        
        layout.addLayout(grid)
        
        # Separador
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: rgba(148, 163, 184, 0.2);")
        layout.addWidget(sep2)
        
        # Perfiles de trabajo
        profiles_title = QLabel("👤 Perfiles de Trabajo")
        profiles_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(profiles_title)
        
        profiles_btn = QPushButton("Ver Todos los Perfiles →")
        profiles_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(99, 102, 241, 0.2);
                color: #818cf8;
                border: 1px solid rgba(99, 102, 241, 0.4);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(99, 102, 241, 0.3);
            }
        """)
        profiles_btn.setCursor(Qt.PointingHandCursor)
        profiles_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        layout.addWidget(profiles_btn)
        
        # Mostrar algunos perfiles
        profiles_grid = QGridLayout()
        profiles_grid.setSpacing(12)
        
        for i, (pid, profile) in enumerate(list(self.policy_engine.job_profiles.items())[:4]):
            card = JobProfileCard(profile)
            profiles_grid.addWidget(card, i // 2, i % 2)
        
        layout.addLayout(profiles_grid)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(screen)
        main_layout.addWidget(scroll)
        
        return screen
    
    def _create_rules_list_screen(self):
        """Crear pantalla de lista de reglas"""
        screen = QFrame()
        screen.setStyleSheet("background-color: #0f172a;")
        
        self.rules_list_layout = QVBoxLayout(screen)
        self.rules_list_layout.setContentsMargins(40, 40, 40, 40)
        self.rules_list_layout.setSpacing(20)
        
        return screen
    
    def _show_category_rules(self, category_id: str):
        """Mostrar reglas de una categoría"""
        self.current_category = category_id
        
        # Limpiar
        while self.rules_list_layout.count():
            item = self.rules_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Volver")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #e5e7eb;
            }
        """)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        header.addWidget(back_btn)
        
        header.addStretch()
        self.rules_list_layout.addLayout(header)
        
        # Título
        category_names = {
            "system": "🖥️ Sistema",
            "security": "🔒 Seguridad", 
            "time": "🕐 Tiempo",
            "financial": "💰 Financiero",
            "compliance": "📋 Compliance",
            "custom": "⚙️ Personalizado"
        }
        
        title = QLabel(category_names.get(category_id, category_id))
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e5e7eb;")
        self.rules_list_layout.addWidget(title)
        
        # Botón nueva regla
        new_btn = QPushButton("+ Nueva Regla")
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
        """)
        new_btn.clicked.connect(self._create_new_rule)
        self.rules_list_layout.addWidget(new_btn)
        
        # Listar reglas
        rules = [r for r in self.policy_engine.rules.values() 
                if r.category == category_id]
        
        if not rules:
            empty = QLabel("No hay reglas en esta categoría")
            empty.setStyleSheet("color: #94a3b8; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self.rules_list_layout.addWidget(empty)
        else:
            for rule in sorted(rules, key=lambda r: r.priority):
                item = RuleItemWidget(rule, rule.enabled)
                item.clicked.connect(self._edit_rule)
                self.rules_list_layout.addWidget(item)
        
        self.rules_list_layout.addStretch()
        
        # Mostrar
        self.stack.setCurrentIndex(1)
    
    def _create_rule_editor(self):
        """Crear pantalla de editor de regla"""
        screen = QFrame()
        screen.setStyleSheet("background-color: #0f172a;")
        
        self.editor_layout = QVBoxLayout(screen)
        self.editor_layout.setContentsMargins(40, 40, 40, 40)
        self.editor_layout.setSpacing(20)
        
        return screen
    
    def _create_profiles_screen(self):
        """Crear pantalla de perfiles de trabajo"""
        screen = QFrame()
        screen.setStyleSheet("background-color: #0f172a;")
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        back_btn = QPushButton("← Volver")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #e5e7eb;
            }
        """)
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        header.addWidget(back_btn)
        
        header.addStretch()
        layout.addLayout(header)
        
        # Título
        title = QLabel("👤 Perfiles de Trabajo")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e5e7eb;")
        layout.addWidget(title)
        
        desc = QLabel("Perfiles predefinidos que determinan reglas por defecto para diferentes tipos de trabajos")
        desc.setStyleSheet("font-size: 14px; color: rgba(226, 232, 240, 0.6);")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Grid de perfiles
        for pid, profile in self.policy_engine.job_profiles.items():
            card = JobProfileCard(profile)
            layout.addWidget(card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(screen)
        main_layout.addWidget(scroll)
        
        return screen
    
    def _edit_rule(self, rule_id: str):
        """Editar una regla existente"""
        # Implementar editor
        QMessageBox.information(self, "Editar Regla", f"Editor de regla {rule_id}\n\n(Implementación completa en desarrollo)")
    
    def _create_new_rule(self):
        """Crear nueva regla"""
        QMessageBox.information(self, "Nueva Regla", "Wizard para crear nueva regla\n\n(Implementación completa en desarrollo)")


# Para compatibilidad con import existente
ControllerView = ControllerViewV2
