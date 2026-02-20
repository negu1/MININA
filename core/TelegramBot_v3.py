"""
MININA v3.0 - Telegram Bot Service (Refactorizado)
Integración completa con MININAApiClient y OrchestratorAgent
"""

import asyncio
import json
import logging
import os
import re
import time
from pathlib import Path
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

# Importar desde core MININA v3.0
from core.CortexBus import bus
from core.CommandEngine.engine import CommandEngine
from core.ui.api_client import api_client, MININAApiClient
from core.orchestrator.orchestrator_agent import OrchestratorAgent
from core.SkillVault import vault

logger = logging.getLogger("TelegramBot")


def _parse_allowed_chat_ids() -> Optional[set[int]]:
    """Parsear IDs de chat permitidos desde variables de entorno"""
    raw = (os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or "").strip()
    raw_multi = (os.environ.get("TELEGRAM_ALLOWED_IDS") or "").strip()
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
    """
    Servicio de Bot de Telegram para MININA v3.0
    Integración completa con api_client y orchestrator
    """
    
    def __init__(self, token: str):
        self.token = token
        self.app: Optional[Application] = None
        self._ce = CommandEngine()
        self._chat_ids: set[int] = set()
        self._retry_sessions: Dict[str, RetryInfo] = {}
        self._allowed_chat_ids: Optional[set[int]] = _parse_allowed_chat_ids()
        
        # Estado de navegación PC
        self._pc_cwd: Dict[int, str] = {}
        self._pc_last_entries: Dict[int, list[dict[str, Any]]] = {}
        self._pc_page_offset: Dict[int, int] = {}
        self._pc_waiting_search: Dict[int, bool] = {}
        self._pc_search_query: Dict[int, str] = {}
        self._auto_refresh_enabled: Dict[int, bool] = {}
        self._auto_refresh_tasks: Dict[int, asyncio.Task] = {}
        self._auto_refresh_last_ts: Dict[int, float] = {}

        # Admin y vault
        self._admin_enabled: Dict[int, bool] = {}
        self._vault_waiting_zip: Dict[int, bool] = {}
        self._vault_staged_zip: Dict[int, str] = {}
        self._builder_state: Dict[int, Dict[str, Any]] = {}
        self._myskills_offset: Dict[int, int] = {}
        
        # Sistema de credenciales
        self._credential_requests: Dict[str, Dict[str, Any]] = {}
        self._pending_credentials: Dict[str, str] = {}

        # Subscribirse a eventos del bus
        bus.subscribe("user.SPEAK", self._on_user_speak)
        bus.subscribe("user.UI_MESSAGE", self._on_user_ui_message)
        bus.subscribe("skill.RETRY_AVAILABLE", self._on_retry_available)

    async def start(self) -> None:
        """Iniciar el bot de Telegram"""
        if self.app is not None:
            return

        self.app = Application.builder().token(self.token).build()

        # Handlers de comandos
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("skills", self._cmd_skills))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("admin", self._cmd_admin))
        self.app.add_handler(CommandHandler("vault", self._cmd_vault))
        self.app.add_handler(CommandHandler("builder", self._cmd_builder))
        self.app.add_handler(CommandHandler("orquestar", self._cmd_orquestar))
        self.app.add_handler(CommandHandler("works", self._cmd_works))
        
        # Handlers de mensajes y callbacks
        self.app.add_handler(CallbackQueryHandler(self._on_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self._on_document))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

        logger.info("Telegram bot v3.0 started")

    async def stop(self) -> None:
        """Detener el bot de Telegram"""
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

    # =========================================================================
    # COMANDOS PRINCIPALES
    # =========================================================================

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /start - Panel principal"""
        chat_id = update.effective_chat.id

        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        self._chat_ids.add(chat_id)
        await self._show_home_panel(chat_id, context)

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /help - Ayuda"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        help_text = """🤖 *Comandos disponibles:*

*Gestión de Skills:*
/skills - Ver skills disponibles
/• `usa skill <nombre> <tarea>` - Ejecutar skill
/vault - Subir skills (.zip)
/builder - Crear skill simple

*Control del Sistema:*
/explorar - Abrir explorador de archivos
/works - Ver trabajos generados
/status - Estado del sistema

*Orquestación Inteligente:*
/orquestar <objetivo> - Ejecutar plan automático

