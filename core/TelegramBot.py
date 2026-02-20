import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

from core.CortexBus import bus
from core.AgentLifecycleManager import agent_manager
from core.CommandEngine.engine import CommandEngine
from core.UserObservabilityStore import store
from core.UserFeedbackManager import feedback_manager
from core.SkillVault import vault

logger = logging.getLogger("TelegramBot")


def _parse_allowed_chat_ids() -> Optional[set[int]]:
    raw = (os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or "").strip()
    raw_multi = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or "").strip()
    if not raw and not raw_multi:
        return None

    ids: set[int] = set()
    parts = []
    if raw:
        parts.append(raw)
    if raw_multi:
        parts.extend([p.strip() for p in raw_multi.split(",") if p.strip()])

    for p in parts:
        try:
            ids.add(int(p))
        except Exception:
            pass

    return ids or None


@dataclass
class RetryInfo:
    chat_id: int
    skill: str


class TelegramBotService:
    def __init__(self, token: str):
        self.token = token
        self.app: Optional[Application] = None
        self._ce = CommandEngine()
        self._chat_ids: set[int] = set()
        self._retry_sessions: Dict[str, RetryInfo] = {}
        self._allowed_chat_ids: Optional[set[int]] = _parse_allowed_chat_ids()
        self._pc_cwd: Dict[int, str] = {}
        self._pc_last_entries: Dict[int, list[dict[str, Any]]] = {}
        self._pc_page_offset: Dict[int, int] = {}
        self._pc_waiting_search: Dict[int, bool] = {}
        self._pc_search_query: Dict[int, str] = {}

        self._auto_refresh_enabled: Dict[int, bool] = {}
        self._auto_refresh_tasks: Dict[int, asyncio.Task] = {}
        self._auto_refresh_last_ts: Dict[int, float] = {}

        self._admin_enabled: Dict[int, bool] = {}
        self._vault_waiting_zip: Dict[int, bool] = {}
        self._vault_staged_zip: Dict[int, str] = {}

        self._builder_state: Dict[int, Dict[str, Any]] = {}
        
        # Nuevos diccionarios para sistema de credenciales
        self._credential_requests: Dict[str, Dict[str, Any]] = {}  # Solicitudes de credenciales pendientes
        self._pending_credentials: Dict[str, str] = {}  # Session IDs de credenciales almacenadas
        self._credential_user_ids: Dict[int, str] = {}  # Mapeo de chat_id a user_id para notificaciones

        self._myskills_offset: Dict[int, int] = {}

        bus.subscribe("user.SPEAK", self._on_user_speak)
        bus.subscribe("user.UI_MESSAGE", self._on_user_ui_message)
        bus.subscribe("skill.RETRY_AVAILABLE", self._on_retry_available)
        bus.subscribe("user.CREDENTIAL_EVENT", self._on_credential_event)

    async def start(self) -> None:
        if self.app is not None:
            return

        self.app = Application.builder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("skills", self._cmd_skills))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("admin", self._cmd_admin))
        self.app.add_handler(CommandHandler("vault", self._cmd_vault))
        self.app.add_handler(CommandHandler("builder", self._cmd_builder))
        self.app.add_handler(CallbackQueryHandler(self._on_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self._on_document))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

        logger.info("Telegram bot started")

    async def stop(self) -> None:
        if self.app is None:
            return
        try:
            await self.app.updater.stop()
        except Exception:
            pass
        try:
            await self.app.stop()
        except Exception:
            pass
        try:
            await self.app.shutdown()
        except Exception:
            pass
        self.app = None

    async def _on_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.effective_chat:
            return
        chat_id = update.effective_chat.id
        if not self._is_allowed(chat_id):
            return

        await self._show_home_panel(chat_id, context)

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id

        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        self._chat_ids.add(chat_id)
        await self._show_home_panel(chat_id, context)

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Ejemplos:\n"
                "- usa skill clock\n"
                "- usa skill echo hola\n"
                "- usa skill web_browser example.com\n\n"
                "Tips:\n"
                "- Cuando una skill falle, verás botón de Reintentar."
            ),
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Baúl de Skills (usuario):\n"
                "- /admin <PIN> (habilita instalación por este chat)\n"
                "- /vault (subir y validar skills .zip)\n"
            ),
        )

    async def _cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        pin = ""
        try:
            if context.args:
                pin = str(context.args[0]).strip()
        except Exception:
            pin = ""

        expected = (os.environ.get("MIIA_ADMIN_PIN") or "").strip()
        if not expected:
            await context.bot.send_message(chat_id=chat_id, text="Admin PIN no configurado (MIIA_ADMIN_PIN).")
            return
        if pin != expected:
            await context.bot.send_message(chat_id=chat_id, text="PIN incorrecto.")
            return

        self._admin_enabled[chat_id] = True
        await context.bot.send_message(chat_id=chat_id, text="✅ Admin habilitado en este chat. Ya puedes usar /vault para subir skills.")

    async def _cmd_vault(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not self._admin_enabled.get(chat_id):
            await context.bot.send_message(chat_id=chat_id, text="🔒 Para subir skills, primero ejecuta: /admin <PIN>")
            return

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📦 Subir skill (.zip)", callback_data="vault:upload")],
            ]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "Baúl de Skills (modo público):\n"
                "- Formato: .zip con manifest.json + skill.py\n"
                "- Primero va a Baúl de prueba (staging)\n"
                "- Luego pasa por Simulador de seguridad\n"
                "- Si pasa: se instala y queda disponible en /skills\n"
            ),
            reply_markup=kb,
        )

    async def _cmd_builder(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        await self._show_builder_menu(chat_id, context)

    async def _show_builder_menu(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📄 Crear Skill PDF", callback_data="builder:create_pdf")],
                [InlineKeyboardButton("❌ Cerrar", callback_data="builder:cancel")],
            ]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "🧰 Creador de Skills\n\n"
                "Te voy guiando paso a paso. Solo escribirás texto cuando sea necesario (por ejemplo el contenido del PDF)."
            ),
            reply_markup=kb,
        )

    async def _show_vault_menu(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not self._admin_enabled.get(chat_id):
            await context.bot.send_message(chat_id=chat_id, text="🔒 Para subir skills, primero ejecuta: /admin <PIN>")
            return

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📦 Subir skill (.zip)", callback_data="vault:upload")],
            ]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "📦 Baúl de Skills\n\n"
                "- Formato recomendado: .zip con skill.yaml (usuario común)\n"
                "- También soporta skill avanzada (Python) con simulador\n"
                "- Primero va a Baúl de prueba y luego se valida\n"
            ),
            reply_markup=kb,
        )

    async def _on_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not self._admin_enabled.get(chat_id):
            return

        if not self._vault_waiting_zip.get(chat_id):
            return

        doc = update.message.document
        if not doc or not doc.file_name:
            await context.bot.send_message(chat_id=chat_id, text="Archivo inválido.")
            return

        try:
            max_zip_mb = int(os.environ.get("MIIA_SKILL_ZIP_MAX_MB", "15") or "15")
        except Exception:
            max_zip_mb = 15

        try:
            if doc.file_size and int(doc.file_size) > max_zip_mb * 1024 * 1024:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"ZIP demasiado grande. Máximo permitido: {max_zip_mb}MB.",
                )
                self._vault_waiting_zip[chat_id] = False
                return
        except Exception:
            pass

        if not doc.file_name.lower().endswith(".zip"):
            await context.bot.send_message(chat_id=chat_id, text="Debe ser un .zip con manifest.json y skill.py")
            return

        self._vault_waiting_zip[chat_id] = False

        tmp_dir = Path(os.environ.get("MIIA_SKILL_UPLOAD_TMP", str(Path(os.getenv("TEMP", ".")) / "miia_uploads")))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        local_path = tmp_dir / f"{int(time.time())}_{doc.file_name}"

        try:
            f = await doc.get_file()
            await f.download_to_drive(custom_path=str(local_path))
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"No se pudo descargar el zip: {e}")
            return

        item = vault.stage_zip(local_path, chat_id=chat_id)
        self._vault_staged_zip[chat_id] = str(item.zip_path)

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🧪 Iniciar prueba de simulador", callback_data="vault:simulate")],
                [
                    InlineKeyboardButton("🗑️ Eliminar", callback_data="vault:delete"),
                    InlineKeyboardButton("🔒 Cuarentena", callback_data="vault:quarantine"),
                ],
            ]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "✅ Skill recibida y puesta en Baúl de prueba.\n\n"
                "Por tu seguridad debe ser validada por el simulador antes de habilitarse."
            ),
            reply_markup=kb,
        )

    async def _cmd_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return
        skills = agent_manager.list_available_skills()
        msg = "Skills disponibles:\n" + ("\n".join([f"- {s}" for s in skills]) if skills else "(ninguna)")
        await context.bot.send_message(chat_id=chat_id, text=msg)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return
        pending = store.get_pending_retries(scan_limit=400)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Estado OK. Reintentos pendientes: {len(pending)}",
        )

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        text = (update.message.text or "").strip()

        if text.lower() in ("hola", "hello", "hi", "buenas", "buenos días", "buenos dias", "buenas noches"):
            await self._show_home_panel(chat_id, context)
            return

        if self._pc_waiting_search.get(chat_id):
            self._pc_waiting_search[chat_id] = False
            q = text.strip()
            if not q:
                await context.bot.send_message(chat_id=chat_id, text="Escribe el texto a buscar. Ej: buscar factura")
                return

            self._pc_search_query[chat_id] = q
            await context.bot.send_message(chat_id=chat_id, text=f"🔎 Buscando: {q}")
            res = await self._run_pc_control(chat_id, action="list_dir")
            await self._send_pc_result(chat_id, res, search_query=q)
            return

        # Skill Builder wizard
        bs = self._builder_state.get(chat_id)
        if isinstance(bs, dict) and bs.get("active"):
            step = str(bs.get("step") or "")
            if step == "pdf_name":
                name = text.strip()
                if not name:
                    await context.bot.send_message(chat_id=chat_id, text="Dime un nombre para tu skill.")
                    return
                bs["name"] = name
                bs["step"] = "pdf_text"
                await context.bot.send_message(chat_id=chat_id, text="Ahora escribe el texto que irá dentro del PDF.")
                return

            if step == "pdf_text":
                content = text.strip()
                if not content:
                    await context.bot.send_message(chat_id=chat_id, text="Escribe el texto del PDF.")
                    return
                bs["text"] = content
                bs["step"] = "pdf_folder"
                kb = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("📄 Documentos", callback_data="builder:folder:documents"),
                            InlineKeyboardButton("⬇️ Descargas", callback_data="builder:folder:downloads"),
                        ],
                        [
                            InlineKeyboardButton("🖥️ Escritorio", callback_data="builder:folder:desktop"),
                        ],
                    ]
                )
                await context.bot.send_message(chat_id=chat_id, text="¿Dónde quieres guardar el archivo?", reply_markup=kb)
                return
        if not text:
            return
        
        # Verificar si es input de credenciales pendiente
        if self._credential_requests.get(f"cred_request_{chat_id}"):
            processed = await self._process_credential_input(chat_id, text, context)
            if processed:
                return
        
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        self._chat_ids.add(chat_id)

        await bus.publish("user.INTERACTION", {"text": text, "channel": "telegram", "chat_id": chat_id}, sender="TelegramBot")

        # NLU mínimo (usuario común): abrir carpetas conocidas con control PC.
        # Ej: "abre carpeta descargas" / "abre la carpeta de descargas"
        m = re.search(
            r"\b(abre|abrir)\b.*\b(carpeta|folder)\b(?:\s+de)?\s+(descargas|downloads|escritorio|desktop|documentos|documents)\b",
            text.lower(),
        )
        if m:
            folder = m.group(3)
            await context.bot.send_message(chat_id=chat_id, text=f"Ok. Abriendo carpeta {folder}...")
            result = await self._run_pc_control(chat_id, action="open_folder", folder=folder)
            await self._send_pc_result(chat_id, result)
            return

        # Navegación: lista / atrás / entra / abre archivo
        if text.strip().lower() in {"lista", "listar", "muestra", "mostrar", "ver", "ls"}:
            result = await self._run_pc_control(chat_id, action="list_dir")
            await self._send_pc_result(chat_id, result)
            return

        if text.strip().lower().startswith("buscar "):
            q = text.strip()[7:].strip()
            if not q:
                await context.bot.send_message(chat_id=chat_id, text="Uso: buscar <texto>")
                return
            self._pc_search_query[chat_id] = q
            result = await self._run_pc_control(chat_id, action="list_dir")
            await self._send_pc_result(chat_id, result, search_query=q)
            return

        if text.strip().lower() in {"atras", "atrás", "volver", "back", "sube", "subir"}:
            result = await self._run_pc_control(chat_id, action="go_back")
            await self._send_pc_result(chat_id, result)
            return

        m = re.search(r"\b(entra|entrar|abrir)\b\s+(?:a|en)?\s*(?:la\s+carpeta\s+)?(.+)$", text.lower())
        if m and ("carpeta" in text.lower() or "folder" in text.lower() or "entra" in text.lower()):
            name = m.group(2).strip().strip('"')
            if name and len(name) <= 120:
                await context.bot.send_message(chat_id=chat_id, text=f"Ok. Entrando a: {name}")
                result = await self._run_pc_control(chat_id, action="enter_dir", folder=name)
                await self._send_pc_result(chat_id, result)
                return

        m = re.search(r"\b(abr[eí]|abrir|open)\b\s+(?:el\s+archivo\s+)?(.+)$", text.lower())
        if m and ("archivo" in text.lower() or "file" in text.lower()):
            name = m.group(2).strip().strip('"')
            if name and len(name) <= 120:
                await context.bot.send_message(chat_id=chat_id, text=f"Ok. Abriendo archivo: {name}")
                result = await self._run_pc_control(chat_id, action="open_file", folder=name)
                await self._send_pc_result(chat_id, result)
                return

        cmd = self._ce.parse(text)
        if not cmd:
            return

        if cmd.intent == "list_skills":
            await self._cmd_skills(update, context)
            return

        if cmd.intent == "status":
            await self._cmd_status(update, context)
            return

        if cmd.intent == "use_skill" and cmd.skill_name:
            await context.bot.send_message(chat_id=chat_id, text=f"Ok. Ejecutando {cmd.skill_name}...")
            result = await agent_manager.use_and_kill(cmd.skill_name, cmd.task, user_id=f"tg:{chat_id}")
            await self._maybe_send_screenshot(chat_id, result)
            await self._send_prepared_file(chat_id, result)
            return

        await context.bot.send_message(chat_id=chat_id, text="Di: usa skill <nombre> <tarea> o /help")

    async def _maybe_send_screenshot(self, chat_id: int, result: Any) -> None:
        """Si una skill devuelve screenshot_path, enviar imagen al chat."""
        if self.app is None:
            return
        if not isinstance(result, dict):
            return

        if not result.get("success"):
            return

        inner = result.get("result")
        if not isinstance(inner, dict):
            return

        payload = inner.get("result")
        if not isinstance(payload, dict):
            return

        screenshot_path = payload.get("screenshot_path")
        if not screenshot_path:
            return

        try:
            with open(screenshot_path, "rb") as f:
                await self.app.bot.send_photo(chat_id=chat_id, photo=f, caption=payload.get("message") or "")
        except Exception:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=f"Captura generada en: {screenshot_path}")
            except Exception:
                pass

    async def _run_pc_control(self, chat_id: int, action: str, folder: str = "") -> Any:
        cwd = self._pc_cwd.get(chat_id, "")
        payload = {
            "action": action,
            "folder": folder,
            "current_path": cwd,
            "task": folder,
        }
        return await agent_manager.use_and_kill(
            "pc_control",
            json.dumps(payload, ensure_ascii=False),
            user_id=f"tg:{chat_id}",
        )

    def _format_breadcrumb(self, current_path: str) -> str:
        try:
            p = Path(current_path).resolve()
            home = Path.home().resolve()
            parts = []
            if str(p).lower().startswith(str(home).lower()):
                parts.append("🏠 Inicio")
                rel = p.relative_to(home)
                for seg in rel.parts:
                    if not seg:
                        continue
                    label = seg
                    if seg.lower() == "desktop":
                        label = "🖥️ Escritorio"
                    elif seg.lower() == "downloads":
                        label = "⬇️ Descargas"
                    elif seg.lower() == "documents":
                        label = "📄 Documentos"
                    elif seg.lower() == "pictures":
                        label = "🖼️ Galería"
                    elif seg.lower() == "videos":
                        label = "🎬 Videos"
                    parts.append(label)
                return " > ".join(parts)
            return f"📁 {p}"
        except Exception:
            return f"📁 {current_path}"

    async def _send_pc_result(self, chat_id: int, result: Any, search_query: str = "") -> None:
        if not isinstance(result, dict):
            return

        if not result.get("success"):
            err = result.get("error") or "Error"
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=f"❌ {err}")
            except Exception:
                pass
            return

        inner = result.get("result")
        if not isinstance(inner, dict):
            return

        payload = inner.get("result")
        if not isinstance(payload, dict):
            return

        current_path = payload.get("current_path")
        if isinstance(current_path, str) and current_path:
            self._pc_cwd[chat_id] = current_path
            self._pc_page_offset.setdefault(chat_id, 0)

        if isinstance(payload.get("entries"), list):
            self._pc_last_entries[chat_id] = payload.get("entries")

        all_entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
        if search_query:
            sq = search_query.lower()
            filtered = []
            for e in all_entries:
                try:
                    if sq in str(e.get("name", "")).lower():
                        filtered.append(e)
                except Exception:
                    pass
            all_entries = filtered

        # cache del listado que se está mostrando (para callbacks)
        self._pc_last_entries[chat_id] = all_entries
        offset = int(self._pc_page_offset.get(chat_id, 0) or 0)
        page_size = 8
        if offset < 0:
            offset = 0
        entries = all_entries[offset : offset + page_size]
        title = payload.get("message") or "OK"

        lines = []
        if current_path:
            lines.append(self._format_breadcrumb(str(current_path)))
        lines.append(str(title))

        if search_query:
            lines.append(f"🔎 Filtro: {search_query}")

        if entries:
            lines.append("\nContenido:")
            for e in entries[:25]:
                try:
                    t = e.get("type")
                    name = e.get("name")
                    prefix = "📂" if t == "dir" else "📄"
                    lines.append(f"{prefix} {name}")
                except Exception:
                    pass

        rows = [
            [
                InlineKeyboardButton("🏠 Inicio", callback_data="menu:home"),
                InlineKeyboardButton("🖥️ Escritorio", callback_data="menu:desktop"),
                InlineKeyboardButton("⬇️ Descargas", callback_data="menu:downloads"),
            ],
            [
                InlineKeyboardButton("📄 Documentos", callback_data="menu:documents"),
                InlineKeyboardButton("🖼️ Galería", callback_data="menu:pictures"),
                InlineKeyboardButton("🎬 Videos", callback_data="menu:videos"),
            ],
            [
                InlineKeyboardButton("🧰 Crear Skill", callback_data="builder:menu"),
                InlineKeyboardButton("📦 Baúl Skills", callback_data="vault:menu"),
            ],
            [
                InlineKeyboardButton("📚 Mis Skills", callback_data="myskills:menu"),
            ],
            [
                InlineKeyboardButton("⬅️ Atrás", callback_data="nav:back"),
                InlineKeyboardButton("🔄 Refrescar", callback_data="nav:refresh"),
            ],
            [
                InlineKeyboardButton("🔍 Buscar", callback_data="nav:search"),
                InlineKeyboardButton(
                    "🟢 Auto-refresh" if self._auto_refresh_enabled.get(chat_id) else "⚪ Auto-refresh",
                    callback_data="nav:auto",
                ),
            ],
        ]

        # Botones por ítem (primeros 8 para no saturar)
        for rel_idx, e in enumerate(entries[:8]):
            try:
                name = str(e.get("name", ""))
                et = e.get("type")
                if not name:
                    continue

                idx = offset + rel_idx

                if et == "dir":
                    rows.append(
                        [
                            InlineKeyboardButton(f"📂 {name}", callback_data=f"nav:enter:{idx}"),
                            InlineKeyboardButton("📤 Enviar", callback_data=f"nav:send:{idx}"),
                        ]
                    )
                else:
                    rows.append(
                        [
                            InlineKeyboardButton(f"📄 {name}", callback_data=f"nav:send:{idx}"),
                        ]
                    )
            except Exception:
                pass

        if all_entries and offset > 0:
            rows.append([InlineKeyboardButton("⬅️ Anterior", callback_data="nav:prev")])
        if all_entries and (offset + page_size) < len(all_entries):
            rows.append([InlineKeyboardButton("➡️ Siguiente", callback_data="nav:next")])

        keyboard = InlineKeyboardMarkup(rows)

        screenshot_path = payload.get("screenshot_path")
        if screenshot_path and self.app is not None:
            try:
                with open(screenshot_path, "rb") as f:
                    await self.app.bot.send_photo(chat_id=chat_id, photo=f, caption="\n".join(lines)[:900], reply_markup=keyboard)
                return
            except Exception:
                pass

        try:
            await self.app.bot.send_message(chat_id=chat_id, text="\n".join(lines)[:3500], reply_markup=keyboard)
        except Exception:
            pass

    async def _on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        if not query:
            return
        await query.answer()

        chat_id = query.message.chat.id if query.message else None
        if chat_id is not None and self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            try:
                await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            except Exception:
                pass
            return

        data = (query.data or "").strip()

        if data == "myskills:menu":
            await self._show_my_skills(query.message.chat.id, context)
            return

        if data == "myskills:next":
            chat = query.message.chat.id
            offset = int(self._myskills_offset.get(chat, 0) or 0)
            self._myskills_offset[chat] = offset + 5
            await self._show_my_skills(chat, context)
            return

        if data == "myskills:prev":
            chat = query.message.chat.id
            offset = int(self._myskills_offset.get(chat, 0) or 0)
            self._myskills_offset[chat] = max(0, offset - 5)
            await self._show_my_skills(chat, context)
            return

        if data.startswith("myskills:run:"):
            chat = query.message.chat.id
            skill = data.split("myskills:run:", 1)[1].strip()
            if not skill:
                return
            await self._execute_skill_with_credentials_check(chat, context, skill, "crear")
            return

        if data.startswith("myskills:delete:"):
            chat = query.message.chat.id
            if not self._admin_enabled.get(chat):
                await context.bot.send_message(chat_id=chat, text="🔒 Solo admin puede eliminar skills. Usa /admin <PIN>.")
                return
            skill = data.split("myskills:delete:", 1)[1].strip()
            if not skill:
                return
            user_dir = Path(os.environ.get("MIIA_USER_SKILLS_DIR", "skills_user"))
            live_dir = Path(os.environ.get("MIIA_SKILL_VAULT_DIR", "skills_vault")) / "live"
            try:
                p = user_dir / f"{skill}.py"
                if p.exists():
                    p.unlink()
            except Exception:
                pass
            try:
                d = live_dir / skill
                if d.exists() and d.is_dir():
                    import shutil

                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass
            await context.bot.send_message(chat_id=chat, text=f"🗑️ Skill eliminada: {skill}")
            await self._show_my_skills(chat, context)
            return

        if data.startswith("home:"):
            chat = query.message.chat.id
            if data == "home:explore":
                await self._show_desktop_menu(chat)
                return
            if data == "home:builder":
                await self._show_builder_menu(chat, context)
                return
            if data == "home:vault":
                await self._show_vault_menu(chat, context)
                return
            if data == "home:help":
                kb = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🖥️ Explorar mi PC", callback_data="home:explore")],
                        [InlineKeyboardButton("🧰 Crear una Skill", callback_data="home:builder")],
                        [InlineKeyboardButton("📦 Baúl de Skills", callback_data="home:vault")],
                    ]
                )
                await context.bot.send_message(
                    chat_id=chat,
                    text=(
                        "❓ Ayuda rápida (1 minuto)\n\n"
                        "1) Toca 🖥️ Explorar mi PC para ver Escritorio/Documentos/Descargas.\n"
                        "2) Usa 📤 Enviar para mandarte archivos al chat.\n"
                        "3) Toca 🧰 Crear una Skill para automatizar (ej: crear PDF y enviarlo).\n"
                        "4) Usa 📦 Baúl de Skills para subir skills avanzadas (.zip) con simulador.\n"
                    ),
                    reply_markup=kb,
                )
                return

        if data == "builder:menu":
            await self._show_builder_menu(query.message.chat.id, context)
            return

        if data == "vault:menu":
            await self._show_vault_menu(query.message.chat.id, context)
            return

        if data.startswith("builder:"):
            chat = query.message.chat.id
            if self._allowed_chat_ids is not None and chat not in self._allowed_chat_ids:
                return

            if data == "builder:create_pdf":
                suggested = f"PDF_{int(time.time())}"
                self._builder_state[chat] = {"active": True, "step": "pdf_name", "suggested_name": suggested}
                kb = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(f"✅ Usar: {suggested}", callback_data="builder:name:auto")],
                        [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                    ]
                )
                await context.bot.send_message(
                    chat_id=chat,
                    text=(
                        "🧰 Crear Skill PDF\n\n"
                        "Elige un nombre sugerido o escribe tu propio nombre."
                    ),
                    reply_markup=kb,
                )
                return

            if data == "builder:name:auto":
                bs = self._builder_state.get(chat)
                if not isinstance(bs, dict) or not bs.get("active") or bs.get("step") != "pdf_name":
                    return
                bs["name"] = str(bs.get("suggested_name") or "Mi Skill")
                bs["step"] = "pdf_text"
                kb = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                        [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                    ]
                )
                await context.bot.send_message(chat_id=chat, text="Ahora escribe el texto que irá dentro del PDF.", reply_markup=kb)
                return

            if data == "builder:cancel":
                self._builder_state.pop(chat, None)
                await context.bot.send_message(chat_id=chat, text="Cancelado.")
                return

            if data == "builder:back":
                bs = self._builder_state.get(chat)
                if not isinstance(bs, dict) or not bs.get("active"):
                    return
                step = str(bs.get("step") or "")
                if step == "pdf_text":
                    bs["step"] = "pdf_name"
                    suggested = str(bs.get("suggested_name") or f"PDF_{int(time.time())}")
                    kb = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton(f"✅ Usar: {suggested}", callback_data="builder:name:auto")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(chat_id=chat, text="Volvimos. Elige o escribe el nombre de la skill.", reply_markup=kb)
                    return
                if step == "pdf_folder":
                    bs["step"] = "pdf_text"
                    kb = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(chat_id=chat, text="Ok. Escribe el texto del PDF.", reply_markup=kb)
                    return
                if step == "pdf_send":
                    bs["step"] = "pdf_folder"
                    kb = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📄 Documentos", callback_data="builder:folder:documents"),
                                InlineKeyboardButton("⬇️ Descargas", callback_data="builder:folder:downloads"),
                            ],
                            [InlineKeyboardButton("🖥️ Escritorio", callback_data="builder:folder:desktop")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(chat_id=chat, text="¿Dónde quieres guardar el archivo?", reply_markup=kb)
                    return
                if step == "pdf_format":
                    bs["step"] = "pdf_send"
                    kb = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("✅ Sí, enviar a Telegram", callback_data="builder:send:yes")],
                            [InlineKeyboardButton("❌ No, solo guardar", callback_data="builder:send:no")],
                            [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(chat_id=chat, text="¿Quieres que también lo envíe a Telegram?", reply_markup=kb)
                    return
                return

            if data.startswith("builder:folder:"):
                bs = self._builder_state.get(chat)
                if not isinstance(bs, dict) or not bs.get("active") or bs.get("step") != "pdf_folder":
                    return
                folder = data.split("builder:folder:", 1)[1]
                bs["folder"] = folder
                bs["step"] = "pdf_send"
                kb = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("✅ Sí, enviar a Telegram", callback_data="builder:send:yes"),
                        ],
                        [
                            InlineKeyboardButton("❌ No, solo guardar", callback_data="builder:send:no"),
                        ],
                        [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                        [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                    ]
                )
                await context.bot.send_message(chat_id=chat, text="¿Quieres que también lo envíe a Telegram?", reply_markup=kb)
                return

            if data.startswith("builder:send:"):
                bs = self._builder_state.get(chat)
                if not isinstance(bs, dict) or not bs.get("active") or bs.get("step") != "pdf_send":
                    return
                bs["send"] = data.split("builder:send:", 1)[1] == "yes"
                bs["step"] = "pdf_format"

                has_reportlab = importlib.util.find_spec("reportlab") is not None
                if has_reportlab:
                    kb = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("📄 Crear PDF real", callback_data="builder:format:pdf")],
                            [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(
                        chat_id=chat,
                        text="✅ Detecté librería PDF (reportlab). ¿Creamos PDF real?",
                        reply_markup=kb,
                    )
                else:
                    kb = InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("📝 Crear HTML/TXT (alternativa)", callback_data="builder:format:html")],
                            [InlineKeyboardButton("⬅️ Atrás", callback_data="builder:back")],
                            [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")],
                        ]
                    )
                    await context.bot.send_message(
                        chat_id=chat,
                        text="⚠️ No detecté librería PDF (reportlab). Puedo crear una alternativa HTML/TXT.",
                        reply_markup=kb,
                    )
                return

            if data.startswith("builder:format:"):
                bs = self._builder_state.get(chat)
                if not isinstance(bs, dict) or not bs.get("active") or bs.get("step") != "pdf_format":
                    return

                fmt = data.split("builder:format:", 1)[1]
                name = str(bs.get("name") or "Mi Skill").strip()
                text = str(bs.get("text") or "").strip()
                folder = str(bs.get("folder") or "documents")
                send_it = bool(bs.get("send"))
                skill_id = re.sub(r"[^a-zA-Z0-9_\-]+", "_", name.strip().lower()).strip("_-") or "mi_skill"

                # preparar skill en temp
                tmp_dir = Path(os.environ.get("MIIA_SKILL_BUILDER_TMP", str(Path(os.getenv("TEMP", ".")) / "miia_builder")))
                out_dir = tmp_dir / f"skill_{skill_id}_{int(time.time())}"
                out_dir.mkdir(parents=True, exist_ok=True)

                permissions = ["fs_write"]
                if send_it:
                    permissions.append("telegram_send")

                manifest = {
                    "id": skill_id,
                    "name": name,
                    "version": "1.0",
                    "permissions": permissions,
                }
                (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

                # generación
                if fmt == "pdf":
                    code = (
                        "import time\n"
                        "from pathlib import Path\n"
                        "\n"
                        "def _resolve_known(folder: str) -> Path:\n"
                        "    f = (folder or '').strip().lower()\n"
                        "    h = Path.home()\n"
                        "    if f in ('documents','documentos','docs'): return h / 'Documents'\n"
                        "    if f in ('downloads','descargas'): return h / 'Downloads'\n"
                        "    if f in ('desktop','escritorio'): return h / 'Desktop'\n"
                        "    return h\n"
                        "\n"
                        "def execute(context):\n"
                        "    from reportlab.pdfgen import canvas\n"
                        f"    text = {json.dumps(text, ensure_ascii=False)}\n"
                        f"    folder = {json.dumps(folder)}\n"
                        f"    send_it = {json.dumps(send_it)}\n"
                        "    base = _resolve_known(folder)\n"
                        "    base.mkdir(parents=True, exist_ok=True)\n"
                        f"    filename = {json.dumps(skill_id)} + '_' + str(int(time.time())) + '.pdf'\n"
                        "    out = (base / filename).resolve()\n"
                        "    c = canvas.Canvas(str(out))\n"
                        "    y = 800\n"
                        "    for line in str(text).splitlines() or ['']:\n"
                        "        c.drawString(40, y, line[:200])\n"
                        "        y -= 16\n"
                        "        if y < 40:\n"
                        "            c.showPage()\n"
                        "            y = 800\n"
                        "    c.save()\n"
                        "    res = {'success': True, 'message': f'PDF creado: {out}', 'path': str(out)}\n"
                        "    if send_it:\n"
                        "        res.update({'send_path': str(out), 'send_kind': 'document', 'original_name': out.name})\n"
                        "    return res\n"
                    )
                else:
                    code = (
                        "import time\n"
                        "from pathlib import Path\n"
                        "\n"
                        "def _resolve_known(folder: str) -> Path:\n"
                        "    f = (folder or '').strip().lower()\n"
                        "    h = Path.home()\n"
                        "    if f in ('documents','documentos','docs'): return h / 'Documents'\n"
                        "    if f in ('downloads','descargas'): return h / 'Downloads'\n"
                        "    if f in ('desktop','escritorio'): return h / 'Desktop'\n"
                        "    return h\n"
                        "\n"
                        "def execute(context):\n"
                        f"    text = {json.dumps(text, ensure_ascii=False)}\n"
                        f"    folder = {json.dumps(folder)}\n"
                        f"    send_it = {json.dumps(send_it)}\n"
                        "    base = _resolve_known(folder)\n"
                        "    base.mkdir(parents=True, exist_ok=True)\n"
                        f"    filename = {json.dumps(skill_id)} + '_' + str(int(time.time())) + '.html'\n"
                        "    out = (base / filename).resolve()\n"
                        "    out.write_text('<pre>' + str(text) + '</pre>', encoding='utf-8')\n"
                        "    res = {'success': True, 'message': f'HTML creado: {out}', 'path': str(out)}\n"
                        "    if send_it:\n"
                        "        res.update({'send_path': str(out), 'send_kind': 'document', 'original_name': out.name})\n"
                        "    return res\n"
                    )

                (out_dir / "skill.py").write_text(code, encoding="utf-8")

                await context.bot.send_message(chat_id=chat, text="🧪 Validando e instalando tu skill...")
                report, module_path = vault.install_from_prepared_dir(out_dir)

                self._builder_state.pop(chat, None)

                if report.ok:
                    await context.bot.send_message(
                        chat_id=chat,
                        text=(
                            f"✅ Skill creada e instalada: {report.skill_id}\n"
                            f"Ya puedes usar: usa skill {report.skill_id} <tarea>\n"
                            f"(Para generar el documento, puedes usar cualquier tarea, por ejemplo: 'crear')"
                        ),
                    )
                else:
                    reasons = "\n".join([f"- {r}" for r in report.reasons]) if report.reasons else "- (sin detalles)"
                    await context.bot.send_message(chat_id=chat, text=f"❌ No se pudo instalar. Motivos:\n{reasons}")
                return

        if data.startswith("vault:"):
            chat = query.message.chat.id
            if self._allowed_chat_ids is not None and chat not in self._allowed_chat_ids:
                return
            if not self._admin_enabled.get(chat):
                await context.bot.send_message(chat_id=chat, text="🔒 Ejecuta /admin <PIN> para usar el baúl.")
                return

            if data == "vault:menu":
                await self._show_vault_menu(chat, context)
                return

            if data == "vault:upload":
                self._vault_waiting_zip[chat] = True
                await context.bot.send_message(chat_id=chat, text="📦 Envíame ahora el archivo .zip (manifest.json + skill.py).")
                return

            staged = Path(self._vault_staged_zip.get(chat, "")) if self._vault_staged_zip.get(chat) else None

            if data == "vault:delete":
                if staged and staged.exists():
                    vault.delete_staged(staged)
                self._vault_staged_zip.pop(chat, None)
                await context.bot.send_message(chat_id=chat, text="🗑️ Eliminada.")
                return

            if data == "vault:quarantine":
                if staged and staged.exists():
                    out = vault.quarantine(staged, reason="Cuarentena manual solicitada por usuario")
                    self._vault_staged_zip[chat] = str(out)
                await context.bot.send_message(chat_id=chat, text="🔒 En cuarentena (no ejecutable).")
                return

            if data == "vault:simulate":
                if not staged or not staged.exists():
                    await context.bot.send_message(chat_id=chat, text="No hay ZIP staged para validar.")
                    return

                await context.bot.send_message(chat_id=chat, text="🧪 Ejecutando simulador de seguridad...")
                report, module_path = vault.validate_and_install(staged)

                if report.ok:
                    self._vault_staged_zip.pop(chat, None)
                    await context.bot.send_message(
                        chat_id=chat,
                        text=(
                            f"✅ Pasó la prueba.\n"
                            f"Skill instalada como: {report.skill_id}\n"
                            f"Ya aparece en /skills y puedes usar: usa skill {report.skill_id} <tarea>"
                        ),
                    )
                    return

                qpath = ""
                try:
                    for r in (report.reasons or []):
                        if isinstance(r, str) and r.startswith("Cuarentena:"):
                            qpath = r.split("Cuarentena:", 1)[1].strip()
                            break
                except Exception:
                    qpath = ""

                reasons = "\n".join([f"- {r}" for r in report.reasons if isinstance(r, str) and not r.startswith("Cuarentena:")]) if report.reasons else "- (sin detalles)"
                if qpath:
                    reasons += f"\n\n📁 Cuarentena: {qpath}"
                kb = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🗑️ Eliminar", callback_data="vault:delete")],
                        [InlineKeyboardButton("🔒 Mantener en cuarentena", callback_data="vault:quarantine")],
                    ]
                )
                await context.bot.send_message(
                    chat_id=chat,
                    text=(
                        "❌ No pasó la prueba de seguridad. Alto % de ser maliciosa.\n\n"
                        "Motivos:\n"
                        f"{reasons}"
                    ),
                    reply_markup=kb,
                )
                return

        if data.startswith("menu:"):
            key = data.split("menu:", 1)[1]
            self._pc_page_offset[query.message.chat.id] = 0
            self._pc_search_query.pop(query.message.chat.id, None)
            if key == "home":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="home")
            elif key == "desktop":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="desktop")
            elif key == "downloads":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="downloads")
            elif key == "documents":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="documents")
            elif key == "pictures":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="pictures")
            elif key == "videos":
                res = await self._run_pc_control(query.message.chat.id, action="open_folder", folder="videos")
            else:
                return
            await self._send_pc_result(query.message.chat.id, res)
            return
        if data == "nav:back":
            self._pc_page_offset[query.message.chat.id] = 0
            res = await self._run_pc_control(query.message.chat.id, action="go_back")
            await self._send_pc_result(query.message.chat.id, res)
            return
        if data == "nav:refresh":
            res = await self._run_pc_control(query.message.chat.id, action="list_dir")
            await self._send_pc_result(query.message.chat.id, res, search_query=self._pc_search_query.get(query.message.chat.id, ""))
            return
        if data == "nav:search":
            self._pc_waiting_search[query.message.chat.id] = True
            await context.bot.send_message(chat_id=query.message.chat.id, text="🔍 Escribe lo que quieres buscar en ESTA carpeta (no recursivo). Ej: buscar factura")
            return
        if data == "nav:auto":
            enabled = not bool(self._auto_refresh_enabled.get(query.message.chat.id))
            self._auto_refresh_enabled[query.message.chat.id] = enabled
            if enabled:
                await context.bot.send_message(chat_id=query.message.chat.id, text="🟢 Auto-refresh activado (cada 6s). Para parar, vuelve a tocar Auto-refresh.")
                self._start_auto_refresh(query.message.chat.id)
            else:
                self._stop_auto_refresh(query.message.chat.id)
                await context.bot.send_message(chat_id=query.message.chat.id, text="⚪ Auto-refresh desactivado.")
            return
        if data == "nav:next":
            all_entries = self._pc_last_entries.get(query.message.chat.id, [])
            offset = int(self._pc_page_offset.get(query.message.chat.id, 0) or 0)
            page_size = 8
            if (offset + page_size) < len(all_entries):
                self._pc_page_offset[query.message.chat.id] = offset + page_size
            res = await self._run_pc_control(query.message.chat.id, action="list_dir")
            await self._send_pc_result(query.message.chat.id, res, search_query=self._pc_search_query.get(query.message.chat.id, ""))
            return
        if data == "nav:prev":
            offset = int(self._pc_page_offset.get(query.message.chat.id, 0) or 0)
            page_size = 8
            offset = max(0, offset - page_size)
            self._pc_page_offset[query.message.chat.id] = offset
            res = await self._run_pc_control(query.message.chat.id, action="list_dir")
            await self._send_pc_result(query.message.chat.id, res, search_query=self._pc_search_query.get(query.message.chat.id, ""))
            return
        if data.startswith("nav:enter:"):
            try:
                idx = int(data.split("nav:enter:", 1)[1])
            except Exception:
                return
            entries = self._pc_last_entries.get(query.message.chat.id, [])
            if 0 <= idx < len(entries):
                name = str(entries[idx].get("name", ""))
                self._pc_page_offset[query.message.chat.id] = 0
                self._pc_search_query.pop(query.message.chat.id, None)
                res = await self._run_pc_control(query.message.chat.id, action="enter_dir", folder=name)
                await self._send_pc_result(query.message.chat.id, res)
            return
        if data.startswith("nav:send:"):
            try:
                idx = int(data.split("nav:send:", 1)[1])
            except Exception:
                return
            entries = self._pc_last_entries.get(query.message.chat.id, [])
            if 0 <= idx < len(entries):
                name = str(entries[idx].get("name", ""))
                res = await self._run_pc_control(query.message.chat.id, action="prepare_send", folder=name)
                await self._send_pc_result(query.message.chat.id, res)
                await self._send_prepared_file(query.message.chat.id, res)
            return
        if data.startswith("retry:"):
            session_id = data.split("retry:", 1)[1]
            await bus.publish("skill.RETRY_REQUEST", {"session_id": session_id, "channel": "telegram"}, sender="TelegramBot")
            await context.bot.send_message(chat_id=query.message.chat.id, text="🔁 Reintentando...")
            return
        
        # Handler para cancelar solicitud de credenciales
        if data.startswith("cred:cancel:"):
            chat = query.message.chat.id
            skill = data.split("cred:cancel:", 1)[1].strip()
            # Limpiar solicitud pendiente
            self._credential_requests.pop(f"cred_request_{chat}", None)
            self._pending_credentials.pop(f"cred_session_{skill}_{chat}", None)
            await context.bot.send_message(
                chat_id=chat,
                text=f"❌ Solicitud de credenciales cancelada. La skill '{skill}' no se ejecutará."
            )
            return

    async def _send_prepared_file(self, chat_id: int, result: Any) -> None:
        if self.app is None:
            return
        if not isinstance(result, dict) or not result.get("success"):
            return
        inner = result.get("result")
        if not isinstance(inner, dict):
            return
        payload = inner.get("result")
        if not isinstance(payload, dict):
            return

        send_path = payload.get("send_path")
        send_kind = payload.get("send_kind")
        name = payload.get("original_name")
        if not send_path or not send_kind:
            return

        try:
            with open(send_path, "rb") as f:
                if send_kind == "photo":
                    await self.app.bot.send_photo(chat_id=chat_id, photo=f, caption=f"📤 {name}")
                elif send_kind == "video":
                    await self.app.bot.send_video(chat_id=chat_id, video=f, caption=f"📤 {name}")
                else:
                    await self.app.bot.send_document(chat_id=chat_id, document=f, filename=str(name))
        except Exception as e:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=f"No se pudo enviar el archivo: {e}")
            except Exception:
                pass

    async def _send_to_all(self, text: str) -> None:
        if not text:
            return
        if self.app is None:
            return

        targets = list(self._chat_ids)
        if self._allowed_chat_ids is not None:
            targets = [cid for cid in targets if cid in self._allowed_chat_ids]

        for chat_id in targets:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                pass

    async def _show_desktop_menu(self, chat_id: int) -> None:
        self._pc_page_offset[chat_id] = 0
        self._pc_search_query.pop(chat_id, None)
        res = await self._run_pc_control(chat_id, action="open_folder", folder="desktop")
        await self._send_pc_result(chat_id, res)

    async def _show_home_panel(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🖥️ Explorar mi PC", callback_data="home:explore")],
                [InlineKeyboardButton("🧰 Crear una Skill", callback_data="home:builder")],
                [InlineKeyboardButton("📦 Baúl de Skills", callback_data="home:vault")],
                [InlineKeyboardButton("📚 Mis Skills", callback_data="myskills:menu")],
                [InlineKeyboardButton("❓ Ayuda", callback_data="home:help")],
            ]
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "MiIA Product-20\n\n"
                "Elige una opción para empezar:"
            ),
            reply_markup=kb,
        )

    def _get_user_skills(self) -> list[str]:
        user_dir = Path(os.environ.get("MIIA_USER_SKILLS_DIR", "skills_user"))
        if not user_dir.exists():
            return []
        out: list[str] = []
        for f in user_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            out.append(f.stem)
        return list(sorted(set(out)))

    async def _show_my_skills(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        skills = self._get_user_skills()
        offset = int(self._myskills_offset.get(chat_id, 0) or 0)
        page_size = 5
        if offset < 0:
            offset = 0
        if offset >= len(skills):
            offset = 0
        self._myskills_offset[chat_id] = offset

        page = skills[offset : offset + page_size]
        rows = []
        for s in page:
            row = [InlineKeyboardButton(f"▶️ {s}", callback_data=f"myskills:run:{s}")]
            if self._admin_enabled.get(chat_id):
                row.append(InlineKeyboardButton("🗑️", callback_data=f"myskills:delete:{s}"))
            rows.append(row)

        nav = []
        if offset > 0:
            nav.append(InlineKeyboardButton("⬅️ Anterior", callback_data="myskills:prev"))
        if (offset + page_size) < len(skills):
            nav.append(InlineKeyboardButton("➡️ Siguiente", callback_data="myskills:next"))
        if nav:
            rows.append(nav)

        rows.append([InlineKeyboardButton("🏠 Inicio", callback_data="home:help")])

        kb = InlineKeyboardMarkup(rows)
        msg = "📚 Mis Skills\n\n"
        msg += "Toca ▶️ para ejecutar (usa tarea por defecto: 'crear').\n"
        if not skills:
            msg += "\n(No tienes skills aún. Usa 🧰 Crear una Skill)"

        await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=kb)

    def _get_skill_permissions(self, skill_name: str) -> list:
        """Obtiene los permisos de una skill desde su manifest"""
        user_dir = Path(os.environ.get("MIIA_USER_SKILLS_DIR", "skills_user"))
        live_dir = Path(os.environ.get("MIIA_SKILL_VAULT_DIR", "skills_vault")) / "live"
        
        manifest_path = user_dir / skill_name / "manifest.json"
        if not manifest_path.exists():
            manifest_path = live_dir / skill_name / "manifest.json"
        
        if manifest_path.exists():
            try:
                import json
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return manifest.get("permissions", [])
            except:
                pass
        return []

    async def _execute_skill_with_credentials_check(
        self, 
        chat_id: int, 
        context: ContextTypes.DEFAULT_TYPE, 
        skill_name: str, 
        task: str
    ) -> None:
        """Ejecuta skill verificando si necesita credenciales"""
        permissions = self._get_skill_permissions(skill_name)
        
        if "credentials" in permissions:
            cred_session_key = f"cred_session_{skill_name}_{chat_id}"
            credential_session = self._pending_credentials.get(cred_session_key)
            
            if not credential_session:
                await self._request_credentials_from_user(chat_id, context, skill_name, task)
                return
            else:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"🔐 Ejecutando {skill_name} con credenciales..."
                )
                result = await agent_manager.use_and_kill(
                    skill_name, task, user_id=f"tg:{chat_id}"
                )
                self._pending_credentials.pop(cred_session_key, None)
                await self._maybe_send_screenshot(chat_id, result)
                await self._send_prepared_file(chat_id, result)
                return
        
        await context.bot.send_message(chat_id=chat_id, text=f"▶️ Ejecutando {skill_name}...")
        result = await agent_manager.use_and_kill(skill_name, task, user_id=f"tg:{chat_id}")
        await self._maybe_send_screenshot(chat_id, result)
        await self._send_prepared_file(chat_id, result)

    async def _request_credentials_from_user(
        self, 
        chat_id: int, 
        context: ContextTypes.DEFAULT_TYPE, 
        skill_name: str,
        task: str
    ) -> None:
        """Solicita credenciales al usuario vía Telegram"""
        cred_request_key = f"cred_request_{chat_id}"
        self._credential_requests[cred_request_key] = {
            "skill_name": skill_name,
            "task": task,
            "requested_at": time.time()
        }
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"cred:cancel:{skill_name}")]
        ])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🔐 La skill **{skill_name}** requiere credenciales.\n\n"
                f"⚠️ **Seguridad:**\n"
                f"• Uso temporal (máx 10 min)\n"
                f"• Eliminación automática\n"
                f"• Nunca en disco\n\n"
                f"Envía credenciales:\n"
                f"```\nusername: tu_usuario\npassword: tu_password\n```"
            ),
            parse_mode="Markdown",
            reply_markup=kb
        )

    async def _process_credential_input(
        self, 
        chat_id: int, 
        text: str, 
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Procesa input de credenciales del usuario"""
        cred_request_key = f"cred_request_{chat_id}"
        request_info = self._credential_requests.get(cred_request_key)
        
        if not request_info:
            return False
        
        if text.lower() in ["cancelar", "cancel", "no"]:
            self._credential_requests.pop(cred_request_key, None)
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Operación cancelada."
            )
            return True
        
        try:
            credentials = {}
            for line in text.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    credentials[key.strip().lower()] = value.strip()
            
            if not credentials:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ Formato inválido. Usa:\n```\nusername: X\npassword: Y\n```"
                )
                return True
            
            from core.SkillCredentialVault import credential_vault
            skill_name = request_info["skill_name"]
            task = request_info["task"]
            
            session_id = credential_vault.store_credentials(
                skill_id=skill_name,
                credentials=credentials,
                ttl_seconds=600
            )
            
            cred_session_key = f"cred_session_{skill_name}_{chat_id}"
            self._pending_credentials[cred_session_key] = session_id
            self._credential_requests.pop(cred_request_key, None)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Credenciales recibidas. Ejecutando {skill_name}..."
            )
            
            result = await agent_manager.use_and_kill(
                skill_name, task, user_id=f"tg:{chat_id}"
            )
            
            self._pending_credentials.pop(cred_session_key, None)
            await self._maybe_send_screenshot(chat_id, result)
            await self._send_prepared_file(chat_id, result)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando credenciales: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)}"
            )
            return True

    def _start_auto_refresh(self, chat_id: int) -> None:
        self._stop_auto_refresh(chat_id)
        self._auto_refresh_last_ts.setdefault(chat_id, 0.0)
        self._auto_refresh_tasks[chat_id] = asyncio.create_task(self._auto_refresh_loop(chat_id))

    def _stop_auto_refresh(self, chat_id: int) -> None:
        t = self._auto_refresh_tasks.pop(chat_id, None)
        if t is not None:
            try:
                t.cancel()
            except Exception:
                pass

    async def _auto_refresh_loop(self, chat_id: int) -> None:
        # liviano: 6s, con límite para no spamear infinito
        max_cycles = int(os.environ.get("MIIA_AUTO_REFRESH_MAX_CYCLES", "30") or "30")
        interval = float(os.environ.get("MIIA_AUTO_REFRESH_SECONDS", "6") or "6")
        cycles = 0
        while self._auto_refresh_enabled.get(chat_id):
            await asyncio.sleep(interval)
            if not self._auto_refresh_enabled.get(chat_id):
                break

            now = time.time()
            last = float(self._auto_refresh_last_ts.get(chat_id, 0.0) or 0.0)
            if (now - last) < max(2.0, interval - 1.0):
                continue
            self._auto_refresh_last_ts[chat_id] = now

            try:
                res = await self._run_pc_control(chat_id, action="list_dir")
                await self._send_pc_result(chat_id, res, search_query=self._pc_search_query.get(chat_id, ""))
            except Exception:
                pass

            cycles += 1
            if cycles >= max_cycles:
                self._auto_refresh_enabled[chat_id] = False
                break

    async def _on_user_speak(self, data: Dict[str, Any]) -> None:
        msg = (data or {}).get("message")
        if msg:
            await self._send_to_all(str(msg))

    async def _on_user_ui_message(self, data: Dict[str, Any]) -> None:
        msg = (data or {}).get("message")
        if msg:
            await self._send_to_all(str(msg))

    async def _on_retry_available(self, data: Dict[str, Any]) -> None:
        if self.app is None:
            return

        session_id = (data or {}).get("session_id")
        skill = (data or {}).get("skill", "skill")
        if not session_id:
            return

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔁 Reintentar", callback_data=f"retry:{session_id}")]]
        )

        text = f"Reintento disponible para: {skill}\nSession: {session_id[:8]}..."

        targets = list(self._chat_ids)
        if self._allowed_chat_ids is not None:
            targets = [cid for cid in targets if cid in self._allowed_chat_ids]

        for chat_id in targets:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
            except Exception:
                pass

    async def _on_credential_event(self, data: Dict[str, Any]) -> None:
        """
        Maneja eventos de credenciales del SkillCredentialVault
        Notifica al usuario cuando una skill accede, falla o es bloqueada
        """
        if self.app is None:
            return
        
        event_type = data.get("event_type")
        skill_id = data.get("skill_id", "unknown")
        message = data.get("message", "")
        user_id = data.get("user_id", "unknown")
        
        # Extraer chat_id del user_id (formato: "tg:{chat_id}")
        if user_id.startswith("tg:"):
            try:
                chat_id = int(user_id.split(":")[1])
            except:
                return
        else:
            return
        
        # Enviar notificación según el tipo de evento
        if event_type == "access":
            emoji = "🔐"
            prefix = "Acceso a credenciales"
        elif event_type == "failed":
            emoji = "⚠️"
            prefix = "⚠️ ADVERTENCIA"
        elif event_type == "blocked":
            emoji = "🚫"
            prefix = "🚫 ALERTA DE SEGURIDAD"
        elif event_type == "expired":
            emoji = "⏰"
            prefix = "Credenciales expiradas"
        elif event_type == "limit_reached":
            emoji = "🚫"
            prefix = "🚫 Límite alcanzado"
        else:
            return
        
        text = f"{emoji} **{prefix}**\n\nSkill: `{skill_id}`\n{message}"
        
        try:
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error enviando notificación de credenciales: {e}")


def get_token_from_env() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if token:
        return token

    try:
        from dotenv import load_dotenv

        load_dotenv()
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        return token
    except Exception:
        return ""


async def run_telegram_bot() -> None:
    token = get_token_from_env()
    if not token:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN (ponlo en .env o en variable de entorno)")

    loop = asyncio.get_running_loop()
    bus.set_loop(loop)

    await store.start()
    await feedback_manager.start()

    svc = TelegramBotService(token)
    await svc.start()

    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await svc.stop()
