"""
MiIA System Watchdog
Sistema de supervisión y recuperación automática para MiIA-Product-20
- Detecta crashes y errores críticos
- Reinicia servicios automáticamente
- Notifica al usuario con mensajes simples
- Guarda reportes técnicos para debugging
"""
import os
import sys
import time
import json
import logging
import asyncio
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psutil

logger = logging.getLogger("MiIAWatchdog")

class ServiceStatus(Enum):
    """Estados posibles de un servicio"""
    HEALTHY = "healthy"           # Funcionando correctamente
    DEGRADED = "degraded"         # Funcionando pero con problemas
    FAILED = "failed"             # Falló, intentando reiniciar
    RECOVERING = "recovering"     # En proceso de recuperación
    STOPPED = "stopped"           # Detenido por el usuario

@dataclass
class ServiceInfo:
    """Información de un servicio monitoreado"""
    name: str
    status: ServiceStatus
    last_heartbeat: float
    restart_count: int
    last_error: Optional[str] = None
    error_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.error_history is None:
            self.error_history = []

@dataclass
class ErrorReport:
    """Reporte de error para debugging"""
    timestamp: str
    service: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    system_state: Optional[Dict[str, Any]] = None
    recovered: bool = False
    recovery_time: Optional[str] = None


class MiIAWatchdog:
    """
    Watchdog principal de MiIA
    Monitorea servicios, detecta fallos y ejecuta recuperación automática
    """
    
    HEARTBEAT_TIMEOUT = 30  # segundos sin heartbeat = servicio caído
    MAX_RESTARTS = 5        # máximo reinicios antes de modo seguro
    RESTART_WINDOW = 300    # ventana de tiempo para contar reinicios (5 min)
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.error_reports: List[ErrorReport] = []
        self._running = False
        self._monitor_task = None
        self._cleanup_task = None
        self._callbacks: List[Callable] = []
        
        # Directorio para reportes
        self.reports_dir = Path.home() / ".config" / "miia-product-20" / "error_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Cargar reportes anteriores
        self._load_reports()
    
    def register_service(self, name: str) -> ServiceInfo:
        """Registrar un nuevo servicio para monitoreo"""
        service = ServiceInfo(
            name=name,
            status=ServiceStatus.HEALTHY,
            last_heartbeat=time.time(),
            restart_count=0
        )
        self.services[name] = service
        logger.info(f"✅ Servicio registrado: {name}")
        return service
    
    def heartbeat(self, service_name: str):
        """Actualizar heartbeat de un servicio"""
        if service_name in self.services:
            self.services[service_name].last_heartbeat = time.time()
            if self.services[service_name].status != ServiceStatus.HEALTHY:
                self.services[service_name].status = ServiceStatus.HEALTHY
                logger.info(f"💚 Servicio {service_name} recuperado")
    
    def report_error(self, service_name: str, error: Exception, 
                    context: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """
        Reportar un error para seguimiento y recuperación
        """
        # Crear reporte
        report = ErrorReport(
            timestamp=datetime.now().isoformat(),
            service=service_name,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc() if error else None,
            system_state=self._get_system_state() if context is None else context
        )
        
        # Guardar en memoria
        self.error_reports.append(report)
        
        # Guardar en disco
        self._save_report(report)
        
        # Actualizar servicio
        if service_name in self.services:
            service = self.services[service_name]
            service.last_error = str(error)
            service.error_history.append({
                "timestamp": report.timestamp,
                "error": str(error),
                "type": type(error).__name__
            })
            
            # Mantener solo últimos 10 errores en memoria
            if len(service.error_history) > 10:
                service.error_history = service.error_history[-10:]
        
        # Notificar callbacks
        for callback in self._callbacks:
            try:
                callback("error", report)
            except Exception as e:
                logger.error(f"Error en callback: {e}")
        
        logger.error(f"❌ Error reportado en {service_name}: {error}")
        return report
    
    async def attempt_recovery(self, service_name: str, 
                               recovery_action: Callable) -> bool:
        """
        Intentar recuperar un servicio fallido
        """
        if service_name not in self.services:
            logger.error(f"Servicio no encontrado: {service_name}")
            return False
        
        service = self.services[service_name]
        
        # Verificar límite de reinicios
        if service.restart_count >= self.MAX_RESTARTS:
            logger.error(f"🚫 Máximo de reinicios alcanzado para {service_name}")
            service.status = ServiceStatus.FAILED
            return False
        
        # Marcar como recuperando
        service.status = ServiceStatus.RECOVERING
        service.restart_count += 1
        
        logger.info(f"🔄 Intentando recuperar {service_name}...")
        
        try:
            # Ejecutar acción de recuperación
            if asyncio.iscoroutinefunction(recovery_action):
                await recovery_action()
            else:
                recovery_action()
            
            # Esperar a que el servicio responda
            await asyncio.sleep(2)
            
            # Verificar si se recuperó
            if service.status == ServiceStatus.HEALTHY:
                logger.info(f"✅ {service_name} recuperado exitosamente")
                
                # Actualizar reporte de error si existe
                for report in reversed(self.error_reports):
                    if report.service == service_name and not report.recovered:
                        report.recovered = True
                        report.recovery_time = datetime.now().isoformat()
                        break
                
                return True
            else:
                logger.warning(f"⚠️ {service_name} no respondió después del reinicio")
                service.status = ServiceStatus.FAILED
                return False
                
        except Exception as e:
            logger.error(f"❌ Error durante recuperación de {service_name}: {e}")
            service.status = ServiceStatus.FAILED
            return False
    
    async def start_monitoring(self):
        """Iniciar monitoreo de servicios"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("🔍 Watchdog iniciado")
    
    async def stop_monitoring(self):
        """Detener monitoreo"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        logger.info("🛑 Watchdog detenido")
    
    async def _monitor_loop(self):
        """Bucle principal de monitoreo"""
        while self._running:
            try:
                current_time = time.time()
                
                for name, service in self.services.items():
                    # Verificar timeout de heartbeat
                    time_since_heartbeat = current_time - service.last_heartbeat
                    
                    if time_since_heartbeat > self.HEARTBEAT_TIMEOUT:
                        if service.status != ServiceStatus.FAILED:
                            logger.warning(f"⚠️ {name} no responde ({time_since_heartbeat:.0f}s)")
                            service.status = ServiceStatus.DEGRADED
                            
                            # Si pasa mucho tiempo, marcar como fallido
                            if time_since_heartbeat > self.HEARTBEAT_TIMEOUT * 2:
                                service.status = ServiceStatus.FAILED
                                
                                # Notificar
                                self._notify_service_down(name)
                
                # Verificar uso de recursos del sistema
                await self._check_system_resources()
                
                await asyncio.sleep(5)  # Revisar cada 5 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self):
        """Bucle de limpieza de reportes antiguos"""
        while self._running:
            try:
                self._cleanup_old_reports()
                await asyncio.sleep(3600)  # Revisar cada hora
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en cleanup loop: {e}")
                await asyncio.sleep(3600)
    
    def _check_system_resources(self):
        """Verificar recursos del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            if cpu_percent > 90:
                logger.warning(f"⚠️ CPU alta: {cpu_percent}%")
                self._notify_resource_warning("CPU", cpu_percent)
            
            if memory.percent > 90:
                logger.warning(f"⚠️ Memoria alta: {memory.percent}%")
                self._notify_resource_warning("Memoria", memory.percent)
                
        except Exception as e:
            logger.error(f"Error verificando recursos: {e}")
    
    def _notify_service_down(self, service_name: str):
        """Notificar que un servicio está caído"""
        message = f"⚠️ El servicio {service_name} no responde. Intentando reiniciar..."
        logger.warning(message)
        
        # Notificar a través del bus de eventos si está disponible
        try:
            # Importación lazy para evitar dependencias circulares
            from core.CortexBus import bus
            asyncio.create_task(
                bus.publish("system.WARNING", {
                    "message": message,
                    "service": service_name,
                    "action": "auto_recovery"
                }, sender="Watchdog")
            )
        except Exception:
            pass
    
    def _notify_resource_warning(self, resource: str, value: float):
        """Notificar advertencia de recursos"""
        try:
            from core.CortexBus import bus
            asyncio.create_task(
                bus.publish("system.WARNING", {
                    "message": f"⚠️ Uso alto de {resource}: {value:.0f}%",
                    "resource": resource,
                    "value": value,
                    "action": "monitor"
                }, sender="Watchdog")
            )
        except Exception:
            pass
    
    def _get_system_state(self) -> Dict[str, Any]:
        """Obtener estado actual del sistema"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "timestamp": datetime.now().isoformat(),
                "services_status": {
                    name: {
                        "status": service.status.value,
                        "last_heartbeat": service.last_heartbeat,
                        "restart_count": service.restart_count
                    }
                    for name, service in self.services.items()
                }
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _save_report(self, report: ErrorReport):
        """Guardar reporte en disco"""
        try:
            filename = f"error_{report.timestamp.replace(':', '-').replace('.', '_')}.json"
            filepath = self.reports_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(report), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    def _load_reports(self):
        """Cargar reportes existentes"""
        try:
            for filepath in self.reports_dir.glob("error_*.json"):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        report = ErrorReport(**data)
                        self.error_reports.append(report)
                except Exception as e:
                    logger.warning(f"Error cargando reporte {filepath}: {e}")
            
            # Ordenar por timestamp
            self.error_reports.sort(key=lambda r: r.timestamp, reverse=True)
            
            # Mantener solo últimos 50 en memoria
            if len(self.error_reports) > 50:
                self.error_reports = self.error_reports[:50]
                
        except Exception as e:
            logger.error(f"Error cargando reportes: {e}")
    
    def _cleanup_old_reports(self, days: int = 7):
        """Eliminar reportes antiguos"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            
            for filepath in self.reports_dir.glob("error_*.json"):
                try:
                    # Extraer fecha del nombre del archivo
                    stat = filepath.stat()
                    file_time = datetime.fromtimestamp(stat.st_mtime)
                    
                    if file_time < cutoff:
                        filepath.unlink()
                        logger.info(f"🗑️ Reporte antiguo eliminado: {filepath.name}")
                except Exception as e:
                    logger.warning(f"Error eliminando {filepath}: {e}")
            
            # También limpiar memoria
            cutoff_str = cutoff.isoformat()
            self.error_reports = [
                r for r in self.error_reports 
                if r.timestamp > cutoff_str
            ]
            
        except Exception as e:
            logger.error(f"Error en cleanup: {e}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado del sistema"""
        healthy_count = sum(1 for s in self.services.values() 
                         if s.status == ServiceStatus.HEALTHY)
        
        failed_services = [
            {"name": name, "status": service.status.value, "error": service.last_error}
            for name, service in self.services.items()
            if service.status in [ServiceStatus.FAILED, ServiceStatus.DEGRADED]
        ]
        
        recent_errors = [
            {
                "timestamp": r.timestamp,
                "service": r.service,
                "error": r.error_message[:100]  # Truncar
            }
            for r in self.error_reports[:5]  # Últimos 5
        ]
        
        return {
            "total_services": len(self.services),
            "healthy_services": healthy_count,
            "failed_services": failed_services,
            "recent_errors": recent_errors,
            "reports_count": len(self.error_reports),
            "reports_retention_days": 7,
            "all_healthy": len(failed_services) == 0
        }
    
    def get_detailed_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener reportes detallados para el panel"""
        return [
            {
                "timestamp": r.timestamp,
                "service": r.service,
                "error_type": r.error_type,
                "error_message": r.error_message,
                "recovered": r.recovered,
                "recovery_time": r.recovery_time
            }
            for r in self.error_reports[:limit]
        ]
    
    def on_error(self, callback: Callable):
        """Registrar callback para notificaciones de error"""
        self._callbacks.append(callback)


# Instancia global del watchdog
watchdog = MiIAWatchdog()


# Funciones de conveniencia
def register_service(name: str) -> ServiceInfo:
    """Registrar un servicio en el watchdog"""
    return watchdog.register_service(name)

def heartbeat(service_name: str):
    """Enviar heartbeat"""
    watchdog.heartbeat(service_name)

def report_error(service_name: str, error: Exception, context: Optional[Dict] = None):
    """Reportar un error"""
    return watchdog.report_error(service_name, error, context)

def get_system_status() -> Dict[str, Any]:
    """Obtener estado del sistema"""
    return watchdog.get_status_summary()

def get_error_reports(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtener reportes de error"""
    return watchdog.get_detailed_reports(limit)
