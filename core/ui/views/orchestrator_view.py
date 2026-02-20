"""
MININA v3.0 - Orchestrator View (Capa 1) - DISEÑO ELEGANTE
Chat inteligente estilo moderno con burbujas y tema oscuro/claro
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QComboBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QPalette

import os

from core.ui.api_client import api_client

from core.AgentLifecycleManager import AgentLifecycleManager

from core.ui.ui_settings import UiSettings

from core.orchestrator.orchestrator_agent import OrchestratorAgent


class _PlanWorker(QThread):
    plan_ready = pyqtSignal(object)
    plan_error = pyqtSignal(str)

    def __init__(self, orchestrator: OrchestratorAgent, objective: str, parent=None):
        super().__init__(parent)
        self._orchestrator = orchestrator
        self._objective = objective

    def run(self):
        try:
            import asyncio

            plan = asyncio.run(self._orchestrator.process_objective(self._objective, context=None))
            self.plan_ready.emit(plan)
        except Exception as e:
            self.plan_error.emit(str(e))


class _ExecuteWorker(QThread):
    progress = pyqtSignal(str)
    finished_ok = pyqtSignal(dict)
    finished_error = pyqtSignal(str)

    def __init__(self, tasks: list, objective: str, parent=None):
        super().__init__(parent)
        self._tasks = tasks or []
        self._objective = objective or ""
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        try:
            ordered = self._toposort_tasks(self._tasks)
            if not ordered:
                self.finished_error.emit("No hay tareas para ejecutar")
                return

            results_by_task_id = {}
            previous_result = None

            for idx, task in enumerate(ordered, start=1):
                if self._stop_requested:
                    self.finished_error.emit("Ejecución cancelada")
                    return

                if not isinstance(task, dict):
                    continue

                task_id = str(task.get("task_id") or f"task_{idx:03d}")
                task_name = str(task.get("name") or task_id)
                required_skill = str(task.get("required_skill") or "").strip()

                if not required_skill:
                    self.finished_error.emit(f"La tarea '{task_name}' no tiene required_skill")
                    return

                self.progress.emit(f" Orquestador: Ejecutando {idx}/{len(ordered)} → {task_name} (skill: {required_skill})")

                context = {
                    "objective": self._objective,
                    "task_id": task_id,
                    "task_name": task_name,
                    "task": task.get("description") or task_name,
                    "input": previous_result,
                    "dependencies": task.get("dependencies") or [],
                    "results_by_task_id": results_by_task_id,
                }

                backend_ok, backend_payload = self._try_execute_backend(required_skill, context)
                if backend_ok:
                    result_payload = backend_payload
                else:
                    local_ok, local_payload = self._try_execute_local(required_skill, context)
                    if not local_ok:
                        err = str(local_payload)
                        self.finished_error.emit(f"Falló la skill '{required_skill}': {err}")
                        return
                    result_payload = local_payload

                results_by_task_id[task_id] = result_payload
                previous_result = result_payload

                self.progress.emit(f" Orquestador: ✅ Completada → {task_name}")

            self.finished_ok.emit({
                "success": True,
                "results_by_task_id": results_by_task_id,
                "final": previous_result,
            })

        except Exception as e:
            self.finished_error.emit(str(e))

    def _try_execute_backend(self, skill_name: str, context: dict):
        try:
            if not api_client.health_check():
                return False, "Backend no disponible"

            resp = api_client.execute_skill(skill_name, context)
            if isinstance(resp, dict) and resp.get("success"):
                return True, resp.get("result")

            return False, (resp.get("error") if isinstance(resp, dict) else "Backend execution failed")
        except Exception as e:
            return False, str(e)

    def _try_execute_local(self, skill_name: str, context: dict):
        try:
            import asyncio

            manager = AgentLifecycleManager()
            resp = asyncio.run(manager.execute_skill(skill_name, context))
            if isinstance(resp, dict) and resp.get("success"):
                return True, resp.get("result")
            return False, (resp.get("error") if isinstance(resp, dict) else "Local execution failed")
        except Exception as e:
            return False, str(e)

    def _toposort_tasks(self, tasks: list):
        tasks_by_id = {}
        for i, t in enumerate(tasks):
            if isinstance(t, dict):
                tid = str(t.get("task_id") or f"task_{i:03d}")
                tasks_by_id[tid] = t

        indeg = {tid: 0 for tid in tasks_by_id}
        outgoing = {tid: [] for tid in tasks_by_id}

        for tid, t in tasks_by_id.items():
            deps = t.get("dependencies") or []
            for d in deps:
                d = str(d)
                if d in tasks_by_id:
                    indeg[tid] += 1
                    outgoing[d].append(tid)

        queue = [tid for tid, v in indeg.items() if v == 0]
        ordered_ids = []

        while queue:
            cur = queue.pop(0)
            ordered_ids.append(cur)
            for nxt in outgoing.get(cur, []):
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)

        if len(ordered_ids) != len(tasks_by_id):
            return [t for t in tasks if isinstance(t, dict)]

        return [tasks_by_id[tid] for tid in ordered_ids]


class ChatBubble(QFrame):
    """Burbuja de mensaje estilo moderno"""
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        
        if is_user:
            bg_color = "#6366f1"
            text_color = "white"
            border_radius = "18px 18px 4px 18px"
        else:
            bg_color = "rgba(15, 23, 42, 0.92)"
            text_color = "#e5e7eb"
            border_radius = "18px 18px 18px 4px"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: {border_radius};
                padding: 12px 16px;
                border: none;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(0)
        
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
                line-height: 1.5;
                background: transparent;
            }}
        """)
        layout.addWidget(self.label)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


