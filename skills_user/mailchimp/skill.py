"""
MININA v3.0 - Mailchimp Skill
Skill para operaciones con Mailchimp
"""

from core.api.mailchimp_manager import mailchimp_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Mailchimp
    
    Args:
        context: {
            "action": str,           # get_lists, add_subscriber, update_subscriber, remove_subscriber, get_subscribers, get_campaigns
            "list_id": str,        # ID de la lista/audiencia
            "email": str,          # Email del suscriptor
            "first_name": str,     # Nombre (opcional)
            "last_name": str,      # Apellido (opcional)
            "status": str,         # subscribed, unsubscribed, cleaned, pending
            "count": int          # Límite de resultados
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
        
        # Verificar que Mailchimp está configurado
        if not mailchimp_manager.is_configured():
            return {
                "success": False,
                "error": "Mailchimp no configurado. Ve a Configuración → Mailchimp para agregar tu API Key."
            }
        
        if action == "get_lists":
            return mailchimp_manager.get_lists()
        
        elif action == "add_subscriber":
            list_id = context.get("list_id", "")
            email = context.get("email", "")
            first_name = context.get("first_name")
            last_name = context.get("last_name")
            status = context.get("status", "subscribed")
            
            if not list_id:
                return {"success": False, "error": "Falta list_id"}
            if not email:
                return {"success": False, "error": "Falta email"}
            
            return mailchimp_manager.add_subscriber(list_id, email, first_name, last_name, status)
        
        elif action == "update_subscriber":
            list_id = context.get("list_id", "")
            email = context.get("email", "")
            first_name = context.get("first_name")
            last_name = context.get("last_name")
            status = context.get("status")
            
            if not list_id:
                return {"success": False, "error": "Falta list_id"}
            if not email:
                return {"success": False, "error": "Falta email"}
            
            return mailchimp_manager.update_subscriber(list_id, email, first_name, last_name, status)
        
        elif action == "remove_subscriber":
            list_id = context.get("list_id", "")
            email = context.get("email", "")
            
            if not list_id:
                return {"success": False, "error": "Falta list_id"}
            if not email:
                return {"success": False, "error": "Falta email"}
            
            return mailchimp_manager.remove_subscriber(list_id, email)
        
        elif action == "get_subscribers":
            list_id = context.get("list_id", "")
            count = context.get("count", 10)
            
            if not list_id:
                return {"success": False, "error": "Falta list_id"}
            
            return mailchimp_manager.get_subscribers(list_id, count)
        
        elif action == "get_campaigns":
            count = context.get("count", 10)
            return mailchimp_manager.get_campaigns(count)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: get_lists, add_subscriber, update_subscriber, remove_subscriber, get_subscribers, get_campaigns"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Mailchimp: {str(e)}"
        }
