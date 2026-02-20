#!/usr/bin/env python3
"""
MiIA WebUI Validator
Sistema de validación para detectar errores estructurales en WebUI.py
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class ValidationError:
    line: int
    severity: str  # 'error', 'warning', 'info'
    message: str
    context: str
    suggestion: str

class WebUIValidator:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.errors: List[ValidationError] = []
        self.lines: List[str] = []
        self.html_start_line: int = 0
        self.html_end_line: int = 0
        
    def load_file(self) -> bool:
        """Carga el archivo y encuentra el bloque HTML_TEMPLATE"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
            return True
        except Exception as e:
            self.errors.append(ValidationError(
                line=0, severity='error',
                message=f"No se pudo cargar el archivo: {e}",
                context="",
                suggestion="Verifica que el archivo existe y tiene permisos de lectura"
            ))
            return False
    
    def find_html_template(self) -> bool:
        """Encuentra las líneas de inicio y fin del HTML_TEMPLATE"""
        in_template = False
        template_depth = 0
        
        for i, line in enumerate(self.lines, 1):
            if 'HTML_TEMPLATE = r\'\'\'' in line or "HTML_TEMPLATE = r'''" in line:
                self.html_start_line = i
                in_template = True
                continue
                
            if in_template:
                # Buscar el cierre del template
                if "'''" in line and not line.strip().startswith('#'):
                    if template_depth == 0:
                        self.html_end_line = i
                        return True
                    template_depth -= 1
                
                # Contar triple quotes anidados
                if line.count("'''") > 0 and 'r\'\'\'' not in line:
                    template_depth += line.count("'''")
        
        if self.html_start_line == 0:
            self.errors.append(ValidationError(
                line=0, severity='error',
                message="No se encontró HTML_TEMPLATE",
                context="",
                suggestion="Verifica que HTML_TEMPLATE esté definido correctamente"
            ))
            return False
        return True
    
    def _extract_html_only(self, html_content: str) -> str:
        """Extrae solo el HTML real, ignorando JavaScript y strings"""
        result = []
        in_script = False
        in_string = False
        string_char = None
        i = 0
        while i < len(html_content):
            # Detectar inicio/fin de script
            if html_content[i:i+7] == '<script':
                in_script = True
                i += 1
                continue
            if html_content[i:i+9] == '</script>':
                in_script = False
                i += 1
                continue
            
            # Si estamos en script, ignorar strings
            if in_script:
                if not in_string:
                    if html_content[i] in '"\'`':
                        in_string = True
                        string_char = html_content[i]
                    elif html_content[i:i+2] in ('""', "''", '``'):
                        in_string = True
                        string_char = html_content[i:i+2]
                        i += 1
                else:
                    if html_content[i] == string_char:
                        if html_content[i-1] != '\\':  # No es escape
                            in_string = False
                            string_char = None
                i += 1
                continue
            
            result.append(html_content[i])
            i += 1
        
        return ''.join(result)
    
    def validate_html_structure(self) -> bool:
        """Valida la estructura HTML - balance de tags"""
        if self.html_start_line == 0 or self.html_end_line == 0:
            return False
            
        html_lines = self.lines[self.html_start_line:self.html_end_line-1]
        html_content = ''.join(html_lines)
        
        # Extraer solo HTML real, ignorar JavaScript
        html_only = self._extract_html_only(html_content)
        
        # Tags importantes que deben estar balanceados
        critical_tags = ['div', 'section', 'main', 'aside', 'nav', 'article', 'header', 'footer']
        tag_stack = []
        line_numbers = []
        
        # Calcular línea real para cada posición en html_only
        line_map = []
        current_line = self.html_start_line
        for line in html_lines:
            for _ in line:
                line_map.append(current_line)
            current_line += 1
        
        # Buscar tags en el HTML limpio
        for match in re.finditer(r'<(/?)(div|section|main|aside|nav|article|header|footer)[^>]*>', html_only, re.IGNORECASE):
            pos = match.start()
            actual_line = line_map[pos] if pos < len(line_map) else self.html_start_line
            
            is_closing = match.group(1) == '/'
            tag_name = match.group(2).lower()
            
            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                    line_numbers.pop()
                else:
                    expected = tag_stack[-1] if tag_stack else "ninguno"
                    self.errors.append(ValidationError(
                        line=actual_line,
                        severity='error',
                        message=f"Tag </{tag_name}> mal cerrado en línea {actual_line}",
                        context=f"Se esperaba </{expected}> pero se encontró </{tag_name}>",
                        suggestion=f"Revisa la estructura HTML cerca de la línea {actual_line}. Posible div extra o faltante."
                    ))
            else:
                tag_stack.append(tag_name)
                line_numbers.append(actual_line)
        
        # Tags que quedaron abiertos
        if tag_stack:
            for tag, line in zip(tag_stack, line_numbers):
                self.errors.append(ValidationError(
                    line=line,
                    severity='error',
                    message=f"Tag <{tag}> abierto en línea {line} pero nunca cerrado",
                    context=f"Falta tag de cierre </{tag}>",
                    suggestion=f"Agrega </{tag}> después de la línea {self.html_end_line} o revisa la estructura"
                ))
        
        return len([e for e in self.errors if e.severity == 'error']) == 0
    
    def validate_python_syntax(self) -> bool:
        """Valida sintaxis Python después del HTML_TEMPLATE"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, self.file_path, 'exec')
            return True
        except SyntaxError as e:
            self.errors.append(ValidationError(
                line=e.lineno or 0,
                severity='error',
                message=f"Error de sintaxis Python: {e.msg}",
                context=e.text or "",
                suggestion="Revisa el código Python cerca de esta línea"
            ))
            return False
        except Exception as e:
            self.errors.append(ValidationError(
                line=0, severity='error',
                message=f"Error inesperado al compilar: {e}",
                context="",
                suggestion="Verifica que el archivo no esté corrupto"
            ))
            return False
    
    def validate_indentation(self) -> bool:
        """Valida que las funciones después de HTML_TEMPLATE estén correctamente indentadas"""
        if self.html_end_line == 0:
            return False
            
        # Buscar la primera función después del HTML_TEMPLATE
        for i in range(self.html_end_line, min(self.html_end_line + 20, len(self.lines))):
            line = self.lines[i]
            # Buscar definición de función
            if re.match(r'^def\s+\w+', line):
                if line.startswith('def '):
                    # Función no indentada - verificar si está al nivel correcto
                    if i > 0 and self.lines[i-1].strip() == '':
                        # Función a nivel de módulo después del template - esto es correcto
                        return True
                elif not line.startswith('    def ') and not line.startswith('\tdef '):
                    self.errors.append(ValidationError(
                        line=i+1,
                        severity='warning',
                        message=f"Función '{line.strip()}' tiene indentación inusual",
                        context=line.rstrip(),
                        suggestion="Las funciones después de HTML_TEMPLATE deben tener 4 espacios de indentación si están anidadas, o 0 si están a nivel de módulo"
                    ))
        return True
    
    def validate_panel_structure(self) -> bool:
        """Valida que todos los paneles tengan estructura correcta"""
        if self.html_start_line == 0:
            return False
            
        html_content = ''.join(self.lines[self.html_start_line:self.html_end_line-1])
        
        # Verificar que cada panel tenga apertura y cierre
        panels = re.findall(r'<div id="panel-(\w+)"[^>]*>', html_content)
        for panel_id in panels:
            # Contar cuántas veces aparece este panel
            openings = len(re.findall(rf'<div id="panel-{panel_id}"', html_content))
            closings = len(re.findall(rf'</div><!--.*panel-{panel_id}.*-->', html_content)) + \
                      len(re.findall(rf'<!--.*panel-{panel_id}.*--></div>', html_content))
            
            if openings != 1:
                self.errors.append(ValidationError(
                    line=0, severity='error',
                    message=f"Panel '{panel_id}' aparece {openings} veces (debe ser 1)",
                    context=f"id='panel-{panel_id}'",
                    suggestion=f"Elimina las definiciones duplicadas del panel '{panel_id}'"
                ))
        
        return True
    
    def validate_javascript_functions(self) -> bool:
        """Valida que las funciones JavaScript críticas existan"""
        if self.html_start_line == 0:
            return False
            
        html_content = ''.join(self.lines[self.html_start_line:self.html_end_line-1])
        
        critical_functions = [
            'showPanel', 'loadPcFolder', 'sendChat', 'updateDashboard',
            'loadUserSkills', 'saveTelegramConfig', 'checkForUpdates'
        ]
        
        for func in critical_functions:
            if f'function {func}(' not in html_content:
                self.errors.append(ValidationError(
                    line=0, severity='warning',
                    message=f"Función JavaScript crítica '{func}' no encontrada",
                    context="",
                    suggestion=f"Verifica que la función {func} esté definida en el script"
                ))
        
        return True
    
    def generate_report(self) -> str:
        """Genera reporte detallado de validación"""
        lines = []
        lines.append("=" * 80)
        lines.append("MIIA WEBUI VALIDATOR - REPORTE DE VALIDACIÓN")
        lines.append("=" * 80)
        lines.append(f"Archivo: {self.file_path}")
        lines.append(f"Líneas totales: {len(self.lines)}")
        lines.append(f"HTML_TEMPLATE: líneas {self.html_start_line} - {self.html_end_line}")
        lines.append("")
        
        if not self.errors:
            lines.append("[OK] NO SE ENCONTRARON ERRORES")
            lines.append("El archivo pasa todas las validaciones.")
            return '\n'.join(lines)
        
        # Agrupar errores por severidad
        errors = [e for e in self.errors if e.severity == 'error']
        warnings = [e for e in self.errors if e.severity == 'warning']
        
        if errors:
            lines.append(f"[ERR] ERRORES ({len(errors)}):")
            lines.append("-" * 80)
            for err in errors:
                lines.append(f"\nLínea {err.line}: {err.message}")
                if err.context:
                    lines.append(f"  Contexto: {err.context[:80]}")
                lines.append(f"  → {err.suggestion}")
        
        if warnings:
            lines.append(f"\n[WRN] ADVERTENCIAS ({len(warnings)}):")
            lines.append("-" * 80)
            for err in warnings:
                lines.append(f"\nLínea {err.line}: {err.message}")
                lines.append(f"  → {err.suggestion}")
        
        lines.append("")
        lines.append("=" * 80)
        lines.append(f"Total: {len(errors)} errores, {len(warnings)} advertencias")
        
        return '\n'.join(lines)
    
    def validate(self) -> bool:
        """Ejecuta todas las validaciones"""
        print(">>> Iniciando validacion de WebUI.py...")
        print("")
        
        if not self.load_file():
            return False
        
        print(f">>> Archivo cargado: {len(self.lines)} lineas")
        
        if not self.find_html_template():
            return False
        
        print(f">>> HTML_TEMPLATE encontrado: lineas {self.html_start_line} - {self.html_end_line}")
        print("")
        
        # Ejecutar validaciones
        print(">>> Validando sintaxis Python...")
        self.validate_python_syntax()
        
        print(">>> Validando estructura HTML...")
        self.validate_html_structure()
        
        print(">>> Validando indentacion...")
        self.validate_indentation()
        
        print(">>> Validando estructura de paneles...")
        self.validate_panel_structure()
        
        print(">>> Validando funciones JavaScript...")
        self.validate_javascript_functions()
        
        print("")
        
        # Mostrar reporte
        report = self.generate_report()
        print(report)
        
        return len([e for e in self.errors if e.severity == 'error']) == 0


def main():
    """Función principal"""
    file_path = sys.argv[1] if len(sys.argv) > 1 else 'core/WebUI.py'
    
    validator = WebUIValidator(file_path)
    success = validator.validate()
    
    if success:
        print("\n✅ VALIDACIÓN EXITOSA")
        sys.exit(0)
    else:
        print("\n❌ VALIDACIÓN FALLIDA")
        print("\nCorrige los errores antes de continuar.")
        sys.exit(1)


if __name__ == '__main__':
    main()
