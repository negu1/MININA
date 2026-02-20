"""
MININA v3.0 - Skill Static Analyzer
Análisis estático de código de skills mediante AST
"""

import ast
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Tuple, Any
from pathlib import Path

from core.security.skill_security_constants import (
    DEFAULT_FORBIDDEN_MODULES,
    DEFAULT_FORBIDDEN_CALLS,
    NETWORK_MODULES,
    SENSITIVE_ENV_VARS,
)


@dataclass
class StaticAnalysisResult:
    """Resultado de análisis estático"""
    is_safe: bool
    skill_id: str
    name: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    permissions_required: Set[str] = field(default_factory=set)
    detected_operations: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_safe": self.is_safe,
            "skill_id": self.skill_id,
            "name": self.name,
            "errors": self.errors,
            "warnings": self.warnings,
            "permissions_required": list(self.permissions_required),
            "detected_operations": self.detected_operations,
        }


class SkillStaticAnalyzer:
    """
    Analizador estático de código de skills.
    Examina el AST (Abstract Syntax Tree) para detectar:
    - Imports prohibidos
    - Llamadas peligrosas
    - Acceso a variables sensibles
    - Operaciones de red/filesystem
    """
    
    def __init__(self):
        self.forbidden_modules = DEFAULT_FORBIDDEN_MODULES
        self.forbidden_calls = DEFAULT_FORBIDDEN_CALLS
        self.network_modules = NETWORK_MODULES
        
    def analyze_file(self, file_path: Path, skill_id: str = "", name: str = "") -> StaticAnalysisResult:
        """Analizar un archivo skill.py"""
        try:
            code = file_path.read_text(encoding="utf-8")
            return self.analyze_code(code, skill_id, name)
        except Exception as e:
            return StaticAnalysisResult(
                is_safe=False,
                skill_id=skill_id,
                name=name,
                errors=[f"Error leyendo archivo: {str(e)}"]
            )
    
    def analyze_code(self, code: str, skill_id: str = "", name: str = "") -> StaticAnalysisResult:
        """Analizar código fuente directamente"""
        errors = []
        warnings = []
        permissions_required = set()
        detected_operations = []
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            line_num = e.lineno if e.lineno else "?"
            col_num = e.offset if e.offset else "?"
            return StaticAnalysisResult(
                is_safe=False,
                skill_id=skill_id,
                name=name,
                errors=[f"Error de sintaxis en línea {line_num}, columna {col_num}: {e.msg}"]
            )
        except Exception as e:
            return StaticAnalysisResult(
                is_safe=False,
                skill_id=skill_id,
                name=name,
                errors=[f"Código Python inválido: {str(e)}"]
            )
        
        # Verificar que tiene función execute
        has_execute = any(
            isinstance(node, ast.FunctionDef) and node.name == "execute"
            for node in ast.walk(tree)
        )
        if not has_execute:
            errors.append("La skill debe exponer una función execute(context)")
        
        # Analizar imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = (alias.name or "").split(".")[0]
                    
                    # Verificar módulos prohibidos
                    if module in self.forbidden_modules:
                        errors.append(f"Import prohibido detectado: '{module}' - Riesgo de seguridad")
                    
                    # Detectar módulos de red
                    if module in self.network_modules:
                        permissions_required.add("network")
                        detected_operations.append({
                            "type": "network_module",
                            "module": module,
                            "line": getattr(node, "lineno", 0),
                        })
                    
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                
                if module in self.forbidden_modules:
                    errors.append(f"Import prohibido detectado: '{module}' - Riesgo de seguridad")
                
                if module in self.network_modules:
                    permissions_required.add("network")
                    detected_operations.append({
                        "type": "network_module",
                        "module": module,
                        "line": getattr(node, "lineno", 0),
                    })
            
            # Analizar llamadas a funciones
            elif isinstance(node, ast.Call):
                # Detectar eval/exec/compile/__import__
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden_calls:
                        errors.append(f"Llamada prohibida detectada: {node.func.id}() - Ejecución de código dinámico")
                
                # Detectar os.system, subprocess, etc.
                if isinstance(node.func, ast.Attribute):
                    attr = node.func.attr
                    if attr in {"system", "popen", "Popen", "run", "call", "check_output"}:
                        errors.append(f"Posible ejecución de comandos del sistema: .{attr}()")
                    
                    # Detectar acceso a variables de entorno
                    if attr in {"getenv", "environ", "getenvb"}:
                        warnings.append("Acceso a variables de entorno detectado")
                        detected_operations.append({
                            "type": "env_access",
                            "method": attr,
                            "line": getattr(node, "lineno", 0),
                        })
                    
                    # Detectar operaciones de archivo
                    if attr in {"remove", "unlink", "rmdir", "removedirs", "makedirs", "mkdir"}:
                        permissions_required.add("fs_write")
                        detected_operations.append({
                            "type": "file_operation",
                            "operation": attr,
                            "line": getattr(node, "lineno", 0),
                        })
        
        # Verificar strings que contengan variables sensibles
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                env_var = node.value
                if env_var in SENSITIVE_ENV_VARS:
                    warnings.append(f"Referencia a variable sensible: '{env_var}'")
                    detected_operations.append({
                        "type": "sensitive_env_var",
                        "variable": env_var,
                        "line": getattr(node, "lineno", 0),
                    })
        
        is_safe = len(errors) == 0
        
        return StaticAnalysisResult(
            is_safe=is_safe,
            skill_id=skill_id,
            name=name,
            errors=errors,
            warnings=warnings,
            permissions_required=permissions_required,
            detected_operations=detected_operations,
        )
    
    def analyze_directory(self, directory: Path) -> StaticAnalysisResult:
        """Analizar un directorio de skill completo"""
        skill_py = directory / "skill.py"
        
        if not skill_py.exists():
            return StaticAnalysisResult(
                is_safe=False,
                skill_id=directory.name,
                name=directory.name,
                errors=["No se encontró skill.py en el directorio"]
            )
        
        # Leer manifest si existe
        manifest = directory / "manifest.json"
        skill_id = directory.name
        name = directory.name
        
        if manifest.exists():
            try:
                import json
                data = json.loads(manifest.read_text(encoding="utf-8"))
                skill_id = data.get("id", skill_id)
                name = data.get("name", name)
            except:
                pass
        
        return self.analyze_file(skill_py, skill_id, name)
