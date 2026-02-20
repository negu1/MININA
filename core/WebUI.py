"""
MININA WebUI - Compatibility Layer
==================================
Este archivo proporciona compatibilidad hacia atrás con el código existente.
La nueva implementación modular está en core/webui/.

MIGRACIÓN:
- Antiguo: from core.WebUI import run_web_server
- Nuevo: from core.webui import create_app, run_web_server

DEPRECATED: Este archivo será removido en versión 2.0
"""
import warnings
import sys
from pathlib import Path

# Emit deprecation warning
warnings.warn(
    "core.WebUI está deprecado. Use core.webui.create_app() para la nueva API modular. "
    "Este archivo será removido en MININA v2.0",
    DeprecationWarning,
    stacklevel=2
)

# Import from new modular structure
from core.webui import create_app, run_web_server
from core.webui.state import get_state_manager

# Re-export for compatibility
__all__ = ['create_app', 'run_web_server', 'start_web_server_background', 'app']

# Lazy app creation - only when accessed
_app = None
def app():
    global _app
    if _app is None:
        _app = create_app()
    return _app

def start_web_server_background(host: str = "127.0.0.1", port: int = 8897):
    """
    Start web server in background (compatibility function).
    
    DEPRECATED: Use asyncio.create_task(run_web_server()) instead.
    """
    warnings.warn(
        "start_web_server_background está deprecado. "
        "Use asyncio.create_task(run_web_server()) directamente.",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        from core.config import get_settings
        settings = get_settings()
        host = host or settings.WEBUI_HOST
        port = int(port or settings.WEBUI_PORT)
    except Exception:
        pass
    try:
        import asyncio
        loop = asyncio.get_running_loop()
        loop.create_task(run_web_server(host=host, port=port))
    except RuntimeError:
        pass


# Legacy state management (for compatibility)
# These are now managed by StateManager in core.webui.state
ui_state = {
    "voice_active": False,
    "current_path": "",
    "llm_status": {},
    "last_actions": [],
    "system_status": "online"
}

ws_connections = []


# Legacy broadcast function (redirects to new implementation)
async def broadcast_message(message: dict):
    """
    Broadcast message to WebSocket clients (compatibility function).
    
    DEPRECATED: Use StateManager.ws_manager.broadcast() instead.
    """
    manager = get_state_manager()
    await manager.ws_manager.broadcast(message)
