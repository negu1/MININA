"""
Sistema de notificaciones para APIs faltantes
Notifica al usuario cuando falta una API necesaria
"""
from typing import List, Optional
from core.api_registry import APIInfo, get_api_registry
import asyncio


class APINotificationManager:
    """
    Gestiona notificaciones cuando faltan APIs.
    Notifica en UI y opcionalmente por Telegram/WhatsApp.
    """
    
    def __init__(self):
        self.ui_callback = None
        self.notification_history = []
    
    def set_ui_callback(self, callback):
        """Establecer callback para notificaciones UI"""
        self.ui_callback = callback
    
    async def notify_missing_apis(self, missing_apis: List[APIInfo], context: str = ""):
        """
        Notificar al usuario sobre APIs faltantes.
        Notifica en UI y por bots configurados.
        """
        if not missing_apis:
            return
        
        # Formatear mensaje
        message = self._format_notification(missing_apis, context)
        
        # 1. Notificar en UI (si hay callback)
        if self.ui_callback:
            try:
                self.ui_callback({
                    "type": "missing_apis",
                    "message": message,
                    "apis": [api.id for api in missing_apis],
                    "context": context
                })
            except Exception as e:
                print(f"Error notificando en UI: {e}")
        
        # 2. Notificar por Telegram (si está configurado)
        await self._notify_telegram(message)
        
        # 3. Notificar por WhatsApp (si está configurado)
        await self._notify_whatsapp(message)
        
        # 4. Registrar en historial
        self.notification_history.append({
            "missing_apis": [api.id for api in missing_apis],
            "context": context,
            "message": message
        })
    
    def _format_notification(self, missing_apis: List[APIInfo], context: str) -> str:
        """Formatear mensaje de notificación"""
        lines = [
            f"⚠️ *APIs Requeridas No Configuradas*",
            f"",
            f"Para completar la acción: _{context}_",
            f"",
            f"Se requieren las siguientes APIs:",
        ]
        
        for api in missing_apis:
            lines.append(f"  • *{api.name}* - {', '.join(api.required_for)}")
        
        lines.extend([
            f"",
            f"💡 *Para configurar:*",
            f"1. Abre Settings > APIs",
            f"2. Selecciona la categoría correspondiente",
            f"3. Configura la API faltante",
        ])
        
        return "\n".join(lines)
    
    async def _notify_telegram(self, message: str):
        """Notificar por Telegram si está configurado"""
        try:
            from core.api.telegram_manager import get_telegram_manager
            tg = get_telegram_manager()
            if tg and tg.is_configured():
                await tg.send_message(message)
        except Exception as e:
            print(f"No se pudo notificar por Telegram: {e}")
    
    async def _notify_whatsapp(self, message: str):
        """Notificar por WhatsApp si está configurado"""
        try:
            from core.api.whatsapp_manager import get_whatsapp_manager
            wa = get_whatsapp_manager()
            if wa and wa.is_configured():
                await wa.send_message(message)
        except Exception as e:
            print(f"No se pudo notificar por WhatsApp: {e}")
    
    def check_and_notify_for_intent(self, intent: str) -> bool:
        """
        Verificar APIs necesarias para un intent y notificar si faltan.
        Retorna True si todas las APIs están disponibles, False si falta alguna.
        """
        registry = get_api_registry()
        missing = registry.check_api_for_intent(intent)
        
        if missing:
            # Ejecutar notificación async
            asyncio.create_task(self.notify_missing_apis(missing, f"Ejecutar: {intent}"))
            return False
        
        return True
    
    def get_last_notifications(self, count: int = 10) -> List[dict]:
        """Obtener últimas notificaciones"""
        return self.notification_history[-count:]


# Singleton
_notification_manager = None

def get_notification_manager() -> APINotificationManager:
    """Obtener instancia singleton"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = APINotificationManager()
    return _notification_manager
