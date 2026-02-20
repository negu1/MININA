"""
MININA v3.0 - Telegram Bot Modo Espejo
Bot simplificado: recibe notificaciones y permite acceso a works
NO permite crear skills (eso es solo en UI)
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

from core.ui.api_client import api_client
from core.TelegramNotificationService import notification_service

logger = logging.getLogger("TelegramBotMirror")


def _parse_allowed_chat_ids() -> Optional[set[int]]:
    """Parsear IDs de chat permitidos"""
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


class TelegramBotMirror:
    """
    Bot de Telegram en modo 'Espejo'
    - Recibe notificaciones de MININA
    - Permite acceder a works generados
    - Configuración de notificaciones
    - NO crea skills (eso es UI)
    """
    
    def __init__(self, token: str):
        self.token = token
        self.app: Optional[Application] = None
        self._chat_ids: set[int] = set()
        self._allowed_chat_ids: Optional[set[int]] = _parse_allowed_chat_ids()
        
        # Registrar este bot en el servicio de notificaciones
        notification_service.set_bot(self)

    async def start(self) -> None:
        """Iniciar el bot"""
        if self.app is not None:
            return

        self.app = Application.builder().token(self.token).build()

        # Comandos principales
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("menu", self._cmd_menu))
        self.app.add_handler(CommandHandler("works", self._cmd_works))
        self.app.add_handler(CommandHandler("config", self._cmd_config))
        self.app.add_handler(CommandHandler("status", self._cmd_status))

        # Callbacks de botones
        self.app.add_handler(CallbackQueryHandler(self._on_callback))
        
        # Mensajes de texto (solo para config inicial)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)

        logger.info("Telegram Bot Mirror iniciado")

    async def stop(self) -> None:
        """Detener el bot"""
        if self.app is None:
            return
        try:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        except Exception:
            pass
        self.app = None

    async def send_message(self, chat_id: int, text: str, **kwargs) -> None:
        """Método para enviar mensajes (usado por NotificationService)"""
        if self.app:
            await self.app.bot.send_message(chat_id=chat_id, text=text, **kwargs)

    async def send_document(self, chat_id: int, document, **kwargs) -> None:
        """Método para enviar documentos"""
        if self.app:
            await self.app.bot.send_document(chat_id=chat_id, document=document, **kwargs)

    # =========================================================================
    # COMANDOS
    # =========================================================================

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /start - Bienvenida y registro"""
        chat_id = update.effective_chat.id

        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="🔒 Acceso no autorizado.")
            return

        self._chat_ids.add(chat_id)
        
        # Crear configuración por defecto
        config = notification_service.get_or_create_config(chat_id)

        welcome_text = f"""🤖 *¡Bienvenido a MININA v3.0!*

Este es tu bot de *notificaciones y acceso a works*.

📱 *Modo Espejo:*
Trabaja en la interfaz de MININA en tu PC, y recibe aquí:
• ✅ Avisos de works completados
• 📄 Acceso a tus archivos generados
• ⚙️ Configuración de notificaciones

*Menú principal:*
📄 /works - Ver y descargar works
⚙️ /config - Configurar notificaciones
❓ /help - Ayuda

_Tus notificaciones están: {'✅ Activadas' if config.enabled else '❌ Desactivadas'}_"""

        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode="Markdown"
        )
        
        await self._show_main_menu(chat_id, context)

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /help - Ayuda"""
        chat_id = update.effective_chat.id
        
        help_text = """🤖 *MININA Bot - Ayuda*

*Comandos:*
/menu - Mostrar menú principal
/works - Ver works generados
/config - Configurar notificaciones
/status - Estado del sistema

*¿Cómo funciona?*
1. Trabaja con MININA en tu PC
2. El bot te avisa cuando hay nuevos works
3. Descarga tus archivos desde aquí

*Configuración de Notificaciones:*
• ✅ Works completados
• 📤 Enviar works automáticamente
• ⚠️ Errores del sistema

*Nota:* Para crear skills o usar funciones avanzadas, usa la interfaz de MININA en tu PC.

