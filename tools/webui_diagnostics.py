#!/usr/bin/env python3
"""
MiIA WebUI Error Diagnostics
Sistema de diagnóstico para detectar problemas en tiempo de ejecución
"""

import re
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class WebUIDiagnostics:
    """Diagnóstico de problemas en WebUI.py"""
    
    def __init__(self, file_path: str = "core/WebUI.py"):
        self.file_path = Path(file_path)
        self.issues: List[Dict[str, Any]] = []
        self.lines: List[str] = []
        
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """Ejecuta diagnóstico completo"""
        print("🔍 Ejecutando diagnóstico completo de WebUI.py...\n")
        
        if not self._load_file():
            return {"success": False, "error": "No se pudo cargar el archivo"}
        
        checks = [
            ("Estructura HTML_TEMPLATE", self._check_html_template_structure),
            ("Balance de tags HTML", self._check_html_balance),
            ("Paneles duplicados", self._check_duplicate_panels),
            ("Funciones JavaScript críticas", self._check_critical_js_functions),
            ("Sintaxis Python", self._check_python_syntax),
            ("Importaciones", self._check_imports),
        ]
        
        results = {}
        for check_name, check_func in checks:
            print(f"  🧪 {check_name}...")
            try:
                result = check_func()
                results[check_name] = result
                status = "✅" if result.get("ok", False) else "❌"
                print(f"     {status} {result.get('message', '')}")
            except Exception as e:
                print(f"     ❌ Error: {e}")
                results[check_name] = {"ok": False, "error": str(e)}
        
        return {
            "success": all(r.get("ok", False) for r in results.values()),
            "timestamp": datetime.now().isoformat(),
            "file": str(self.file_path),
            "total_lines": len(self.lines),
            "checks": results,
            "issues": self.issues
        }
    
    def _load_file(self) -> bool:
        """Carga el archivo"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
            return True
        except Exception as e:
            self.issues.append({
                "type": "error",
                "message": f"Error cargando archivo: {e}",
                "line": 0
            })
            return False
    
    def _check_html_template_structure(self) -> Dict[str, Any]:
        """Verifica la estructura de HTML_TEMPLATE"""
        html_start = None
        html_end = None
        
        for i, line in enumerate(self.lines, 1):
            if "HTML_TEMPLATE = r'''" in line or 'HTML_TEMPLATE = r\'\'\'' in line:
                html_start = i
            elif html_start and "'''" in line and not line.strip().startswith("#"):
                html_end = i
                break
        
        if not html_start:
            return {"ok": False, "message": "No se encontró HTML_TEMPLATE", "line": 0}
        
        if not html_end:
            return {"ok": False, "message": "HTML_TEMPLATE no está cerrado", "line": html_start}
        
        return {
            "ok": True, 
            "message": f"HTML_TEMPLATE: líneas {html_start} - {html_end}",
            "html_start": html_start,
            "html_end": html_end
        }
    
    def _check_html_balance(self) -> Dict[str, Any]:
        """Verifica balance de tags HTML críticos"""
        result = self._check_html_template_structure()
        if not result["ok"]:
            return result
        
        html_lines = self.lines[result["html_start"]:result["html_end"]-1]
        html_content = ''.join(html_lines)
        
        # Contar tags críticos
        critical_tags = ['div', 'section', 'main', 'aside', 'nav']
        imbalances = []
        
        for tag in critical_tags:
            opens = len(re.findall(rf'<{tag}[\s>]', html_content, re.IGNORECASE))
            closes = len(re.findall(rf'</{tag}>', html_content, re.IGNORECASE))
            
            if opens != closes:
                imbalances.append(f"<{tag}>: {opens} aperturas, {closes} cierres")
                self.issues.append({
                    "type": "error",
                    "message": f"Tag <{tag}> desbalanceado: {opens} abre, {closes} cierra",
                    "line": result["html_start"]
                })
        
        if imbalances:
            return {"ok": False, "message": "; ".join(imbalances)}
        
        return {"ok": True, "message": "Todos los tags están balanceados"}
    
    def _check_duplicate_panels(self) -> Dict[str, Any]:
        """Verifica que no haya paneles duplicados"""
        result = self._check_html_template_structure()
        if not result["ok"]:
            return result
        
        html_content = ''.join(self.lines[result["html_start"]:result["html_end"]-1])
        
        panels = re.findall(r'<div id="panel-(\w+)"', html_content)
        duplicates = []
        
        for panel in set(panels):
            count = panels.count(panel)
            if count > 1:
                duplicates.append(f"panel-{panel}: {count} veces")
                self.issues.append({
                    "type": "error",
                    "message": f"Panel '{panel}' definido {count} veces",
                    "line": 0
                })
        
        if duplicates:
            return {"ok": False, "message": "; ".join(duplicates)}
        
        return {"ok": True, "message": f"{len(set(panels))} paneles únicos encontrados"}
    
    def _check_critical_js_functions(self) -> Dict[str, Any]:
        """Verifica funciones JavaScript críticas"""
        result = self._check_html_template_structure()
        if not result["ok"]:
            return result
        
        html_content = ''.join(self.lines[result["html_start"]:result["html_end"]-1])
        
        critical = [
            'showPanel', 'loadPcFolder', 'sendChat', 'updateDashboard',
            'toggleVoice', 'saveTelegramConfig', 'loadUserSkills'
        ]
        
        missing = []
        for func in critical:
            if f'function {func}(' not in html_content:
                missing.append(func)
                self.issues.append({
                    "type": "warning",
                    "message": f"Función '{func}' no encontrada",
                    "line": 0
                })
        
        if missing:
            return {"ok": False, "message": f"Faltan: {', '.join(missing)}"}
        
        return {"ok": True, "message": f"{len(critical)} funciones críticas presentes"}
    
    def _check_python_syntax(self) -> Dict[str, Any]:
        """Verifica sintaxis Python"""
        try:
            code = ''.join(self.lines)
            compile(code, str(self.file_path), 'exec')
            return {"ok": True, "message": "Sintaxis Python válida"}
        except SyntaxError as e:
            self.issues.append({
                "type": "error",
                "message": f"SyntaxError: {e.msg} en línea {e.lineno}",
                "line": e.lineno or 0
            })
            return {"ok": False, "message": f"Error línea {e.lineno}: {e.msg}"}
    
    def _check_imports(self) -> Dict[str, Any]:
        """Verifica importaciones necesarias"""
        required = ['fastapi', 'asyncio', 'json', 'logging']
        code = ''.join(self.lines)
        
        missing = []
        for imp in required:
            if f'import {imp}' not in code and f'from {imp}' not in code:
                missing.append(imp)
        
        if missing:
            return {"ok": False, "message": f"Faltan imports: {', '.join(missing)}"}
        
        return {"ok": True, "message": "Todas las importaciones necesarias presentes"}
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Genera reporte de diagnóstico"""
        lines = []
        lines.append("=" * 80)
        lines.append("MIIA WEBUI DIAGNOSTICS - REPORTE")
        lines.append("=" * 80)
        lines.append(f"Archivo: {results['file']}")
        lines.append(f"Líneas: {results['total_lines']}")
        lines.append(f"Timestamp: {results['timestamp']}")
        lines.append("")
        
        if results['success']:
            lines.append("✅ TODAS LAS VERIFICACIONES PASARON")
        else:
            lines.append("❌ SE ENCONTRARON PROBLEMAS")
        
        lines.append("")
        lines.append("Detalle de verificaciones:")
        lines.append("-" * 80)
        
        for check_name, result in results['checks'].items():
            status = "✅" if result.get("ok", False) else "❌"
            lines.append(f"{status} {check_name}: {result.get('message', '')}")
        
        if results['issues']:
            lines.append("")
            lines.append("Problemas encontrados:")
            lines.append("-" * 80)
            for issue in results['issues']:
                icon = "❌" if issue['type'] == 'error' else "⚠️"
                line_info = f" (línea {issue['line']})" if issue['line'] > 0 else ""
                lines.append(f"{icon} {issue['message']}{line_info}")
        
        lines.append("")
        lines.append("=" * 80)
        
        return '\n'.join(lines)


def main():
    """Función principal"""
    import sys
    
    file_path = sys.argv[1] if len(sys.argv) > 1 else "core/WebUI.py"
    
    diagnostics = WebUIDiagnostics(file_path)
    results = diagnostics.run_full_diagnostic()
    
    report = diagnostics.generate_report(results)
    print("\n" + report)
    
    # Guardar reporte a archivo
    report_file = Path("webui_diagnostics_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Reporte guardado en: {report_file}")
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
