"""
MININA v3.0 - Google Calendar Skill
Skill para operaciones con Google Calendar
"""

from core.api.google_calendar_manager import google_calendar_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Google Calendar
    
    Args:
        context: {
            "action": str,           # list_events, create_event, delete_event, update_event
            "calendar_id": str,      # ID del calendario (default: primary)
            "summary": str,            # Título del evento (para crear/actualizar)
            "start_time": str,         # Fecha/hora inicio ISO format
            "end_time": str,           # Fecha/hora fin ISO format
            "description": str,        # Descripción del evento
            "location": str,           # Ubicación
            "attendees": list,         # Lista de emails
            "event_id": str            # ID del evento (para delete/update)
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
        
        # Verificar que Calendar está configurado
        if not google_calendar_manager.is_configured():
            return {
                "success": False,
                "error": "Google Calendar no configurado. Ve a Configuración → Google Calendar."
            }
        
        if action == "list_events":
            calendar_id = context.get("calendar_id", "primary")
            return google_calendar_manager.list_events(calendar_id)
        
        elif action == "create_event":
            summary = context.get("summary", "")
            start_time = context.get("start_time", "")
            end_time = context.get("end_time", "")
            description = context.get("description", "")
            location = context.get("location", "")
            attendees = context.get("attendees", [])
            calendar_id = context.get("calendar_id", "primary")
            
            if not summary:
                return {"success": False, "error": "Falta título del evento (summary)"}
            
            return google_calendar_manager.create_event(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                attendees=attendees,
                calendar_id=calendar_id
            )
        
        elif action == "delete_event":
            event_id = context.get("event_id", "")
            calendar_id = context.get("calendar_id", "primary")
            
            if not event_id:
                return {"success": False, "error": "Falta event_id"}
            
            return google_calendar_manager.delete_event(event_id, calendar_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_events, create_event, delete_event"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Calendar: {str(e)}"
        }