💡 *Tip:* Usa /config para personalizar qué notificaciones recibes."""

        await context.bot.send_message(
            chat_id=chat_id,
            text=help_text,
            parse_mode="Markdown"
        )

    async def _cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /menu - Mostrar menú principal"""
        chat_id = update.effective_chat.id
        await self._show_main_menu(chat_id, context)

    async def _cmd_works(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /works - Ver works disponibles"""
        chat_id = update.effective_chat.id
        
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="🔒 Acceso no autorizado.")
            return

        await self._show_works_list(chat_id, context)

    async def _cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /config - Configurar notificaciones"""
        chat_id = update.effective_chat.id
        
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="🔒 Acceso no autorizado.")
            return

        await self._show_config_menu(chat_id, context)

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Comando /status - Ver estado"""
        chat_id = update.effective_chat.id
        
        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            await context.bot.send_message(chat_id=chat_id, text="🔒 Acceso no autorizado.")
            return

        try:
            health = api_client.health_check()
            works = api_client.get_works()
            stats = notification_service.get_stats()
            
            status_text = f"""📊 *Estado de MININA*

✅ Backend: {'Online' if health else 'Offline'}
📄 Works totales: {len(works)}
👥 Usuarios con notificaciones: {stats['enabled']}

*Tu configuración:*
• Notificaciones: {'✅ Activas' if notification_service.get_or_create_config(chat_id).enabled else '❌ Inactivas'}
• Auto-envío: {'✅ Sí' if notification_service.get_or_create_config(chat_id).notify_auto_send_works else '❌ No'}

