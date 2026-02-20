"""
MININA v3.0 - Skill Purity Validator
Sistema de validación de pureza de skills - 3 capas de protección

PRINCIPIO FUNDAMENTAL:
- Skill = Caja negra: INPUT -> ACCIÓN -> OUTPUT
- Skill NO piensa, NO sabe del usuario, NO sabe del objetivo final
- Skill NO llama a otras skills (eso lo hace el Orchestrator)
- Contexto vive en el Agente, NO en la Skill
- Orquestación SIEMPRE externa

TEST DE PUREZA:
"Si ejecuto esta skill sola, sin IA, ¿funciona igual?"
Si SÍ -> Skill pura ✓
Si NO -> Skill está pensando, está mal ✗
"""

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import os


@dataclass
class PurityReport:
    """Reporte de pureza de una skill"""
    skill_id: str
    is_pure: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    input_contract: Dict[str, Any] = field(default_factory=dict)
    output_contract: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "is_pure": self.is_pure,
            "violations": self.violations,
            "warnings": self.warnings,
            "input_contract": self.input_contract,
            "output_contract": self.output_contract
        }


class SkillPurityValidator:
    """
    Validador de pureza de skills para MININA
    
    Detecta skills que:
    1. "Piensan" (llamadas a LLM, lógica condicional compleja)
    2. Acceden a contexto que no les corresponde
    3. Intentan llamar otras skills
    4. Intentan escapar del sandbox
    """
    
    # Patrones que indican que una skill "está pensando"
    _LLM_PATTERNS = {
        # Llamadas a APIs de IA
        "openai", "anthropic", "groq", "gemini", "claude", "gpt",
        # Módulos de IA comunes
        "langchain", "llama_index", "transformers", "torch",
        # Funciones de generación de texto
        "chat.completions", "completions.create", "generate_text",
        "ask_llm", "query_llm", "call_llm", "get_ai_response",
    }
    
    # Patrones de escape del sandbox
    _ESCAPE_PATTERNS = {
        # Acceso a sistema de archivos fuera del scope
        "__file__", "__name__", "sys.modules", "globals()", "locals()",
        # Manipulación de imports dinámicos
        "importlib", "__import__", "reload", "imp.",
        # Acceso a variables de entorno sensibles
        "os.environ", "getenv", "environ[",
        # Introspección
        "inspect.", "traceback.", "sys._getframe",
    }
    
    # Patrones de llamada a otras skills
    _SKILL_CALL_PATTERNS = {
        "execute(", "run_skill", "call_skill", "skill.execute",
        "import skill", "from skill", "skills[", "skill_registry",
    }
    
    # Funciones built-in peligrosas
    _DANGEROUS_BUILTINS = {
        "eval", "exec", "compile", "open", "input", "raw_input",
        "help", "dir", "vars", "globals", "locals", "getattr",
        "setattr", "delattr", "hasattr", "isinstance", "type",
    }
    
    # Patrones de decisión compleja (indican "pensamiento")
    _COMPLEX_LOGIC_PATTERNS = [
        # Múltiples niveles de if/else anidados
        r"if.*:\s*\n.*if.*:\s*\n.*if",
        # Lógica de decisión sobre contexto
        r"if.*context.*(?:user|goal|objective|history)",
        # Intento de "entender" la intención
        r"(?:intent|intention|understand|interpret)",
        # Fallbacks complejos que intentan "ayudar"
        r"(?:else.*try|except.*pass|fallback|alternative)",
    ]
    
    def __init__(self):
        self.violations: List[str] = []
        self.warnings: List[str] = []
    
    def validate_skill_file(self, skill_path: Path) -> PurityReport:
        """
        Validar un archivo skill.py completo
        
        Args:
            skill_path: Ruta al archivo skill.py
            
        Returns:
            PurityReport con el resultado de la validación
        """
        self.violations = []
        self.warnings = []
        
        if not skill_path.exists():
            return PurityReport(
                skill_id="unknown",
                is_pure=False,
                violations=["Archivo skill.py no encontrado"]
            )
        
        # Leer código
        try:
            code = skill_path.read_text(encoding="utf-8")
        except Exception as e:
            return PurityReport(
                skill_id="unknown",
                is_pure=False,
                violations=[f"Error leyendo skill: {e}"]
            )
        
        # Parse AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return PurityReport(
                skill_id="unknown",
                is_pure=False,
                violations=[f"Error de sintaxis: {e}"]
            )
        
        # Extraer skill_id del nombre del directorio padre
        skill_id = skill_path.parent.name
        
        # Validaciones
        self._check_has_execute_function(tree, skill_id)
        self._check_no_llm_calls(code, tree, skill_id)
        self._check_no_skill_calls(code, tree, skill_id)
        self._check_no_escape_patterns(code, tree, skill_id)
        self._check_simple_logic(tree, skill_id)
        self._check_input_contract(tree, skill_id)
        self._check_output_contract(tree, skill_id)
        self._check_no_global_state(tree, skill_id)
        
        is_pure = len(self.violations) == 0
        
        return PurityReport(
            skill_id=skill_id,
            is_pure=is_pure,
            violations=self.violations.copy(),
            warnings=self.warnings.copy(),
            input_contract=self._extract_input_contract(tree),
            output_contract=self._extract_output_contract(tree)
        )
    
    def _check_has_execute_function(self, tree: ast.AST, skill_id: str):
        """Verificar que existe función execute(context)"""
        has_execute = False
        execute_has_context = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                has_execute = True
                # Verificar que recibe context como parámetro
                args = node.args
                if args.args:
                    first_arg = args.args[0].arg
                    if first_arg == "context":
                        execute_has_context = True
                break
        
        if not has_execute:
            self.violations.append(
                "[VIOLACIÓN CRÍTICA] Skill debe tener función 'execute(context)'"
            )
        elif not execute_has_context:
            self.violations.append(
                "[VIOLACIÓN CRÍTICA] Función execute debe recibir 'context' como primer parámetro"
            )
    
    def _check_no_llm_calls(self, code: str, tree: ast.AST, skill_id: str):
        """Detectar llamadas a LLM o APIs de IA"""
        code_lower = code.lower()
        
        for pattern in self._LLM_PATTERNS:
            if pattern.lower() in code_lower:
                # Verificar si es solo un import o una llamada real
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if pattern.lower() in line.lower():
                        # Ignorar imports
                        if not line.strip().startswith(('import ', 'from ')):
                            self.violations.append(
                                f"[VIOLACIÓN CRÍTICA] Skill contiene llamada a IA/LLM "
                                f"(patrón: '{pattern}' en línea {i+1}). "
                                f"Las skills NO deben pensar, solo ejecutar."
                            )
                            return
        
        # Chequeo AST más profundo
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name:
                    func_lower = func_name.lower()
                    if any(llm in func_lower for llm in ['openai', 'anthropic', 'claude', 'gpt', 'llm', 'ai']):
                        self.violations.append(
                            f"[VIOLACIÓN CRÍTICA] Skill llama a función de IA: '{func_name}'. "
                            f"Las skills NO deben pensar, solo ejecutar."
                        )
                        return
    
    def _check_no_skill_calls(self, code: str, tree: ast.AST, skill_id: str):
        """Detectar intentos de llamar a otras skills"""
        code_lower = code.lower()
        
        for pattern in self._SKILL_CALL_PATTERNS:
            if pattern.lower() in code_lower:
                # Buscar la línea específica
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if pattern.lower() in line.lower():
                        # Ignorar comentarios
                        if not line.strip().startswith('#'):
                            self.violations.append(
                                f"[VIOLACIÓN CRÍTICA] Skill intenta llamar a otra skill "
                                f"(patrón: '{pattern}' en línea {i+1}). "
                                f"Solo el Orchestrator puede llamar skills. "
                                f"FLUJO: Humano -> Orchestrator -> Skill (una sola)"
                            )
                            return
    
    def _check_no_escape_patterns(self, code: str, tree: ast.AST, skill_id: str):
        """Detectar intentos de escapar del sandbox"""
        code_lower = code.lower()
        
        for pattern in self._ESCAPE_PATTERNS:
            if pattern.lower() in code_lower:
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if pattern.lower() in line.lower():
                        if not line.strip().startswith('#'):
                            self.violations.append(
                                f"[VIOLACIÓN CRÍTICA] Skill intenta acceder a recursos del sistema "
                                f"(patrón: '{pattern}' en línea {i+1}). "
                                f"Las skills deben ser cajas negras puras."
                            )
                            return
        
        # Chequeo de llamadas peligrosas
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in self._DANGEROUS_BUILTINS:
                    self.violations.append(
                        f"[VIOLACIÓN CRÍTICA] Skill usa función peligrosa: '{func_name}'. "
                        f"Las skills no deben usar eval, exec, compile, etc."
                    )
                    return
    
    def _check_simple_logic(self, tree: ast.AST, skill_id: str):
        """Verificar que la lógica sea simple (no piensa)"""
        # Contar niveles de anidamiento de if
        max_depth = 0
        
        def count_if_depth(node, current_depth=0):
            nonlocal max_depth
            if isinstance(node, ast.If):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            for child in ast.iter_child_nodes(node):
                count_if_depth(child, current_depth)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                count_if_depth(node, 0)
        
        if max_depth > 3:
            self.violations.append(
                f"[VIOLACIÓN] Lógica demasiado compleja ({max_depth} niveles de if anidados). "
                f"Las skills deben tener lógica simple: if action == X -> haz Y. "
                f"NO deben tomar decisiones complejas."
            )
        elif max_depth > 2:
            self.warnings.append(
                f"[ADVERTENCIA] Lógica con {max_depth} niveles de if. "
                f"Considera simplificar: la skill debe ser una caja negra simple."
            )
    
    def _check_input_contract(self, tree: ast.AST, skill_id: str):
        """Verificar que el input sea predecible"""
        # Buscar uso de .get() con defaults (buena práctica)
        # vs acceso directo [] (puede fallar)
        has_direct_access = False
        has_safe_access = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == "context":
                    has_direct_access = True
            
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name == "context.get":
                    has_safe_access = True
        
        if has_direct_access and not has_safe_access:
            self.warnings.append(
                "[ADVERTENCIA] Skill accede directamente a context[] sin .get(). "
                "Usa context.get('key', default) para ser más robusta."
            )
    
    def _check_output_contract(self, tree: ast.AST, skill_id: str):
        """Verificar que el output sea predecible"""
        # Buscar returns consistentes
        return_nodes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        return_nodes.append(child)
        
        if not return_nodes:
            self.violations.append(
                "[VIOLACIÓN CRÍTICA] Función execute no tiene return. "
                "Toda skill debe retornar un resultado predecible."
            )
        else:
            # Verificar que todos los returns sean dicts con success/error
            for ret in return_nodes:
                if not isinstance(ret.value, ast.Dict):
                    self.warnings.append(
                        "[ADVERTENCIA] Return no es un dict. "
                        "Las skills deben retornar siempre {success: bool, result/error: ...}"
                    )
    
    def _check_no_global_state(self, tree: ast.AST, skill_id: str):
        """Verificar que no accede a estado global"""
        # Buscar uso de variables globales
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                self.violations.append(
                    "[VIOLACIÓN CRÍTICA] Skill usa 'global'. "
                    "Las skills no deben tener estado global. "
                    "Todo el estado debe venir en context."
                )
                return
            
            if isinstance(node, ast.Name):
                if node.id in ['self', 'cls'] and isinstance(node.ctx, ast.Load):
                    # Podría ser uso de clase - verificar si es dentro de una clase
                    parent = None
                    # Esto es simplificado, en la práctica necesitaríamos el parent
                    pass
    
    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        """Extraer el nombre de una llamada de función"""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Manejar cosas como context.get, obj.method, etc.
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return None
    
    def _extract_input_contract(self, tree: ast.AST) -> Dict[str, Any]:
        """Extraer el contrato de input de la función execute"""
        contract = {
            "required": [],
            "optional": [],
            "description": ""
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                # Extraer docstring
                if (node.body and 
                    isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    contract["description"] = node.body[0].value.value
                
                # Buscar uso de .get() para detectar campos opcionales
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func_name = self._get_call_name(child)
                        if func_name == "context.get":
                            if child.args:
                                if isinstance(child.args[0], ast.Constant):
                                    contract["optional"].append(child.args[0].value)
                break
        
        return contract
    
    def _extract_output_contract(self, tree: ast.AST) -> Dict[str, Any]:
        """Extraer el contrato de output de los returns"""
        contract = {
            "success_field": False,
            "error_field": False,
            "result_field": False
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                        for key in child.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                if key.value == "success":
                                    contract["success_field"] = True
                                elif key.value == "error":
                                    contract["error_field"] = True
                                elif key.value == "result":
                                    contract["result_field"] = True
                break
        
        return contract
    
    def validate_skill_directory(self, skill_dir: Path) -> PurityReport:
        """Validar un directorio de skill completo"""
        skill_py = skill_dir / "skill.py"
        return self.validate_skill_file(skill_py)
    
    def batch_validate(self, skills_root: Path) -> List[PurityReport]:
        """Validar todas las skills en un directorio"""
        reports = []
        
        for skill_dir in skills_root.iterdir():
            if skill_dir.is_dir():
                skill_py = skill_dir / "skill.py"
                if skill_py.exists():
                    report = self.validate_skill_file(skill_py)
                    reports.append(report)
        
        return reports


# Singleton
skill_purity_validator = SkillPurityValidator()


def validate_skill_purity(skill_path: Path) -> PurityReport:
    """Función de conveniencia para validar pureza"""
    return skill_purity_validator.validate_skill_file(skill_path)


def is_skill_pure(skill_path: Path) -> bool:
    """Check rápido: ¿es pura esta skill?"""
    report = skill_purity_validator.validate_skill_file(skill_path)
    return report.is_pure


def get_purity_summary(skills_root: Path) -> Dict[str, Any]:
    """Obtener resumen de pureza de todas las skills"""
    validator = SkillPurityValidator()
    reports = validator.batch_validate(skills_root)
    
    pure_count = sum(1 for r in reports if r.is_pure)
    impure_count = len(reports) - pure_count
    
    return {
        "total_skills": len(reports),
        "pure_skills": pure_count,
        "impure_skills": impure_count,
        "purity_percentage": (pure_count / len(reports) * 100) if reports else 0,
        "violations_by_skill": {
            r.skill_id: r.violations for r in reports if not r.is_pure
        }
    }
