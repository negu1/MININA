#!/usr/bin/env python3
"""
MININA - Launcher Principal
Inicia WebUI y servicios esenciales
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MININA-Launcher")

# Cargar variables de entorno
load_dotenv()

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


async def start_webui():
    """Inicia el servidor WebUI"""
    from core.WebUI import run_web_server
    from core.config import get_settings
    settings = get_settings()
    logger.info(f"🌐 Iniciando MININA WebUI en http://{settings.WEBUI_HOST}:{settings.WEBUI_PORT}")
    await run_web_server(host=settings.WEBUI_HOST, port=settings.WEBUI_PORT)


async def start_telegram():
    """Inicia el bot de Telegram si está configurado"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.info("ℹ️  Telegram no configurado (opcional)")
        return
    
    from core.TelegramBot import run_telegram_bot
    logger.info("📱 Iniciando Bot de Telegram")
    await run_telegram_bot()


async def main():
    """Función principal de inicio"""
    parser = argparse.ArgumentParser(description='MININA - Asistente Virtual')
    parser.add_argument('--webui-only', action='store_true', help='Solo WebUI')
    parser.add_argument('--telegram-only', action='store_true', help='Solo Telegram')
    args = parser.parse_args()
    
    print("🚀 MININA - Iniciando...\n")
    
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ Dependencias verificadas\n")
    
    # Iniciar servicios
    tasks = []
    
    if args.webui_only:
        tasks.append(start_webui())
    elif args.telegram_only:
        tasks.append(start_telegram())
    else:
        tasks.append(start_webui())
        tasks.append(start_telegram())
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo MININA...")


if __name__ == "__main__":
    asyncio.run(main())
