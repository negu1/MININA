"""
LLM Config Router
=================
Endpoints para configuración de LLM.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from core.logging_config import get_logger
from core.LLMManager import LLMManager, DEFAULT_PROVIDERS, AVAILABLE_MODELS, ProviderType
from core.exceptions import LLMConfigurationError
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.LLM")
router = APIRouter()
llm_manager = LLMManager()


@router.get("/providers")
@handle_route_errors("MININA.WebUI.LLM")
async def get_providers() -> Dict[str, Any]:
    """Get available LLM providers."""
    providers = []
    for provider_type, config in DEFAULT_PROVIDERS.items():
        providers.append({
            "id": provider_type.value,
            "name": provider_type.value.upper(),
            "description": config.description,
            "base_url": config.base_url,
            "default_model": config.model,
            "is_local": config.is_local,
            "enabled": llm_manager.providers.get(provider_type, config).enabled
        })
    
    return {
        "success": True,
        "providers": providers,
        "active_provider": llm_manager.active_provider.value if llm_manager.active_provider else None
    }


@router.get("/models/{provider}")
@handle_route_errors("MININA.WebUI.LLM")
async def get_models(provider: str) -> Dict[str, Any]:
    """Get available models for a provider."""
    try:
        provider_type = ProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    models = AVAILABLE_MODELS.get(provider_type, [])
    
    return {
        "success": True,
        "provider": provider,
        "models": [{"id": m[0], "name": m[1]} for m in models]
    }


@router.post("/configure")
@handle_route_errors("MININA.WebUI.LLM")
async def configure_provider(data: Dict[str, Any]) -> Dict[str, Any]:
    """Configure LLM provider."""
    provider = data.get("provider")
    api_key = data.get("api_key")
    model = data.get("model")
    
    if not provider:
        raise HTTPException(status_code=400, detail="provider is required")
    
    try:
        provider_type = ProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    logger.info(f"Configuring provider: {provider}", extra={"provider": provider})
    
    # Update configuration
    if provider_type in llm_manager.providers:
        llm_manager.providers[provider_type].enabled = True
        if api_key:
            llm_manager.providers[provider_type].api_key = api_key
        if model:
            llm_manager.providers[provider_type].model = model
    
    llm_manager._save_config()
    
    return {
        "success": True,
        "provider": provider,
        "message": f"Provider {provider} configured successfully"
    }


@router.post("/activate")
@handle_route_errors("MININA.WebUI.LLM")
async def activate_provider(data: Dict[str, Any]) -> Dict[str, Any]:
    """Activate a provider as default."""
    provider = data.get("provider")
    
    if not provider:
        raise HTTPException(status_code=400, detail="provider is required")
    
    try:
        provider_type = ProviderType(provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    llm_manager.active_provider = provider_type
    llm_manager._save_config()
    
    logger.info(f"Activated provider: {provider}", extra={"provider": provider})
    
    return {
        "success": True,
        "active_provider": provider
    }


@router.post("/chat")
@handle_route_errors("MININA.WebUI.LLM")
async def chat_completion(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send message to LLM and get completion."""
    message = data.get("message")
    
    if not message:
        raise HTTPException(status_code=400, detail="message is required")
    
    # Verificar que hay un proveedor activo
    if not llm_manager.active_provider:
        raise LLMConfigurationError(
            provider="none",
            missing_config=["active_provider"]
        )
    
    # TODO: Implement actual chat completion with real LLM call
    # Esto requeriría integrar con el gateway de LLM
    logger.info(f"Chat completion requested", extra={
        "provider": llm_manager.active_provider.value,
        "message_length": len(message)
    })
    
    return {
        "success": True,
        "response": "LLM response placeholder - implementar integración real",
        "provider": llm_manager.active_provider.value
    }
