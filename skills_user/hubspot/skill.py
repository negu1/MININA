"""
MININA v3.0 - HubSpot Skill
Skill para operaciones con HubSpot
"""

from core.api.hubspot_manager import hubspot_manager


def execute(context: dict) -> dict:
    """
    Operaciones con HubSpot
    
    Args:
        context: {
            "action": str,           # create_contact, get_contact, search_contacts, update_contact, delete_contact, create_deal
            "email": str,          # Email del contacto
            "firstname": str,      # Nombre (opcional)
            "lastname": str,       # Apellido (opcional)
            "phone": str,          # Teléfono (opcional)
            "company": str,        # Empresa (opcional)
            "contact_id": str,     # ID del contacto (para get/update/delete)
            "query": str,         # Búsqueda (para search)
            "properties": dict,   # Propiedades a actualizar (para update)
            "dealname": str,      # Nombre del deal (para create_deal)
            "amount": float,      # Monto del deal (opcional)
            "stage": str,         # Etapa del deal (opcional)
            "pipeline": str       # Pipeline (opcional)
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
        
        # Verificar que HubSpot está configurado
        if not hubspot_manager.is_configured():
            return {
                "success": False,
                "error": "HubSpot no configurado. Ve a Configuración → HubSpot para agregar tu Private App Token."
            }
        
        if action == "create_contact":
            email = context.get("email", "")
            firstname = context.get("firstname")
            lastname = context.get("lastname")
            phone = context.get("phone")
            company = context.get("company")
            
            if not email:
                return {"success": False, "error": "Falta email"}
            
            return hubspot_manager.create_contact(email, firstname, lastname, phone, company)
        
        elif action == "get_contact":
            contact_id = context.get("contact_id", "")
            
            if not contact_id:
                return {"success": False, "error": "Falta contact_id"}
            
            return hubspot_manager.get_contact(contact_id)
        
        elif action == "search_contacts":
            query = context.get("query", "")
            limit = context.get("limit", 10)
            
            if not query:
                return {"success": False, "error": "Falta query"}
            
            return hubspot_manager.search_contacts(query, limit)
        
        elif action == "update_contact":
            contact_id = context.get("contact_id", "")
            properties = context.get("properties", {})
            
            if not contact_id:
                return {"success": False, "error": "Falta contact_id"}
            if not properties:
                return {"success": False, "error": "Falta properties"}
            
            return hubspot_manager.update_contact(contact_id, properties)
        
        elif action == "delete_contact":
            contact_id = context.get("contact_id", "")
            
            if not contact_id:
                return {"success": False, "error": "Falta contact_id"}
            
            return hubspot_manager.delete_contact(contact_id)
        
        elif action == "create_deal":
            dealname = context.get("dealname", "")
            amount = context.get("amount")
            stage = context.get("stage")
            pipeline = context.get("pipeline")
            
            if not dealname:
                return {"success": False, "error": "Falta dealname"}
            
            return hubspot_manager.create_deal(dealname, amount, stage, pipeline)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: create_contact, get_contact, search_contacts, update_contact, delete_contact, create_deal"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de HubSpot: {str(e)}"
        }
