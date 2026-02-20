#!/usr/bin/env python3
"""
Script de limpieza para preparar MININA para GitHub
Elimina datos sensibles, credenciales, y archivos que no deben ser publicados
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def clean_directory():
    """Limpia el directorio de MININA para subir a GitHub"""
    
    root = Path(__file__).resolve().parent
    log(f"Limpiando directorio: {root}")
    
    # 1. Eliminar directorios de datos sensibles
    sensitive_dirs = [
        root / "data",
        root / "skills_user",
        root / ".git" / "logs",
        root / "__pycache__",
        root / ".pytest_cache",
        root / ".venv",
        root / "venv",
        root / "ENV",
        root / ".env",
        root / ".env.local",
        root / ".env.production",
    ]
    
    for d in sensitive_dirs:
        if d.exists():
            try:
                shutil.rmtree(d)
                log(f"✅ Eliminado: {d}")
            except Exception as e:
                log(f"⚠️ No se pudo eliminar {d}: {e}")
    
    # 2. Eliminar archivos de credenciales y configuración
    sensitive_files = [
        root / ".env",
        root / ".env.local",
        root / ".env.production",
        root / "data" / "admin_pin.json",
        root / "data" / "bot_pin.json",
        root / "data" / "telegram_bot_config.json",
        root / "data" / "telegram_notifications.json",
        root / "data" / "credentials.json",
        root / "data" / "secure_credentials.db",
        root / "requirements.txt",
        root / "requirements-ui.txt",
        root / "*.log",
        root / "*.db",
        root / "*.sqlite",
        root / "*.sqlite3",
    ]
    
    for pattern in sensitive_files:
        if "*" in str(pattern):
            # Patrón glob
            for f in root.glob(pattern.name):
                try:
                    f.unlink()
                    log(f"✅ Eliminado: {f}")
                except Exception as e:
                    log(f"⚠️ No se pudo eliminar {f}: {e}")
        else:
            if pattern.exists():
                try:
                    pattern.unlink()
                    log(f"✅ Eliminado: {pattern}")
                except Exception as e:
                    log(f"⚠️ No se pudo eliminar {pattern}: {e}")
    
    # 3. Eliminar archivos __pycache__ y .pyc recursivamente
    log("Eliminando archivos de caché de Python...")
    for pycache in root.rglob("__pycache__"):
        try:
            shutil.rmtree(pycache)
            log(f"✅ Eliminado: {pycache}")
        except Exception as e:
            log(f"⚠️ No se pudo eliminar {pycache}: {e}")
    
    for pyc in root.rglob("*.pyc"):
        try:
            pyc.unlink()
        except Exception:
            pass
    
    for pyo in root.rglob("*.pyo"):
        try:
            pyo.unlink()
        except Exception:
            pass
    
    # 4. Eliminar archivos de backup y temporales
    backup_patterns = [
        "*.bak",
        "*.backup",
        "*.tmp",
        "*.temp",
        "*~",
        "*.swp",
        "*.swo",
    ]
    
    for pattern in backup_patterns:
        for f in root.rglob(pattern):
            try:
                f.unlink()
                log(f"✅ Eliminado: {f}")
            except Exception:
                pass
    
    # 5. Crear directorios necesarios vacíos con .gitkeep
    dirs_to_keep = [
        root / "data",
        root / "skills_user",
        root / "tests" / "e2e",
        root / "tests" / "integration",
        root / "tests" / "unit",
    ]
    
    for d in dirs_to_keep:
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        gitkeep.touch()
        log(f"✅ Creado: {d} con .gitkeep")
    
    # 6. Crear archivos de ejemplo
    create_example_files(root)
    
    log("\n✅ Limpieza completada!")
    log("Revisa el .gitignore para asegurar que todo esté correctamente excluido.")


def create_example_files(root: Path):
    """Crea archivos de ejemplo para que los usuarios sepan qué configurar"""
    
    # .env.example
    env_example = root / ".env.example"
    env_content = """# ==========================================
# MININA v3.0 - Configuración de Ejemplo
# ==========================================
# Copia este archivo a .env y rellena tus valores
# NUNCA subas el archivo .env real a GitHub

# --- Telegram Bot (Obligatorio) ---
# Obtén tu token de @BotFather en Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Tu Chat ID de Telegram (obténlo de @userinfobot)
TELEGRAM_ALLOWED_CHAT_ID=123456789

# --- LLM Providers (Al menos uno es necesario) ---
# Groq (Recomendado - tier gratuito generoso)
GROQ_API_KEY=gsk_tu_api_key_aqui

# OpenAI (Opcional - requiere tarjeta de crédito)
# OPENAI_API_KEY=sk-tu_api_key_aqui

# Anthropic Claude (Opcional)
# ANTHROPIC_API_KEY=sk-ant-tu_api_key_aqui

# --- Integraciones Opcionales ---
# Asana (para gestión de tareas)
# ASANA_ACCESS_TOKEN=tu_token_aqui

