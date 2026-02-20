#!/usr/bin/env python3
"""
MININA - Launcher Principal
Inicia UI Local PyQt5 y servicios esenciales
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MININA-Launcher")


class _RedactTelegramTokenFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            if isinstance(msg, str) and "/bot" in msg:
                record.msg = re.sub(r"/bot[0-9]+:[A-Za-z0-9_-]+", "/bot<redacted>", msg)
                record.args = ()
        except Exception:
            pass
        return True


try:
    import re

    _flt = _RedactTelegramTokenFilter()
    root_logger = logging.getLogger()
    for h in list(getattr(root_logger, "handlers", []) or []):
        try:
            h.addFilter(_flt)
        except Exception:
            pass

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
except Exception:
    pass

# Cargar variables de entorno
load_dotenv()


def _kill_other_minina_instances() -> None:
    """Opción B: si ya hay otra instancia de MININA corriendo, la termina y continúa con la nueva."""
    try:
        import psutil

        this_pid = os.getpid()
        launcher_path = str((Path(__file__).resolve())).lower()
        for p in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
            try:
                pid = int(p.info.get("pid") or 0)
                if not pid or pid == this_pid:
                    continue

                cmd = p.info.get("cmdline") or []
                cmd_str = " ".join([str(x) for x in cmd]).lower()
                if "iniciar_minina.py" not in cmd_str:
                    continue

                # Evitar matar otros scripts que casualmente contienen el texto; requerir match con la ruta real si es posible
                if launcher_path not in cmd_str and "\\minina\\iniciar_minina.py" not in cmd_str:
                    continue

                try:
                    psutil.Process(pid).terminate()
                except Exception:
                    pass
            except Exception:
                continue

        # Dar un momento para liberar getUpdates y recursos
        time.sleep(0.3)
    except Exception:
        pass

# Verificar Python version
if sys.version_info < (3, 9):
    print("❌ Error: Se requiere Python 3.9 o superior")
    sys.exit(1)


def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    required = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('python-telegram-bot', 'telegram'),
        ('python-dotenv', 'dotenv'),
        ('Pillow', 'PIL'),
        ('psutil', 'psutil'),
        ('cryptography', 'cryptography'),
        ('aiohttp', 'aiohttp')
    ]
    
    missing = []
    for package_name, import_name in required:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    if missing:
        print("❌ Faltan dependencias:")
        for m in missing:
            print(f"   - {m}")
        print("\n💡 Instala con: pip install -r requirements.txt")
        return False
    
    return True


async def start_ui_local(stop_event: asyncio.Event):
    """Inicia la UI Local PyQt5"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from core.ui.main_window import MainWindow
    import sys
    
    logger.info("🖥️  Iniciando MININA UI Local")
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("MININA")
    app.setApplicationVersion("3.0.0")
    
    # Crear ventana principal
    window = MainWindow()
    window.show()
    
    logger.info("✅ UI Local iniciada")
    
    # Ejecutar loop de Qt
    while window.isVisible() and not stop_event.is_set():
        app.processEvents()
        await asyncio.sleep(0.01)
    
    logger.info("🛑 UI Local cerrada")
    stop_event.set()


async def start_telegram(stop_event: asyncio.Event):
    """Inicia el bot de Telegram si está configurado"""
    announced_waiting = False

    while not stop_event.is_set():
        token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()

        # Fallback: leer credenciales seguras (UI nueva / BotConfigManager)
        if not token:
            try:
                from core.llm_extension import credential_store

                token = (credential_store.get_api_key("telegram_bot_token") or "").strip()
                chat_id = (credential_store.get_api_key("telegram_chat_id") or "").strip()
                if token:
                    os.environ["TELEGRAM_BOT_TOKEN"] = token
                if chat_id and not (os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or "").strip():
                    os.environ["TELEGRAM_ALLOWED_CHAT_ID"] = chat_id
            except Exception as e:
                logger.warning(f"No se pudo leer SecureCredentialStore de Telegram: {e}")

        # Fallback: leer config guardada por la UI
        if not token:
            try:
                cfg_path = Path(__file__).parent / "data" / "telegram_bot_config.json"
                if cfg_path.exists():
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    token = (cfg.get("token") or "").strip()
                    chat_id = (cfg.get("chat_id") or "").strip()
                    if token:
                        os.environ["TELEGRAM_BOT_TOKEN"] = token
                    if chat_id and not (os.environ.get("TELEGRAM_ALLOWED_CHAT_ID") or "").strip():
                        os.environ["TELEGRAM_ALLOWED_CHAT_ID"] = chat_id
            except Exception as e:
                logger.warning(f"No se pudo leer telegram_bot_config.json: {e}")

        if token and not stop_event.is_set():
            from core.TelegramBot import run_telegram_bot
            logger.info("📱 Iniciando Bot de Telegram")
            await run_telegram_bot(stop_event)
            return

        if not announced_waiting:
            logger.info("ℹ️  Telegram no configurado (opcional). Esperando configuración desde la UI...")
            announced_waiting = True

        await asyncio.sleep(5)

    logger.info("🛑 Telegram task finalizada")


async def main():
    """Función principal de inicio"""
    parser = argparse.ArgumentParser(description='MININA - Asistente Virtual')
    parser.add_argument('--ui-only', action='store_true', help='Solo UI Local')
    parser.add_argument('--telegram-only', action='store_true', help='Solo Telegram')
    args = parser.parse_args()
    
    print("🚀 MININA - Iniciando...\n")

    # Evitar múltiples instancias (modo B: mata la anterior)
    _kill_other_minina_instances()
    
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ Dependencias verificadas\n")
    
    # Iniciar servicios
    tasks = []

    stop_event = asyncio.Event()
    
    if args.ui_only:
        tasks.append(start_ui_local(stop_event))
    elif args.telegram_only:
        tasks.append(start_telegram(stop_event))
    else:
        tasks.append(start_ui_local(stop_event))
        tasks.append(start_telegram(stop_event))
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo MININA...")


if __name__ == "__main__":
    asyncio.run(main())
