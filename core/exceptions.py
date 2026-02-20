"""
MININA Custom Exceptions
========================
Excepciones específicas para manejo de errores estructurado.
"""
from typing import Optional, Dict, Any, List


class MININAException(Exception):
    """
    Base exception for all MININA errors.
    
    Provides structured error information for logging and debugging.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "MININA_ERROR"
        self.details = details or {}
        self.suggestion = suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
            "exception_type": self.__class__.__name__
        }
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


# ==========================================
# Skill Exceptions
# ==========================================

class SkillNotFoundError(MININAException):
    """Raised when a requested skill is not found."""
    
    def __init__(
        self,
        skill_name: str,
        available_skills: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Skill '{skill_name}' no encontrada"
        if available_skills:
            message += f". Disponibles: {', '.join(available_skills[:10])}"
        
        super().__init__(
            message=message,
            error_code="SKILL_NOT_FOUND",
            details={"skill_name": skill_name, "available": available_skills, **(details or {})},
            suggestion="Verifica el nombre de la skill o lista las skills disponibles con 'lista skills'"
        )
        self.skill_name = skill_name
        self.available_skills = available_skills or []


class SkillExecutionError(MININAException):
    """Raised when skill execution fails."""
    
    def __init__(
        self,
        skill_name: str,
        context: Dict[str, Any],
        original_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Error ejecutando skill '{skill_name}'"
        if original_error:
            message += f": {str(original_error)}"
        
        super().__init__(
            message=message,
            error_code="SKILL_EXECUTION_ERROR",
            details={
                "skill_name": skill_name,
                "context": context,
                "original_error": str(original_error) if original_error else None,
                **(details or {})
            },
            suggestion="Verifica los parámetros de la skill o revisa los logs para más detalles"
        )
        self.skill_name = skill_name
        self.context = context
        self.original_error = original_error


class SkillTimeoutError(SkillExecutionError):
    """Raised when skill execution times out."""
    
    def __init__(
        self,
        skill_name: str,
        timeout_seconds: float,
        context: Dict[str, Any]
    ):
        super().__init__(
            skill_name=skill_name,
            context=context,
            details={"timeout_seconds": timeout_seconds}
        )
        self.error_code = "SKILL_TIMEOUT"
        self.message = f"Skill '{skill_name}' excedió el tiempo límite de {timeout_seconds}s"
        self.suggestion = "La skill está tomando demasiado tiempo. Considera optimizarla o dividirla en tareas más pequeñas"
        self.timeout_seconds = timeout_seconds


class SkillImportError(MININAException):
    """Raised when skill import fails."""
    
    def __init__(self, skill_name: str, import_error: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Error importando skill '{skill_name}': {import_error}",
            error_code="SKILL_IMPORT_ERROR",
            details={"skill_name": skill_name, "import_error": import_error, **(details or {})},
            suggestion="Verifica que el archivo de la skill no esté corrupto y sea código Python válido"
        )
        self.skill_name = skill_name
        self.import_error = import_error


# ==========================================
# Security Exceptions
# ==========================================

class SafetyValidationError(MININAException):
    """Raised when skill safety validation fails."""
    
    def __init__(
        self,
        skill_name: str,
        reasons: List[str],
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Validación de seguridad fallida para '{skill_name}': {'; '.join(reasons)}",
            error_code="SAFETY_VALIDATION_FAILED",
            details={"skill_name": skill_name, "reasons": reasons, **(details or {})},
            suggestion="Revisa los permisos declarados en skill.yaml y asegúrate de no usar imports prohibidos"
        )
        self.skill_name = skill_name
        self.reasons = reasons


class QuarantineError(MININAException):
    """Raised when a skill is quarantined."""
    
    def __init__(self, skill_name: str, quarantine_path: str, reasons: List[str]):
        super().__init__(
            message=f"Skill '{skill_name}' ha sido puesta en cuarentena",
            error_code="SKILL_QUARANTINED",
            details={"skill_name": skill_name, "quarantine_path": quarantine_path, "reasons": reasons},
            suggestion="Contacta al administrador del sistema para revisar esta skill"
        )
        self.skill_name = skill_name
        self.quarantine_path = quarantine_path
        self.reasons = reasons


class PermissionDeniedError(MININAException):
    """Raised when skill lacks required permission."""
    
    def __init__(
        self,
        skill_name: str,
        required_permission: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Skill '{skill_name}' requiere permiso '{required_permission}'",
            error_code="PERMISSION_DENIED",
            details={
                "skill_name": skill_name,
                "required_permission": required_permission,
                **(details or {})
            },
            suggestion=f"Agrega '{required_permission}' a la lista de permisos en skill.yaml"
        )
        self.skill_name = skill_name
        self.required_permission = required_permission


# ==========================================
# LLM Exceptions
# ==========================================

class LLMProviderError(MININAException):
    """Raised when LLM provider fails."""
    
    def __init__(
        self,
        provider: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Error con proveedor {provider}: {message}",
            error_code="LLM_PROVIDER_ERROR",
            details={
                "provider": provider,
                "status_code": status_code,
                **(details or {})
            },
            suggestion="Verifica tu conexión a internet y las credenciales del proveedor"
        )
        self.provider = provider
        self.status_code = status_code


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM rate limit is hit."""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            provider=provider,
            message="Rate limit exceeded",
            status_code=429
        )
        self.error_code = "LLM_RATE_LIMIT"
        self.retry_after = retry_after
        if retry_after:
            self.suggestion = f"Espera {retry_after} segundos antes de intentar nuevamente"
        else:
            self.suggestion = "Espera un momento antes de intentar nuevamente"