*Admin:*
/admin <PIN> - Acceso administrador

*Ejemplos:*
• `usa skill clock`
• `usa skill web_browser google.com`
• `orquestar Genera un reporte de ventas`"""

        await context.bot.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode="Markdown"
        )

    async def _cmd_skills(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /skills - Listar skills disponibles"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        try:
            # Usar api_client para obtener skills
            skills = api_client.get_skills()
            
            if not skills:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📦 No hay skills disponibles. Usa /builder para crear una."
                )
                return

            # Crear botones para cada skill
            rows = []
            for skill in skills[:10]:  # Mostrar máximo 10
                skill_id = skill.get('id', 'unknown')
                skill_name = skill.get('name', skill_id)
                rows.append([InlineKeyboardButton(
                    f"▶️ {skill_name}",
                    callback_data=f"skill:run:{skill_id}"
                )])

            rows.append([InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")])
            kb = InlineKeyboardMarkup(rows)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📚 *Skills disponibles ({len(skills)}):*\n\nToca para ejecutar:",
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Error listando skills: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error al obtener skills: {str(e)}"
            )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /status - Estado del sistema"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        try:
            # Verificar health del sistema
            health = api_client.health_check()
            skills = api_client.get_skills()
            works = api_client.get_works()

            status_text = f"""📊 *Estado MININA v3.0*

✅ Backend: {'Online' if health else 'Offline'}
📦 Skills: {len(skills)} disponibles
📄 Works: {len(works)} generados
🔌 APIs: Ollama, OpenAI, Groq (configurables)

