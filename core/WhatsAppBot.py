"""
MiIA WhatsApp Business API Integration
Servicio de integración con WhatsApp Cloud API (Meta)
"""
import os
import json
import logging
import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("WhatsAppBot")

@dataclass
class WhatsAppMessage:
    """Mensaje de WhatsApp"""
    from_number: str
    text: str
    message_id: str
    timestamp: str


class WhatsAppBotService:
    """
    Servicio de bot para WhatsApp Business API
    Integra con Meta Cloud API para enviar y recibir mensajes
    """
    
    API_VERSION = "v17.0"
    BASE_URL = "https://graph.facebook.com"
    
    def __init__(self, phone_number_id: str, access_token: str, business_account_id: str = ""):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.business_account_id = business_account_id
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._webhook_running = False
        self._handlers: List[callable] = []
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtener o crear sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def send_text_message(self, to_number: str, text: str) -> Dict[str, Any]:
        """
        Enviar mensaje de texto a un número de WhatsApp
        
        Args:
            to_number: Número del destinatario (con código de país, sin +)
            text: Texto del mensaje
            
        Returns:
            Respuesta de la API
        """
        url = f"{self.BASE_URL}/{self.API_VERSION}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {
                "body": text
            }
        }
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"✅ Mensaje enviado a {to_number}")
                    return {"success": True, "data": result}
                else:
                    error_msg = result.get("error", {}).get("message", "Error desconocido")
                    logger.error(f"❌ Error enviando mensaje: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(self, to_number: str, template_name: str, 
                                   language_code: str = "es",
                                   components: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Enviar mensaje usando plantilla aprobada
        
        Args:
            to_number: Número del destinatario
            template_name: Nombre de la plantilla
            language_code: Código de idioma (default: es)
            components: Componentes de la plantilla
        """
        url = f"{self.BASE_URL}/{self.API_VERSION}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info(f"✅ Plantilla enviada a {to_number}")
                    return {"success": True, "data": result}
                else:
                    error_msg = result.get("error", {}).get("message", "Error desconocido")
                    logger.error(f"❌ Error enviando plantilla: {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ Error enviando plantilla: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_business_profile(self) -> Dict[str, Any]:
        """Obtener perfil de negocio"""
        url = f"{self.BASE_URL}/{self.API_VERSION}/{self.phone_number_id}/whatsapp_business_profile"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "fields": "about,address,description,email,profile_picture_url,websites,vertical"
        }
        
        try:
            session = await self._get_session()
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                
                if response.status == 200:
                    return {"success": True, "data": result}
                else:
                    error_msg = result.get("error", {}).get("message", "Error desconocido")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo perfil: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_connection(self) -> bool:
        """Verificar que la conexión con WhatsApp API funciona"""
        result = await self.get_business_profile()
        return result.get("success", False)
    
    async def close(self):
        """Cerrar sesión HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("🛑 Sesión de WhatsApp cerrada")


class WhatsAppWebhookHandler:
    """
    Manejador de webhooks para WhatsApp
    Recibe mensajes entrantes de Meta
    """
    
    def __init__(self, verify_token: str):
        self.verify_token = verify_token
        self._message_handlers: List[callable] = []
    
    def on_message(self, handler: callable):
        """Registrar handler para mensajes entrantes"""
        self._message_handlers.append(handler)
        return handler
    
    def handle_verification(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verificar webhook con Meta
        
        Returns:
            challenge si la verificación es exitosa, None si falla
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("✅ Webhook verificado correctamente")
            return challenge
        else:
            logger.error("❌ Verificación de webhook fallida")
            return None
    
    async def handle_incoming_message(self, payload: Dict[str, Any]):
        """Procesar mensaje entrante"""
        try:
            # Extraer datos del mensaje
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            if "messages" in value:
                for msg in value["messages"]:
                    if msg.get("type") == "text":
                        whatsapp_msg = WhatsAppMessage(
                            from_number=msg.get("from"),
                            text=msg.get("text", {}).get("body", ""),
                            message_id=msg.get("id"),
                            timestamp=msg.get("timestamp")
                        )
                        
                        # Notificar a todos los handlers
                        for handler in self._message_handlers:
                            try:
                                await handler(whatsapp_msg)
                            except Exception as e:
                                logger.error(f"Error en handler: {e}")
                                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")


# Instancia global del servicio (se inicializa desde BotConfigManager)
whatsapp_service: Optional[WhatsAppBotService] = None

async def init_whatsapp_service(phone_number_id: str, access_token: str, 
                                 business_account_id: str = "") -> bool:
    """
    Inicializar servicio de WhatsApp global
    
    Returns:
        True si la conexión es exitosa
    """
    global whatsapp_service
    
    try:
        whatsapp_service = WhatsAppBotService(
            phone_number_id=phone_number_id,
            access_token=access_token,
            business_account_id=business_account_id
        )
        
        # Verificar conexión
        if await whatsapp_service.verify_connection():
            logger.info("✅ Servicio de WhatsApp inicializado correctamente")
            return True
        else:
            logger.error("❌ No se pudo verificar conexión con WhatsApp")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error inicializando WhatsApp: {e}")
        return False

async def send_whatsapp_message(to_number: str, text: str) -> Dict[str, Any]:
    """Enviar mensaje usando el servicio global"""
    if whatsapp_service is None:
        return {"success": False, "error": "Servicio de WhatsApp no inicializado"}
    
    return await whatsapp_service.send_text_message(to_number, text)
