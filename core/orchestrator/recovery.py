"""
MININA v3.0 - Orchestrator Error Recovery
Sistema de recuperación de errores y rollback
"""

import asyncio
import traceback
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from core.orchestrator.guardian import guardian, ActionType, RiskLevel


class RecoveryStrategy(Enum):
    """Estrategias de recuperación"""
    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    ABORT = "abort"
    ALTERNATIVE = "alternative"


@dataclass
class ErrorContext:
    """Contexto de un error"""
    error: Exception
    plan_id: str
    task_id: str
    task_index: int
    skill_name: str
    attempt_number: int
    max_attempts: int = 3


class OrchestratorRecovery:
    """
    Sistema de recuperación de errores del Orquestador
    
    Capacidades:
    - Retry automático con backoff
    - Rollback a checkpoints
    - Estrategias alternativas
    - Reporte de fallos
    """
    
    def __init__(self):
        self.retry_delays = [1, 2, 5]  # Segundos entre reintentos
        self.error_handlers: Dict[str, Callable] = {}
        self.failed_tasks: List[Dict[str, Any]] = []
        
    async def handle_task_error(
        self,
        error: Exception,
        plan_id: str,
        task: Dict[str, Any],
        task_index: int,
        context: Dict[str, Any],
        execute_fn: Callable
    ) -> Dict[str, Any]:
        """Manejar error en ejecución de tarea"""
        
        error_ctx = ErrorContext(
            error=error,
            plan_id=plan_id,
            task_id=task.get('task_id', ''),
            task_index=task_index,
            skill_name=task.get('required_skill', ''),
            attempt_number=0
        )
        
        # Determinar estrategia de recuperación
        strategy = self._determine_strategy(error_ctx)
        
        # Auditar el error
        guardian.audit_action(
            action=ActionType.ERROR_DETECTED,
            plan_id=plan_id,
            task_id=error_ctx.task_id,
            skill_name=error_ctx.skill_name,
            result=f"Error: {str(error)}",
            risk_level=RiskLevel.HIGH,
            details={
                "strategy": strategy.value,
                "error_type": type(error).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        # Ejecutar estrategia
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_task(error_ctx, task, context, execute_fn)
        
        elif strategy == RecoveryStrategy.ROLLBACK:
            return await self._rollback_and_retry(error_ctx, plan_id, task, execute_fn)
        
        elif strategy == RecoveryStrategy.ALTERNATIVE:
            return await self._try_alternative(error_ctx, task, context, execute_fn)
        
        elif strategy == RecoveryStrategy.SKIP:
            return {"success": False, "skipped": True, "error": str(error)}
        
        else:  # ABORT
            raise error
    
    def _determine_strategy(self, ctx: ErrorContext) -> RecoveryStrategy:
        """Determinar mejor estrategia de recuperación"""
        
        error_str = str(ctx.error).lower()
        error_type = type(ctx.error).__name__
        
        # Errores de red/conexión: retry
        if any(kw in error_str for kw in ['timeout', 'connection', 'network', 'unreachable']):
            if ctx.attempt_number < ctx.max_attempts:
                return RecoveryStrategy.RETRY
        
        # Errores de permisos: abortar
        if any(kw in error_str for kw in ['permission', 'access denied', 'unauthorized']):
            return RecoveryStrategy.ABORT
        
        # Errores de skill no encontrada: rollback
        if 'skill' in error_str and ('not found' in error_str or 'missing' in error_str):
            return RecoveryStrategy.ROLLBACK
        
        # Errores de validación: skip
        if any(kw in error_str for kw in ['validation', 'invalid', 'bad request']):
            return RecoveryStrategy.SKIP
        
        # Default: retry si quedan intentos
        if ctx.attempt_number < ctx.max_attempts:
            return RecoveryStrategy.RETRY
        
        return RecoveryStrategy.ABORT
    
    async def _retry_task(
        self,
        ctx: ErrorContext,
        task: Dict[str, Any],
        context: Dict[str, Any],
        execute_fn: Callable
    ) -> Dict[str, Any]:
        """Reintentar tarea con backoff"""
        
        for attempt in range(ctx.attempt_number, ctx.max_attempts):
            delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
            
            print(f"🔄 Reintentando {ctx.skill_name} en {delay}s (intento {attempt + 1}/{ctx.max_attempts})")
            await asyncio.sleep(delay)
            
            try:
                result = await execute_fn(task, context)
                
                # Auditar éxito
                guardian.audit_action(
                    action=ActionType.TASK_COMPLETED,
                    plan_id=ctx.plan_id,
                    task_id=ctx.task_id,
                    skill_name=ctx.skill_name,
                    result="Recuperado tras retry",
                    risk_level=RiskLevel.LOW
                )
                
                return result
                
            except Exception as e:
                ctx.error = e
                ctx.attempt_number = attempt + 1
                
                if attempt == ctx.max_attempts - 1:
                    # Último intento fallido
                    self.failed_tasks.append({
                        "plan_id": ctx.plan_id,
                        "task_id": ctx.task_id,
                        "skill": ctx.skill_name,
                        "error": str(e),
                        "attempts": ctx.max_attempts
                    })
                    raise
        
        raise ctx.error
    
    async def _rollback_and_retry(
        self,
        ctx: ErrorContext,
        plan_id: str,
        task: Dict[str, Any],
        execute_fn: Callable
    ) -> Dict[str, Any]:
        """Hacer rollback y reintentar"""
        
        # Buscar checkpoint más reciente
        checkpoint_id = None
        for chk_id, chk in guardian.checkpoints.items():
            if chk.plan_id == plan_id:
                checkpoint_id = chk_id
                break
        
        if checkpoint_id and guardian.can_rollback(checkpoint_id):
            print(f"⏪ Haciendo rollback a checkpoint {checkpoint_id}")
            
            try:
                state = guardian.rollback(checkpoint_id)
                # Reintentar con estado restaurado
                return await execute_fn(task, {"restored_state": state})
            except Exception as e:
                print(f"❌ Rollback falló: {e}")
        
        # Si no hay checkpoint, intentar sin rollback
        return await self._retry_task(ctx, task, {}, execute_fn)
    
    async def _try_alternative(
        self,
        ctx: ErrorContext,
        task: Dict[str, Any],
        context: Dict[str, Any],
        execute_fn: Callable
    ) -> Dict[str, Any]:
        """Intentar estrategia alternativa"""
        
        # Buscar skill alternativa
        original_skill = ctx.skill_name
        alternative_skills = self._find_alternatives(original_skill)
        
        for alt_skill in alternative_skills:
            print(f"🔄 Intentando skill alternativa: {alt_skill}")
            
            # Crear tarea modificada
            alt_task = task.copy()
            alt_task['required_skill'] = alt_skill
            
            try:
                result = await execute_fn(alt_task, context)
                
                # Auditar éxito con alternativa
                guardian.audit_action(
                    action=ActionType.TASK_COMPLETED,
                    plan_id=ctx.plan_id,
                    task_id=ctx.task_id,
                    skill_name=alt_skill,
                    result=f"Completado con skill alternativa (original: {original_skill})",
                    risk_level=RiskLevel.MEDIUM
                )
                
                return result
                
            except Exception as e:
                print(f"❌ Alternativa {alt_skill} también falló: {e}")
                continue
        
        # Ninguna alternativa funcionó
        raise ctx.error
    
    def _find_alternatives(self, skill_name: str) -> List[str]:
        """Buscar skills alternativas"""
        # Mapa de alternativas
        alternatives_map = {
            "email_sender": ["smtp_client", "email_api"],
            "file_reader": ["file_parser", "document_loader"],
            "web_scraper": ["http_client", "browser_automation"],
            "data_analyzer": ["pandas_skill", "csv_processor"],
        }
        
        return alternatives_map.get(skill_name, [])
    
    def get_recovery_report(self) -> Dict[str, Any]:
        """Generar reporte de recuperación"""
        return {
            "failed_tasks": self.failed_tasks,
            "total_failures": len(self.failed_tasks),
            "retry_statistics": {
                "max_attempts_configured": self.retry_delays
            }
        }


# Singleton
recovery = OrchestratorRecovery()
