"""
MiIA Bot Configuration Manager
Sistema de configuración segura para bots de Telegram y WhatsApp
- Guías paso a paso para usuarios
- Almacenamiento encriptado de credenciales
- Panel de configuración en WebUI
- Integración automática con servicios de bot
"""
import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger("BotConfigManager")

# Usar el mismo sistema de credenciales que LLM
from core.llm_extension import SecureCredentialStore

# Importar servicio de Telegram (si está disponible)
try:
    from core.TelegramBot import TelegramBotService
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("TelegramBot no disponible")

# Importar servicio de WhatsApp (si está disponible)
try:
    from core.WhatsAppBot import WhatsAppBotService, init_whatsapp_service
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    logger.warning("WhatsAppBot no disponible")

@dataclass
class TelegramBotConfig:
    """Configuración de bot de Telegram"""
    bot_token: str = ""
    chat_id: str = ""
    bot_name: str = ""
    is_active: bool = False
    
@dataclass
class WhatsAppBotConfig:
    """Configuración de bot de WhatsApp Business"""
    phone_number_id: str = ""
    business_account_id: str = ""
    access_token: str = ""
    api_version: str = "v17.0"
    is_active: bool = False


class BotConfigurationManager:
    """
    Gestor de configuración de bots para MiIA
    - Almacena credenciales de forma segura
    - Proporciona guías paso a paso
    - Permite cambiar/reemplazar tokens fácilmente
    - Integra automáticamente con servicios de bot
    """
    
    def __init__(self):
        self.credential_store = SecureCredentialStore(app_name="miia-product-20")
        self.config_file = Path.home() / ".config" / "miia-product-20" / "bot_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
        
        # Instancias de servicios de bot
        self._telegram_service = None
        self._whatsapp_service = None
        
        # Iniciar bots configurados al arrancar
        self._loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else None
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración de bots"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando config: {e}")
        return {"telegram": {}, "whatsapp": {}}
    
    def _save_config(self) -> bool:
        """Guardar configuración"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error guardando config: {e}")
            return False
    
    async def _start_telegram_bot(self, token: str) -> bool:
        """Iniciar servicio de Telegram automáticamente"""
        if not TELEGRAM_AVAILABLE:
            logger.error("TelegramBotService no está disponible")
            return False
        
        try:
            # Detener bot anterior si existe
            if self._telegram_service:
                await self._telegram_service.stop()
                self._telegram_service = None
            
            # Crear e iniciar nuevo bot
            self._telegram_service = TelegramBotService(token=token)
            await self._telegram_service.start()
            logger.info("✅ Bot de Telegram iniciado automáticamente")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando bot de Telegram: {e}")
            return False
    
    async def _stop_telegram_bot(self):
        """Detener bot de Telegram"""
        if self._telegram_service:
            try:
                await self._telegram_service.stop()
                self._telegram_service = None
                logger.info("🛑 Bot de Telegram detenido")
            except Exception as e:
                logger.error(f"Error deteniendo bot: {e}")
    
    # ============= TELEGRAM =============
    
    def get_telegram_guide(self) -> Dict[str, Any]:
        """
        Guía completa paso a paso para configurar bot de Telegram
        """
        return {
            "title": "🤖 Configurar Bot de Telegram",
            "warnings": [
                "⚠️ NUNCA compartas tu Bot Token con nadie",
                "⚠️ Guarda el token en un lugar seguro",
                "⚠️ Si el token se filtra, cualquiera puede controlar tu bot",
                "🔒 MiIA encriptará y protegerá tu token automáticamente"
            ],
            "steps": [
                {
                    "step": 1,
                    "title": "Crear el Bot con BotFather",
                    "instructions": [
                        "Abre Telegram y busca: @BotFather",
                        "Inicia conversación y escribe: /newbot",
                        "Elige un nombre para tu bot (ej: MiIA Asistente)",
                        "Elige un username que termine en 'bot' (ej: miia_asistente_bot)"
                    ],
                    "result": "BotFather te dará un TOKEN (largo, con números y letras)"
                },
                {
                    "step": 2,
                    "title": "Obtener tu Chat ID",
                    "instructions": [
                        "Busca en Telegram: @userinfobot",
                        "Inicia conversación con el bot",
                        "El bot responderá automáticamente con tu información"
                    ],
                    "result": "Copia el número que aparece después de 'Id:'"
                },
                {
                    "step": 3,
                    "title": "Configurar en MiIA",
                    "instructions": [
                        "Abre la WebUI de MiIA",
                        "Ve al panel 'Configuración de Bot'",
                        "Pega el TOKEN en el campo correspondiente",
                        "Pega el CHAT ID en el campo correspondiente",
                        "Haz clic en 'Guardar Configuración'",
                        "✅ El bot se iniciará automáticamente"
                    ],
                    "result": "✅ Tu bot de Telegram está listo y funcionando"
                }
            ],
            "links": {
                "botfather": "https://t.me/BotFather",
                "userinfobot": "https://t.me/userinfobot"
            },
            "example_token": "123456789:ABCdefGHIjklMNOpqrSTUvwxyz",
            "example_chat_id": "123456789"
        }
    
    def save_telegram_config(self, token: str, chat_id: str, bot_name: str = "") -> Dict[str, Any]:
        """
        Guardar configuración de Telegram de forma segura e iniciar bot automáticamente
        """
        # Validar token básico
        if not token or len(token) < 20:
            return {
                "success": False,
                "error": "Token inválido. Debe tener al menos 20 caracteres."
            }
        
        # Validar chat_id
        if not chat_id or not chat_id.lstrip('-').isdigit():
            return {
                "success": False,
                "error": "Chat ID inválido. Debe ser un número."
            }
        
        try:
            # Guardar en el store seguro
            self.credential_store.set_api_key("telegram_bot_token", token)
            self.credential_store.set_api_key("telegram_chat_id", chat_id)
            
            # Guardar metadata
            self._config["telegram"] = {
                "bot_name": bot_name or "MiIA Bot",
                "chat_id": chat_id,
                "is_active": True,
                "configured_at": str(Path.home() / ".config" / "miia-product-20")
            }
            
            self._save_config()
            
            # 🚀 INICIAR BOT AUTOMÁTICAMENTE
            logger.info("Iniciando bot de Telegram automáticamente...")
            
            # Usar asyncio para iniciar el bot
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Si hay un loop corriendo, crear tarea
                    asyncio.create_task(self._start_telegram_bot(token))
                else:
                    # Si no hay loop, iniciar sincrónicamente
                    loop.run_until_complete(self._start_telegram_bot(token))
            except Exception as e:
                logger.error(f"Error al iniciar bot automáticamente: {e}")
                # No fallar si no se puede iniciar, el usuario puede reiniciar
            
            return {
                "success": True,
                "message": "✅ Configuración de Telegram guardada y bot iniciado",
                "bot_name": bot_name or "MiIA Bot"
            }
            
        except Exception as e:
            logger.error(f"Error guardando config Telegram: {e}")
            return {
                "success": False,
                "error": f"Error al guardar: {str(e)}"
            }
    
    def update_telegram_token(self, new_token: str) -> Dict[str, Any]:
        """
        Actualizar token de Telegram (reemplazar el anterior) y reiniciar bot
        """
        # Obtener chat_id actual
        current_chat_id = self.credential_store.get_api_key("telegram_chat_id")
        bot_name = self._config.get("telegram", {}).get("bot_name", "MiIA Bot")
        
        # Guardar nuevo token
        result = self.save_telegram_config(new_token, current_chat_id or "", bot_name)
        
        if result["success"]:
            result["message"] = "✅ Token actualizado y bot reiniciado correctamente"
        
        return result
    
    def delete_telegram_config(self) -> Dict[str, Any]:
        """
        Eliminar completamente la configuración de Telegram y detener bot
        """
        try:
            # Detener bot primero
            asyncio.create_task(self._stop_telegram_bot())
            
            self.credential_store.delete_api_key("telegram_bot_token")
            self.credential_store.delete_api_key("telegram_chat_id")
            self._config["telegram"] = {}
            self._save_config()
            
            return {
                "success": True,
                "message": "🗑️ Configuración de Telegram eliminada y bot detenido"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al eliminar: {str(e)}"
            }
    
    def get_telegram_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de configuración de Telegram
        """
        has_token = self.credential_store.has_key("telegram_bot_token")
        has_chat_id = self.credential_store.has_key("telegram_chat_id")
        
        return {
            "is_configured": has_token and has_chat_id,
            "has_token": has_token,
            "has_chat_id": has_chat_id,
            "bot_name": self._config.get("telegram", {}).get("bot_name", ""),
            "is_active": self._telegram_service is not None,
            "bot_running": self._telegram_service is not None
        }
    
    async def _start_whatsapp_bot(self, phone_id: str, access_token: str, business_id: str) -> bool:
        """Iniciar servicio de WhatsApp automáticamente"""
        if not WHATSAPP_AVAILABLE:
            logger.error("WhatsAppBotService no está disponible")
            return False
        
        try:
            # Usar la función global de inicialización
            success = await init_whatsapp_service(phone_id, access_token, business_id)
            if success:
                self._whatsapp_service = True  # Marcamos como activo
                logger.info("✅ Bot de WhatsApp inicializado automáticamente")
                return True
            else:
                logger.error("❌ No se pudo inicializar WhatsApp")
                return False
            
        except Exception as e:
            logger.error(f"Error iniciando bot de WhatsApp: {e}")
            return False
    
    async def _stop_whatsapp_bot(self):
        """Detener bot de WhatsApp"""
        from core.WhatsAppBot import whatsapp_service
        if whatsapp_service:
            try:
                await whatsapp_service.close()
                self._whatsapp_service = None
                logger.info("🛑 Bot de WhatsApp detenido")
            except Exception as e:
                logger.error(f"Error deteniendo bot WhatsApp: {e}")
    
    def get_whatsapp_guide(self) -> Dict[str, Any]:
        """
        Guía paso a paso para configurar WhatsApp Business API
        """
        return {
            "title": "💬 Configurar WhatsApp Business API",
            "warnings": [
                "⚠️ Requiere cuenta de Meta Business",
                "⚠️ Número de teléfono dedicado (no personal)",
                "⚠️ Proceso de verificación puede tardar días",
                "🔒 MiIA encriptará todas las credenciales"
            ],
            "steps": [
                {
                    "step": 1,
                    "title": "Crear cuenta Meta Business",
                    "instructions": [
                        "Ve a: business.facebook.com",
                        "Crea una cuenta de Meta Business",
                        "Verifica tu cuenta con documento de identidad"
                    ],
                    "result": "Tendrás un Business Account ID"
                },
                {
                    "step": 2,
                    "title": "Configurar WhatsApp Business",
                    "instructions": [
                        "En Meta Business Suite, ve a 'Configuración'",
                        "Selecciona 'Canales' → 'WhatsApp'",
                        "Agrega un número de teléfono dedicado",
                        "Verifica el número por SMS"
                    ],
                    "result": "Obtendrás el Phone Number ID"
                },
                {
                    "step": 3,
                    "title": "Obtener Access Token",
                    "instructions": [
                        "Ve a: developers.facebook.com",
                        "Crea una nueva app (tipo 'Business')",
                        "Agrega producto 'WhatsApp'",
                        "En 'Configuración' → 'Tokens de acceso'",
                        "Genera token permanente con permisos: whatsapp_business_messaging"
                    ],
                    "result": "Copia el Access Token (largo, empieza con EA...)",
                    "note": "⚠️ El token temporal expira en 24h, usa token permanente"
                },
                {
                    "step": 4,
                    "title": "Configurar en MiIA",
                    "instructions": [
                        "Abre la WebUI de MiIA",
                        "Ve al panel 'Configuración de Bot'",
                        "Selecciona pestaña 'WhatsApp'",
                        "Ingresa: Phone Number ID, Business Account ID, Access Token",
                        "Haz clic en 'Guardar Configuración'"
                    ],
                    "result": "✅ Tu bot de WhatsApp está configurado"
                }
            ],
            "links": {
                "meta_business": "https://business.facebook.com",
                "developers": "https://developers.facebook.com",
                "docs": "https://developers.facebook.com/docs/whatsapp/cloud-api"
            },
            "example": {
                "phone_number_id": "123456789012345",
                "business_account_id": "987654321098765",
                "access_token": "EAABsB... (muy largo)"
            }
        }
    
    def save_whatsapp_config(self, phone_id: str, business_id: str, 
                             access_token: str) -> Dict[str, Any]:
        """
        Guardar configuración de WhatsApp e iniciar servicio automáticamente
        """
        # Validaciones básicas
        if not all([phone_id, business_id, access_token]):
            return {
                "success": False,
                "error": "Todos los campos son requeridos"
            }
        
        try:
            # Guardar en el store seguro
            self.credential_store.set_api_key("whatsapp_phone_id", phone_id)
            self.credential_store.set_api_key("whatsapp_business_id", business_id)
            self.credential_store.set_api_key("whatsapp_access_token", access_token)
            
            # Guardar metadata
            self._config["whatsapp"] = {
                "phone_number_id": phone_id,
                "business_account_id": business_id,
                "is_active": True
            }
            
            self._save_config()
            
            # 🚀 INICIAR WHATSAPP AUTOMÁTICAMENTE
            logger.info("Iniciando servicio de WhatsApp automáticamente...")
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._start_whatsapp_bot(phone_id, access_token, business_id))
                else:
                    loop.run_until_complete(self._start_whatsapp_bot(phone_id, access_token, business_id))
            except Exception as e:
                logger.error(f"Error al iniciar WhatsApp automáticamente: {e}")
            
            return {
                "success": True,
                "message": "✅ Configuración de WhatsApp guardada y servicio iniciado"
            }
            
        except Exception as e:
            logger.error(f"Error guardando config WhatsApp: {e}")
            return {
                "success": False,
                "error": f"Error al guardar: {str(e)}"
            }
    
    def update_whatsapp_token(self, new_token: str) -> Dict[str, Any]:
        """
        Actualizar token de WhatsApp
        """
        current_config = self._config.get("whatsapp", {})
        return self.save_whatsapp_config(
            current_config.get("phone_number_id", ""),
            current_config.get("business_account_id", ""),
            new_token
        )
    
    def delete_whatsapp_config(self) -> Dict[str, Any]:
        """
        Eliminar configuración de WhatsApp
        """
        try:
            self.credential_store.delete_api_key("whatsapp_phone_id")
            self.credential_store.delete_api_key("whatsapp_business_id")
            self.credential_store.delete_api_key("whatsapp_access_token")
            self._config["whatsapp"] = {}
            self._save_config()
            
            return {
                "success": True,
                "message": "🗑️ Configuración de WhatsApp eliminada"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al eliminar: {str(e)}"
            }
    
    def get_whatsapp_status(self) -> Dict[str, Any]:
        """
        Obtener estado de WhatsApp
        """
        has_phone = self.credential_store.has_key("whatsapp_phone_id")
        has_business = self.credential_store.has_key("whatsapp_business_id")
        has_token = self.credential_store.has_key("whatsapp_access_token")
        
        return {
            "is_configured": has_phone and has_business and has_token,
            "has_phone_id": has_phone,
            "has_business_id": has_business,
            "has_token": has_token,
            "is_active": self._config.get("whatsapp", {}).get("is_active", False)
        }
    
    # ============= GENERAL =============
    
    def get_all_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los bots"""
        return {
            "telegram": self.get_telegram_status(),
            "whatsapp": self.get_whatsapp_status()
        }


# Instancia global
bot_config_manager = BotConfigurationManager()