💡 Usa /help para ver comandos disponibles."""

            await context.bot.send_message(
                chat_id=chat_id,
                text=status_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error en status: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Error verificando estado: {str(e)}"
            )

    async def _cmd_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /admin - Habilitar modo administrador"""
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
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔒 Admin PIN no configurado (MIIA_ADMIN_PIN)."
            )
            return

        if pin != expected:
            await context.bot.send_message(chat_id=chat_id, text="❌ PIN incorrecto.")
            return

        self._admin_enabled[chat_id] = True
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ *Admin habilitado*\n\nAhora puedes:\n• Usar /vault para subir skills\n• Eliminar skills\n• Ver todos los works",
            parse_mode="Markdown"
        )

    async def _cmd_vault(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /vault - Gestión de vault de skills"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        if not self._admin_enabled.get(chat_id):
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔒 Ejecuta: /admin <PIN> primero"
            )
            return

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Subir skill (.zip)", callback_data="vault:upload")],
            [InlineKeyboardButton("📚 Ver mis skills", callback_data="myskills:menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="menu:close")]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text="📦 *Baúl de Skills*\n\nGestiona tus skills personalizadas.",
            parse_mode="Markdown",
            reply_markup=kb
        )

    async def _cmd_builder(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /builder - Crear skill simple"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        await self._show_builder_menu(chat_id, context)

    async def _cmd_orquestar(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Comando /orquestar - Ejecutar objetivo con orquestador
        Uso: /orquestar <objetivo>
        Ejemplo: /orquestar Crea un reporte de ventas en PDF
        """
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        # Obtener el objetivo del mensaje
        if not context.args:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Uso: /orquestar <objetivo>\n\nEjemplo:\n• `/orquestar Crea un PDF con el resumen de ventas`\n• `/orquestar Busca archivos de trabajo y organiza por fecha`",
                parse_mode="Markdown"
            )
            return

        objective = " ".join(context.args)
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎯 *Orquestando:* _{objective}_\n\n⏳ Analizando y planificando tareas...",
            parse_mode="Markdown"
        )

        try:
            # Usar OrchestratorAgent para procesar el objetivo
            orchestrator = OrchestratorAgent()
            
            # Procesar el objetivo
            plan = await orchestrator.process_objective(objective, context={
                "chat_id": chat_id,
                "channel": "telegram",
                "user_id": f"tg:{chat_id}"
            })

            if plan and plan.get("tasks"):
                tasks = plan.get("tasks", [])
                
                # Mostrar plan generado
                plan_text = "📋 *Plan generado:*\n\n"
                for i, task in enumerate(tasks[:5], 1):
                    plan_text += f"{i}. {task.get('description', 'Tarea')}\n"
                
                if len(tasks) > 5:
                    plan_text += f"\n... y {len(tasks) - 5} tareas más"

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=plan_text,
                    parse_mode="Markdown"
                )

                # Ejecutar el plan
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🚀 *Ejecutando plan...*"
                )

                result = await orchestrator.execute_plan(plan, context={
                    "chat_id": chat_id,
                    "channel": "telegram",
                    "user_id": f"tg:{chat_id}"
                })

                # Enviar resultado
                if result.get("success"):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ *¡Objetivo completado!*\n\n{result.get('message', 'Plan ejecutado correctamente')}"
                    )
                    
                    # Si hay archivos generados, enviarlos
                    if result.get("works"):
                        for work_id in result.get("works", []):
                            await self._send_work_to_chat(chat_id, work_id)
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ *Error ejecutando plan:*\n{result.get('error', 'Error desconocido')}"
                    )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ No se pudo generar un plan para este objetivo."
                )

        except Exception as e:
            logger.error(f"Error en orquestación: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)}"
            )

    async def _cmd_works(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /works - Ver trabajos generados"""
        chat_id = update.effective_chat.id
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        try:
            works = api_client.get_works()
            
            if not works:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📭 No hay works generados aún."
                )
                return

            # Mostrar últimos 10 works
            works_text = "📄 *Works recientes:*\n\n"
            for i, work in enumerate(works[:10], 1):
                name = work.get('original_name', 'Sin nombre')
                works_text += f"{i}. {name}\n"

            if len(works) > 10:
                works_text += f"\n... y {len(works) - 10} más"

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refrescar", callback_data="works:refresh")],
                [InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")]
            ])

            await context.bot.send_message(
                chat_id=chat_id,
                text=works_text,
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Error obteniendo works: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)}"
            )

    # =========================================================================
    # PANELES Y MENÚS
    # =========================================================================

    async def _show_home_panel(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar panel principal"""
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🖥️ Explorar PC", callback_data="home:explore")],
                [InlineKeyboardButton("🎯 Orquestar Tarea", callback_data="home:orquestar")],
                [InlineKeyboardButton("📚 Mis Skills", callback_data="myskills:menu")],
                [InlineKeyboardButton("📄 Works", callback_data="works:menu")],
                [InlineKeyboardButton("❓ Ayuda", callback_data="home:help")],
            ]
        )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 *MININA v3.0*\n\nTu asistente inteligente. Elige una opción:",
            parse_mode="Markdown",
            reply_markup=kb,
        )

    async def _show_builder_menu(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar menú de builder de skills"""
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Crear PDF", callback_data="builder:pdf")],
            [InlineKeyboardButton("📊 Crear Excel", callback_data="builder:excel")],
            [InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text="🧰 *Creador de Skills*\n\n¿Qué tipo de skill quieres crear?",
            parse_mode="Markdown",
            reply_markup=kb
        )

    # =========================================================================
    # MANEJO DE MENSAJES
    # =========================================================================

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar mensajes de texto"""
        chat_id = update.effective_chat.id
        text = (update.message.text or "").strip()

        if not text:
            return

        # Saludos
        if text.lower() in ("hola", "hello", "hi", "buenas", "inicio"):
            await self._show_home_panel(chat_id, context)
            return

        # Verificar si es input de credenciales pendiente
        if self._credential_requests.get(f"cred_request_{chat_id}"):
            processed = await self._process_credential_input(chat_id, text, context)
            if processed:
                return

        # Verificar si es búsqueda de archivos
        if self._pc_waiting_search.get(chat_id):
            self._pc_waiting_search[chat_id] = False
            await self._handle_file_search(chat_id, text, context)
            return

        # Verificar si es builder wizard
        bs = self._builder_state.get(chat_id)
        if isinstance(bs, dict) and bs.get("active"):
            await self._handle_builder_step(chat_id, text, context, bs)
            return

        # Verificar acceso
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="Acceso no autorizado.")
            return

        self._chat_ids.add(chat_id)

        # Publicar interacción al bus
        await bus.publish(
            "user.INTERACTION",
            {"text": text, "channel": "telegram", "chat_id": chat_id},
            sender="TelegramBot"
        )

        # Parsear comando
        cmd = self._ce.parse(text)
        if not cmd:
            # Si no es comando, tratar como orquestación simple
            await self._handle_natural_input(chat_id, text, context)
            return

        if cmd.intent == "list_skills":
            await self._cmd_skills(update, context)
            return

        if cmd.intent == "status":
            await self._cmd_status(update, context)
            return

        if cmd.intent == "use_skill" and cmd.skill_name:
            await self._execute_skill_via_api(chat_id, cmd.skill_name, cmd.task, context)
            return

        # Comando no reconocido
        await context.bot.send_message(
            chat_id=chat_id,
            text="❓ Comando no reconocido. Usa /help para ver opciones."
        )

    async def _handle_natural_input(self, chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar input natural del usuario"""
        # Detectar intenciones comunes
        text_lower = text.lower()

        # Intención de explorar archivos
        if any(word in text_lower for word in ["archivo", "carpeta", "documento", "abre"]):
            await context.bot.send_message(
                chat_id=chat_id,
                text="🖥️ Abriendo explorador de archivos..."
            )
            await self._show_file_explorer(chat_id, context)
            return

        # Intención de crear algo
        if any(word in text_lower for word in ["crea", "genera", "haz", "elabora"]):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🎯 Procesando: _{text}_\n\nUsando orquestador...",
                parse_mode="Markdown"
            )
            
            # Simular comando orquestar
            update = type('Update', (), {'effective_chat': type('Chat', (), {'id': chat_id})(), 'message': type('Message', (), {'text': text})()})()
            fake_context = type('Context', (), {'args': text.split()[1:], 'bot': context.bot})()
            await self._cmd_orquestar(update, fake_context)
            return

        # Respuesta genérica
        await context.bot.send_message(
            chat_id=chat_id,
            text="🤔 No entendí bien. ¿Quieres:\n\n• Ver archivos: toca 🖥️ Explorar PC\n• Ejecutar skill: usa /skills\n• Crear algo: usa /orquestar <objetivo>\n\nO escribe /help para más opciones."
        )

    # =========================================================================
    # EJECUCIÓN DE SKILLS VÍA API
    # =========================================================================

    async def _execute_skill_via_api(
        self,
        chat_id: int,
        skill_name: str,
        task: str,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Ejecutar skill usando MININAApiClient"""
        
        # Verificar si skill requiere credenciales
        permissions = self._get_skill_permissions(skill_name)
        
        if "credentials" in permissions:
            cred_session_key = f"cred_session_{skill_name}_{chat_id}"
            credential_session = self._pending_credentials.get(cred_session_key)
            
            if not credential_session:
                await self._request_credentials_from_user(chat_id, context, skill_name, task)
                return

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"▶️ Ejecutando *{skill_name}*...",
            parse_mode="Markdown"
        )

        try:
            # Usar api_client para ejecutar skill
            result = api_client.execute_skill(skill_name, task, user_id=f"tg:{chat_id}")
            
            if result.get("success"):
                # Enviar mensaje de resultado
                message = result.get("message", "Skill ejecutada correctamente")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"✅ {message}"
                )
                
                # Si hay screenshot, enviarlo
                await self._maybe_send_screenshot_api(chat_id, result, context)
                
                # Si hay archivo, enviarlo
                await self._maybe_send_file_api(chat_id, result, context)
            else:
                error = result.get("error", "Error desconocido")
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ Error: {error}"
                )
                
        except Exception as e:
            logger.error(f"Error ejecutando skill {skill_name}: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error ejecutando skill: {str(e)}"
            )

    async def _maybe_send_screenshot_api(
        self,
        chat_id: int,
        result: dict,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Enviar screenshot si existe en resultado de API"""
        screenshot_path = result.get("screenshot_path") or result.get("result", {}).get("screenshot_path")
        
        if screenshot_path and Path(screenshot_path).exists():
            try:
                with open(screenshot_path, "rb") as f:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=f,
                        caption="📸 Captura de pantalla"
                    )
            except Exception as e:
                logger.warning(f"No se pudo enviar screenshot: {e}")

    async def _maybe_send_file_api(
        self,
        chat_id: int,
        result: dict,
        context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Enviar archivo si existe en resultado de API"""
        send_path = result.get("send_path") or result.get("result", {}).get("send_path")
        send_kind = result.get("send_kind") or result.get("result", {}).get("send_kind", "document")
        
        if send_path and Path(send_path).exists():
            try:
                with open(send_path, "rb") as f:
                    if send_kind == "photo":
                        await context.bot.send_photo(chat_id=chat_id, photo=f)
                    elif send_kind == "video":
                        await context.bot.send_video(chat_id=chat_id, video=f)
                    else:
                        await context.bot.send_document(chat_id=chat_id, document=f)
            except Exception as e:
                logger.warning(f"No se pudo enviar archivo: {e}")

    async def _send_work_to_chat(self, chat_id: int, work_id: str) -> None:
        """Descargar y enviar un work al chat"""
        try:
            # Obtener works y buscar el work_id
            works = api_client.get_works()
            work = None
            for w in works:
                if w.get('id') == work_id:
                    work = w
                    break
            
            if not work:
                return

            # Descargar archivo
            import tempfile
            tmp_path = Path(tempfile.gettempdir()) / work.get('original_name', 'file')
            
            if api_client.download_work(work_id, tmp_path):
                # Enviar archivo
                with open(tmp_path, "rb") as f:
                    await self.app.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=f"📄 {work.get('original_name')}"
                    )
                
                # Limpiar
                tmp_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error enviando work {work_id}: {e}")

    # =========================================================================
    # SISTEMA DE CREDENCIALES
    # =========================================================================

    def _get_skill_permissions(self, skill_name: str) -> list:
        """Obtener permisos de skill desde vault"""
        try:
            user_dir = Path(os.environ.get("MIIA_USER_SKILLS_DIR", "skills_user"))
            live_dir = Path(os.environ.get("MIIA_SKILL_VAULT_DIR", "skills_vault")) / "live"
            
            manifest_path = user_dir / skill_name / "manifest.json"
            if not manifest_path.exists():
                manifest_path = live_dir / skill_name / "manifest.json"
            
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                return manifest.get("permissions", [])
        except Exception:
            pass
        return []

    async def _request_credentials_from_user(
        self,
        chat_id: int,
        context: ContextTypes.DEFAULT_TYPE,
        skill_name: str,
        task: str
    ) -> None:
        """Solicitar credenciales al usuario"""
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
            text=f"🔐 La skill *{skill_name}* requiere credenciales.\n\nEnvía las credenciales en formato:\n```\nusername: tu_usuario\npassword: tu_password\n```",
            parse_mode="Markdown",
            reply_markup=kb
        )

    async def _process_credential_input(
        self,
        chat_id: int,
        text: str,
        context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Procesar input de credenciales"""
        cred_request_key = f"cred_request_{chat_id}"
        request_info = self._credential_requests.get(cred_request_key)
        
        if not request_info:
            return False
        
        if text.lower() in ["cancelar", "cancel", "no"]:
            self._credential_requests.pop(cred_request_key, None)
            await context.bot.send_message(chat_id=chat_id, text="❌ Cancelado.")
            return True
        
        try:
            # Parsear credenciales
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
            
            # Guardar en vault de credenciales
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
            
            # Ejecutar skill con credenciales
            await self._execute_skill_via_api(chat_id, skill_name, task, context)
            
            return True
            
        except Exception as e:
            logger.error(f"Error procesando credenciales: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")
            return True

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    async def _on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar callbacks de botones"""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        chat_id = query.message.chat.id if query.message else None
        if chat_id is None:
            return

        # Verificar acceso
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            return

        data = (query.data or "").strip()

        # Home menu
        if data == "home:menu":
            await self._show_home_panel(chat_id, context)
            return

        if data == "home:explore":
            await self._show_file_explorer(chat_id, context)
            return

        if data == "home:orquestar":
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎯 *Orquestar tarea*\n\nEscribe tu objetivo:\n```\n/orquestar Crea un reporte de ventas\n```",
                parse_mode="Markdown"
            )
            return

        if data == "home:help":
            await self._cmd_help(update, context)
            return

        # Skills
        if data == "myskills:menu":
            await self._show_my_skills_panel(chat_id, context)
            return

        if data.startswith("skill:run:"):
            skill_name = data.split("skill:run:", 1)[1]
            await self._execute_skill_via_api(chat_id, skill_name, "crear", context)
            return

        # Works
        if data == "works:menu" or data == "works:refresh":
            await self._cmd_works(update, context)
            return

        # Vault
        if data == "vault:upload":
            if not self._admin_enabled.get(chat_id):
                await context.bot.send_message(chat_id=chat_id, text="🔒 Necesitas admin.")
                return
            self._vault_waiting_zip[chat_id] = True
            await context.bot.send_message(
                chat_id=chat_id,
                text="📦 Envía el archivo .zip con la skill"
            )
            return

        if data.startswith("vault:"):
            await self._handle_vault_callback(chat_id, data, context)
            return

        # Credenciales
        if data.startswith("cred:cancel:"):
            skill = data.split("cred:cancel:", 1)[1]
            self._credential_requests.pop(f"cred_request_{chat_id}", None)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Credenciales canceladas para {skill}"
            )
            return

        # Builder
        if data.startswith("builder:"):
            await self._handle_builder_callback(chat_id, data, context)
            return

    async def _show_my_skills_panel(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar panel de skills del usuario"""
        try:
            skills = api_client.get_skills()
            
            if not skills:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🧰 Crear Skill", callback_data="builder:menu")],
                    [InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")]
                ])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📭 No tienes skills. Crea una con /builder",
                    reply_markup=kb
                )
                return

            # Crear botones
            rows = []
            for skill in skills[:10]:
                skill_id = skill.get('id', 'unknown')
                skill_name = skill.get('name', skill_id)
                rows.append([InlineKeyboardButton(
                    f"▶️ {skill_name}",
                    callback_data=f"skill:run:{skill_id}"
                )])

            rows.append([InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")])
            kb = InlineKeyboardMarkup(rows)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📚 *Tus Skills ({len(skills)}):*\n\nToca para ejecutar:",
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception as e:
            logger.error(f"Error mostrando skills: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

    async def _handle_vault_callback(self, chat_id: int, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar callbacks de vault"""
        if not self._admin_enabled.get(chat_id):
            await context.bot.send_message(chat_id=chat_id, text="🔒 Necesitas admin.")
            return

        staged = Path(self._vault_staged_zip.get(chat_id, "")) if self._vault_staged_zip.get(chat_id) else None

        if data == "vault:delete":
            if staged and staged.exists():
                vault.delete_staged(staged)
            self._vault_staged_zip.pop(chat_id, None)
            await context.bot.send_message(chat_id=chat_id, text="🗑️ Eliminada.")
            return

        if data == "vault:quarantine":
            if staged and staged.exists():
                out = vault.quarantine(staged, reason="Cuarentena manual")
                self._vault_staged_zip[chat_id] = str(out)
            await context.bot.send_message(chat_id=chat_id, text="🔒 En cuarentena.")
            return

        if data == "vault:simulate":
            if not staged or not staged.exists():
                await context.bot.send_message(chat_id=chat_id, text="No hay ZIP para validar.")
                return

            await context.bot.send_message(chat_id=chat_id, text="🧪 Validando...")
            
            try:
                report, module_path = vault.validate_and_install(staged)
                
                if report.ok:
                    self._vault_staged_zip.pop(chat_id, None)
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ Skill instalada: *{report.skill_id}*\n\nYa puedes usarla con:\n`usa skill {report.skill_id} crear`",
                        parse_mode="Markdown"
                    )
                else:
                    reasons = "\n".join([f"- {r}" for r in report.reasons]) if report.reasons else "Error desconocido"
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"❌ No pasó validación:\n{reasons}"
                    )
            except Exception as e:
                await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")
            return

    # =========================================================================
    # EXPLORADOR DE ARCHIVOS
    # =========================================================================

    async def _show_file_explorer(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar explorador de archivos"""
        self._pc_page_offset[chat_id] = 0
        self._pc_search_query.pop(chat_id, None)
        
        # Listar directorio home por defecto
        home_path = Path.home()
        entries = self._list_directory(home_path)
        
        self._pc_cwd[chat_id] = str(home_path)
        self._pc_last_entries[chat_id] = entries
        
        await self._send_file_list(chat_id, context, entries, str(home_path))

    def _list_directory(self, path: Path) -> list:
        """Listar contenido de directorio"""
        entries = []
        try:
            for item in path.iterdir():
                entries.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "path": str(item)
                })
        except Exception as e:
            logger.error(f"Error listando directorio {path}: {e}")
        
        return sorted(entries, key=lambda x: (x["type"] != "dir", x["name"].lower()))

    async def _send_file_list(
        self,
        chat_id: int,
        context: ContextTypes.DEFAULT_TYPE,
        entries: list,
        current_path: str,
        search_query: str = ""
    ) -> None:
        """Enviar lista de archivos al chat"""
        # Filtrar si hay búsqueda
        if search_query:
            entries = [e for e in entries if search_query.lower() in e["name"].lower()]

        # Paginación
        offset = self._pc_page_offset.get(chat_id, 0)
        page_size = 8
        page_entries = entries[offset:offset + page_size]

        # Construir mensaje
        lines = [f"📁 *{Path(current_path).name or current_path}*\n"]
        
        if search_query:
            lines.append(f"🔎 Búsqueda: _{search_query}_\n")

        if not page_entries:
            lines.append("_(vacío)_")
        else:
            for e in page_entries:
                icon = "📂" if e["type"] == "dir" else "📄"
                lines.append(f"{icon} {e['name']}")

        # Botones de navegación
        rows = [
            [
                InlineKeyboardButton("🏠 Home", callback_data="nav:home"),
                InlineKeyboardButton("⬆️ Arriba", callback_data="nav:up"),
            ],
            [
                InlineKeyboardButton("🔍 Buscar", callback_data="nav:search"),
                InlineKeyboardButton("🔄 Refresh", callback_data="nav:refresh"),
            ],
        ]

        # Botones de archivos
        for i, e in enumerate(page_entries[:6]):
            idx = offset + i
            if e["type"] == "dir":
                rows.append([InlineKeyboardButton(f"📂 {e['name'][:20]}", callback_data=f"nav:enter:{idx}")])
            else:
                rows.append([InlineKeyboardButton(f"📄 {e['name'][:20]}", callback_data=f"nav:send:{idx}")])

        # Navegación de páginas
        nav_buttons = []
        if offset > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="nav:prev"))
        if (offset + page_size) < len(entries):
            nav_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data="nav:next"))
        if nav_buttons:
            rows.append(nav_buttons)

        rows.append([InlineKeyboardButton("🏠 Inicio", callback_data="home:menu")])
        
        kb = InlineKeyboardMarkup(rows)

        await context.bot.send_message(
            chat_id=chat_id,
            text="\n".join(lines),
            parse_mode="Markdown",
            reply_markup=kb
        )

    async def _handle_file_search(self, chat_id: int, query: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar búsqueda de archivos"""
        self._pc_search_query[chat_id] = query
        
        entries = self._pc_last_entries.get(chat_id, [])
        current_path = self._pc_cwd.get(chat_id, str(Path.home()))
        
        await self._send_file_list(chat_id, context, entries, current_path, query)

    # =========================================================================
    # BUILDER DE SKILLS
    # =========================================================================

    async def _handle_builder_callback(self, chat_id: int, data: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar callbacks de builder"""
        if data == "builder:pdf":
            suggested = f"PDF_{int(time.time())}"
            self._builder_state[chat_id] = {
                "active": True,
                "type": "pdf",
                "step": "name",
                "suggested_name": suggested
            }
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"✅ Usar: {suggested}", callback_data="builder:use_suggested")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="builder:cancel")]
            ])
            
            await context.bot.send_message(
                chat_id=chat_id,
                text="🧰 *Crear Skill PDF*\n\n¿Qué nombre le ponemos?",
                parse_mode="Markdown",
                reply_markup=kb
            )
            return

        if data == "builder:use_suggested":
            bs = self._builder_state.get(chat_id)
            if bs:
                bs["name"] = bs.get("suggested_name", "MiPDF")
                bs["step"] = "content"
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📝 Escribe el contenido del PDF:"
                )
            return

        if data == "builder:cancel":
            self._builder_state.pop(chat_id, None)
            await context.bot.send_message(chat_id=chat_id, text="❌ Cancelado.")
            return

    async def _handle_builder_step(
        self,
        chat_id: int,
        text: str,
        context: ContextTypes.DEFAULT_TYPE,
        bs: dict
    ) -> None:
        """Manejar pasos del builder wizard"""
        step = bs.get("step")
        builder_type = bs.get("type")

        if step == "name":
            bs["name"] = text.strip() or "MiSkill"
            bs["step"] = "content"
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Nombre: *{bs['name']}*\n\n📝 Ahora escribe el contenido:",
                parse_mode="Markdown"
            )
            return

        if step == "content":
            bs["content"] = text
            bs["step"] = "folder"
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📄 Documentos", callback_data="builder:folder:documents")],
                [InlineKeyboardButton("⬇️ Descargas", callback_data="builder:folder:downloads")],
                [InlineKeyboardButton("🖥️ Escritorio", callback_data="builder:folder:desktop")],
            ])
            
            await context.bot.send_message(
                chat_id=chat_id,
                text="📂 ¿Dónde guardar el archivo?",
                reply_markup=kb
            )
            return

        if step == "folder":
            # Esperar selección de carpeta por callback
            return

    # =========================================================================
    # MANEJO DE DOCUMENTOS
    # =========================================================================

    async def _on_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar documentos subidos"""
        chat_id = update.effective_chat.id
        
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            return

        if not self._admin_enabled.get(chat_id):
            return

        if not self._vault_waiting_zip.get(chat_id):
            return

        doc = update.message.document
        if not doc or not doc.file_name:
            await context.bot.send_message(chat_id=chat_id, text="Archivo inválido.")
            return

        if not doc.file_name.lower().endswith(".zip"):
            await context.bot.send_message(chat_id=chat_id, text="Solo se aceptan archivos .zip")
            return

        self._vault_waiting_zip[chat_id] = False

        # Descargar archivo
        import tempfile
        tmp_dir = Path(tempfile.gettempdir())
        local_path = tmp_dir / f"{int(time.time())}_{doc.file_name}"

        try:
            f = await doc.get_file()
            await f.download_to_drive(custom_path=str(local_path))
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error descargando: {e}")
            return

        # Staging en vault
        try:
            item = vault.stage_zip(local_path, chat_id=chat_id)
            self._vault_staged_zip[chat_id] = str(item.zip_path)

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🧪 Validar", callback_data="vault:simulate")],
                [InlineKeyboardButton("🗑️ Eliminar", callback_data="vault:delete")],
            ])

            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ Skill recibida. ¿Qué hacer?",
                reply_markup=kb
            )
        except Exception as e:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {e}")

    # =========================================================================
    # EVENTOS DEL BUS
    # =========================================================================

    async def _on_user_speak(self, data: Dict[str, Any]) -> None:
        """Handler para eventos user.SPEAK"""
        msg = (data or {}).get("message")
        if msg:
            await self._send_to_all(str(msg))

    async def _on_user_ui_message(self, data: Dict[str, Any]) -> None:
        """Handler para eventos user.UI_MESSAGE"""
        msg = (data or {}).get("message")
        if msg:
            await self._send_to_all(str(msg))

    async def _on_retry_available(self, data: Dict[str, Any]) -> None:
        """Handler para skill.RETRY_AVAILABLE"""
        if self.app is None:
            return

        session_id = (data or {}).get("session_id")
        if not session_id:
            return

        # Notificar a chats sobre retry disponible
        for chat_id in self._chat_ids:
            if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
                continue
            
            try:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Reintentar", callback_data=f"retry:{session_id}")]
                ])
                await self.app.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Una skill falló. ¿Quieres reintentar?",
                    reply_markup=kb
                )
            except Exception:
                pass

    async def _send_to_all(self, text: str) -> None:
        """Enviar mensaje a todos los chats activos"""
        if not text or self.app is None:
            return

        targets = list(self._chat_ids)
        if self._allowed_chat_ids is not None:
            targets = [cid for cid in targets if cid in self._allowed_chat_ids]

        for chat_id in targets:
            try:
                await self.app.bot.send_message(chat_id=chat_id, text=str(text)[:4000])
            except Exception:
                pass


# Instancia global para importación
_telegram_service: Optional[TelegramBotService] = None


def init_telegram_bot(token: str) -> TelegramBotService:
    """Inicializar servicio de Telegram"""
    global _telegram_service
    _telegram_service = TelegramBotService(token)
    return _telegram_service


def get_telegram_bot() -> Optional[TelegramBotService]:
    """Obtener instancia del servicio"""
    return _telegram_service
