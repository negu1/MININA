"""
MININA v3.0 - Orchestrator Guardian
Sistema de monitoreo, auditoría y seguridad del Orquestador
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path


class ActionType(Enum):
    """Tipos de acciones del orquestador"""
    PLAN_CREATED = "plan_created"
    PLAN_APPROVED = "plan_approved"
    PLAN_EXECUTED = "plan_executed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    SKILL_INVOKED = "skill_invoked"
    ROLLBACK_TRIGGERED = "rollback_triggered"
    ERROR_DETECTED = "error_detected"
    RESOURCE_LIMIT_HIT = "resource_limit_hit"


class RiskLevel(Enum):
    """Niveles de riesgo de las acciones"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OrchestratorAuditRecord:
    """Registro de auditoría del orquestador"""
    timestamp: str
    action: str
    plan_id: Optional[str]
    task_id: Optional[str]
    skill_name: Optional[str]
    user_input: str
    result: str
    risk_level: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionCheckpoint:
    """Checkpoint para rollback"""
    checkpoint_id: str
    plan_id: str
    task_index: int
    state_before: Dict[str, Any]
    timestamp: str
    can_rollback: bool = True


class OrchestratorGuardian:
    """
    Guardian del Orquestador - Vigilante de seguridad
    
    Responsabilidades:
    1. Auditar todas las acciones del orquestador
    2. Detectar comportamientos anómalos
    3. Enforzar límites de recursos
    4. Permitir rollback de operaciones
    5. Generar reportes de seguridad
    """
    
    def __init__(self, audit_dir: str = "data/audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Límites de seguridad
        self.max_tasks_per_plan = 50
        self.max_execution_time_seconds = 300  # 5 minutos
        self.max_skills_invoked = 20
        self.max_concurrent_plans = 3
        
        # Estado actual
        self.current_plans: Dict[str, Dict[str, Any]] = {}
        self.checkpoints: Dict[str, ExecutionCheckpoint] = {}
        self.error_count = 0
        self.last_error_time = None
        
        # Historial de auditoría en memoria (últimos 100)
        self.recent_audits: List[OrchestratorAuditRecord] = []
        
    def audit_action(
        self,
        action: ActionType,
        plan_id: Optional[str] = None,
        task_id: Optional[str] = None,
        skill_name: Optional[str] = None,
        user_input: str = "",
        result: str = "",
        risk_level: RiskLevel = RiskLevel.LOW,
        details: Optional[Dict[str, Any]] = None
    ) -> OrchestratorAuditRecord:
        """Registrar una acción del orquestador"""
        
        record = OrchestratorAuditRecord(
            timestamp=datetime.now().isoformat(),
            action=action.value,
            plan_id=plan_id,
            task_id=task_id,
            skill_name=skill_name,
            user_input=user_input,
            result=result,
            risk_level=risk_level.value,
            details=details or {}
        )
        
        # Guardar en memoria
        self.recent_audits.append(record)
        if len(self.recent_audits) > 100:
            self.recent_audits.pop(0)
        
        # Persistir a disco
        self._persist_audit(record)
        
        # Verificar alertas de seguridad
        self._check_security_alerts(record)
        
        return record
    
    def _persist_audit(self, record: OrchestratorAuditRecord):
        """Guardar registro de auditoría en archivo"""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            audit_file = self.audit_dir / f"audit_{date_str}.jsonl"
            
            with open(audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error guardando auditoría: {e}")
    
    def _check_security_alerts(self, record: OrchestratorAuditRecord):
        """Verificar si la acción genera alertas de seguridad"""
        
        # Alerta: múltiples errores en poco tiempo
        if record.action == ActionType.ERROR_DETECTED.value:
            self.error_count += 1
            self.last_error_time = time.time()
            
            if self.error_count >= 5:
                print(f"⚠️ ALERTA DE SEGURIDAD: {self.error_count} errores detectados")
        
        # Resetear contador si pasó tiempo
        if self.last_error_time and (time.time() - self.last_error_time) > 60:
            self.error_count = 0
    
    def validate_plan_creation(self, plan: Dict[str, Any]) -> tuple[bool, str]:
        """Validar que un plan es seguro antes de crearlo"""
        
        tasks = plan.get('tasks', [])
        
        # Verificar número de tareas
        if len(tasks) > self.max_tasks_per_plan:
            return False, f"Plan excede máximo de {self.max_tasks_per_plan} tareas"
        
        # Verificar skills requeridos
        skills = set()
        for task in tasks:
            skill = task.get('required_skill', '')
            if skill:
                skills.add(skill)
        
        if len(skills) > self.max_skills_invoked:
            return False, f"Plan requiere demasiados skills ({len(skills)} > {self.max_skills_invoked})"
        
        # Verificar dependencias cíclicas
        if self._has_cyclic_dependencies(tasks):
            return False, "Plan tiene dependencias cíclicas"
        
        return True, "Plan validado"
    
    def _has_cyclic_dependencies(self, tasks: List[Dict[str, Any]]) -> bool:
        """Detectar dependencias cíclicas en tareas"""
        # Construir grafo
        graph = {}
        for task in tasks:
            tid = task.get('task_id', '')
            deps = task.get('dependencies', [])
            graph[tid] = deps
        
        # DFS para detectar ciclos
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False
    
    def create_checkpoint(self, plan_id: str, task_index: int, state: Dict[str, Any]) -> ExecutionCheckpoint:
        """Crear un checkpoint para posible rollback"""
        
        checkpoint = ExecutionCheckpoint(
            checkpoint_id=f"chk_{int(time.time())}_{plan_id}",
            plan_id=plan_id,
            task_index=task_index,
            state_before=state.copy(),
            timestamp=datetime.now().isoformat()
        )
        
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        
        # Limitar número de checkpoints
        if len(self.checkpoints) > 50:
            oldest = min(self.checkpoints.keys(), 
                        key=lambda k: self.checkpoints[k].timestamp)
            del self.checkpoints[oldest]
        
        return checkpoint
    
    def can_rollback(self, checkpoint_id: str) -> bool:
        """Verificar si se puede hacer rollback a un checkpoint"""
        if checkpoint_id not in self.checkpoints:
            return False
        
        checkpoint = self.checkpoints[checkpoint_id]
        return checkpoint.can_rollback
    
    def rollback(self, checkpoint_id: str) -> Dict[str, Any]:
        """Ejecutar rollback a un checkpoint"""
        if not self.can_rollback(checkpoint_id):
            raise ValueError(f"No se puede hacer rollback a {checkpoint_id}")
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        # Auditar el rollback
        self.audit_action(
            action=ActionType.ROLLBACK_TRIGGERED,
            plan_id=checkpoint.plan_id,
            result=f"Rollback a tarea {checkpoint.task_index}",
            risk_level=RiskLevel.HIGH,
            details={"checkpoint_id": checkpoint_id, "state_restored": checkpoint.state_before}
        )
        
        return checkpoint.state_before
    
    def check_resource_limits(self, plan_id: str) -> tuple[bool, str]:
        """Verificar límites de recursos"""
        
        # Verificar planes concurrentes
        if len(self.current_plans) >= self.max_concurrent_plans:
            return False, f"Máximo de {self.max_concurrent_plans} planes concurrentes alcanzado"
        
        return True, "Recursos disponibles"
    
    def start_plan(self, plan_id: str, plan_data: Dict[str, Any]):
        """Registrar inicio de plan"""
        self.current_plans[plan_id] = {
            "started_at": time.time(),
            "tasks_completed": 0,
            "tasks_failed": 0,
            "skills_invoked": set(),
            "data": plan_data
        }
    
    def end_plan(self, plan_id: str, success: bool):
        """Registrar fin de plan"""
        if plan_id in self.current_plans:
            plan_info = self.current_plans[plan_id]
            duration = time.time() - plan_info["started_at"]
            
            # Limpiar
            del self.current_plans[plan_id]
            
            return {
                "duration_seconds": duration,
                "tasks_completed": plan_info["tasks_completed"],
                "tasks_failed": plan_info["tasks_failed"],
                "success": success
            }
        
        return None
    
    def get_audit_report(self, since_hours: int = 24) -> Dict[str, Any]:
        """Generar reporte de auditoría"""
        
        cutoff_time = time.time() - (since_hours * 3600)
        
        # Filtrar auditorías recientes
        recent = [r for r in self.recent_audits 
                 if datetime.fromisoformat(r.timestamp).timestamp() > cutoff_time]
        
        # Calcular métricas
        actions_by_type = {}
        errors = []
        high_risk_actions = []
        
        for record in recent:
            # Contar por tipo
            actions_by_type[record.action] = actions_by_type.get(record.action, 0) + 1
            
            # Registrar errores
            if record.action == ActionType.ERROR_DETECTED.value:
                errors.append(record)
            
            # Registrar riesgos altos
            if record.risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
                high_risk_actions.append(record)
        
        return {
            "period_hours": since_hours,
            "total_actions": len(recent),
            "actions_by_type": actions_by_type,
            "error_count": len(errors),
            "high_risk_count": len(high_risk_actions),
            "errors": [e.to_dict() for e in errors],
            "high_risk_actions": [a.to_dict() for a in high_risk_actions],
            "generated_at": datetime.now().isoformat()
        }
    
    def validate_user_input(self, user_input: str) -> tuple[bool, str, RiskLevel]:
        """Validar input del usuario para detectar posibles problemas"""
        
        # Palabras clave sospechosas
        suspicious_patterns = [
            "borrar todo", "eliminar todo", "delete all",
            "formatear", "format", "rm -rf",
            "sudo", "admin", "root",
            "contraseña", "password", "token",
            "__import__", "eval(", "exec(",
        ]
        
        input_lower = user_input.lower()
        
        # Verificar patrones sospechosos
        for pattern in suspicious_patterns:
            if pattern in input_lower:
                return False, f"Input contiene patrón sospechoso: '{pattern}'", RiskLevel.HIGH
        
        # Verificar longitud excesiva
        if len(user_input) > 10000:
            return False, "Input demasiado largo (>10000 caracteres)", RiskLevel.MEDIUM
        
        return True, "Input validado", RiskLevel.LOW


# Singleton
guardian = OrchestratorGuardian()
