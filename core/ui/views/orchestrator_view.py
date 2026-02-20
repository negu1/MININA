"""
MININA v3.0 - Orchestrator View (Capa 1) - DISEÑO ELEGANTE
Chat inteligente estilo moderno con burbujas y tema oscuro/claro
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QComboBox
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
            # ciclo o deps faltantes: fallback a orden original
            return [t for t in tasks if isinstance(t, dict)]

        return [tasks_by_id[tid] for tid in ordered_ids]


class ChatBubble(QFrame):
    """Burbuja de mensaje estilo moderno"""
    def __init__(self, text, is_user=False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        
        # Colores del tema
        if is_user:
            bg_color = "#6366f1"  # Indigo
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
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(0)
        
        # Label del mensaje
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
        
        # Sombra sutil
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


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
        self._setup_ui()

        UiSettings.subscribe(self._on_ui_settings)
        
    def _setup_ui(self):
        """Configurar interfaz elegante del Orquestador"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Panel izquierdo: Chat moderno
        left_panel = self._create_chat_panel()
        layout.addWidget(left_panel, 1)
        
        # Panel derecho: Plan visual
        right_panel = self._create_plan_panel()
        layout.addWidget(right_panel, 1)
        
    def _create_chat_panel(self) -> QWidget:
        """Crear panel de chat con selector de API"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header con selector de API
        header_layout = QHBoxLayout()
        
        header = QLabel("🐱 Orquestador")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Selector de API
        api_label = QLabel("Modelo:")
        api_label.setStyleSheet("font-size: 12px; color: #64748b;")
        header_layout.addWidget(api_label)
        
        self.api_selector = QComboBox()
        self.api_selector.addItems([
            "🦙 Ollama (Local)",
            "🔬 LM Studio (Local)", 
            "🤖 Jan (Local)",
            "🤖 OpenAI GPT-4",
            "⚡ Groq LLaMA",
            "🧠 Anthropic Claude"
        ])
        self.api_selector.setMinimumWidth(180)
        header_layout.addWidget(self.api_selector)

        self.api_status_dot = QLabel("●")
        self.api_status_dot.setStyleSheet("color: #ef4444; font-size: 14px;")
        self.api_status_dot.setToolTip("Sin conexión")
        header_layout.addWidget(self.api_status_dot)

        self.api_selector.currentIndexChanged.connect(self._update_api_status)
        
        layout.addLayout(header_layout)
        
        subtitle = QLabel("Describe tu objetivo y crearé un plan de ejecución")
        subtitle.setStyleSheet("color: rgba(226, 232, 240, 0.72); font-size: 12px;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)

        self._update_api_status()
        
        # Historial de chat
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("El historial aparecerá aquí...")
        self.chat_history.setMinimumHeight(200)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background-color: rgba(2, 6, 23, 0.45);
                border: 1px solid rgba(148, 163, 184, 0.16);
                border-radius: 16px;
                padding: 12px;
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
                border-radius: 16px;
                padding: 12px;
            }
            QTextEdit:focus {
                border: 1px solid rgba(99, 102, 241, 0.8);
            }
        """)
        layout.addWidget(self.objective_input)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton(" Analizar")
        self.analyze_btn.clicked.connect(self._analyze_objective)
        buttons_layout.addWidget(self.analyze_btn)
        
        self.execute_btn = QPushButton(" Ejecutar")
        self.execute_btn.clicked.connect(self._execute_plan)
        self.execute_btn.setEnabled(False)
        buttons_layout.addWidget(self.execute_btn)

        self.cancel_btn = QPushButton(" Cancelar")
        self.cancel_btn.clicked.connect(self._cancel_execution)
        self.cancel_btn.setEnabled(False)
        buttons_layout.addWidget(self.cancel_btn)

        self.create_skill_btn = QPushButton(" Crear skill")
        self.create_skill_btn.clicked.connect(self._create_missing_skill)
        self.create_skill_btn.setEnabled(False)
        buttons_layout.addWidget(self.create_skill_btn)
        
        layout.addLayout(buttons_layout)
        
        return panel
        
    def _create_plan_panel(self) -> QWidget:
        """Crear panel visual del plan"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QLabel(" Plan de Ejecución")
        header.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(header)

        self.plan_metrics = QLabel("")
        self.plan_metrics.setWordWrap(True)
        self.plan_metrics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.plan_metrics.setStyleSheet("""
            QLabel {
                background-color: rgba(2, 6, 23, 0.35);
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 14px;
                padding: 10px 12px;
                color: rgba(226, 232, 240, 0.9);
                font-size: 12px;
            }
        """)
        layout.addWidget(self.plan_metrics)
        
        # Área del plan
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
        
        # Estado
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
            
        # Añadir al historial
        self._add_to_history(f" Tú: {objective}")
        
        # Simular análisis
        self._add_to_history(" Orquestador: Analizando objetivo...")

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
        self._add_to_history(f" Orquestador: Error generando plan: {error}")

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

        parts = [f"<b>Plan para:</b> {objective}<br><br>"]
        parts.append("<b>Tareas identificadas:</b><br>")
        if tasks:
            for i, t in enumerate(tasks, start=1):
                name = t.get("name", f"Tarea {i}") if isinstance(t, dict) else f"Tarea {i}"
                desc = t.get("description", "") if isinstance(t, dict) else ""
                rs = t.get("required_skill", "") if isinstance(t, dict) else ""
                dur = t.get("estimated_duration", "?") if isinstance(t, dict) else "?"
                parts.append(f"{i}️⃣ <b>{name}</b><br>")
                if desc:
                    parts.append(f" └─ {desc}<br>")
                if rs:
                    parts.append(f" └─ Skill: {rs}<br>")
                parts.append(f" └─ Duración estimada: {dur}s<br><br>")
        else:
            parts.append("No se pudieron generar tareas.<br>")

        parts.append(f"<b>Skills requeridos:</b> {len(required_skills)}<br>")
        if required_skills:
            parts.append("<b>Lista:</b> " + ", ".join(required_skills) + "<br>")

        self.plan_content.setText("".join(parts))

        if missing:
            self.status_label.setText("Estado: Faltan skills - Requiere intervención")
            self.execute_btn.setEnabled(False)
            self.create_skill_btn.setEnabled(True)
            self.create_skill_btn.setText(" Crear skill")
            self._add_to_history(" Orquestador: No tengo skills instaladas para: " + ", ".join(missing))
        else:
            self.status_label.setText("Estado: Plan generado - Listo para ejecutar")
            self.execute_btn.setEnabled(True)
            self.create_skill_btn.setEnabled(False)
            self.create_skill_btn.setText(" Crear skill")

        self._add_to_history(" Orquestador: Plan generado")

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
                self.status_label.setText("Estado: Faltan skills - Requiere intervención")
                self.execute_btn.setEnabled(False)
                self.create_skill_btn.setEnabled(True)
                self.create_skill_btn.setText(" Crear skill")
            else:
                self.status_label.setText("Estado: Plan generado - Listo para ejecutar")
                self.execute_btn.setEnabled(True)
                self.create_skill_btn.setEnabled(False)
                self.create_skill_btn.setText(" Crear skill")
        except Exception:
            pass

    def _get_available_skills_catalog(self):
        """Obtener catálogo de skills disponibles (backend -> fallback local)."""
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
        """Atajo UX: navegar a Skills y prellenar prompt para crear skill faltante."""
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
            self.create_skill_btn.setText(f" Crear siguiente ({remaining})")
            self._add_to_history(f" Orquestador: Siguiente skill pendiente: {self._last_missing_skills[0]}")
        else:
            self.create_skill_btn.setEnabled(False)
            self.create_skill_btn.setText(" Crear skill")
        
    def _execute_plan(self):
        """Ejecutar el plan generado"""
        self.on_activated()
        if self._last_missing_skills:
            self._add_to_history(" Orquestador: No puedo ejecutar. Faltan skills: " + ", ".join(self._last_missing_skills))
            self.status_label.setText("Estado: Faltan skills")
            self.execute_btn.setEnabled(False)
            self.create_skill_btn.setEnabled(True)
            return

        if not self.current_plan:
            self._add_to_history(" Orquestador: No hay plan para ejecutar")
            return

        tasks = list(getattr(self.current_plan, "tasks", []) or [])
        objective = getattr(self.current_plan, "objective", self._last_objective) or self._last_objective
        if not tasks:
            self._add_to_history(" Orquestador: El plan no tiene tareas")
            return

        if self._exec_worker is not None and self._exec_worker.isRunning():
            self._add_to_history(" Orquestador: Ya hay una ejecución en curso")
            return

        self.status_label.setText("Estado: Ejecutando...")
        self.execute_btn.setEnabled(False)
        self.create_skill_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._add_to_history(" Orquestador: Ejecutando plan...")

        self._exec_worker = _ExecuteWorker(tasks=tasks, objective=objective, parent=self)
        self._exec_worker.progress.connect(self._add_to_history)
        self._exec_worker.finished_ok.connect(self._on_execute_ok)
        self._exec_worker.finished_error.connect(self._on_execute_error)
        self._exec_worker.start()

    def _provider_ready_status(self, provider_text: str):
        p = provider_text or ""
        is_cloud = ("OpenAI" in p) or ("Groq" in p) or ("Anthropic" in p)

        if not is_cloud:
            if api_client.health_check():
                return True, "Conectado"
            return False, "Sin conexión al servidor local"

        if "OpenAI" in p:
            ok = bool(os.environ.get("OPENAI_API_KEY"))
            return ok, ("OK" if ok else "Falta OPENAI_API_KEY")
        if "Groq" in p:
            ok = bool(os.environ.get("GROQ_API_KEY"))
            return ok, ("OK" if ok else "Falta GROQ_API_KEY")
        if "Anthropic" in p:
            ok = bool(os.environ.get("ANTHROPIC_API_KEY"))
            return ok, ("OK" if ok else "Falta ANTHROPIC_API_KEY")

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
                self._add_to_history(f" Orquestador: ⚠️ {msg} para '{provider}'")
        except Exception:
            pass

    def _cancel_execution(self):
        """Cancelar ejecución en curso."""
        if self._exec_worker is not None and self._exec_worker.isRunning():
            try:
                self._exec_worker.request_stop()
            except Exception:
                pass
            self.status_label.setText("Estado: Cancelando...")
            self._add_to_history(" Orquestador: Cancelando ejecución...")
            self.cancel_btn.setEnabled(False)

    def _on_execute_ok(self, payload: dict):
        self.status_label.setText("Estado: Completado")
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self._add_to_history(" Orquestador: ✅ Plan completado")

    def _on_execute_error(self, error: str):
        self.status_label.setText("Estado: Error")
        self.execute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        # Detectar si es error de cuota/saldo
        if "sin saldo" in error.lower() or "cuota" in error.lower() or "quota" in error.lower() or "billing" in error.lower():
            self._add_to_history(f" Orquestador: 🔴 Error de saldo/cuota")
            self._add_to_history(f" Orquestador: {error}")
        else:
            self._add_to_history(f" Orquestador: ❌ Error ejecutando plan: {error}")
        
    def _add_to_history(self, message: str):
        """Añadir mensaje al historial"""
        try:
            self._history_lines.append(message)
            self.chat_history.setHtml("<br>".join(self._history_lines))
        except Exception:
            current = self.chat_history.toHtml()
            self.chat_history.setHtml(f"{current}<br>{message}")
        
        # Auto-scroll al final
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
