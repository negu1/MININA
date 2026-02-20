#!/usr/bin/env python3
"""
MININA - Launcher Directo
Inicia solo WebUI sin verificaciones
"""

import asyncio
import sys
from pathlib import Path

# Asegurar que core esté en path
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    """Inicia WebUI directamente"""
    print("🚀 MININA - Iniciando WebUI...")
    print("")
    
    try:
        from core.WebUI import run_web_server
        from core.config import get_settings
        settings = get_settings()
        print(f"🌐 WebUI iniciando en http://{settings.WEBUI_HOST}:{settings.WEBUI_PORT}")
        print("📱 Abre tu navegador en esa dirección")
        print("")
        await run_web_server(host=settings.WEBUI_HOST, port=settings.WEBUI_PORT)
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Instala dependencias: pip install fastapi uvicorn")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 MININA detenida")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Detenido por usuario")
