import asyncio
import json
import logging
import os
import re
import time
import hmac
import hashlib
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

        # Seguridad HIGH: aprobación + PIN
        self._pending_security_actions: Dict[str, Dict[str, Any]] = {}
        self._waiting_pin_token: Dict[int, str] = {}
        self._pin_path = Path(__file__).resolve().parent.parent / "data" / "bot_pin.json"
        self._admin_pin_path = Path(__file__).resolve().parent.parent / "data" / "admin_pin.json"

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
        self.app.add_handler(CommandHandler("setadminpin", self._cmd_setadminpin))
        self.app.add_handler(CommandHandler("setpin", self._cmd_setpin))
        self.app.add_handler(CommandHandler("vault", self._cmd_vault))
        self.app.add_handler(CommandHandler("builder", self._cmd_builder))
        self.app.add_handler(CallbackQueryHandler(self._on_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self._on_document))

        await self.app.initialize()
        await self.app.start()
        try:
            await self.app.bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass
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

        # Validación segura: preferir admin_pin.json (hash). Fallback de compatibilidad a env MIIA_ADMIN_PIN (migración automática).
        if self._admin_pin_is_set():
            if not self._verify_admin_pin(pin):
                await context.bot.send_message(chat_id=chat_id, text="PIN incorrecto.")
                return
        else:
            expected_env = (os.environ.get("MIIA_ADMIN_PIN") or "").strip()
            if expected_env:
                if pin != expected_env:
                    await context.bot.send_message(chat_id=chat_id, text="PIN incorrecto.")
                    return
                # Migración automática a almacenamiento controlado
                try:
                    self._set_admin_pin_hash(pin)
                except Exception:
                    pass
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🔒 Admin PIN no configurado. Usa /setadminpin <PIN> (desde un chat permitido).",
                )
                return

        self._admin_enabled[chat_id] = True
        await context.bot.send_message(chat_id=chat_id, text="✅ Admin habilitado en este chat. Ya puedes usar /vault para subir skills.")

    async def _cmd_setadminpin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not context.args:
            await context.bot.send_message(chat_id=chat_id, text="Uso: /setadminpin <PIN>")
            return

        new_pin = str(context.args[0]).strip()
        if len(new_pin) < 4:
            await context.bot.send_message(chat_id=chat_id, text="❌ PIN muy corto. Mínimo 4 dígitos.")
            return

        # Si ya existe PIN admin, solo permitir cambio si este chat está en modo admin
        if self._admin_pin_is_set() and not self._admin_enabled.get(chat_id):
            await context.bot.send_message(chat_id=chat_id, text="🔒 Para cambiar el PIN admin, primero ejecuta: /admin <PIN>")
            return

        try:
            self._set_admin_pin_hash(new_pin)
            await context.bot.send_message(chat_id=chat_id, text="✅ PIN admin configurado/actualizado.")
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text="❌ No se pudo configurar el PIN admin.")
            return

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

        # Iniciar wizard directamente (modo usuario): crear Skill PDF paso a paso
        self._builder_state[chat_id] = {"active": True, "kind": "pdf", "step": "pdf_name"}
        await context.bot.send_message(chat_id=chat_id, text="Nombre de la skill PDF (ej: pdf_test):")

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

        # Si se está esperando el PIN, procesarlo aquí y no pasarlo a bus/LLM.
        pending_token = self._waiting_pin_token.get(chat_id)
        if pending_token:
            handled = await self._handle_pin_input(chat_id, pending_token, text, context, update=update)
            if handled:
                return

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
            await self._execute_skill_with_credentials_check(chat_id, context, cmd.skill_name, cmd.task)
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

        if data.startswith("sec:"):
            await self._handle_security_callback(query, context, data)
            return

        if data == "builder:create_pdf":
            chat = query.message.chat.id
            self._builder_state[chat] = {"active": True, "kind": "pdf", "step": "pdf_name"}
            await context.bot.send_message(chat_id=chat, text="Nombre de la skill PDF (ej: pdf_test):")
            return

        if data == "builder:cancel":
            chat = query.message.chat.id
            self._builder_state.pop(chat, None)
            await context.bot.send_message(chat_id=chat, text="❌ Cancelado.")
            return

        if data.startswith("builder:folder:"):
            chat = query.message.chat.id
            bs = self._builder_state.get(chat)
            if not isinstance(bs, dict) or not bs.get("active"):
                return
            if str(bs.get("step") or "") != "pdf_folder":
                return
            folder_key = data.split("builder:folder:", 1)[1].strip()
            bs["folder"] = folder_key
            try:
                skill_name = str(bs.get("name") or "").strip()
                pdf_text = str(bs.get("text") or "").strip()
                if not skill_name or not pdf_text:
                    raise ValueError("Faltan datos del builder")
                created = self._create_pdf_skill_files(skill_name=skill_name, pdf_text=pdf_text, folder_key=folder_key)
                self._builder_state.pop(chat, None)
                await context.bot.send_message(
                    chat_id=chat,
                    text=f"✅ Skill creada: {created}.\n\nAhora ejecútala con: usa skill {created} crear",
                )
            except Exception:
                self._builder_state.pop(chat, None)
                await context.bot.send_message(chat_id=chat, text="❌ No se pudo crear la skill.")
            return

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

    def _load_pin_record(self) -> Dict[str, Any]:
        try:
            if self._pin_path.exists():
                return json.loads(self._pin_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_pin_record(self, rec: Dict[str, Any]) -> None:
        try:
            self._pin_path.parent.mkdir(parents=True, exist_ok=True)
            self._pin_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_admin_pin_record(self) -> Dict[str, Any]:
        try:
            if self._admin_pin_path.exists():
                return json.loads(self._admin_pin_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_admin_pin_record(self, rec: Dict[str, Any]) -> None:
        try:
            self._admin_pin_path.parent.mkdir(parents=True, exist_ok=True)
            self._admin_pin_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _hash_pin(self, pin: str, salt_hex: str, rounds: int = 120_000) -> str:
        pin_b = (pin or "").encode("utf-8")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", pin_b, salt, int(rounds))
        return dk.hex()

    def _admin_pin_is_set(self) -> bool:
        rec = self._load_admin_pin_record()
        return bool(rec.get("pin_hash") and rec.get("salt"))

    def _verify_admin_pin(self, pin: str) -> bool:
        rec = self._load_admin_pin_record()
        salt = str(rec.get("salt") or "").strip()
        pin_hash = str(rec.get("pin_hash") or "").strip()
        rounds = int(rec.get("rounds") or 120_000)
        if not salt or not pin_hash:
            return False
        try:
            calc = self._hash_pin(pin, salt_hex=salt, rounds=rounds)
            return hmac.compare_digest(calc, pin_hash)
        except Exception:
            return False

    def _set_admin_pin_hash(self, pin: str) -> None:
        salt = os.urandom(16).hex()
        rounds = 120_000
        pin_hash = self._hash_pin(pin, salt_hex=salt, rounds=rounds)
        self._save_admin_pin_record({"salt": salt, "rounds": rounds, "pin_hash": pin_hash, "updated_at": time.time()})

    def _pin_is_set(self) -> bool:
        rec = self._load_pin_record()
        return bool(rec.get("pin_hash") and rec.get("salt"))

    def _verify_pin(self, pin: str) -> bool:
        rec = self._load_pin_record()
        salt = str(rec.get("salt") or "").strip()
        pin_hash = str(rec.get("pin_hash") or "").strip()
        rounds = int(rec.get("rounds") or 120_000)
        if not salt or not pin_hash:
            return False
        try:
            calc = self._hash_pin(pin, salt_hex=salt, rounds=rounds)
            return hmac.compare_digest(calc, pin_hash)
        except Exception:
            return False

    async def _cmd_setpin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not self._admin_enabled.get(chat_id):
            await context.bot.send_message(chat_id=chat_id, text="🔒 Ejecuta /admin <PIN_ADMIN> antes de configurar el PIN.")
            return

        if not context.args:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Uso: /setpin <PIN>\nEj: /setpin 1234\n\nNota: MININA guarda solo el hash (no el PIN).",
            )
            return

        pin = str(context.args[0]).strip()
        if len(pin) < 4:
            await context.bot.send_message(chat_id=chat_id, text="❌ PIN muy corto. Mínimo 4 dígitos.")
            return

        salt = os.urandom(16).hex()
        rounds = 120_000
        pin_hash = self._hash_pin(pin, salt_hex=salt, rounds=rounds)
        self._save_pin_record({"salt": salt, "rounds": rounds, "pin_hash": pin_hash, "updated_at": time.time()})

        await context.bot.send_message(chat_id=chat_id, text="✅ PIN configurado. Se pedirá para acciones de riesgo alto.")

    def _risk_from_permissions(self, permissions: list) -> str:
        perms = {str(p).strip().lower() for p in (permissions or [])}
        if any(p in perms for p in ["network", "fs_write", "pc_control", "telegram_send"]):
            return "high"
        if "fs_read" in perms:
            return "medium"
        return "low"

    def _escape_md(self, text: str) -> str:
        # Markdown (legacy) en Telegram es frágil con '_' y otros caracteres.
        # Escapamos lo mínimo para que no rompa el mensaje.
        s = str(text or "")
        for ch in ["_", "*", "`", "[", "]"]:
            s = s.replace(ch, f"\\{ch}")
        return s

    async def _request_security_approval(
        self,
        chat_id: int,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        title: str,
        description: str,
        action: Dict[str, Any],
        ttl_seconds: int = 90,
    ) -> None:
        token = f"sec_{chat_id}_{int(time.time()*1000)}"
        self._pending_security_actions[token] = {
            "chat_id": chat_id,
            "created_at": time.time(),
            "expires_at": time.time() + ttl_seconds,
            "stage": "confirm",
            "action": action,
            "title": title,
            "description": description,
        }

        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Aprobar", callback_data=f"sec:approve:{token}")],
                [InlineKeyboardButton("❌ Cancelar", callback_data=f"sec:deny:{token}")],
            ]
        )

        pin_note = "\n\n🔐 Luego se pedirá tu PIN." if self._pin_is_set() else "\n\n⚠️ PIN no configurado. Usa /admin y /setpin."
        safe_title = self._escape_md(title)
        safe_desc = self._escape_md(description)
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚠️ *Acción de riesgo alto*\n\n"
                f"*{safe_title}*\n"
                f"{safe_desc}{pin_note}\n\n"
                f"¿Confirmas?"
            ),
            parse_mode="Markdown",
            reply_markup=kb,
        )

    async def _handle_security_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data: str) -> None:
        chat_id = query.message.chat.id if query.message else None
        if chat_id is None:
            return

        parts = data.split(":", 2)
        if len(parts) < 3:
            return
        cmd = parts[1]
        token = parts[2]
        entry = self._pending_security_actions.get(token)
        if not isinstance(entry, dict):
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Sesión de aprobación no encontrada o expirada.")
            return

        if entry.get("chat_id") != chat_id:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ Sesión no válida.")
            return

        if time.time() > float(entry.get("expires_at") or 0):
            self._pending_security_actions.pop(token, None)
            await context.bot.send_message(chat_id=chat_id, text="⏰ Aprobación expirada. Vuelve a solicitar la acción.")
            return

        if cmd == "deny":
            self._pending_security_actions.pop(token, None)
            self._waiting_pin_token.pop(chat_id, None)
            await context.bot.send_message(chat_id=chat_id, text="❌ Cancelado.")
            return

        if cmd == "approve":
            if not self._pin_is_set():
                await context.bot.send_message(chat_id=chat_id, text="⚠️ PIN no configurado. Usa /admin y /setpin primero.")
                return
            entry["stage"] = "pin"
            self._waiting_pin_token[chat_id] = token
            await context.bot.send_message(chat_id=chat_id, text="🔐 Escribe tu PIN para continuar (no será enviado a ninguna API).")
            return

    async def _handle_pin_input(
        self,
        chat_id: int,
        token: str,
        pin_text: str,
        context: ContextTypes.DEFAULT_TYPE,
        *,
        update: Optional[Update] = None,
    ) -> bool:
        entry = self._pending_security_actions.get(token)
        if not isinstance(entry, dict) or entry.get("chat_id") != chat_id:
            self._waiting_pin_token.pop(chat_id, None)
            return False

        if time.time() > float(entry.get("expires_at") or 0):
            self._pending_security_actions.pop(token, None)
            self._waiting_pin_token.pop(chat_id, None)
            await context.bot.send_message(chat_id=chat_id, text="⏰ Aprobación expirada.")
            return True

        # Intentar borrar el mensaje del PIN (best effort)
        try:
            if update and update.message:
                await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        except Exception:
            pass

        pin = (pin_text or "").strip()
        if not self._verify_pin(pin):
            await context.bot.send_message(chat_id=chat_id, text="❌ PIN incorrecto. Cancelado.")
            self._pending_security_actions.pop(token, None)
            self._waiting_pin_token.pop(chat_id, None)
            return True

        action = entry.get("action") if isinstance(entry.get("action"), dict) else {}
        self._pending_security_actions.pop(token, None)
        self._waiting_pin_token.pop(chat_id, None)

        # Ejecutar acción ya aprobada (sin exponer PIN)
        kind = str(action.get("kind") or "").strip()
        if kind == "skill_exec":
            skill = str(action.get("skill") or "").strip()
            task = str(action.get("task") or "").strip()
            if not skill:
                await context.bot.send_message(chat_id=chat_id, text="⚠️ Acción inválida.")
                return True
            await context.bot.send_message(chat_id=chat_id, text=f"✅ Aprobado. Ejecutando {skill}...")
            try:
                result = await agent_manager.use_and_kill(skill, task, user_id=f"tg:{chat_id}")
                await self._maybe_send_screenshot(chat_id, result)
                await self._send_prepared_file(chat_id, result)
            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text=f"❌ Error ejecutando: {str(e)}")
            return True

        await context.bot.send_message(chat_id=chat_id, text="⚠️ Acción no soportada.")
        return True

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
        root_dir = Path(__file__).resolve().parent.parent
        candidates = [root_dir / "skills_user", root_dir / "data" / "skills_user"]
        out: set[str] = set()
        for user_dir in candidates:
            try:
                if not user_dir.exists():
                    continue
                for f in user_dir.glob("*.py"):
                    if f.name.startswith("_"):
                        continue
                    out.add(f.stem)
            except Exception:
                pass
        return list(sorted(out))

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
        base_data = Path(__file__).resolve().parent.parent / "data"
        live_dir = base_data / "skills_vault" / "live"

        root_dir = Path(__file__).resolve().parent.parent
        user_dir_root = root_dir / "skills_user"
        user_dir_data = root_dir / "data" / "skills_user"

        manifest_candidates = [
            live_dir / skill_name / "manifest.json",
            user_dir_root / f"{skill_name}.manifest.json",
            user_dir_data / f"{skill_name}.manifest.json",
            user_dir_root / skill_name / "manifest.json",
            user_dir_data / skill_name / "manifest.json",
        ]

        manifest_path = None
        for p in manifest_candidates:
            if p.exists():
                manifest_path = p
                break
        
        if manifest_path is not None and manifest_path.exists():
            try:
                import json
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return manifest.get("permissions", [])
            except:
                pass
        return []

    def _create_pdf_skill_files(self, *, skill_name: str, pdf_text: str, folder_key: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_\-]", "_", (skill_name or "").strip().lower())
        safe = re.sub(r"_+", "_", safe).strip("_")
        if not safe:
            safe = f"pdf_{int(time.time())}"

        root_dir = Path(__file__).resolve().parent.parent
        out_dir = root_dir / "skills_user"
        out_dir.mkdir(parents=True, exist_ok=True)

        skill_path = out_dir / f"{safe}.py"
        manifest_path = out_dir / f"{safe}.manifest.json"

        # Manifest para que el bot lo clasifique como HIGH (fs_write)
        manifest = {
            "id": safe,
            "name": safe,
            "version": "1.0.0",
            "description": "PDF builder (Telegram)",
            "permissions": ["fs_write"],
            "builder": {"kind": "pdf", "folder": str(folder_key or "")},
        }

        code = (
            "import time\n"
            "from pathlib import Path\n"
            "\n"
            "def execute(ctx):\n"
            "    text = str((ctx or {}).get('task') or '').strip()\n"
            "    if not text:\n"
            "        text = '" + pdf_text.replace("\\", "\\\\").replace("\n", "\\n").replace("\"", "\\\"") + "'\n"
            "    ts = int(time.time())\n"
            "    out_dir = Path('output')\n"
            "    out_dir.mkdir(parents=True, exist_ok=True)\n"
            "    pdf_path = out_dir / f'" + safe + "_{ts}.pdf'\n"
            "    body = text.replace('\\r', '')\n"
            "    content = (\n"
            "        '%PDF-1.4\\n'\n"
            "        '1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\\n'\n"
            "        '2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\\n'\n"
            "        '3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\\n'\n"
            "        + f'4 0 obj<< /Length {len(body)+50} >>stream\\nBT\\n/F1 12 Tf\\n72 720 Td\\n(' + body.replace('(', '[').replace(')', ']') + ') Tj\\nET\\nendstream\\nendobj\\n'\n"
            "        '5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\\n'\n"
            "        'xref\\n0 6\\n0000000000 65535 f\\n'\n"
            "        'trailer<< /Root 1 0 R /Size 6 >>\\nstartxref\\n0\\n%%EOF\\n'\n"
            "    )\n"
            "    pdf_path.write_bytes(content.encode('latin-1', errors='ignore'))\n"
            "    return {\n"
            "        'success': True,\n"
            "        'message': f'PDF generado: {pdf_path.name}',\n"
            "        'send_kind': 'document',\n"
            "        'send_path': str(pdf_path),\n"
            "        'original_name': pdf_path.name,\n"
            "    }\n"
        )

        skill_path.write_text(code, encoding="utf-8")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return safe

    async def _execute_skill_with_credentials_check(
        self, 
        chat_id: int, 
        context: ContextTypes.DEFAULT_TYPE, 
        skill_name: str, 
        task: str
    ) -> None:
        """Ejecuta skill verificando si necesita credenciales"""
        try:
            permissions = self._get_skill_permissions(skill_name)

            # Gate de seguridad: acciones de riesgo alto requieren doble aprobación (botón + PIN)
            if self._risk_from_permissions(permissions) == "high":
                perms_txt = ", ".join([str(p) for p in (permissions or [])])
                await self._request_security_approval(
                    chat_id,
                    context,
                    title=f"Ejecutar skill: {skill_name}",
                    description=f"Tarea: {task or '(sin tarea)'}\nPermisos: {perms_txt}",
                    action={"kind": "skill_exec", "skill": skill_name, "task": task},
                )
                return

            # Si requiere credenciales, pedirlas/usar sesión
            if "credentials" in permissions:
                cred_session_key = f"cred_session_{skill_name}_{chat_id}"
                credential_session = self._pending_credentials.get(cred_session_key)
                if not credential_session:
                    await self._request_credentials_from_user(chat_id, context, skill_name, task)
                    return

                await context.bot.send_message(chat_id=chat_id, text=f"🔐 Ejecutando {skill_name} con credenciales...")
                result = await agent_manager.use_and_kill(skill_name, task, user_id=f"tg:{chat_id}")
                self._pending_credentials.pop(cred_session_key, None)
                await self._maybe_send_screenshot(chat_id, result)
                await self._send_prepared_file(chat_id, result)
                return

            # Ejecución normal
            await context.bot.send_message(chat_id=chat_id, text=f"▶️ Ejecutando {skill_name}...")
            result = await agent_manager.use_and_kill(skill_name, task, user_id=f"tg:{chat_id}")
            await self._maybe_send_screenshot(chat_id, result)
            await self._send_prepared_file(chat_id, result)
        except Exception as e:
            try:
                await context.bot.send_message(chat_id=chat_id, text=f"❌ Error ejecutando {skill_name}: {e}")
            except Exception:
                pass

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


async def run_telegram_bot(stop_event: Optional[asyncio.Event] = None) -> None:
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
            if stop_event is not None and stop_event.is_set():
                break
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        raise
    finally:
        await svc.stop()
