"""
MININA Structured Logging
=========================
Logging en formato JSON para mejor observabilidad.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from core.config import get_settings


class JSONFormatter(logging.Formatter):
    """
    Formatter que genera logs en formato JSON.
    
    Ejemplo de salida:
    {
        "timestamp": "2024-01-15T10:30:00.123456",
        "level": "INFO",
        "logger": "MININAWebUI",
        "message": "Servidor iniciado",
        "module": "WebUI",
        "function": "run_web_server",
        "line": 45,
        "request_id": "abc-123",
        "extra": {"user_id": "user123"}
    }
    """
    
    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process,
        }
        
        # Agregar extra data si existe
        if self.include_extra and hasattr(record, "extra_data"):
            log_obj["extra"] = record.extra_data
        
        # Agregar exception info si existe
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Agregar request_id si existe
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        
        # Agregar user_id si existe
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        
        # Agregar skill_id si existe
        if hasattr(record, "skill_id"):
            log_obj["skill_id"] = record.skill_id
            
        return json.dumps(log_obj, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Formatter tradicional para desarrollo local."""
    
    def __init__(self, include_timestamp: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
    
    def format(self, record: logging.LogRecord) -> str:
        """Format in traditional text format."""
        parts = []
        
        if self.include_timestamp:
            parts.append(f"[{self.formatTime(record)}]")
        
        parts.append(f"[{record.levelname}]")
        parts.append(f"[{record.name}]")
        parts.append(record.getMessage())
        
        if record.exc_info:
            parts.append("\n" + self.formatException(record.exc_info))
        
        return " ".join(parts)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter que permite agregar contexto estructurado.
    
    Uso:
        logger = get_logger("WebUI", extra={"request_id": "abc123"})
        logger.info("Request processed", extra={"duration_ms": 150})
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message with extra data."""
        if "extra" in kwargs:
            # Merge extra data with adapter's extra
            merged_extra = {**(self.extra or {}), **kwargs["extra"]}
            kwargs["extra"] = {"extra_data": merged_extra}
        else:
            kwargs["extra"] = {"extra_data": self.extra}
        
        return msg, kwargs


def setup_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    log_file: Optional[Path] = None
) -> None:
    """
    Configure MININA logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json, text)
        log_file: Optional file path for logging
    """
    settings = get_settings()
    
    # Use settings if not provided
    if level is None:
        level = settings.LOG_LEVEL
    if format_type is None:
        format_type = settings.LOG_FORMAT
    if log_file is None:
        log_file = settings.LOG_FILE
    
    # Get numeric level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    # Log configuration complete
    logger = logging.getLogger("MININA")
    logger.info("Logging configured", extra={
        "level": level,
        "format": format_type,
        "file": str(log_file) if log_file else None
    })


def get_logger(name: str, extra: Optional[Dict[str, Any]] = None) -> StructuredLoggerAdapter:
    """
    Get a structured logger with optional context.
    
    Args:
        name: Logger name
        extra: Optional extra context data
        
    Returns:
        StructuredLoggerAdapter instance
    """
    logger = logging.getLogger(name)
    return StructuredLoggerAdapter(logger, extra or {})


def get_request_logger(request_id: str, user_id: Optional[str] = None) -> StructuredLoggerAdapter:
    """
    Get a logger with request context.
    
    Args:
        request_id: Unique request identifier
        user_id: Optional user identifier
        
    Returns:
        Logger with request context
    """
    extra = {"request_id": request_id}
    if user_id:
        extra["user_id"] = user_id
    return get_logger("MININA.Request", extra)


def get_skill_logger(skill_name: str, skill_id: Optional[str] = None) -> StructuredLoggerAdapter:
    """
    Get a logger with skill context.
    
    Args:
        skill_name: Name of the skill
        skill_id: Optional skill identifier
        
    Returns:
        Logger with skill context
    """
    extra = {"skill_name": skill_name}
    if skill_id:
        extra["skill_id"] = skill_id
    return get_logger(f"MININA.Skill.{skill_name}", extra)


# Alias para compatibilidad hacia atrás
def configure_logging(**kwargs) -> None:
    """Alias for setup_logging."""
    setup_logging(**kwargs)
