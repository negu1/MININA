"""
Backup Router
=============
Endpoints para sistema de backup.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from core.logging_config import get_logger
from core.BackupManager import BackupManager
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.Backup")
router = APIRouter()
backup_manager = BackupManager()


@router.get("/status")
@handle_route_errors("MININA.WebUI.Backup")
async def get_backup_status() -> Dict[str, Any]:
    """Get backup configuration status."""
    config = backup_manager.config
    return {
        "success": True,
        "enabled": config.auto_backup,
        "frequency": config.backup_frequency,
        "last_backup": config.last_backup,
        "next_backup": config.next_backup,
        "provider": config.provider,
        "max_backups": config.max_backups
    }


@router.post("/create")
@handle_route_errors("MININA.WebUI.Backup")
async def create_backup() -> Dict[str, Any]:
    """Create manual backup."""
    logger.info("Creating manual backup")
    result = await backup_manager.create_backup(manual=True)
    return result


@router.post("/configure")
@handle_route_errors("MININA.WebUI.Backup")
async def configure_backup(data: Dict[str, Any]) -> Dict[str, Any]:
    """Configure backup settings."""
    backup_manager.config.auto_backup = data.get("enabled", True)
    backup_manager.config.backup_frequency = data.get("frequency", "weekly")
    backup_manager.config.max_backups = data.get("max_backups", 5)
    backup_manager.config.provider = data.get("provider", "local")
    
    backup_manager.save_config()
    
    logger.info("Backup configuration updated")
    
    return {
        "success": True,
        "message": "Backup configuration updated"
    }


@router.get("/list")
@handle_route_errors("MININA.WebUI.Backup")
async def list_backups() -> Dict[str, Any]:
    """List available backups."""
    backup_dir = backup_manager.BACKUP_DIR
    backups = []
    
    if backup_dir.exists():
        for file in sorted(backup_dir.glob("*.zip"), reverse=True):
            try:
                backups.append({
                    "name": file.name,
                    "size": file.stat().st_size,
                    "created": file.stat().st_mtime
                })
            except (OSError, PermissionError):
                continue
    
    return {
        "success": True,
        "backups": backups,
        "count": len(backups)
    }
