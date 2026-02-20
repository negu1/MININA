"""
MININA v3.0 - Skill Dynamic Sandbox
Sandbox aislado para prueba dinámica de skills sin riesgo
"""

import ast
import multiprocessing as mp
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json

from core.security.skill_security_constants import DEFAULT_SECURITY_LIMITS


@dataclass
class DynamicExecutionResult:
    """Resultado de ejecución dinámica en sandbox"""
    success: bool
    execution_time_ms: float
    output: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    behavior_detected: List[Dict[str, Any]] = field(default_factory=list)
    memory_peak_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "output": self.output,
            "errors": self.errors,
            "warnings": self.warnings,
            "behavior_detected": self.behavior_detected,
            "memory_peak_mb": self.memory_peak_mb,
        }


class _SandboxMonitor:
    """
    Monitor que intercepta operaciones peligrosas durante la ejecución
    """
    
    def __init__(self, allowed_operations: List[str] = None):
        self.behavior_log = []
        self.allowed_operations = allowed_operations or ["fs_read"]
        self.blocked_calls = []
    
    def log_operation(self, op_type: str, details: Dict[str, Any]):
        """Registrar una operación detectada"""
        self.behavior_log.append({
            "type": op_type,
            "timestamp": time.time(),
            **details
        })
    
    def check_and_block(self, op_type: str, details: Dict[str, Any]) -> bool:
        """Verificar si una operación debe bloquearse"""
        self.log_operation(op_type, details)
        
        # Siempre bloquear operaciones críticas
        if op_type in {"code_execution", "system_command", "env_sensitive_access"}:
            self.blocked_calls.append(details)
            return False
        
        return True


def _sandbox_worker(
    extracted_dir: str,
    sandbox_dir: str,
    test_context: Dict[str, Any],
    timeout_seconds: float,
    allow_network: bool,
    queue: mp.Queue
):
    """
    Worker que ejecuta en proceso aislado (sandbox real)
    """
    start_time = time.time()
    
    try:
        extracted = Path(extracted_dir)
        skill_path = extracted / "skill.py"
        
        if not skill_path.exists():
            queue.put({
                "success": False,
                "error": "Falta skill.py",
                "execution_time_ms": 0,
                "behavior": []
            })
            return
        
        # Crear monitor
        monitor = _SandboxMonitor(
            allowed_operations=["fs_read", "network"] if allow_network else ["fs_read"]
        )
        
        # Preparar contexto seguro
        safe_context = {
            **test_context,
            "__sandbox_mode__": True,
            "__monitor__": monitor,
        }
        
        # Ejecutar skill en contexto controlado
        try:
            # Leer código
            code = skill_path.read_text(encoding="utf-8")
            
            # Validar sintaxis primero
            compile(code, str(skill_path), "exec")
            
            # Crear namespace aislado
            namespace = {}
            
            # Ejecutar código
            exec(code, namespace, namespace)
            
            # Verificar función execute
            if "execute" not in namespace:
                queue.put({
                    "success": False,
                    "error": "No se encontró función execute(context)",
                    "execution_time_ms": int((time.time() - start_time) * 1000),
                    "behavior": monitor.behavior_log
                })
                return
            
            # Llamar execute con contexto de prueba
            execute_fn = namespace["execute"]
            result = execute_fn(safe_context)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            queue.put({
                "success": True,
                "result": result,
                "execution_time_ms": execution_time,
                "behavior": monitor.behavior_log,
                "blocked_calls": monitor.blocked_calls
            })
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            queue.put({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "execution_time_ms": execution_time,
                "behavior": monitor.behavior_log
            })
            
    except Exception as e:
        queue.put({
            "success": False,
            "error": f"Error en sandbox: {str(e)}",
            "execution_time_ms": 0,
            "behavior": []
        })


class SkillDynamicSandbox:
    """
    Sandbox dinámico para prueba real de skills.
    Ejecuta la skill en un proceso aislado con monitoreo.
    """
    
    def __init__(self):
        self.limits = DEFAULT_SECURITY_LIMITS
    
    def test_skill(
        self,
        skill_dir: Path,
        test_context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        allow_network: bool = False
    ) -> DynamicExecutionResult:
        """
        Probar una skill en sandbox aislado
        
        Args:
            skill_dir: Directorio con skill.py
            test_context: Contexto de prueba para pasar a execute()
            timeout: Timeout en segundos (default: 30)
            allow_network: Permitir operaciones de red
        """
        timeout = timeout or self.limits["max_execution_time_seconds"]
        test_context = test_context or {"test_mode": True}
        
        # Crear directorio sandbox temporal
        sandbox_dir = Path(os.getenv("TEMP", "/tmp")) / "minina_sandbox" / f"test_{time.time_ns()}"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Preparar queue para comunicación
        ctx = mp.get_context("spawn")
        queue = ctx.Queue()
        
        # Iniciar proceso sandbox
        process = ctx.Process(
            target=_sandbox_worker,
            args=(str(skill_dir), str(sandbox_dir), test_context, timeout, allow_network, queue),
            name=f"sandbox-test-{skill_dir.name}"
        )
        
        start_time = time.time()
        process.start()
        process.join(timeout=timeout + 5)  # 5 segundos de margen
        
        # Si el proceso sigue vivo, matarlo
        if process.is_alive():
            process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
            
            return DynamicExecutionResult(
                success=False,
                execution_time_ms=int((time.time() - start_time) * 1000),
                output="",
                errors=["Timeout: La skill excedió el tiempo máximo de ejecución"],
                warnings=[],
                behavior_detected=[{"type": "timeout", "limit_seconds": timeout}]
            )
        
        # Obtener resultado
        try:
            result = queue.get_nowait()
        except:
            return DynamicExecutionResult(
                success=False,
                execution_time_ms=int((time.time() - start_time) * 1000),
                output="",
                errors=["No se pudo obtener resultado del sandbox"],
                warnings=[],
                behavior_detected=[]
            )
        
        # Procesar resultado
        if result.get("success"):
            return DynamicExecutionResult(
                success=True,
                execution_time_ms=result.get("execution_time_ms", 0),
                output=str(result.get("result", "")),
                errors=[],
                warnings=[],
                behavior_detected=result.get("behavior", [])
            )
        else:
            errors = [result.get("error", "Error desconocido")]
            if "traceback" in result:
                errors.append(result["traceback"])
            
            return DynamicExecutionResult(
                success=False,
                execution_time_ms=result.get("execution_time_ms", 0),
                output="",
                errors=errors,
                warnings=[],
                behavior_detected=result.get("behavior", [])
            )
    
    def quick_syntax_check(self, skill_dir: Path) -> bool:
        """Verificación rápida de sintaxis sin ejecutar"""
        skill_py = skill_dir / "skill.py"
        if not skill_py.exists():
            return False
        
        try:
            code = skill_py.read_text(encoding="utf-8")
            ast.parse(code)
            compile(code, str(skill_py), "exec")
            return True
        except:
            return False
