"""
MININA v3.0 - Skill Security Constants
Constantes y configuraciones para validación de seguridad de skills
"""

from typing import Set, Dict, Any

# Módulos Python prohibidos en skills (riesgo de seguridad)
DEFAULT_FORBIDDEN_MODULES: Set[str] = {
    "ctypes",           # Acceso a C/DLLs
    "socket",           # Conexiones de red raw
    "importlib",        # Importación dinámica
    "inspect",          # Introspección de código
    "asyncio.subprocess",  # Subprocesos
    "subprocess",       # Ejecución de comandos
    "shutil",           # Operaciones de archivo peligrosas
    "win32api",         # API de Windows
    "win32con",         # Constantes Windows
    "win32gui",         # GUI Windows
    "pyautogui",        # Control de mouse/teclado
    "keyring",          # Acceso a almacenes de contraseñas
    "getpass",          # Lectura de passwords
    "os",               # Peligroso: os.system, os.remove
    "sys",              # Peligroso: sys.exit, manipulación de path
}

# Variables de entorno sensibles que las skills NO deben acceder
SENSITIVE_ENV_VARS: Set[str] = {
    # Tokens y API Keys
    "TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_API_KEY",
    "WHATSAPP_TOKEN", "WHATSAPP_ACCESS_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY",
    
    # Credenciales del sistema
    "MIIA_ADMIN_PIN", "ADMIN_PASSWORD", "SECRET_KEY", "JWT_SECRET",
    "DATABASE_URL", "DB_PASSWORD", "REDIS_PASSWORD", "MONGO_URI",
    
    # Cloud providers
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
    "AZURE_CLIENT_SECRET", "AZURE_STORAGE_KEY", "GCP_SERVICE_ACCOUNT_KEY",
    
    # Otros servicios
    "GITHUB_TOKEN", "GITLAB_TOKEN", "DOCKER_TOKEN",
    "STRIPE_SECRET_KEY", "PAYPAL_CLIENT_SECRET",
    
    # Genéricas
    "PASSWORD", "SECRET", "PRIVATE_KEY", "API_SECRET", "AUTH_TOKEN",
    "FACEBOOK_PASSWORD", "INSTAGRAM_PASSWORD", "TWITTER_PASSWORD",
    "EMAIL_PASSWORD", "SMTP_PASSWORD", "IMAP_PASSWORD", "SSH_KEY",
}

# Llamadas a funciones prohibidas
DEFAULT_FORBIDDEN_CALLS: Set[str] = {
    "eval",         # Ejecución de código dinámico
    "exec",         # Ejecución de código
    "compile",      # Compilación de código
    "__import__",   # Importación dinámica
    "getattr",      # Acceso a atributos por string (riesgo)
    "setattr",      # Modificación de atributos
}

# Módulos de red - requieren permiso explícito "network"
NETWORK_MODULES: Set[str] = {
    "requests", "httpx", "urllib", "urllib3", "aiohttp", 
    "http.client", "ftplib", "smtplib", "poplib", "imaplib"
}

# Módulos de filesystem - requieren permiso "fs_read" o "fs_write"
FILESYSTEM_MODULES: Set[str] = {
    "os.path", "pathlib", "glob", "fnmatch", "fileinput", "tempfile"
}

# Límites de seguridad por defecto
DEFAULT_SECURITY_LIMITS: Dict[str, Any] = {
    "max_zip_size_mb": 15,
    "max_zip_files": 60,
    "max_uncompressed_mb": 40,
    "sandbox_timeout_seconds": 4,
    "max_execution_time_seconds": 30,
    "max_memory_mb": 128,
}

# Patrones de código sospechosos (para análisis AST)
SUSPICIOUS_PATTERNS: Dict[str, str] = {
    "env_access": "Acceso a variables de entorno",
    "file_delete": "Eliminación de archivos detectada",
    "file_write": "Escritura de archivos detectada",
    "network_call": "Llamada de red detectada",
    "system_command": "Comando de sistema detectado",
    "code_execution": "Ejecución de código dinámico",
    "data_exfiltration": "Posible exfiltración de datos",
}
