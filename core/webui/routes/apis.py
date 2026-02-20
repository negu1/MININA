"""
APIs Router
===========
Endpoints para gestión de API Keys (Gemini, OpenAI, Groq, Meta, Ollama, etc.)
Integrado con sistema de credenciales seguras de MININA.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from core.logging_config import get_logger
from core.SecureCredentials import credential_store
from core.LLMManager import llm_manager, ProviderType
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.APIs")
router = APIRouter()


class ApiKeySaveRequest(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None


class ApiKeyDeleteRequest(BaseModel):
    provider: str


@router.get("/list")
@handle_route_errors("MININA.WebUI.APIs")
async def list_api_configs() -> Dict[str, Any]:
    """List all configured API keys and settings."""
    providers = {}
    
    for provider_type in ProviderType:
        provider_key = provider_type.value
        
        # Get from credential store
        api_key = credential_store.get_credential("llm_apis", f"{provider_key}_key") or ""
        base_url = credential_store.get_credential("llm_apis", f"{provider_key}_url") or ""
        model = credential_store.get_credential("llm_apis", f"{provider_key}_model") or ""
        
        # Get from LLMManager if available
        config = llm_manager.providers.get(provider_type)
        is_local = config.is_local if config else False
        default_model = config.model if config else ""
        
        providers[provider_key] = {
            "has_key": bool(api_key),
            "api_key_masked": mask_key(api_key) if api_key else "",
            "base_url": base_url or (config.base_url if config else ""),
            "model": model or default_model,
            "is_local": is_local,
            "enabled": bool(api_key) or is_local
        }
    
    return {
        "success": True,
        "providers": providers,
        "active_provider": llm_manager.active_provider.value if llm_manager.active_provider else None
    }


@router.post("/save")
@handle_route_errors("MININA.WebUI.APIs")
async def save_api_key(request: ApiKeySaveRequest) -> Dict[str, Any]:
    """Save an API key securely."""
    provider = request.provider.lower()
    api_key = request.api_key
    
    logger.info(f"=== SAVE API KEY === Provider: {provider}, HasKey: {bool(api_key)}")
    
    try:
        # Validate provider
        try:
            provider_type = ProviderType(provider)
            logger.info(f"Provider type validated: {provider_type}")
        except ValueError as e:
            logger.error(f"Invalid provider: {provider}, Error: {e}")
            return {
                "success": False,
                "error": f"Provider inválido: {provider}"
            }
        
        # Save to secure credential store
        if api_key:
            logger.info(f"Saving credential to store: llm_apis/{provider}_key")
            result = credential_store.set_credential("llm_apis", f"{provider}_key", api_key)
            logger.info(f"Credential store result: {result}")
        
        if request.base_url:
            logger.info(f"Saving base_url: {request.base_url}")
            credential_store.set_credential("llm_apis", f"{provider}_url", request.base_url)
        
        if request.model:
            logger.info(f"Saving model: {request.model}")
            credential_store.set_credential("llm_apis", f"{provider}_model", request.model)
        
        # Update LLMManager
        logger.info(f"Updating LLMManager for {provider}")
        llm_manager.set_api_key(provider_type, api_key)
        
        # Mark as enabled if API key provided
        if api_key:
            llm_manager.providers[provider_type].enabled = True
            llm_manager._save_config()
            logger.info(f"Provider {provider} marked as enabled")
        
        if request.model:
            llm_manager.set_model(provider_type, request.model)
        
        # If this is the first API configured, make it active
        if not llm_manager.active_provider or llm_manager.active_provider == provider_type:
            logger.info(f"Setting {provider} as active provider")
            llm_manager.set_active_provider(provider_type)
        
        logger.info(f"=== SAVE SUCCESS === {provider}")
        return {
            "success": True,
            "message": f"API Key de {provider.capitalize()} guardada exitosamente",
            "provider": provider,
            "masked_key": mask_key(api_key) if api_key else ""
        }
        
    except Exception as e:
        logger.error(f"=== SAVE ERROR === {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/delete")
@handle_route_errors("MININA.WebUI.APIs")
async def delete_api_key(request: ApiKeyDeleteRequest) -> Dict[str, Any]:
    """Delete an API key."""
    provider = request.provider.lower()
    
    logger.info(f"Deleting API key for provider: {provider}")
    
    try:
        # Delete from credential store
        credential_store.delete_credential("llm_apis", f"{provider}_key")
        credential_store.delete_credential("llm_apis", f"{provider}_url")
        credential_store.delete_credential("llm_apis", f"{provider}_model")
        
        # Update LLMManager
        try:
            provider_type = ProviderType(provider)
            llm_manager.providers[provider_type].api_key = ""
            llm_manager.providers[provider_type].enabled = False
            llm_manager._save_config()
        except ValueError:
            pass
        
        return {
            "success": True,
            "message": f"API Key de {provider.capitalize()} eliminada"
        }
        
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/active")
@handle_route_errors("MININA.WebUI.APIs")
async def get_active_provider() -> Dict[str, Any]:
    """Get currently active provider."""
    active = llm_manager.active_provider
    
    if not active:
        return {
            "success": True,
            "active_provider": None,
            "message": "No hay provider activo"
        }
    
    config = llm_manager.get_active_config()
    
    return {
        "success": True,
        "active_provider": active.value,
        "is_local": config.is_local if config else False,
        "model": config.model if config else ""
    }


@router.post("/set-active/{provider}")
@handle_route_errors("MININA.WebUI.APIs")
async def set_active_provider_api(provider: str) -> Dict[str, Any]:
    """Set active provider."""
    try:
        provider_type = ProviderType(provider)
        success = llm_manager.set_active_provider(provider_type)
        
        if success:
            return {
                "success": True,
                "message": f"Provider activo: {provider}",
                "active_provider": provider
            }
        else:
            return {
                "success": False,
                "error": f"No se pudo activar {provider}. Verifica que esté configurado."
            }
            
    except ValueError:
        return {
            "success": False,
            "error": f"Provider inválido: {provider}"
        }


def mask_key(key: str) -> str:
    """Mask API key for display (show only last 4 chars)."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
