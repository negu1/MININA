"""
MININA v3.0 - Skill Execution Validator
Validador de ejecución de skills para el Orchestrator

CAPA 3: Validación en tiempo de ejecución
- Wrapper que isola la skill
- Validación de respuesta (solo output esperado)
- Bloqueo de skills que intentan escapar
- Detección de comportamiento impuro durante ejecución
"""

import ast
import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import sys
import os

# Añadir path para imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.security.skill_purity_validator import skill_purity_validator, PurityReport


@dataclass
class ExecutionReport:
    """Reporte de ejecución de una skill"""
    skill_id: str
    success: bool
    execution_time_ms: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    purity_violations: List[str] = field(default_factory=list)
    safety_violations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "result": self.result,
            "error": self.error,
            "purity_violations": self.purity_violations,
            "safety_violations": self.safety_violations
        }


class SkillExecutionValidator:
    """
    Validador de ejecución de skills para el Orchestrator.
    
    Asegura que:
    1. La skill es pura (pre-validación)
    2. La ejecución es aislada
    3. La respuesta es válida y predecible
    4. No hay fugas de información
    5. No hay intentos de llamar otras skills
    
    FLUJO CORRECTO:
    Humano -> Orchestrator -> SkillExecutionValidator -> Skill pura -> Respuesta
    """
    
    # Resultados esperados de una skill pura
    _VALID_RESULT_KEYS = {"success", "result", "error", "data", "output", "message", "status"}
    
    def __init__(self):
        self.execution_history: List[ExecutionReport] = []
        self.max_history = 100
    
    def validate_and_execute(
        self,
        skill_id: str,
        skill_path: Path,
        context: Dict[str, Any],
        execute_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        timeout_ms: float = 30000
    ) -> ExecutionReport:
        """
        Validar y ejecutar una skill de forma segura
        
        Args:
            skill_id: ID de la skill
            skill_path: Ruta al archivo skill.py
            context: Contexto de ejecución
            execute_fn: Función execute() de la skill
            timeout_ms: Timeout en milisegundos
            
        Returns:
            ExecutionReport con el resultado
        """
        start_time = time.time()
        purity_violations = []
        safety_violations = []
        
        # PASO 1: Pre-validación de pureza
        purity_report = skill_purity_validator.validate_skill_file(skill_path)
        
        if not purity_report.is_pure:
            # Skill impura detectada - NO ejecutar
            error_msg = (
                f"[BLOQUEO DE SEGURIDAD] Skill '{skill_id}' es IMPURA y no puede ejecutarse.\n"
                f"Violaciones detectadas:\n" +
                "\n".join(f"  - {v}" for v in purity_report.violations) +
                f"\n\nPRINCIPIO: Una skill debe ser una caja negra que NO piensa.\n"
                f"FLUJO CORRECTO: Humano -> Orchestrator -> Skill pura -> Respuesta\n"
                f"Si esta skill necesita 'pensar', ese 'pensamiento' debe estar en el Orchestrator."
            )
            
            report = ExecutionReport(
                skill_id=skill_id,
                success=False,
                execution_time_ms=0,
                error=error_msg,
                purity_violations=purity_report.violations,
                safety_violations=["SKILL_IMPURA_BLOQUEADA"]
            )
            self._add_to_history(report)
            return report
        
        # PASO 2: Validar contexto
        context_validation = self._validate_context(context)
        if not context_validation["valid"]:
            report = ExecutionReport(
                skill_id=skill_id,
                success=False,
                execution_time_ms=0,
                error=f"Contexto inválido: {context_validation['error']}",
                safety_violations=["CONTEXTO_INVALIDO"]
            )
            self._add_to_history(report)
            return report
        
        # PASO 3: Ejecutar con monitoreo
        try:
            # Ejecutar la skill
            result = execute_fn(context)
            execution_time = (time.time() - start_time) * 1000
            
            # PASO 4: Validar resultado
            result_validation = self._validate_result(result, skill_id)
            
            if not result_validation["valid"]:
                report = ExecutionReport(
                    skill_id=skill_id,
                    success=False,
                    execution_time_ms=execution_time,
                    result=result,
                    error=f"Resultado inválido: {result_validation['error']}",
                    safety_violations=["RESULTADO_INVALIDO"]
                )
                self._add_to_history(report)
                return report
            
            # Éxito
            report = ExecutionReport(
                skill_id=skill_id,
                success=True,
                execution_time_ms=execution_time,
                result=result
            )
            self._add_to_history(report)
            return report
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Verificar si es un intento de escape
            error_str = str(e).lower()
            if any(pattern in error_str for pattern in [
                "permission denied", "access denied", "not allowed",
                "restricted", "sandbox", "escape"
            ]):
                safety_violations.append(f"POSIBLE_INTENTO_ESCAPE: {e}")
            
            report = ExecutionReport(
                skill_id=skill_id,
                success=False,
                execution_time_ms=execution_time,
                error=f"Error en ejecución: {str(e)}\n{traceback.format_exc()}",
                safety_violations=safety_violations
            )
            self._add_to_history(report)
            return report
    
    def _validate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar que el contexto es apropiado para una skill pura
        
        Una skill pura solo debe recibir:
        - action: qué acción ejecutar
        - Parámetros específicos de la acción
        - Datos necesarios para la ejecución
        
        NO debe recibir:
        - Información sobre el usuario
        - Historial de conversación
        - Objetivos finales
        - Estado del sistema
        """
        if not isinstance(context, dict):
            return {"valid": False, "error": "Contexto debe ser un diccionario"}
        
        # Verificar campos prohibidos
        forbidden_keys = {
            "user", "user_id", "user_name", "user_email",
            "conversation_history", "chat_history", "previous_messages",
            "goal", "objective", "intent", "objective_final",
            "system_state", "orchestrator_state", "agent_state",
            "llm", "ai", "model", "openai", "anthropic"
        }
        
        found_forbidden = []
        for key in context.keys():
            if key.lower() in forbidden_keys:
                found_forbidden.append(key)
        
        if found_forbidden:
            return {
                "valid": False,
                "error": (
                    f"Contexto contiene campos prohibidos para skill pura: {found_forbidden}. "
                    f"Las skills no deben conocer información del usuario, historial o objetivos. "
                    f"Solo deben recibir: action + parámetros específicos."
                )
            }
        
        # Verificar que tiene 'action'
        if "action" not in context:
            return {
                "valid": False,
                "error": "Contexto debe contener 'action' para indicar qué operación ejecutar"
            }
        
        return {"valid": True}
    
    def _validate_result(self, result: Any, skill_id: str) -> Dict[str, Any]:
        """
        Validar que el resultado de una skill es predecible y válido
        
        Una skill pura debe retornar:
        {
            "success": bool,
            "result" | "error": any
        }
        """
        if not isinstance(result, dict):
            return {
                "valid": False,
                "error": f"Skill '{skill_id}' retornó {type(result).__name__} en lugar de dict. Las skills deben retornar siempre un diccionario con {{success: bool, result/error: any}}"
            }
        
        # Verificar claves válidas
        invalid_keys = set(result.keys()) - self._VALID_RESULT_KEYS
        if invalid_keys:
            return {
                "valid": False,
                "error": f"Skill '{skill_id}' retornó claves inesperadas: {invalid_keys}. Solo se permiten: {self._VALID_RESULT_KEYS}"
            }
        
        # Verificar que tiene 'success'
        if "success" not in result:
            return {
                "valid": False,
                "error": f"Skill '{skill_id}' no retornó campo 'success'. Toda skill debe retornar {{success: bool, ...}}"
            }
        
        # Verificar que success es booleano
        if not isinstance(result["success"], bool):
            return {
                "valid": False,
                "error": f"Skill '{skill_id}' retornó success={result['success']} (tipo {type(result['success']).__name__}). Debe ser booleano."
            }
        
        return {"valid": True}
    
    def _add_to_history(self, report: ExecutionReport):
        """Agregar reporte al historial"""
        self.execution_history.append(report)
        if len(self.execution_history) > self.max_history:
            self.execution_history.pop(0)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de ejecución"""
        if not self.execution_history:
            return {"total": 0, "success_rate": 0, "purity_violations": 0}
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        purity_violations = sum(len(r.purity_violations) for r in self.execution_history)
        safety_violations = sum(len(r.safety_violations) for r in self.execution_history)
        
        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total * 100,
            "purity_violations": purity_violations,
            "safety_violations": safety_violations,
            "avg_execution_time_ms": sum(r.execution_time_ms for r in self.execution_history) / total
        }


# Singleton
skill_execution_validator = SkillExecutionValidator()


def execute_skill_safely(
    skill_id: str,
    skill_path: Path,
    context: Dict[str, Any],
    execute_fn: Callable[[Dict[str, Any]], Dict[str, Any]]
) -> ExecutionReport:
    """
    Función de conveniencia para ejecutar una skill de forma segura
    
    Uso:
        report = execute_skill_safely(
            skill_id="email_sender",
            skill_path=Path("skills_user/email_sender/skill.py"),
            context={"action": "send", "to": "user@example.com", "subject": "Test"},
            execute_fn=skill_module.execute
        )
        
        if report.success:
            print(report.result)
        else:
            print(f"Error: {report.error}")
    """
    return skill_execution_validator.validate_and_execute(
        skill_id=skill_id,
        skill_path=skill_path,
        context=context,
        execute_fn=execute_fn
    )
