"""
Logs Router
===========
Endpoints para visualización de logs y estado del sistema.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from core.logging_config import get_logger
from core.SystemWatchdog import watchdog
from core.webui.decorators import handle_route_errors
import psutil

logger = get_logger("MININA.WebUI.Logs")
router = APIRouter()


@router.get("/system")
@handle_route_errors("MININA.WebUI.Logs")
async def get_system_status() -> Dict[str, Any]:
    """Get system status information."""
    # CPU usage (non-blocking)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    
    # Disk usage
    disk = psutil.disk_usage('/')
    
    # Process info
    process = psutil.Process()
    
    return {
        "success": True,
        "cpu": {
            "percent": cpu_percent,
            "count": psutil.cpu_count()
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        },
        "disk": {
            "total": disk.total,
            "free": disk.free,
            "used": disk.used,
            "percent": (disk.used / disk.total) * 100
        },
        "process": {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent()
        }
    }


@router.get("/services")
@handle_route_errors("MININA.WebUI.Logs")
async def get_services_status() -> Dict[str, Any]:
    """Get status of monitored services."""
    services = []
    for name, info in watchdog.services.items():
        services.append({
            "name": name,
            "status": info.status.value,
            "last_heartbeat": info.last_heartbeat,
            "restart_count": info.restart_count,
            "last_error": info.last_error
        })
    
    return {
        "success": True,
        "services": services,
        "count": len(services)
    }


@router.get("/recent")
@handle_route_errors("MININA.WebUI.Logs")
async def get_recent_logs(limit: int = 100) -> Dict[str, Any]:
    """Get recent log entries."""
    # TODO: Implementar almacenamiento de logs para recuperación
    # Por ahora retornar mensaje informativo
    return {
        "success": True,
        "logs": [],
        "count": 0,
        "message": "Log storage not yet implemented. Configure LOG_FILE in .env to enable.",
        "config_hint": "Set LOG_FILE=data/minina.log to store logs"
    }
