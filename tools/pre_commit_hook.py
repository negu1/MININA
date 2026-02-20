#!/usr/bin/env python3
"""
MiIA Pre-Commit Hook
Ejecuta validaciones antes de guardar cambios en WebUI.py
"""

import os
import sys
import subprocess
from pathlib import Path

def check_webui():
    """Ejecuta el validador de WebUI"""
    tools_dir = Path(__file__).parent
    project_dir = tools_dir.parent
    validator = tools_dir / "validate_webui.py"
    webui_file = project_dir / "core" / "WebUI.py"
    
    if not validator.exists():
        print("❌ No se encontró el validador")
        return False
    
    if not webui_file.exists():
        print("❌ No se encontró WebUI.py")
        return True  # No hay nada que validar
    
    print("🔍 Validando WebUI.py antes de guardar...")
    result = subprocess.run(
        [sys.executable, str(validator), str(webui_file)],
        capture_output=True,
        text=True,
        cwd=project_dir
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Función principal del hook"""
    if not check_webui():
        print("\n❌ VALIDACIÓN FALLIDA - Cambios no guardados")
        print("\nCorrige los errores mostrados arriba antes de guardar.")
        print("Si necesitas forzar el guardado, usa: git commit --no-verify")
        return 1
    
    print("✅ Validación exitosa - Procediendo con el guardado")
    return 0

if __name__ == "__main__":
    sys.exit(main())
