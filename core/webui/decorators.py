"""
WebUI Decorators
================
Decoradores para manejo de errores y logging en routers.
Elimina duplicación de código try/except en los endpoints.
"""
import functools
import traceback
from typing import Callable, Any, Optional
from fastapi import HTTPException

from core.logging_config import get_logger
from core.exceptions import (
    MININAException,
    SkillNotFoundError,
    SkillExecutionError,
    SafetyValidationError,
    LLMProviderError,
    CredentialError,
    PermissionDeniedError,
)


def handle_route_errors(logger_name: Optional[str] = None):
    """
    Decorador para manejo estándar de errores en routes.
    
    Convierte excepciones de MININA a HTTPExceptions apropiadas.
    Loguea errores con contexto.
    
    Uso:
        @router.get("/endpoint")
        @handle_route_errors("MININA.WebUI.Skills")
        async def my_endpoint():
            return await some_operation()
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(logger_name or f"MININA.WebUI.{func.__module__.split('.')[-1]}")
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            
            # Errores de MININA - ya tienen mensajes y sugerencias
            except SkillNotFoundError as e:
                logger.warning(f"Skill not found: {e.skill_name}", extra={"skill_name": e.skill_name})
                raise HTTPException(status_code=404, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "available_skills": e.available_skills[:10] if e.available_skills else [],
                    "suggestion": e.suggestion
                })
            
            except SkillExecutionError as e:
                logger.error(
                    f"Skill execution failed: {e.skill_name}",
                    extra={"skill_name": e.skill_name, "context": e.context, "original_error": str(e.original_error)}
                )
                raise HTTPException(status_code=500, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "skill_name": e.skill_name,
                    "suggestion": e.suggestion
                })
            
            except SafetyValidationError as e:
                logger.warning(
                    f"Safety validation failed for {e.skill_name}",
                    extra={"skill_name": e.skill_name, "reasons": e.reasons}
                )
                raise HTTPException(status_code=403, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "reasons": e.reasons,
                    "suggestion": e.suggestion
                })
            
            except PermissionDeniedError as e:
                logger.warning(
                    f"Permission denied: {e.required_permission}",
                    extra={"skill_name": e.skill_name, "permission": e.required_permission}
                )
                raise HTTPException(status_code=403, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "required_permission": e.required_permission,
                    "suggestion": e.suggestion
                })
            
            except LLMProviderError as e:
                status_code = 429 if hasattr(e, 'status_code') and e.status_code == 429 else 503
                logger.error(
                    f"LLM provider error: {e.provider}",
                    extra={"provider": e.provider, "status_code": getattr(e, 'status_code', None)}
                )
                raise HTTPException(status_code=status_code, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "provider": e.provider,
                    "suggestion": e.suggestion
                })
            
            except CredentialError as e:
                logger.warning(f"Credential error: {e}", extra={"service": getattr(e, 'service', None)})
                raise HTTPException(status_code=401, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "suggestion": e.suggestion
                })
            
            except MININAException as e:
                # Cualquier otra excepción de MININA
                logger.error(f"MININA error: {e}", extra={"error_code": e.error_code})
                raise HTTPException(status_code=500, detail={
                    "error": str(e),
                    "error_code": e.error_code,
                    "suggestion": e.suggestion
                })
            
            except HTTPException:
                # Re-lanzar HTTPExceptions sin modificar
                raise
            
            except Exception as e:
                # Error inesperado - log detallado
                logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Internal server error",
                        "error_code": "INTERNAL_ERROR",
                        "message": str(e)
                    }
                )
        
        return wrapper
    return decorator


def require_auth(permission: Optional[str] = None):
    """
    Decorador para requerir autenticación (placeholder para futura implementación).
    
    Uso:
        @router.post("/admin/action")
        @require_auth(permission="admin")
        async def admin_action():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # TODO: Implementar verificación de autenticación
            # Por ahora, deja pasar todas las requests
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_execution_time(logger_name: Optional[str] = None):
    """
    Decorador para loguear tiempo de ejecución de endpoints.
    
    Uso:
        @router.get("/slow-endpoint")
        @log_execution_time("MININA.WebUI")
        async def slow_endpoint():
            pass
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(logger_name or "MININA.WebUI.Performance")
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import time
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if duration > 1.0:  # Log si toma más de 1 segundo
                    logger.warning(
                        f"Slow endpoint: {func.__name__} took {duration:.2f}s",
                        extra={"endpoint": func.__name__, "duration_ms": duration * 1000}
                    )
        return wrapper
    return decorator
