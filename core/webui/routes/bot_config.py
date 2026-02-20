"""
Bot Config Router
=================
Endpoints para configuración de bots (Telegram/WhatsApp).
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os

from core.logging_config import get_logger
from core.config import get_settings
from core.webui.decorators import handle_route_errors

logger = get_logger("MININA.WebUI.Bot")
router = APIRouter()


@router.get("/telegram/status")
@handle_route_errors("MININA.WebUI.Bot")
async def get_telegram_status() -> Dict[str, Any]:
    """Get Telegram bot configuration status."""
    settings = get_settings()
    return {
        "success": True,
        "configured": settings.is_telegram_configured,
        "has_token": settings.TELEGRAM_BOT_TOKEN is not None,
        "allowed_chat_ids": list(settings.telegram_allowed_ids) if settings.telegram_allowed_ids else None
    }


@router.post("/telegram/configure")
@handle_route_errors("MININA.WebUI.Bot")
async def configure_telebot(data: Dict[str, Any]) -> Dict[str, Any]:
    """Configure Telegram bot."""
    token = data.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    
    # Update environment variable
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    
    logger.info("Telegram bot configured", extra={"configured": True})
    
    return {
        "success": True,
        "message": "Telegram bot configured successfully"
    }


@router.get("/whatsapp/status")
@handle_route_errors("MININA.WebUI.Bot")
async def get_whatsapp_status() -> Dict[str, Any]:
    """Get WhatsApp bot configuration status."""
    settings = get_settings()
    return {
        "success": True,
        "configured": settings.is_whatsapp_configured,
        "phone_id": settings.WHATSAPP_PHONE_ID is not None,
        "has_token": settings.WHATSAPP_ACCESS_TOKEN is not None
    }


@router.post("/whatsapp/configure")
@handle_route_errors("MININA.WebUI.Bot")
async def configure_whatsapp(data: Dict[str, Any]) -> Dict[str, Any]:
    """Configure WhatsApp bot."""
    phone_id = data.get("phone_id")
    business_id = data.get("business_id")
    token = data.get("token")
    
    if not all([phone_id, token]):
        raise HTTPException(status_code=400, detail="phone_id and token are required")
    
    # Update environment variables
    os.environ["WHATSAPP_PHONE_ID"] = phone_id
    if business_id:
        os.environ["WHATSAPP_BUSINESS_ID"] = business_id
    os.environ["WHATSAPP_ACCESS_TOKEN"] = token
    
    logger.info("WhatsApp bot configured", extra={
        "phone_id": phone_id,
        "has_business_id": business_id is not None
    })
    
    return {
        "success": True,
        "message": "WhatsApp bot configured successfully"
    }
