"""
MININA v3.0 - ExecutionSupervisor (Capa 2)
Supervisión y validación de ejecuciones
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from core.orchestrator.bus import bus, EventType, CortexEvent


class ValidationResult(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class ExecutionMetrics:
    """Métricas de ejecución"""
    execution_id: str
    start_time: datetime
    end_time: Optional[datetime]
    cpu_usage: float
    memory_usage: float
    duration_seconds: float


class ExecutionSupervisor:
    """
    Supervisor de Ejecución - Capa 2
    Valida resultados y detecta anomalías
    """
    
    def __init__(self):
        self.active_executions: Dict[str, ExecutionMetrics] = {}
        self.anomaly_threshold = 10.0  # segundos
        
    async def monitor_execution(self, execution_id: str):
        """Monitorear ejecución en tiempo real"""
        metrics = ExecutionMetrics(
            execution_id=execution_id,
            start_time=datetime.now(),
            end_time=None,
            cpu_usage=0.0,
            memory_usage=0.0,
            duration_seconds=0.0
        )
        self.active_executions[execution_id] = metrics
        
        # Publicar inicio
        await bus.publish(CortexEvent(
            type=EventType.SKILL_STARTED,
            source="supervisor",
            payload={"execution_id": execution_id},
            timestamp=datetime.now(),
            event_id=f"evt_{execution_id}_start"
        ))
    
    async def validate_result(self, execution_id: str, result: Dict[str, Any]) -> ValidationResult:
        """Validar resultado de ejecución"""
        if execution_id not in self.active_executions:
            return ValidationResult.FAILED
            
        metrics = self.active_executions[execution_id]
        metrics.end_time = datetime.now()
        metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
        
        # Validaciones básicas
        success = result.get("success", False)
        has_output = bool(result.get("result") or result.get("generated_files"))
        
        # Detectar anomalías
        if metrics.duration_seconds > self.anomaly_threshold:
            await bus.publish(CortexEvent(
                type=EventType.ANOMALY_DETECTED,
                source="supervisor",
                payload={
                    "execution_id": execution_id,
                    "type": "slow_execution",
                    "duration": metrics.duration_seconds
                },
                timestamp=datetime.now(),
                event_id=f"evt_{execution_id}_anomaly"
            ))
        
        # Determinar resultado
        if success and has_output:
            result_type = ValidationResult.SUCCESS
            event_type = EventType.SKILL_VALIDATED
        elif success:
            result_type = ValidationResult.PARTIAL
            event_type = EventType.SKILL_VALIDATED
        else:
            result_type = ValidationResult.FAILED
            event_type = EventType.SKILL_FAILED
        
        # Publicar resultado
        await bus.publish(CortexEvent(
            type=event_type,
            source="supervisor",
            payload={
                "execution_id": execution_id,
                "validation": result_type.value,
                "duration": metrics.duration_seconds
            },
            timestamp=datetime.now(),
            event_id=f"evt_{execution_id}_end"
        ))
        
        # Limpiar
        del self.active_executions[execution_id]
        
        return result_type
