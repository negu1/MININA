"""
MININA v3.0 - Slack Skill
Skill para operaciones con Slack
"""

from core.api.slack_manager import slack_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Slack
    
    Args:
        context: {
            "action": str,           # list_channels, post_message, get_history, upload_file
            "channel": str,        # ID o nombre del canal
            "text": str,           # Texto del mensaje
            "thread_ts": str,      # Thread timestamp (opcional)
            "file_path": str,      # Ruta del archivo (para upload)
            "title": str,          # Título del archivo
            "initial_comment": str # Comentario inicial (para upload)
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
        
        # Verificar que Slack está configurado
        if not slack_manager.is_configured():
            return {
                "success": False,
                "error": "Slack no configurado. Ve a Configuración → Slack para agregar tu Bot Token."
            }
        
        if action == "list_channels":
            types = context.get("types", "public_channel,private_channel")
            return slack_manager.list_channels(types)
        
        elif action == "post_message":
            channel = context.get("channel", "")
            text = context.get("text", "")
            thread_ts = context.get("thread_ts")
            
            if not channel or not text:
                return {"success": False, "error": "Faltan channel o text"}
            
            return slack_manager.post_message(channel, text, thread_ts)
        
        elif action == "get_history":
            channel = context.get("channel", "")
            limit = context.get("limit", 100)
            
            if not channel:
                return {"success": False, "error": "Falta channel"}
            
            return slack_manager.get_channel_history(channel, limit)
        
        elif action == "upload_file":
            channel = context.get("channel", "")
            file_path = context.get("file_path", "")
            title = context.get("title", "")
            initial_comment = context.get("initial_comment", "")
            
            if not channel or not file_path:
                return {"success": False, "error": "Faltan channel o file_path"}
            
            return slack_manager.upload_file(channel, file_path, title, initial_comment)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_channels, post_message, get_history, upload_file"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Slack: {str(e)}"
        }
