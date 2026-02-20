"""
Sistema de Auditoría General para MININA
Registra todas las ejecuciones de skills con retención de 30 días
"""
import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger("Auditoria")

AUDITORIA_PATH = Path("data/auditoria")
RETENTION_DAYS = 30

@dataclass
class RegistroAuditoria:
    id: str
    skill_name: str
    skill_id: str
    action: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: Optional[float]
    details: Dict[str, Any]
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AuditoriaManager:
    """Gestor centralizado de auditoría"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        AUDITORIA_PATH.mkdir(parents=True, exist_ok=True)
        self.registros: List[RegistroAuditoria] = []
        self._cargar_registros()
    
    def _get_file_path(self, date_str: str) -> Path:
        """Obtener ruta del archivo para una fecha específica"""
        return AUDITORIA_PATH / f"auditoria_{date_str}.json"
    
    def _cargar_registros(self):
        """Cargar registros de los últimos 30 días"""
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        
        for archivo in AUDITORIA_PATH.glob("auditoria_*.json"):
            try:
                fecha_str = archivo.stem.replace("auditoria_", "")
                fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
                
                if fecha < cutoff_date:
                    # Eliminar archivos antiguos
                    archivo.unlink()
                    logger.info(f"Eliminado registro antiguo: {archivo.name}")
                    continue
                
                with open(archivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for reg in data.get("registros", []):
                        self.registros.append(RegistroAuditoria(**reg))
                        
            except Exception as e:
                logger.error(f"Error cargando auditoría {archivo}: {e}")
        
        logger.info(f"Cargados {len(self.registros)} registros de auditoría")
    
    def _guardar_registros_dia(self, date_str: str):
        """Guardar registros de un día específico"""
        registros_dia = [r for r in self.registros if r.created_at.startswith(date_str)]
        
        if registros_dia:
            archivo = self._get_file_path(date_str)
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump({
                    "fecha": date_str,
                    "registros": [r.to_dict() for r in registros_dia],
                    "total": len(registros_dia)
                }, f, indent=2, ensure_ascii=False)
    
    def iniciar_registro(self, skill_name: str, skill_id: str, action: str, details: Dict = None) -> str:
        """Iniciar un nuevo registro de auditoría"""
        now = datetime.now()
        registro_id = f"{skill_id}_{now.strftime('%Y%m%d_%H%M%S')}_{int(time.time()*1000)%1000}"
        
        registro = RegistroAuditoria(
            id=registro_id,
            skill_name=skill_name,
            skill_id=skill_id,
            action=action,
            status="running",
            start_time=now.isoformat(),
            end_time=None,
            duration_seconds=None,
            details=details or {},
            created_at=now.strftime("%Y-%m-%d")
        )
        
        self.registros.append(registro)
        logger.info(f"[AUDITORIA] Iniciado: {skill_name} - {action} (ID: {registro_id})")
        
        return registro_id
    
    def finalizar_registro(self, registro_id: str, status: str = "completed", details_update: Dict = None):
        """Finalizar un registro de auditoría"""
        for registro in self.registros:
            if registro.id == registro_id:
                registro.status = status
                registro.end_time = datetime.now().isoformat()
                
                start = datetime.fromisoformat(registro.start_time)
                end = datetime.now()
                registro.duration_seconds = (end - start).total_seconds()
                
                if details_update:
                    registro.details.update(details_update)
                
                # Guardar inmediatamente
                self._guardar_registros_dia(registro.created_at)
                
                logger.info(f"[AUDITORIA] Finalizado: {registro.skill_name} - {status} ({registro.duration_seconds:.2f}s)")
                return True
        
        return False
    
    def obtener_registros(self, skill_id: str = None, status: str = None, 
                         fecha_desde: str = None, fecha_hasta: str = None,
                         limit: int = 1000) -> List[Dict]:
        """Obtener registros con filtros"""
        resultado = self.registros
        
        if skill_id:
            resultado = [r for r in resultado if r.skill_id == skill_id]
        
        if status:
            resultado = [r for r in resultado if r.status == status]
        
        if fecha_desde:
            resultado = [r for r in resultado if r.created_at >= fecha_desde]
        
        if fecha_hasta:
            resultado = [r for r in resultado if r.created_at <= fecha_hasta]
        
        # Ordenar por fecha descendente
        resultado = sorted(resultado, key=lambda x: x.start_time, reverse=True)
        
        return [r.to_dict() for r in resultado[:limit]]
    
    def obtener_estadisticas(self) -> Dict:
        """Obtener estadísticas de auditoría"""
        total = len(self.registros)
        completed = len([r for r in self.registros if r.status == "completed"])
        failed = len([r for r in self.registros if r.status == "failed"])
        running = len([r for r in self.registros if r.status == "running"])
        
        # Agrupar por skill
        skills_count = {}
        for r in self.registros:
            skills_count[r.skill_name] = skills_count.get(r.skill_name, 0) + 1
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "retention_days": RETENTION_DAYS,
            "skills_mas_usadas": sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
        }


# Instancia global
auditoria_manager = AuditoriaManager()