# Dropbox (para almacenamiento en la nube)
# DROPBOX_ACCESS_TOKEN=tu_token_aqui

# Discord (para notificaciones)
# DISCORD_BOT_TOKEN=tu_token_aqui

# Email SMTP (para envío de correos)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=tuemail@gmail.com
# SMTP_PASSWORD=tu_app_password

# --- Configuración Avanzada ---
# MIIA_ADMIN_PIN=1234  # PIN para acceso admin (legacy, usar /setadminpin)
# MIIA_SKILL_ZIP_MAX_MB=15  # Tamaño máximo de skills .zip
# MIIA_AUTO_REFRESH_MAX_CYCLES=30  # Ciclos máximos de auto-refresh
# MIIA_AUTO_REFRESH_SECONDS=6  # Intervalo de auto-refresh en segundos
"""
    env_example.write_text(env_content, encoding="utf-8")
    log(f"✅ Creado: {env_example}")
    
    # README para data/
    data_readme = root / "data" / "README.md"
    data_readme_content = """# Directorio de Datos

Este directorio contiene datos persistentes de MININA:

- `admin_pin.json` - PIN de administrador (hash + salt)
- `bot_pin.json` - PIN del bot (hash + salt)
- `telegram_bot_config.json` - Configuración del bot
- `telegram_notifications.json` - Preferencias de notificaciones
- `SecureCredentialStore/` - Credenciales encriptadas
- `skills/` - Skills del sistema
- `skills_user/` - Skills personalizadas del usuario
- `skills_vault/` - Baúl de skills (staging + live)
- `temp_sandbox/` - Sandboxes temporales de ejecución

**Nota**: Este directorio está en .gitignore y NO debe subirse a GitHub.
"""
    data_readme.write_text(data_readme_content, encoding="utf-8")
    log(f"✅ Creado: {data_readme}")
    
    # README para skills_user/
    skills_readme = root / "skills_user" / "README.md"
    skills_readme_content = """# Skills de Usuario

Coloca aquí tus skills personalizadas.

Formatos soportados:
- `*.py` - Skills en Python
- `*.manifest.json` - Manifestos de permisos

Ejemplo de estructura:
```
skills_user/
├── mi_skill.py
├── mi_skill.manifest.json
└── README.md
```

**Nota**: Este directorio está en .gitignore. Tus skills personales no se subirán a GitHub.
"""
    skills_readme.write_text(skills_readme_content, encoding="utf-8")
    log(f"✅ Creado: {skills_readme}")


def verify_gitignore(root: Path):
    """Verifica que .gitignore tenga todas las exclusiones necesarias"""
    
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        log("⚠️ .gitignore no encontrado!")
        return False
    
    content = gitignore.read_text(encoding="utf-8")
    
    required_patterns = [
        ".env",
        ".env.*",
        "data/",
        "skills_user/",
        "__pycache__/",
        "*.pyc",
        "*.log",
        "*.db",
        "*.sqlite",
        "venv/",
        ".venv/",
    ]
    
    missing = []
    for pattern in required_patterns:
        if pattern not in content:
            missing.append(pattern)
    
    if missing:
        log(f"⚠️ .gitignore está incompleto. Faltan: {missing}")
        return False
    else:
        log("✅ .gitignore verificado - todas las exclusiones necesarias presentes")
        return True


def print_final_instructions():
    """Imprime instrucciones finales"""
    print("\n" + "="*60)
    print("  PREPARACIÓN PARA GITHUB COMPLETADA")
    print("="*60)
    print("""
Próximos pasos:

1. Revisa que todo esté correcto:
   git status

2. Asegúrate de que NO haya archivos sensibles:
   git status --short | grep -E "(env|data/|skills_user/)"
   (No debería mostrar nada)

3. Crea el commit inicial:
   git add .
   git commit -m "Initial commit: MININA v3.0 - Sistema de Automatización Segura"

4. Conecta con GitHub y sube:
   git remote add origin https://github.com/TU_USUARIO/minina.git
   git branch -M main
   git push -u origin main

⚠️  VERIFICACIÓN IMPORTANTE:
   - Revisa que .env NO esté en el repo
   - Revisa que data/ NO esté en el repo
   - Revisa que no haya tokens ni API keys en el código
   - Revisa que skills_user/ NO esté en el repo

✅ El repositorio está listo para ser público de forma segura.
""")


def main():
    print("="*60)
    print("  SCRIPT DE LIMPIEZA PARA GITHUB - MININA v3.0")
    print("="*60)
    print()
    
    root = Path(__file__).resolve().parent
    
    # Verificar .gitignore
    verify_gitignore(root)
    print()
    
    # Confirmación
    resp = input("¿Estás seguro de que quieres limpiar este directorio para GitHub? (s/N): ")
    if resp.lower() not in ("s", "si", "sí", "y", "yes"):
        print("Cancelado.")
        sys.exit(0)
    
    print()
    clean_directory()
    print()
    verify_gitignore(root)
    print()
    print_final_instructions()


if __name__ == "__main__":
    main()
