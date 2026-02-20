"""
MININA v3.0 - Skill Analyzer
Análisis funcional de skills - describe qué hace una skill
"""

import ast
import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from pathlib import Path


@dataclass
class SkillFunctionality:
    """Descripción funcional de una skill"""
    skill_id: str
    name: str
    description: str
    purpose: str  # "Qué hace esta skill en lenguaje humano"
    operations: List[Dict[str, Any]] = field(default_factory=list)
    inputs_expected: List[str] = field(default_factory=list)
    outputs_expected: List[str] = field(default_factory=list)
    permissions_used: Set[str] = field(default_factory=set)
    risk_level: str = "unknown"  # "low", "medium", "high"
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "operations": self.operations,
            "inputs_expected": self.inputs_expected,
            "outputs_expected": self.outputs_expected,
            "permissions_used": list(self.permissions_used),
            "risk_level": self.risk_level,
            "dependencies": self.dependencies,
        }
    
    def to_human_readable(self) -> str:
        """Generar descripción en lenguaje natural"""
        lines = [
            f"📦 Skill: {self.name}",
            f"🆔 ID: {self.skill_id}",
            f"📝 Descripción: {self.description}",
            f"🎯 Propósito: {self.purpose}",
            f"⚠️ Nivel de riesgo: {self.risk_level.upper()}",
            "",
            "🔧 Operaciones detectadas:",
        ]
        
        for op in self.operations:
            op_type = op.get("type", "unknown")
            desc = op.get("description", "Operación")
            lines.append(f"  • {desc}")
        
        if self.inputs_expected:
            lines.extend(["", "📥 Entradas esperadas:"])
            for inp in self.inputs_expected:
                lines.append(f"  • {inp}")
        
        if self.outputs_expected:
            lines.extend(["", "📤 Salidas esperadas:"])
            for out in self.outputs_expected:
                lines.append(f"  • {out}")
        
        if self.permissions_used:
            lines.extend(["", "🔐 Permisos requeridos:"])
            for perm in self.permissions_used:
                lines.append(f"  • {perm}")
        
        return "\n".join(lines)


