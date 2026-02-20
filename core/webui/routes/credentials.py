"""
Credentials Router
==================
Endpoints para el vault de credenciales.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from core.logging_config import get_logger
from core.SkillCredentialVault import credential_vault
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.Credentials")
router = APIRouter()


@router.get("/stats")
@handle_route_errors("MININA.WebUI.Credentials")
async def get_credential_stats() -> Dict[str, Any]:
    """Get credential vault statistics."""
    stats = credential_vault.get_stats()
    return {
        "success": True,
        "stats": stats
    }


@router.post("/store")
@handle_route_errors("MININA.WebUI.Credentials")
async def store_credentials(data: Dict[str, Any]) -> Dict[str, Any]:
    """Store credentials temporarily."""
    skill_id = data.get("skill_id")
    credentials = data.get("credentials", {})
    ttl_seconds = data.get("ttl_seconds", 300)
    
    if not skill_id or not credentials:
        raise HTTPException(status_code=400, detail="skill_id and credentials are required")
    
    session_id = credential_vault.store_credentials(skill_id, credentials, ttl_seconds)
    
    logger.info(f"Stored credentials for skill: {skill_id}", extra={
        "skill_id": skill_id,
        "ttl_seconds": ttl_seconds,
        "credential_keys": list(credentials.keys())
    })
    
    return {
        "success": True,
        "session_id": session_id,
        "message": "Credenciales almacenadas temporalmente",
        "expires_in": ttl_seconds
    }


@router.post("/release")
@handle_route_errors("MININA.WebUI.Credentials")
async def release_credentials(data: Dict[str, Any]) -> Dict[str, Any]:
    """Release and clear credentials."""
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    result = credential_vault.release_credentials(session_id)
    
    logger.info(f"Released credentials: {session_id}", extra={
        "session_id": session_id,
        "success": result
    })
    
    return {
        "success": result,
        "message": "Credenciales liberadas" if result else "No se pudieron liberar las credenciales"
    }


@router.post("/validate-request")
@handle_route_errors("MININA.WebUI.Credentials")
async def validate_credential_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if a skill can request credentials."""
    skill_id = data.get("skill_id")
    permissions = data.get("permissions", [])
    
    if not skill_id:
        raise HTTPException(status_code=400, detail="skill_id is required")
    
    result = credential_vault.validate_skill_credential_request(skill_id, permissions)
    
    return {
        "success": True,
        "validation": result
    }
