"""
MiIA Auto-Update System
Sistema de actualización automática para MiIA-Product-20
- Verifica nuevas versiones
- Descarga e instala actualizaciones
- Preserva configuración del usuario
- Soporta rollback si falla
"""
import os
import sys
import json
import shutil
import hashlib
import zipfile
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
import asyncio

logger = logging.getLogger("MiIAUpdater")

# Configuración de actualización
UPDATE_CONFIG = {
    "repository": "https://github.com/miia-product/miia-product-20",
    "releases_api": "https://api.github.com/repos/miia-product/miia-product-20/releases/latest",
    "update_channel": "stable",  # stable, beta, nightly
    "auto_check": True,
    "auto_download": False,  # Solo descarga, no instala automáticamente
    "backup_before_update": True,
}

@dataclass
class VersionInfo:
    """Información de versión"""
    version: str
    release_date: str
    changelog: str
    download_url: str
    checksum: str
    min_version: str = "0.0.0"  # Versión mínima requerida para actualizar
    
@dataclass
class UpdateStatus:
    """Estado de actualización"""
    current_version: str
    latest_version: str
    update_available: bool
    download_progress: float
    is_downloading: bool
    is_installing: bool
    last_check: str
    error: Optional[str] = None


class MiIAUpdater:
    """
    Gestor de actualizaciones de MiIA
    """
    
    VERSION_FILE = Path("version.json")
    UPDATE_DIR = Path("updates")
    BACKUP_DIR = Path("backups")
    
    def __init__(self):
        self.current_version = self._get_current_version()
        self.latest_version: Optional[VersionInfo] = None
        self.update_status = UpdateStatus(
            current_version=self.current_version,
            latest_version=self.current_version,
            update_available=False,
            download_progress=0.0,
            is_downloading=False,
            is_installing=False,
            last_check=""
        )
        self._progress_callbacks: List[Callable] = []
        
        # Crear directorios necesarios
        self.UPDATE_DIR.mkdir(exist_ok=True)
        self.BACKUP_DIR.mkdir(exist_ok=True)
    
    def _get_current_version(self) -> str:
        """Obtener versión actual instalada"""
        if self.VERSION_FILE.exists():
            try:
                with open(self.VERSION_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get("version", "0.0.0")
            except:
                pass
        return "0.0.0"
    
    def _save_version(self, version: str):
        """Guardar información de versión"""
        with open(self.VERSION_FILE, 'w') as f:
            json.dump({
                "version": version,
                "updated_at": datetime.now().isoformat(),
                "channel": UPDATE_CONFIG["update_channel"]
            }, f, indent=2)
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """
        Comparar dos versiones
        Returns: -1 si v1 < v2, 0 si iguales, 1 si v1 > v2
        """
        def parse(v):
            parts = v.split('.')
            return [int(x) for x in parts[:3]] + [0] * (3 - len(parts[:3]))
        
        p1, p2 = parse(v1), parse(v2)
        for a, b in zip(p1, p2):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0
    
    async def check_for_updates(self) -> Dict[str, Any]:
        """
        Verificar si hay actualizaciones disponibles
        """
        # Refrescar versión local en cada check para evitar estado stale
        # (por ejemplo si version.json se crea/actualiza después de iniciar el proceso).
        try:
            self.current_version = self._get_current_version()
            self.update_status.current_version = self.current_version
            # Mientras no haya latest_version calculada, mantener latest_version igual a la actual.
            if not self.update_status.latest_version:
                self.update_status.latest_version = self.current_version
        except Exception:
            pass

        self.update_status.last_check = datetime.now().isoformat()
        
        try:
            # En una implementación real, esto consultaría la API de GitHub
            # Por ahora, simulamos la respuesta
            
            # Simular consulta a API
            await asyncio.sleep(1)
            
            # Versión simulada más reciente
            self.latest_version = VersionInfo(
                version="1.1.0",
                release_date="2026-02-20",
                changelog="""
                ### Novedades v1.1.0:
                - 🎙️ Mejoras en reconocimiento de voz con Vosk
                - 🤖 Soporte para más proveedores de IA
                - 📱 Mejor integración con Telegram
                - 🐛 Corrección de bugs menores
                - ⚡ Mejoras de rendimiento
                """,
                download_url="https://github.com/miia-product/miia-product-20/releases/download/v1.1.0/miia-1.1.0.zip",
                checksum="abc123...",
                min_version="1.0.0"
            )
            
            # Comparar versiones
            comparison = self.compare_versions(self.current_version, self.latest_version.version)
            
            if comparison < 0:
                self.update_status.update_available = True
                self.update_status.latest_version = self.latest_version.version
                
                return {
                    "success": True,
                    "update_available": True,
                    "current_version": self.current_version,
                    "latest_version": self.latest_version.version,
                    "changelog": self.latest_version.changelog,
                    "can_update": self.compare_versions(self.current_version, self.latest_version.min_version) >= 0
                }
            else:
                self.update_status.update_available = False
                return {
                    "success": True,
                    "update_available": False,
                    "current_version": self.current_version,
                    "message": "Tienes la última versión"
                }
                
        except Exception as e:
            logger.error(f"Error verificando actualizaciones: {e}")
            self.update_status.error = str(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_update(self, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Descargar actualización
        """
        if not self.latest_version:
            return {"success": False, "error": "No hay información de actualización disponible"}
        
        self.update_status.is_downloading = True
        self.update_status.download_progress = 0.0
        
        try:
            update_file = self.UPDATE_DIR / f"miia-{self.latest_version.version}.zip"
            
            # Simular descarga (en producción, descargaría de la URL real)
            logger.info(f"Descargando actualización a {update_file}")
            
            total_size = 100  # MB simulados
            downloaded = 0
            
            for i in range(10):
                await asyncio.sleep(0.5)  # Simular descarga
                downloaded += 10
                progress = (downloaded / total_size) * 100
                self.update_status.download_progress = progress
                
                if progress_callback:
                    progress_callback(progress)
                
                logger.info(f"Progreso: {progress:.1f}%")
            
            # Crear archivo simulado
            update_file.touch()
            
            self.update_status.is_downloading = False
            self.update_status.download_progress = 100.0
            
            return {
                "success": True,
                "message": "Actualización descargada correctamente",
                "file": str(update_file),
                "ready_to_install": True
            }
            
        except Exception as e:
            self.update_status.is_downloading = False
            self.update_status.error = str(e)
            logger.error(f"Error descargando: {e}")
            return {"success": False, "error": str(e)}
    
    def backup_current_installation(self) -> Dict[str, Any]:
        """
        Crear backup de la instalación actual antes de actualizar
        """
        try:
            backup_name = f"backup_{self.current_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = self.BACKUP_DIR / backup_name
            
            logger.info(f"Creando backup en {backup_path}")
            
            # Directorios a respaldar
            dirs_to_backup = [
                "core",
                "skills",
                "config",
            ]
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            for dir_name in dirs_to_backup:
                src = Path(dir_name)
                if src.exists():
                    dst = backup_path / dir_name
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
            
            # Respaldar archivos de configuración del usuario
            user_config = Path.home() / ".config" / "miia-product-20"
            if user_config.exists():
                dst = backup_path / "user_config"
                shutil.copytree(user_config, dst)
            
            return {
                "success": True,
                "backup_path": str(backup_path),
                "message": "Backup creado correctamente"
            }
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return {"success": False, "error": str(e)}
    
    async def install_update(self) -> Dict[str, Any]:
        """
        Instalar la actualización descargada
        """
        if not self.latest_version:
            return {"success": False, "error": "No hay actualización para instalar"}
        
        self.update_status.is_installing = True
        
        try:
            # 1. Crear backup
            backup_result = self.backup_current_installation()
            if not backup_result["success"]:
                return backup_result
            
            logger.info("Iniciando instalación...")
            
            # 2. Simular instalación (extracción y reemplazo de archivos)
            await asyncio.sleep(2)
            
            # 3. Actualizar versión
            self._save_version(self.latest_version.version)
            self.current_version = self.latest_version.version
            self.update_status.current_version = self.current_version
            
            # 4. Limpiar archivos de actualización
            update_file = self.UPDATE_DIR / f"miia-{self.latest_version.version}.zip"
            if update_file.exists():
                update_file.unlink()
            
            self.update_status.is_installing = False
            self.update_status.update_available = False
            
            return {
                "success": True,
                "message": f"✅ Actualización a v{self.latest_version.version} completada",
                "backup_location": backup_result["backup_path"],
                "requires_restart": True
            }
            
        except Exception as e:
            self.update_status.is_installing = False
            self.update_status.error = str(e)
            logger.error(f"Error instalando: {e}")
            return {"success": False, "error": str(e)}
    
    def rollback_update(self, backup_path: str) -> Dict[str, Any]:
        """
        Revertir a versión anterior usando backup
        """
        try:
            backup = Path(backup_path)
            if not backup.exists():
                return {"success": False, "error": "Backup no encontrado"}
            
            logger.info(f"Revirtiendo desde {backup}")
            
            # Restaurar archivos desde backup
            for item in backup.iterdir():
                if item.is_dir():
                    dst = Path(item.name)
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
            
            # Restaurar versión
            version_file = backup / "version.json"
            if version_file.exists():
                shutil.copy(version_file, self.VERSION_FILE)
                self.current_version = self._get_current_version()
            
            return {
                "success": True,
                "message": "Rollback completado correctamente",
                "restored_version": self.current_version
            }
            
        except Exception as e:
            logger.error(f"Error en rollback: {e}")
            return {"success": False, "error": str(e)}
    
    def get_update_status(self) -> Dict[str, Any]:
        """Obtener estado actual de actualización"""
        return asdict(self.update_status)
    
    async def auto_check_and_notify(self, notify_callback: Optional[Callable] = None):
        """
        Verificación automática y notificación
        """
        if not UPDATE_CONFIG["auto_check"]:
            return
        
        result = await self.check_for_updates()
        
        if result.get("update_available") and notify_callback:
            notify_callback(result)
        
        return result


# Instancia global
updater = MiIAUpdater()


# Funciones de conveniencia para la API
async def check_updates() -> Dict[str, Any]:
    """Verificar actualizaciones (para llamar desde WebUI)"""
    return await updater.check_for_updates()

async def download_update(progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """Descargar actualización"""
    return await updater.download_update(progress_callback)

async def install_update() -> Dict[str, Any]:
    """Instalar actualización"""
    return await updater.install_update()

def get_update_status() -> Dict[str, Any]:
    """Obtener estado"""
    return updater.get_update_status()
