"""
MININA Configuration Module
===========================
Configuración centralizada y validada con Pydantic.
"""
from pathlib import Path
from typing import List, Optional, Set
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field, validator
from pathlib import Path
from typing import Optional, Set, List
import os


class MININAConfig(BaseSettings):
    """
    Configuración centralizada de MININA.
    
    Carga desde:
    1. Variables de entorno
    2. Archivo .env
    3. Valores por defecto
    """
    
    # ==========================================
    # Paths y Directorios
    # ==========================================
    DATA_DIR: Path = Field(default=Path("data"))
    SKILLS_DIR: Path = Field(default=Path("data/skills"))
    SKILLS_USER_DIR: Path = Field(default=Path("data/skills_user"))
    SKILLS_VAULT_DIR: Path = Field(default=Path("data/skills_vault"))
    OUTPUT_DIR: Path = Field(default=Path("data/output"))
    BACKUP_DIR: Path = Field(default=Path("backups"))
    TEMP_DIR: Path = Field(default=Path("data/temp_sandbox"))
    
    # ==========================================
    # WebUI Configuration
    # ==========================================
    WEBUI_HOST: str = Field(default="127.0.0.1")
    WEBUI_PORT: int = Field(default=8897, ge=1024, le=65535)
    WEBUI_RATE_LIMIT: int = Field(default=60, ge=1, le=1000)
    WEBUI_RATE_LIMIT_WINDOW: int = Field(default=60, ge=1)  # segundos
    WEBUI_ENABLE_SECURITY_HEADERS: bool = Field(default=True)
    WEBUI_ENABLE_CORS: bool = Field(default=True)
    WEBUI_CORS_ORIGINS: List[str] = Field(default=["*"])
    
    # ==========================================
    # Telegram Bot
    # ==========================================
    TELEGRAM_BOT_TOKEN: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_ALLOWED_CHAT_IDS: Optional[str] = Field(default=None)
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(default=None)
    
    # ==========================================
    # WhatsApp Bot
    # ==========================================
    WHATSAPP_PHONE_ID: Optional[str] = Field(default=None)
    WHATSAPP_BUSINESS_ID: Optional[str] = Field(default=None)
    WHATSAPP_ACCESS_TOKEN: Optional[str] = Field(default=None)
    
    # ==========================================
    # LLM Configuration
    # ==========================================
    DEFAULT_LLM_PROVIDER: str = Field(default="ollama")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    LLM_TIMEOUT: int = Field(default=30, ge=1, le=300)
    LLM_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    
    # ==========================================
    # Skills Configuration
    # ==========================================
    SKILL_ZIP_MAX_MB: int = Field(default=15, ge=1, le=100)
    SKILL_ZIP_MAX_FILES: int = Field(default=60, ge=1, le=500)
    SKILL_ZIP_MAX_UNCOMPRESSED_MB: int = Field(default=40, ge=1, le=200)
    SKILL_SIM_TIMEOUT: float = Field(default=4.0, ge=0.1, le=60.0)
    SKILL_MAX_LIFETIME: int = Field(default=300, ge=10, le=3600)  # segundos
    
    # ==========================================
    # Security
    # ==========================================
    ENABLE_RATE_LIMITING: bool = Field(default=True)
    ENABLE_SECURITY_HEADERS: bool = Field(default=True)
    ENABLE_REQUEST_VALIDATION: bool = Field(default=True)
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")  # json, text
    LOG_FILE: Optional[Path] = Field(default=None)
    
    # ==========================================
    # Backup
    # ==========================================
    BACKUP_ENABLED: bool = Field(default=True)
    BACKUP_FREQUENCY: str = Field(default="weekly")  # daily, weekly, monthly
    BACKUP_MAX_COUNT: int = Field(default=5, ge=1, le=100)
    BACKUP_INCLUDE_SETTINGS: bool = Field(default=True)
    BACKUP_INCLUDE_SKILLS: bool = Field(default=True)
    BACKUP_INCLUDE_HISTORY: bool = Field(default=False)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # ==========================================
    # Validators
    # ==========================================
    @validator("TELEGRAM_ALLOWED_CHAT_IDS")
    def parse_telegram_chat_ids(cls, v):
        """Parse comma-separated chat IDs."""
        if v is None or v == "":
            return None
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper
    
    @validator("BACKUP_FREQUENCY")
    def validate_backup_frequency(cls, v):
        """Validate backup frequency."""
        valid = ["daily", "weekly", "monthly"]
        v_lower = v.lower()
        if v_lower not in valid:
            raise ValueError(f"BACKUP_FREQUENCY must be one of {valid}")
        return v_lower
    
    # ==========================================
    # Properties
    # ==========================================
    @property
    def telegram_allowed_ids(self) -> Optional[Set[int]]:
        """Get set of allowed Telegram chat IDs."""
        if not self.TELEGRAM_ALLOWED_CHAT_IDS:
            return None
        try:
            return {
                int(x.strip())
                for x in self.TELEGRAM_ALLOWED_CHAT_IDS.split(",")
                if x.strip().isdigit()
            }
        except ValueError:
            return None
    
    @property
    def is_telegram_configured(self) -> bool:
        """Check if Telegram bot is properly configured."""
        return self.TELEGRAM_BOT_TOKEN is not None and len(self.TELEGRAM_BOT_TOKEN) > 0
    
    @property
    def is_whatsapp_configured(self) -> bool:
        """Check if WhatsApp bot is properly configured."""
        return all([
            self.WHATSAPP_PHONE_ID,
            self.WHATSAPP_ACCESS_TOKEN
        ])
    
    @property
    def is_openai_configured(self) -> bool:
        """Check if OpenAI is configured."""
        return self.OPENAI_API_KEY is not None and len(self.OPENAI_API_KEY) > 0
    
    @property
    def is_groq_configured(self) -> bool:
        """Check if Groq is configured."""
        return self.GROQ_API_KEY is not None and len(self.GROQ_API_KEY) > 0
    
    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        dirs = [
            self.DATA_DIR,
            self.SKILLS_DIR,
            self.SKILLS_USER_DIR,
            self.SKILLS_VAULT_DIR,
            self.OUTPUT_DIR,
            self.BACKUP_DIR,
            self.TEMP_DIR,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


# Instancia global de configuración
settings = MININAConfig()


def get_settings() -> MININAConfig:
    """Get MININA configuration instance."""
    return settings


def reload_settings() -> MININAConfig:
    """Reload settings from environment."""
    global settings
    settings = MININAConfig()
    return settings
