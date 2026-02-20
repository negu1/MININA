#!/usr/bin/env python3
"""
MININA - Launcher Principal
Inicia UI Local PyQt5 y servicios esenciales
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


async def start_ui_local():
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
    while window.isVisible():
        app.processEvents()
        await asyncio.sleep(0.01)
    
    logger.info("🛑 UI Local cerrada")


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
    parser.add_argument('--ui-only', action='store_true', help='Solo UI Local')
    parser.add_argument('--telegram-only', action='store_true', help='Solo Telegram')
    args = parser.parse_args()
    
    print("🚀 MININA - Iniciando...\n")
    
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ Dependencias verificadas\n")
    
    # Iniciar servicios
    tasks = []
    
    if args.ui_only:
        tasks.append(start_ui_local())
    elif args.telegram_only:
        tasks.append(start_telegram())
    else:
        tasks.append(start_ui_local())
        tasks.append(start_telegram())
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo MININA...")


if __name__ == "__main__":
    asyncio.run(main())