💡 Usa /config para cambiar preferencias."""

            await context.bot.send_message(
                chat_id=chat_id,
                text=status_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ Error: {str(e)}"
            )

    # =========================================================================
    # MENÚS
    # =========================================================================

    async def _show_main_menu(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar menú principal"""
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Ver Works", callback_data="menu:works")],
            [InlineKeyboardButton("⚙️ Configuración", callback_data="menu:config")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="menu:help")],
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text="🏠 *Menú Principal*\n\n¿Qué quieres hacer?",
            parse_mode="Markdown",
            reply_markup=kb
        )

    async def _show_works_list(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar lista de works"""
        try:
            works = api_client.get_works()
            
            if not works:
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refrescar", callback_data="works:refresh")],
                    [InlineKeyboardButton("🏠 Menú", callback_data="menu:main")]
                ])
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="📭 *No hay works aún*\n\nTrabaja en MININA desde tu PC para generar archivos. ¡Te avisaré aquí cuando estén listos!",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
                return

            # Crear botones para cada work
            rows = []
            for work in works[:15]:  # Mostrar últimos 15
                work_id = work.get('id', 'unknown')
                work_name = work.get('original_name', 'Sin nombre')[:25]
                rows.append([InlineKeyboardButton(
                    f"📄 {work_name}",
                    callback_data=f"work:download:{work_id}"
                )])

            rows.append([InlineKeyboardButton("🔄 Refrescar", callback_data="works:refresh")])
            rows.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="menu:main")])
            
            kb = InlineKeyboardMarkup(rows)

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📄 *Tus Works ({len(works)} total)*\n\nToca para descargar:",
                parse_mode="Markdown",
                reply_markup=kb
            )
            
        except Exception as e:
            logger.error(f"Error mostrando works: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Error: {str(e)}"
            )

    async def _show_config_menu(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Mostrar menú de configuración"""
        config = notification_service.get_or_create_config(chat_id)
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"{'✅' if config.enabled else '❌'} Notificaciones Activas",
                callback_data="config:toggle_enabled"
            )],
            [InlineKeyboardButton(
                f"{'✅' if config.notify_works_completed else '❌'} Avisar Works Completados",
                callback_data="config:toggle_works"
            )],
            [InlineKeyboardButton(
                f"{'✅' if config.notify_auto_send_works else '❌'} Enviar Works Automáticamente",
                callback_data="config:toggle_autosend"
            )],
            [InlineKeyboardButton(
                f"{'✅' if config.notify_errors else '❌'} Avisar Errores",
                callback_data="config:toggle_errors"
            )],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="menu:main")]
        ])

        config_text = f"""⚙️ *Configuración de Notificaciones*

Toca para activar/desactivar:

_Estado actual:_
• Notificaciones: {'✅ Activadas' if config.enabled else '❌ Desactivadas'}
• Avisar works: {'✅ Sí' if config.notify_works_completed else '❌ No'}
• Auto-envío: {'✅ Sí' if config.notify_auto_send_works else '❌ No'}
• Avisar errores: {'✅ Sí' if config.notify_errors else '❌ No'}

💡 Con *auto-envío* activado, recibirás los archivos automáticamente sin tener que descargarlos."""

        await context.bot.send_message(
            chat_id=chat_id,
            text=config_text,
            parse_mode="Markdown",
            reply_markup=kb
        )

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

        if self._allowed_chat_ids is not None and chat_id not in self._allowed_chat_ids:
            return

        data = (query.data or "").strip()

        # Menú principal
        if data == "menu:main":
            await self._show_main_menu(chat_id, context)
            return

        if data == "menu:works":
            await self._show_works_list(chat_id, context)
            return

        if data == "menu:config":
            await self._show_config_menu(chat_id, context)
            return

        if data == "menu:help":
            await self._cmd_help(update, context)
            return

        # Works
        if data == "works:refresh":
            await self._show_works_list(chat_id, context)
            return

        if data.startswith("work:download:"):
            work_id = data.split("work:download:", 1)[1]
            await self._download_and_send_work(chat_id, work_id, context)
            return

        # Configuración
        if data == "config:toggle_enabled":
            config = notification_service.get_or_create_config(chat_id)
            notification_service.update_config(chat_id, enabled=not config.enabled)
            await self._show_config_menu(chat_id, context)
            return

        if data == "config:toggle_works":
            config = notification_service.get_or_create_config(chat_id)
            notification_service.update_config(chat_id, notify_works_completed=not config.notify_works_completed)
            await self._show_config_menu(chat_id, context)
            return

        if data == "config:toggle_autosend":
            config = notification_service.get_or_create_config(chat_id)
            notification_service.update_config(chat_id, notify_auto_send_works=not config.notify_auto_send_works)
            await self._show_config_menu(chat_id, context)
            return

        if data == "config:toggle_errors":
            config = notification_service.get_or_create_config(chat_id)
            notification_service.update_config(chat_id, notify_errors=not config.notify_errors)
            await self._show_config_menu(chat_id, context)
            return

    async def _download_and_send_work(self, chat_id: int, work_id: str, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Descargar y enviar un work al usuario"""
        try:
            # Obtener works
            works = api_client.get_works()
            work = None
            for w in works:
                if w.get('id') == work_id:
                    work = w
                    break

            if not work:
                await context.bot.send_message(chat_id=chat_id, text="❌ Work no encontrado.")
                return

            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏳ Descargando *{work.get('original_name')}*...",
                parse_mode="Markdown"
            )

            # Descargar archivo temporal
            import tempfile
            tmp_path = Path(tempfile.gettempdir()) / work.get('original_name', 'file')
            
            if api_client.download_work(work_id, tmp_path):
                # Enviar archivo
                with open(tmp_path, "rb") as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=f"📄 {work.get('original_name')}"
                    )
                
                # Limpiar
                tmp_path.unlink(missing_ok=True)
                
                # Mostrar menú de works de nuevo
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📄 Más Works", callback_data="menu:works")],
                    [InlineKeyboardButton("🏠 Menú", callback_data="menu:main")]
                ])
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ *Archivo enviado*",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            else:
                await context.bot.send_message(chat_id=chat_id, text="❌ Error descargando archivo.")
                
        except Exception as e:
            logger.error(f"Error enviando work: {e}")
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

    # =========================================================================
    # MENSAJES
    # =========================================================================

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Manejar mensajes de texto"""
        chat_id = update.effective_chat.id
        text = (update.message.text or "").strip().lower()

        if text in ("hola", "hi", "hello", "inicio", "menu"):
            await self._show_main_menu(chat_id, context)
            return

        # Respuesta por defecto
        await context.bot.send_message(
            chat_id=chat_id,
            text="🤖 Usa /menu para ver las opciones disponibles.\n\n📄 /works - Ver archivos\n⚙️ /config - Configurar notificaciones\n❓ /help - Ayuda"
        )


# Instancia global
_bot_mirror: Optional[TelegramBotMirror] = None


def init_mirror_bot(token: str) -> TelegramBotMirror:
    """Inicializar bot modo espejo"""
    global _bot_mirror
    _bot_mirror = TelegramBotMirror(token)
    return _bot_mirror


def get_mirror_bot() -> Optional[TelegramBotMirror]:
    """Obtener instancia del bot"""
    return _bot_mirror