class SkillAnalyzer:
    """
    Analizador funcional de skills.
    Determina qué hace una skill sin ejecutarla.
    """
    
    # Patrones de operaciones comunes
    OPERATION_PATTERNS = {
        "file_read": {
            "keywords": ["open", "read", "read_text", "read_bytes", "json.load", "csv.reader"],
            "description": "Lee archivos del sistema",
        },
        "file_write": {
            "keywords": ["write", "save", "dump", "to_csv", "to_json"],
            "description": "Escribe/Guarda archivos",
        },
        "http_request": {
            "keywords": ["requests.get", "requests.post", "httpx", "urllib"],
            "description": "Realiza peticiones HTTP/Red",
        },
        "data_processing": {
            "keywords": ["pandas", "numpy", "process", "transform", "parse"],
            "description": "Procesa o transforma datos",
        },
        "email": {
            "keywords": ["email", "smtp", "send_mail", "imap"],
            "description": "Operaciones con email",
        },
        "database": {
            "keywords": ["sql", "sqlite", "postgres", "mysql", "query"],
            "description": "Acceso a bases de datos",
        },
        "web_scraping": {
            "keywords": ["beautifulsoup", "bs4", "scrape", "crawl", "html.parser"],
            "description": "Extracción de datos web (scraping)",
        },
        "image_processing": {
            "keywords": ["pillow", "pil", "image", "opencv", "cv2"],
            "description": "Procesamiento de imágenes",
        },
        "pdf": {
            "keywords": ["pdf", "pypdf", "pdfplumber"],
            "description": "Operaciones con PDFs",
        },
        "excel": {
            "keywords": ["excel", "xlsx", "openpyxl", "xlrd"],
            "description": "Operaciones con Excel",
        },
    }
    
    def analyze_directory(self, skill_dir: Path) -> SkillFunctionality:
        """Analizar un directorio de skill completo"""
        # Leer manifest
        manifest_path = skill_dir / "manifest.json"
        skill_id = skill_dir.name
        name = skill_dir.name
        description = ""
        
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                skill_id = data.get("id", skill_id)
                name = data.get("name", name)
                description = data.get("description", "")
            except:
                pass
        
        # Analizar código
        skill_py = skill_dir / "skill.py"
        if not skill_py.exists():
            return SkillFunctionality(
                skill_id=skill_id,
                name=name,
                description="No se encontró skill.py",
                purpose="Skill incompleta",
                risk_level="high"
            )
        
        try:
            code = skill_py.read_text(encoding="utf-8")
            return self.analyze_code(code, skill_id, name, description)
        except Exception as e:
            return SkillFunctionality(
                skill_id=skill_id,
                name=name,
                description=f"Error analizando: {str(e)}",
                purpose="Error",
                risk_level="high"
            )
    
    def analyze_code(
        self,
        code: str,
        skill_id: str,
        name: str,
        description: str = ""
    ) -> SkillFunctionality:
        """Analizar código fuente de una skill"""
        
        try:
            tree = ast.parse(code)
        except:
            return SkillFunctionality(
                skill_id=skill_id,
                name=name,
                description="Código inválido",
                purpose="Error de sintaxis",
                risk_level="high"
            )
        
        operations = []
        permissions = set()
        inputs_expected = []
        outputs_expected = []
        dependencies = []
        
        # Analizar imports (dependencias)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    dependencies.append(module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    dependencies.append(module)
        
        # Detectar operaciones por patrones
        code_lower = code.lower()
        for op_type, pattern in self.OPERATION_PATTERNS.items():
            for keyword in pattern["keywords"]:
                if keyword.lower() in code_lower:
                    operations.append({
                        "type": op_type,
                        "description": pattern["description"],
                        "keyword": keyword,
                    })
                    # Asignar permisos según operación
                    if op_type in ["file_read", "file_write"]:
                        permissions.add("fs_read")
                        if op_type == "file_write":
                            permissions.add("fs_write")
                    elif op_type == "http_request":
                        permissions.add("network")
                    elif op_type in ["email", "database", "web_scraping"]:
                        permissions.add("network")
                    break
        
        # Analizar función execute para inputs/outputs
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                # Buscar return statements para outputs
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Return):
                        if subnode.value:
                            if isinstance(subnode.value, ast.Dict):
                                for key in subnode.value.keys:
                                    if isinstance(key, ast.Constant):
                                        outputs_expected.append(str(key.value))
                            elif isinstance(subnode.value, ast.Constant):
                                outputs_expected.append("result")
                
                # Buscar uso de context
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Subscript):
                        if isinstance(subnode.value, ast.Name) and subnode.value.id == "context":
                            if isinstance(subnode.slice, ast.Constant):
                                inputs_expected.append(str(subnode.slice.value))
        
        # Determinar propósito
        purpose = self._infer_purpose(operations, dependencies, name, description)
        
        # Calcular nivel de riesgo
        risk_level = self._calculate_risk(operations, permissions, dependencies, code)
        
        return SkillFunctionality(
            skill_id=skill_id,
            name=name,
            description=description or purpose,
            purpose=purpose,
            operations=operations,
            inputs_expected=list(set(inputs_expected)),
            outputs_expected=list(set(outputs_expected)),
            permissions_used=permissions,
            risk_level=risk_level,
            dependencies=list(set(dependencies)),
        )
    
    def _infer_purpose(
        self,
        operations: List[Dict[str, Any]],
        dependencies: List[str],
        name: str,
        description: str
    ) -> str:
        """Inferir el propósito de la skill en lenguaje humano"""
        
        if description:
            return description
        
        # Construir propósito basado en operaciones
        op_types = [op["type"] for op in operations]
        
        if "file_read" in op_types and "file_write" in op_types:
            return f"Procesa y transforma archivos (lee entrada, genera salida)"
        elif "http_request" in op_types or "web_scraping" in op_types:
            return f"Obtiene datos de internet/web y los procesa"
        elif "email" in op_types:
            return f"Gestiona operaciones de email (enviar/leer/organizar)"
        elif "database" in op_types:
            return f"Interactúa con bases de datos (consultas/almacenamiento)"
        elif "data_processing" in op_types:
            return f"Procesa y analiza datos"
        elif "image_processing" in op_types:
            return f"Procesa y manipula imágenes"
        elif "pdf" in op_types:
            return f"Opera con documentos PDF (lee/escribe/modifica)"
        elif "excel" in op_types:
            return f"Trabaja con hojas de cálculo Excel"
        
        # Default basado en nombre
        return f"Automatiza tareas relacionadas con: {name}"
    
    def _calculate_risk(
        self,
        operations: List[Dict[str, Any]],
        permissions: Set[str],
        dependencies: List[str],
        code: str
    ) -> str:
        """Calcular nivel de riesgo de la skill"""
        risk_score = 0
        
        # Riesgo por permisos
        if "network" in permissions:
            risk_score += 2
        if "fs_write" in permissions:
            risk_score += 2
        if "fs_read" in permissions:
            risk_score += 1
        
        # Riesgo por operaciones específicas
        op_types = [op["type"] for op in operations]
        high_risk_ops = ["database", "email", "web_scraping"]
        for op in high_risk_ops:
            if op in op_types:
                risk_score += 1
        
        # Riesgo por código peligroso
        dangerous_patterns = [
            "eval(", "exec(", "__import__", "os.system", "subprocess",
            "delete", "remove", "unlink", "rmtree"
        ]
        for pattern in dangerous_patterns:
            if pattern in code.lower():
                risk_score += 3
        
        # Determinar nivel
        if risk_score >= 6:
            return "high"
        elif risk_score >= 3:
            return "medium"
        else:
            return "low"