from core.LLMManager import llm_manager, ProviderType


class OrchestratorView(QWidget):
    """
    Vista del Orquestador - Interfaz principal
    Chat para objetivos y visualización de planes
    """
    
    plan_created = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.orchestrator = OrchestratorAgent()
        self.current_plan = None
        self._last_missing_skills = []
        self._last_objective = ""
        from collections import deque
        self._history_lines = deque(maxlen=UiSettings.get().chat_history_limit)
        self._plan_started_at = None
        self._worker = None
        self._exec_worker = None
        self._mode = "planning"
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interfaz elegante del Orquestador"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        left_panel = self._create_chat_panel()
        layout.addWidget(left_panel, 1)
        
        right_panel = self._create_plan_panel()
        layout.addWidget(right_panel, 1)
        
    def _create_chat_panel(self) -> QWidget:
        """Crear panel de chat con selector de API"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("🐱 Orquestador")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Indicador de modo
        self.mode_label = QLabel("🟡 MODO: PLANNING")
        self.mode_label.setStyleSheet("""
            font-size: 12px; font-weight: bold; color: #f59e0b;
            background-color: rgba(245, 158, 11, 0.1);
            border-radius: 8px; padding: 4px 8px;
        """)
        header_layout.addWidget(self.mode_label)
        
        # Indicador de seguridad
        self.security_label = QLabel("🛡️ PROTEGIDO")
        self.security_label.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #10b981;
            background-color: rgba(16, 185, 129, 0.15);
            border-radius: 8px; padding: 4px 8px;
        """)
        self.security_label.setToolTip("OrchestratorAgent protegido por Guardian")
        header_layout.addWidget(self.security_label)
        
        # Botón aprobar plan
        self.approve_btn = QPushButton("✅ Aprobar Plan")
        self.approve_btn.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; border: none;
                border-radius: 8px; padding: 6px 12px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.approve_btn.setVisible(False)
        self.approve_btn.clicked.connect(self._approve_plan)
        header_layout.addWidget(self.approve_btn)
        
        header_layout.addSpacing(10)
        
        # Botón de Ayuda
        self.help_btn = QPushButton("❓ Ayuda")
        self.help_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; border: none;
                border-radius: 8px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.help_btn.clicked.connect(self._show_help_manual)
        header_layout.addWidget(self.help_btn)
        
        # Selector de API
        api_label = QLabel("Modelo:")
        api_label.setStyleSheet("font-size: 12px; color: #64748b;")
        header_layout.addWidget(api_label)
        
        self.api_selector = QComboBox()
        self.api_selector.addItems([
            "🦙 Ollama (Local)", "🔬 LM Studio (Local)", "🤖 Jan (Local)",
            "🤖 OpenAI GPT-4", "⚡ Groq LLaMA", "🧠 Anthropic Claude"
        ])
        self.api_selector.setMinimumWidth(180)
        header_layout.addWidget(self.api_selector)

        self.api_status_dot = QLabel("●")
        self.api_status_dot.setStyleSheet("color: #ef4444; font-size: 14px;")
        self.api_status_dot.setToolTip("Sin conexión")
        header_layout.addWidget(self.api_status_dot)

        layout.addLayout(header_layout)
        
        subtitle = QLabel("Describe tu objetivo y crearé un plan de ejecución")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.72); font-size: 12px;")
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # Conectar cambio de API
        self.api_selector.currentIndexChanged.connect(self._on_api_changed)
        
        # Historial de chat
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("El historial aparecerá aquí...")
        self.chat_history.setMinimumHeight(200)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(2, 6, 23, 0.45);
                border: 1px solid rgba(148, 163, 184, 0.16);
                border-radius: 16px; padding: 12px;
            }
        """)
        layout.addWidget(self.chat_history)
        
        # Input de objetivo
        input_label = QLabel("¿Qué necesitas hacer?")
        layout.addWidget(input_label)

        self.objective_input = QTextEdit()
        self.objective_input.setPlaceholderText("Ej: Genera un reporte de ventas mensual y envíalo por email...")
        self.objective_input.setMaximumHeight(80)
        self.objective_input.setStyleSheet("""
            QTextEdit {
                background-color: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(148, 163, 184, 0.18);
                border-radius: 16px; padding: 12px;
            }
            QTextEdit:focus { border: 1px solid rgba(99, 102, 241, 0.8); }
        """)
        layout.addWidget(self.objective_input)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.chat_btn = QPushButton("💬 Enviar")
        self.chat_btn.clicked.connect(self._chat_with_orchestrator)
        buttons_layout.addWidget(self.chat_btn)
        
        self.analyze_btn = QPushButton("📊 Analizar")
        self.analyze_btn.clicked.connect(self._analyze_objective)
        self.analyze_btn.setVisible(False)
        buttons_layout.addWidget(self.analyze_btn)
        
        self.execute_btn = QPushButton("▶️ Ejecutar")
        self.execute_btn.clicked.connect(self._execute_plan)
        self.execute_btn.setEnabled(False)
        buttons_layout.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton("⏹️ Cancelar")
        self.cancel_btn.clicked.connect(self._cancel_execution)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)

        self.create_skill_btn = QPushButton("🔧 Crear skill")
        self.create_skill_btn.clicked.connect(self._create_missing_skill)
        self.create_skill_btn.setEnabled(False)
        buttons_layout.addWidget(self.create_skill_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
        
    def _on_api_changed(self, index):
        """Cambiar API activa en LLMManager cuando se selecciona otra"""
        provider_text = self.api_selector.currentText()
        
        provider_map = {
            "Ollama": ProviderType.OLLAMA,
            "LM Studio": ProviderType.OLLAMA,
            "Jan": ProviderType.OLLAMA,
            "OpenAI": ProviderType.OPENAI,
            "Groq": ProviderType.GROQ,
            "Anthropic": ProviderType.GEMINI,
        }
        
        selected_provider = None
        for key, ptype in provider_map.items():
            if key in provider_text:
                selected_provider = ptype
                break
        
        if selected_provider:
            success = llm_manager.set_active_provider(selected_provider)
            if success:
                self._add_to_history(f"🤖 API cambiada a: {provider_text}")
            else:
                config = llm_manager.providers.get(selected_provider)
                if config and not config.is_local and not config.api_key:
                    self._add_to_history(f"⚠️ {provider_text} no tiene API key configurada. Ve a Configuración.")
        
        self._update_api_status()
        
    def _create_plan_panel(self) -> QWidget:
        """Crear panel visual del plan"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QLabel("📋 Plan de Ejecución")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        self.plan_metrics = QLabel("")
        self.plan_metrics.setWordWrap(True)
        self.plan_metrics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.plan_metrics.setStyleSheet("""
            QLabel {
                background-color: rgba(2, 6, 23, 0.35);
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 14px; padding: 10px 12px;
                color: rgba(226, 232, 240, 0.9); font-size: 12px;
            }
        """)
        layout.addWidget(self.plan_metrics)
        
        self.plan_area = QScrollArea()
        self.plan_area.setWidgetResizable(True)
        self.plan_area.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.plan_content = QLabel("No hay plan generado aún")
        self.plan_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.plan_content.setWordWrap(True)
        self.plan_content.setMinimumHeight(300)
        self.plan_content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        self.plan_area.setWidget(self.plan_content)
        layout.addWidget(self.plan_area)
        
        self.status_label = QLabel("Estado: Esperando objetivo")
        self.status_label.setStyleSheet("color: rgba(226, 232, 240, 0.72); font-style: italic;")
        layout.addWidget(self.status_label)
        
        return panel
        
    def _analyze_objective(self):
        """Analizar objetivo del usuario"""
        objective = self.objective_input.toPlainText().strip()
        if not objective:
            return

        self._last_objective = objective
        self._add_to_history(f"👤 Tú: {objective}")
        self._add_to_history("🤖 Orquestador: Analizando objetivo...")

        try:
            import time
            self._plan_started_at = time.time()
        except Exception:
            self._plan_started_at = None

        self.execute_btn.setEnabled(False)
        self.create_skill_btn.setEnabled(False)
        self.status_label.setText("Estado: Analizando...")

        if self._worker is not None and self._worker.isRunning():
            try:
                self._worker.terminate()
            except Exception:
                pass

        self._worker = _PlanWorker(self.orchestrator, objective, parent=self)
        self._worker.plan_ready.connect(self._on_plan_ready)
        self._worker.plan_error.connect(self._on_plan_error)
        self._worker.start()

    def _on_plan_error(self, error: str):
        self.status_label.setText("Estado: Error analizando")
        self._add_to_history(f"❌ Orquestador: Error generando plan: {error}")

    def _on_plan_ready(self, plan):
        self.current_plan = plan

        tasks = []
        try:
            tasks = list(getattr(plan, "tasks", []) or [])
        except Exception:
            tasks = []

        objective = getattr(plan, "objective", self._last_objective) or self._last_objective

        required_skills = []
        for t in tasks:
            if isinstance(t, dict):
                rs = t.get("required_skill")
                if rs:
                    required_skills.append(str(rs))

        required_skills = sorted(set(required_skills))
        missing = self._get_missing_skills(required_skills)
        self._last_missing_skills = missing

        total_duration = 0
        for t in tasks:
            if isinstance(t, dict):
                try:
                    total_duration += int(t.get("estimated_duration") or 0)
                except Exception:
                    pass

        planning_ms = None
        try:
            import time
            if self._plan_started_at:
                planning_ms = int((time.time() - self._plan_started_at) * 1000)
        except Exception:
            planning_ms = None

        metrics_parts = []
        metrics_parts.append(f"<b>Tareas</b>: {len(tasks)}")
        metrics_parts.append(f"<b>Skills</b>: {len(required_skills)}")
        metrics_parts.append(f"<b>Duración estimada</b>: {total_duration}s")
        if planning_ms is not None:
            metrics_parts.append(f"<b>Planificado en</b>: {planning_ms}ms")
        if missing:
            metrics_parts.append(f"<b>Faltan</b>: {len(missing)}")
        self.plan_metrics.setText(" · ".join(metrics_parts))

        parts = [f"<b>🎯 Plan para:</b> {objective}<br><br>"]
        parts.append("<b>📋 Tareas identificadas:</b><br>")
        if tasks:
            for i, t in enumerate(tasks, start=1):
                name = t.get("name", f"Tarea {i}") if isinstance(t, dict) else f"Tarea {i}"
                desc = t.get("description", "") if isinstance(t, dict) else ""
                rs = t.get("required_skill", "") if isinstance(t, dict) else ""
                dur = t.get("estimated_duration", "?") if isinstance(t, dict) else "?"
                parts.append(f"{i}️⃣ <b>{name}</b><br>")
                if desc:
                    parts.append(f"   ├─ {desc}<br>")
                if rs:
                    parts.append(f"   ├─ Skill: <code>{rs}</code><br>")
                parts.append(f"   └─ Duración: {dur}s<br><br>")
        else:
            parts.append("No se pudieron generar tareas.<br>")

        parts.append(f"<br><b>🔧 Skills requeridos:</b> {len(required_skills)}<br>")
        if required_skills:
            parts.append("<b>Lista:</b> " + ", ".join(required_skills) + "<br>")

        self.plan_content.setText("".join(parts))

        if missing:
            self.status_label.setText("Estado: ❌ Faltan skills")
            self.execute_btn.setEnabled(False)
            self.create_skill_btn.setEnabled(True)
            self.create_skill_btn.setText(f"🔧 Crear skill ({len(missing)})")
            self._add_to_history(f"⚠️ Orquestador: Faltan skills: {', '.join(missing)}")
        else:
            self.status_label.setText("Estado: ✅ Listo para ejecutar")
            self.execute_btn.setEnabled(True)
            self.create_skill_btn.setEnabled(False)
            self.create_skill_btn.setText("🔧 Crear skill")

        self._add_to_history("✅ Orquestador: Plan generado correctamente")

    def on_activated(self):
        """Hook de activación de vista (llamado por MainWindow al navegar)."""
        try:
            if not self.current_plan:
                return

            tasks = list(getattr(self.current_plan, "tasks", []) or [])
            required_skills = []
            for t in tasks:
                if isinstance(t, dict):
                    rs = t.get("required_skill")
                    if rs:
                        required_skills.append(str(rs))
            required_skills = sorted(set(required_skills))

            missing = self._get_missing_skills(required_skills)
            self._last_missing_skills = list(missing)

            if missing:
                self.status_label.setText("Estado: ❌ Faltan skills")
                self.execute_btn.setEnabled(False)
                self.create_skill_btn.setEnabled(True)
                self.create_skill_btn.setText(f"🔧 Crear skill ({len(missing)})")
            else:
                self.status_label.setText("Estado: ✅ Listo para ejecutar")
                self.execute_btn.setEnabled(True)
                self.create_skill_btn.setEnabled(False)
                self.create_skill_btn.setText("🔧 Crear skill")
        except Exception:
            pass

    def _get_available_skills_catalog(self):
        """Obtener catálogo de skills disponibles."""
        try:
            if api_client.health_check():
                skills = api_client.get_skills() or []
                names = []
                for s in skills:
                    if isinstance(s, dict):
                        n = s.get("id") or s.get("name")
                        if n:
                            names.append(str(n))
                    elif isinstance(s, str):
                        names.append(s)
                return set(names)
        except Exception:
            pass

        try:
            from pathlib import Path
            root = Path(__file__).parent.parent.parent.parent
            data_dir = root / "data"
            names = []
            for folder in [data_dir / "skills", data_dir / "skills_user"]:
                if folder.exists():
                    for f in folder.glob("*.py"):
                        if not f.name.startswith("_"):
                            names.append(f.stem)
            return set(names)
        except Exception:
            return set()

    def _get_missing_skills(self, required_skills):
        catalog = self._get_available_skills_catalog()
        missing = []
        for s in required_skills or []:
            if s and s not in catalog:
                missing.append(s)
        return missing

    def _create_missing_skill(self):
        """Navegar a Skills para crear skill faltante."""
        if not self._last_missing_skills:
            return

        skill_name = self._last_missing_skills.pop(0)
        objective = self._last_objective

        prompt = (
            f"Necesito crear una skill llamada: {skill_name}\n"
            f"Objetivo del usuario: {objective}\n\n"
            "Requisitos:\n"
            "- Implementar execute(context)\n"
            "- Devolver un dict con success/result\n"
            "- Manejo de errores profesional\n\n"
            "Genera el código y explícame cómo probarla en Sandbox."
        )

        try:
            main_window = self.window()
            if hasattr(main_window, "navigate_to"):
                main_window.navigate_to("skills")
            if hasattr(main_window, "get_view"):
                skills_view = main_window.get_view("skills")
                if hasattr(skills_view, "prefill_prompt"):
                    skills_view.prefill_prompt(prompt)
        except Exception:
            pass

        remaining = len(self._last_missing_skills)
        if remaining > 0:
            self.create_skill_btn.setEnabled(True)
            self.create_skill_btn.setText(f"🔧 Crear siguiente ({remaining})")
            self._add_to_history(f"⏭️ Orquestador: Siguiente skill: {self._last_missing_skills[0]}")
        else:
            self.create_skill_btn.setEnabled(False)
            self.create_skill_btn.setText("🔧 Crear skill")
        
    def _execute_plan(self):
        """Ejecutar el plan generado"""
        self.on_activated()
        if self._last_missing_skills:
            self._add_to_history(f"❌ Orquestador: No puedo ejecutar. Faltan: {', '.join(self._last_missing_skills)}")
            self.status_label.setText("Estado: ❌ Faltan skills")
            self.execute_btn.setEnabled(False)
            self.create_skill_btn.setEnabled(True)
            return

        if not self.current_plan:
            self._add_to_history("❌ Orquestador: No hay plan para ejecutar")
            return

        tasks = list(getattr(self.current_plan, "tasks", []) or [])
        objective = getattr(self.current_plan, "objective", self._last_objective) or self._last_objective
        if not tasks:
            self._add_to_history("❌ Orquestador: El plan no tiene tareas")
            return

        if self._exec_worker is not None and self._exec_worker.isRunning():
            self._add_to_history("⏳ Orquestador: Ya hay ejecución en curso")
            return

        self.status_label.setText("Estado: ⏳ Ejecutando...")
        self.execute_btn.setEnabled(False)
        self.create_skill_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._add_to_history("🚀 Orquestador: Ejecutando plan...")

        self._exec_worker = _ExecuteWorker(tasks=tasks, objective=objective, parent=self)
        self._exec_worker.progress.connect(self._add_to_history)
        self._exec_worker.finished_ok.connect(self._on_execute_ok)
        self._exec_worker.finished_error.connect(self._on_execute_error)
        self._exec_worker.start()

    def _provider_ready_status(self, provider_text: str):
        """Verificar estado usando LLMManager"""
        p = provider_text or ""
        is_cloud = ("OpenAI" in p) or ("Groq" in p) or ("Anthropic" in p)
        
        if not is_cloud:
            provider_map = {
                "Ollama": ProviderType.OLLAMA,
                "LM Studio": ProviderType.OLLAMA,
                "Jan": ProviderType.OLLAMA,
            }
            for key, ptype in provider_map.items():
                if key in p:
                    config = llm_manager.providers.get(ptype)
                    if config:
                        return True, "Local listo"
                    return False, "No configurado"
            return False, "Proveedor no reconocido"
        
        provider_map = {
            "OpenAI": ProviderType.OPENAI,
            "Groq": ProviderType.GROQ,
            "Anthropic": ProviderType.GEMINI,
        }
        
        for key, ptype in provider_map.items():
            if key in p:
                config = llm_manager.providers.get(ptype)
                if config and config.api_key:
                    return True, "API key configurada"
                return False, f"Falta API key para {key}"
        
        return False, "Proveedor no configurado"

    def _update_api_status(self):
        try:
            provider = self.api_selector.currentText()
            ok, msg = self._provider_ready_status(provider)
            if ok:
                self.api_status_dot.setStyleSheet("color: #22c55e; font-size: 14px;")
                self.api_status_dot.setToolTip(f"🟢 {msg}")
            else:
                self.api_status_dot.setStyleSheet("color: #ef4444; font-size: 14px;")
                self.api_status_dot.setToolTip(f"🔴 {msg}")
                self._add_to_history(f"⚠️ Orquestador: {msg} para '{provider}'")
        except Exception:
            pass

    def _cancel_execution(self):
        """Cancelar ejecución en curso."""
        if self._exec_worker is not None and self._exec_worker.isRunning():
            try:
                self._exec_worker.request_stop()
            except Exception:
                pass
            self.status_label.setText("Estado: ⏹️ Cancelando...")
            self._add_to_history("⏹️ Orquestador: Cancelando ejecución...")
            self.cancel_btn.setEnabled(False)

    def _on_execute_ok(self, payload: dict):
        self.status_label.setText("Estado: ✅ Completado")
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._add_to_history("✅ Orquestador: Plan completado exitosamente")
        
        self.security_label.setText("🛡️ PROTEGIDO")
        self.security_label.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #10b981;
            background-color: rgba(16, 185, 129, 0.15);
            border-radius: 8px; padding: 4px 8px;
        """)

    def _on_execute_error(self, error: str):
        self.status_label.setText("Estado: ❌ Error")
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if "sin saldo" in error.lower() or "cuota" in error.lower() or "quota" in error.lower() or "billing" in error.lower():
            self._add_to_history(f"💳 Orquestador: Error de saldo/cuota")
            self._add_to_history(f"❌ {error}")
        else:
            self._add_to_history(f"❌ Orquestador: Error ejecutando plan: {error}")
        
        self.security_label.setText("⚠️ ERROR")
        self.security_label.setStyleSheet("""
            font-size: 11px; font-weight: bold; color: #ef4444;
            background-color: rgba(239, 68, 68, 0.15);
            border-radius: 8px; padding: 4px 8px;
        """)
        
    def _add_to_history(self, message: str):
        """Añadir mensaje al historial"""
        try:
            self._history_lines.append(message)
            self.chat_history.setHtml("<br>".join(self._history_lines))
        except Exception:
            current = self.chat_history.toHtml()
            self.chat_history.setHtml(f"{current}<br>{message}")
        
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_ui_settings(self, data):
        try:
            from collections import deque
            limit = int(getattr(data, "chat_history_limit", 20) or 20)
            if limit < 5:
                limit = 5
            if limit > 200:
                limit = 200

            if getattr(self._history_lines, "maxlen", None) == limit:
                return

            self._history_lines = deque(list(self._history_lines)[-limit:], maxlen=limit)
            try:
                self.chat_history.setHtml("<br>".join(self._history_lines))
            except Exception:
                pass
        except Exception:
            pass
            
    def _chat_with_orchestrator(self):
        """Chat en modo planning - conversación para entender el objetivo"""
        user_input = self.objective_input.toPlainText().strip()
        if not user_input:
            return
        
        self._last_objective = user_input
        self._add_to_history(f"👤 Tú: {user_input}")
        self.objective_input.clear()
        
        self._add_to_history("🛡️ Guardian: Validando input de seguridad...")
        
        import asyncio
        try:
            # Para PyQt5 con event loop ya corriendo, usamos create_task y callback
            loop = asyncio.get_event_loop()
            
            # Función para manejar el resultado asíncrono
            def handle_response(task):
                try:
                    response = task.result()
                    self._handle_planning_response(response)
                except Exception as e:
                    self._add_to_history(f"❌ Orquestador: Error en conversación: {str(e)}")
            
            # Crear task y conectar callback
            task = loop.create_task(self.orchestrator.chat_in_planning_mode(user_input))
            task.add_done_callback(handle_response)
            
        except Exception as e:
            self._add_to_history(f"❌ Orquestador: Error en conversación: {str(e)}")
    
    def _handle_planning_response(self, response):
        """Procesar respuesta del modo planning"""
        try:
            if response.type == "error":
                self._add_to_history(f"🛡️ Guardian: {response.message}")
                if response.suggestions:
                    suggestions_text = "\n".join([f"💡 {s}" for s in response.suggestions])
                    self._add_to_history(f"Sugerencias:\n{suggestions_text}")
                self.status_label.setText("Estado: ⚠️ Validación fallida")
                
            elif response.type == "question":
                questions_text = "\n".join([f"• {q}" for q in response.questions])
                self._add_to_history(f"🤖 Orquestador: {response.message}\n{questions_text}")
                self.status_label.setText("Estado: ❓ Necesito más información")
                
            elif response.type == "plan_ready":
                self.current_plan = response.plan
                self._add_to_history(f"✅ Guardian: Plan validado y auditado")
                self._add_to_history(f"🤖 Orquestador: {response.message}")
                self.status_label.setText("Estado: 🛡️ Plan protegido - Listo para aprobar")
                self.approve_btn.setVisible(True)
                
                self.security_label.setText("🛡️ MONITOREANDO")
                self.security_label.setStyleSheet("""
                    font-size: 11px; font-weight: bold; color: #6366f1;
                    background-color: rgba(99, 102, 241, 0.15);
                    border-radius: 8px; padding: 4px 8px;
                """)
                
                self._display_plan(response.plan)
                
            elif response.type == "suggestion":
                self._add_to_history(f"🤖 Orquestador: {response.message}")
                self.status_label.setText("Estado: 💡 Necesito más detalles")
        except Exception as e:
            self._add_to_history(f"❌ Orquestador: Error procesando respuesta: {str(e)}")
    
    def _display_plan(self, plan):
        """Mostrar plan en el panel derecho"""
        objective = getattr(plan, "objective", "Sin objetivo")
        tasks = getattr(plan, "tasks", [])
        
        parts = [f"<b>🎯 Plan para:</b> {objective}<br><br>"]
        parts.append("<b>📋 Pasos detallados:</b><br><br>")
        
        if tasks:
            for i, task in enumerate(tasks, start=1):
                if isinstance(task, dict):
                    name = task.get('user_friendly_name', task.get('name', f'Paso {i}'))
                    desc = task.get('description', '')
                    skill = task.get('required_skill', '')
                    outcome = task.get('expected_outcome', '')
                    
                    parts.append(f"<b>{i}. {name}</b><br>")
                    if desc:
                        parts.append(f"   📝 {desc}<br>")
                    if skill:
                        parts.append(f"   🤖 Skill: <code>{skill}</code><br>")
                    if outcome:
                        parts.append(f"   ✅ Resultado: {outcome}<br>")
                    parts.append("<br>")
        
        parts.append("<br><b>💡 El plan está listo para ejecutarse una vez aprobado.</b>")
        self.plan_content.setText("".join(parts))
        
        total_tasks = len(tasks)
        total_duration = sum(t.get('estimated_duration', 0) for t in tasks if isinstance(t, dict))
        self.plan_metrics.setText(f"<b>Tareas:</b> {total_tasks} · <b>Duración estimada:</b> {total_duration}s")
    
    def _approve_plan(self):
        """Aprobar plan y pasar a modo ejecución"""
        if not self.current_plan:
            return
        
        plan_id = getattr(self.current_plan, "plan_id", None)
        if not plan_id:
            return
        
        self._add_to_history("🛡️ Guardian: Activando monitoreo de seguridad...")
        self._add_to_history("🛡️ Guardian: Checkpoint creado para rollback")
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            
            def handle_approval(task):
                try:
                    success = task.result()
                    if success:
                        self._mode = "execution"
                        self.mode_label.setText("🟢 MODO: EJECUCIÓN")
                        self.mode_label.setStyleSheet("""
                            font-size: 12px; font-weight: bold; color: #10b981;
                            background-color: rgba(16, 185, 129, 0.1);
                            border-radius: 8px; padding: 4px 8px;
                        """)
                        
                        self.security_label.setText("🛡️ EJECUTANDO")
                        self.security_label.setStyleSheet("""
                            font-size: 11px; font-weight: bold; color: #f59e0b;
                            background-color: rgba(245, 158, 11, 0.15);
                            border-radius: 8px; padding: 4px 8px;
                        """)
                        
                        self.approve_btn.setVisible(False)
                        self.analyze_btn.setVisible(True)
                        self.chat_btn.setVisible(False)
                        self._add_to_history("✅ Orquestador: Plan aprobado. Modo EJECUCIÓN activado.")
                        self._add_to_history("🛡️ Guardian: Monitoreo activo - Plan protegido")
                        self._add_to_history("🤖 Orquestador: Presiona 'Ejecutar' para comenzar.")
                        self.status_label.setText("Estado: 🛡️ Plan aprobado - Listo para ejecutar")
                        self.execute_btn.setEnabled(True)
                    else:
                        self._add_to_history("❌ Orquestador: No se pudo aprobar el plan")
                        self.security_label.setText("⚠️ ERROR")
                except Exception as e:
                    self._add_to_history(f"❌ Orquestador: Error aprobando plan: {str(e)}")
                    self.security_label.setText("⚠️ ERROR")
            
            task = loop.create_task(self.orchestrator.approve_plan(plan_id))
            task.add_done_callback(handle_approval)
            
        except Exception as e:
            self._add_to_history(f"❌ Orquestador: Error aprobando plan: {str(e)}")
            self.security_label.setText("⚠️ ERROR")
            
    def _show_help_manual(self):
        """Mostrar manual de ayuda del Orquestador"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📖 Manual del Orquestador - MININA v3.0")
        dialog.setFixedSize(800, 500)
        dialog.setStyleSheet("QDialog { background-color: #f8fafc; }")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("📖 Manual del Orquestador")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #6366f1; background: transparent;")
        layout.addWidget(title)
        
        help_text = """<h3>🐱 ¿Qué es el Orquestador?</h3>
        <p>El Orquestador es el <b>cerebro de MININA</b>. Tiene <b>dos modos</b>:</p>
        <h3>🟡 MODO PLANNING (Asistente)</h3>
        <p>NO ejecuta nada. Solo conversa para:</p>
        <ul>
        <li>Entender qué quieres hacer</li>
        <li>Hacer preguntas si es ambiguo</li>
        <li>Proponer un plan detallado</li>
        </ul>
        <h3>🟢 MODO EJECUCIÓN (Acción)</h3>
        <p>Ejecuta el plan aprobado paso a paso.</p>
        <h3>💬 Cómo usar</h3>
        <ol>
        <li>Escribe tu objetivo y presiona "💬 Enviar"</li>
        <li>Responde las preguntas del Orquestador</li>
        <li>Cuando veas el plan, presiona "✅ Aprobar Plan"</li>
        <li>Presiona "▶️ Ejecutar" para correr el plan</li>
        </ol>"""
        
        text_edit = QTextEdit()
        text_edit.setHtml(help_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit { background-color: #ffffff; border: 2px solid #e2e8f0;
                border-radius: 10px; padding: 15px; color: #1f293b; font-size: 13px; }
        """)
        layout.addWidget(text_edit)
        
        close_btn = QPushButton("✓ Entendido")
        close_btn.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: white; border: none;
                border-radius: 8px; padding: 10px 24px; font-weight: bold; font-size: 14px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec_()
