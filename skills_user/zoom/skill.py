"""
MININA v3.0 - Zoom Skill
Skill para operaciones con Zoom
"""

from core.api.zoom_manager import zoom_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Zoom
    
    Args:
        context: {
            "action": str,           # create_meeting, delete_meeting, list_meetings, get_details
            "topic": str,          # Título de la reunión (para create)
            "start_time": str,     # ISO 8601 format (para create)
            "duration": int,       # Duración en minutos (opcional, default 60)
            "timezone": str,       # Zona horaria (opcional, default UTC)
            "meeting_id": str      # ID de la reunión (para delete/get_details)
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
        
        # Verificar que Zoom está configurado
        if not zoom_manager.is_configured():
            return {
                "success": False,
                "error": "Zoom no configurado. Ve a Configuración → Zoom para agregar tus credenciales."
            }
        
        if action == "create_meeting":
            topic = context.get("topic", "")
            start_time = context.get("start_time", "")
            duration = context.get("duration", 60)
            timezone = context.get("timezone", "UTC")
            
            if not topic:
                return {"success": False, "error": "Falta topic"}
            if not start_time:
                return {"success": False, "error": "Falta start_time (formato ISO 8601)"}
            
            return zoom_manager.create_meeting(topic, start_time, duration, timezone)
        
        elif action == "delete_meeting":
            meeting_id = context.get("meeting_id", "")
            if not meeting_id:
                return {"success": False, "error": "Falta meeting_id"}
            return zoom_manager.delete_meeting(meeting_id)
        
        elif action == "list_meetings":
            meeting_type = context.get("type", "scheduled")
            return zoom_manager.list_meetings(meeting_type)
        
        elif action == "get_details":
            meeting_id = context.get("meeting_id", "")
            if not meeting_id:
                return {"success": False, "error": "Falta meeting_id"}
            return zoom_manager.get_meeting_details(meeting_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: create_meeting, delete_meeting, list_meetings, get_details"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Zoom: {str(e)}"
        }
