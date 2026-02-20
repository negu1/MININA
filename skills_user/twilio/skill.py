"""
MININA v3.0 - Twilio Skill
Skill para operaciones con Twilio (SMS, llamadas, WhatsApp)
"""

from core.api.twilio_manager import twilio_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Twilio
    
    Args:
        context: {
            "action": str,           # send_sms, send_whatsapp, make_call, get_message, list_messages, lookup_number
            "to_number": str,      # Número destino (para send/call)
            "message": str,        # Mensaje (para send)
            "call_url": str,       # URL TwiML (para make_call)
            "message_sid": str,    # SID del mensaje (para get_message)
            "from_number": str,   # Filtro (opcional para list)
            "limit": int,         # Límite de mensajes (default 50)
            "phone_number": str   # Número a buscar (para lookup)
        }
    
    Returns:
        {
            "success": bool,
            "result": dict,
            "error": str (si falla)
        }
    """
    try:
        action = context.get("action", "")
        
        # Verificar que Twilio está configurado
        if not twilio_manager.is_configured():
            return {
                "success": False,
                "error": "Twilio no configurado. Ve a Configuración → Twilio para agregar tus credenciales."
            }
        
        if action == "send_sms":
            to_number = context.get("to_number", "")
            message = context.get("message", "")
            
            if not to_number:
                return {"success": False, "error": "Falta to_number"}
            if not message:
                return {"success": False, "error": "Falta message"}
            
            return twilio_manager.send_sms(to_number, message)
        
        elif action == "send_whatsapp":
            to_number = context.get("to_number", "")
            message = context.get("message", "")
            
            if not to_number:
                return {"success": False, "error": "Falta to_number"}
            if not message:
                return {"success": False, "error": "Falta message"}
            
            return twilio_manager.send_whatsapp(to_number, message)
        
        elif action == "make_call":
            to_number = context.get("to_number", "")
            call_url = context.get("call_url", "")
            
            if not to_number:
                return {"success": False, "error": "Falta to_number"}
            if not call_url:
                return {"success": False, "error": "Falta call_url (URL con TwiML)"}
            
            return twilio_manager.make_call(to_number, call_url)
        
        elif action == "get_message":
            message_sid = context.get("message_sid", "")
            
            if not message_sid:
                return {"success": False, "error": "Falta message_sid"}
            
            return twilio_manager.get_message(message_sid)
        
        elif action == "list_messages":
            to_number = context.get("to_number")
            from_number = context.get("from_number")
            limit = context.get("limit", 50)
            
            return twilio_manager.list_messages(to_number, from_number, limit)
        
        elif action == "lookup_number":
            phone_number = context.get("phone_number", "")
            
            if not phone_number:
                return {"success": False, "error": "Falta phone_number"}
            
            return twilio_manager.lookup_phone_number(phone_number)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: send_sms, send_whatsapp, make_call, get_message, list_messages, lookup_number"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Twilio: {str(e)}"
        }