class LLMTimeoutError(LLMProviderError):
    """Raised when LLM request times out."""
    
    def __init__(self, provider: str, timeout_seconds: float):
        super().__init__(
            provider=provider,
            message=f"Request timeout after {timeout_seconds}s",
            details={"timeout_seconds": timeout_seconds}
        )
        self.error_code = "LLM_TIMEOUT"
        self.suggestion = "El proveedor está tardando en responder. Intenta con un modelo más rápido o verifica tu conexión"
        self.timeout_seconds = timeout_seconds


class LLMConfigurationError(MININAException):
    """Raised when LLM is not properly configured."""
    
    def __init__(self, provider: str, missing_config: List[str]):
        super().__init__(
            message=f"Proveedor '{provider}' no configurado correctamente. Falta: {', '.join(missing_config)}",
            error_code="LLM_CONFIG_ERROR",
            details={"provider": provider, "missing_config": missing_config},
            suggestion=f"Configura las credenciales para {provider} en la interfaz web o variables de entorno"
        )
        self.provider = provider
        self.missing_config = missing_config


# ==========================================
# Credential Exceptions
# ==========================================

class CredentialError(MININAException):
    """Base exception for credential-related errors."""
    pass


class CredentialNotFoundError(CredentialError):
    """Raised when a credential is not found."""
    
    def __init__(self, service: str, key: str):
        super().__init__(
            message=f"Credencial '{key}' no encontrada para servicio '{service}'",
            error_code="CREDENTIAL_NOT_FOUND",
            details={"service": service, "key": key},
            suggestion="Configura la credencial en el panel de administración"
        )
        self.service = service
        self.key = key


class CredentialValidationError(CredentialError):
    """Raised when credential validation fails."""
    
    def __init__(self, service: str, key: str, validation_error: str):
        super().__init__(
            message=f"Credencial '{key}' inválida: {validation_error}",
            error_code="CREDENTIAL_INVALID",
            details={"service": service, "key": key, "validation_error": validation_error}
        )


# ==========================================
# System Exceptions
# ==========================================

class SystemResourceError(MININAException):
    """Raised when system resources are insufficient."""
    
    def __init__(
        self,
        resource_type: str,
        current: float,
        required: float,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=f"Recurso insuficiente: {resource_type} (actual: {current}, requerido: {required})",
            error_code="RESOURCE_EXHAUSTED",
            details={
                "resource_type": resource_type,
                "current": current,
                "required": required,
                **(details or {})
            },
            suggestion="Cierra aplicaciones innecesarias o reinicia el sistema"
        )
        self.resource_type = resource_type
        self.current = current
        self.required = required


class BackupError(MININAException):
    """Raised when backup operation fails."""
    
    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Error en operación de backup '{operation}': {reason}",
            error_code="BACKUP_ERROR",
            details={"operation": operation, "reason": reason, **(details or {})}
        )
        self.operation = operation


class UpdateError(MININAException):
    """Raised when update operation fails."""
    
    def __init__(self, version: str, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Error actualizando a versión {version}: {reason}",
            error_code="UPDATE_ERROR",
            details={"target_version": version, "reason": reason, **(details or {})}
        )
        self.target_version = version


# ==========================================
# Bot Exceptions
# ==========================================

class BotConfigurationError(MININAException):
    """Raised when bot configuration is invalid."""
    
    def __init__(self, bot_type: str, missing: List[str]):
        super().__init__(
            message=f"Bot {bot_type} no configurado. Falta: {', '.join(missing)}",
            error_code="BOT_CONFIG_ERROR",
            details={"bot_type": bot_type, "missing_config": missing}
        )
        self.bot_type = bot_type


class BotAPIError(MININAException):
    """Raised when bot API call fails."""
    
    def __init__(
        self,
        bot_type: str,
        api_method: str,
        status_code: int,
        response: Optional[str] = None
    ):
        super().__init__(
            message=f"Error en API de {bot_type} ({api_method}): {status_code}",
            error_code="BOT_API_ERROR",
            details={
                "bot_type": bot_type,
                "api_method": api_method,
                "status_code": status_code,
                "response": response
            }
        )
        self.bot_type = bot_type
        self.status_code = status_code


# ==========================================
# Network Exceptions
# ==========================================

class NetworkError(MININAException):
    """Raised when network operation fails."""
    
    def __init__(self, url: str, method: str, error: str):
        super().__init__(
            message=f"Error de red {method} {url}: {error}",
            error_code="NETWORK_ERROR",
            details={"url": url, "method": method, "error": error}
        )


class DownloadError(NetworkError):
    """Raised when download fails."""
    
    def __init__(self, url: str, reason: str):
        super().__init__(url, "GET", reason)
        self.error_code = "DOWNLOAD_ERROR"
