"""
MININA v3.0 - Discord Skill
Skill para operaciones con Discord
"""

from core.api.discord_manager import discord_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Discord
    
    Args:
        context: {
            "action": str,           # send_message, get_messages, get_channels, create_dm, get_user
            "channel_id": str,     # ID del canal (para send/get_messages)
            "content": str,        # Contenido del mensaje
            "guild_id": str,       # ID del servidor (para get_channels)
            "user_id": str,        # ID del usuario (para create_dm, get_user)
            "limit": int           # Límite de mensajes (default 50)
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
        
        # Verificar que Discord está configurado
        if not discord_manager.is_configured():
            return {
                "success": False,
                "error": "Discord no configurado. Ve a Configuración → Discord para agregar tu Bot Token."
            }
        
        if action == "send_message":
            channel_id = context.get("channel_id", "")
            content = context.get("content", "")
            
            if not channel_id:
                return {"success": False, "error": "Falta channel_id"}
            if not content:
                return {"success": False, "error": "Falta content"}
            
            return discord_manager.send_message(channel_id, content)
        
        elif action == "get_messages":
            channel_id = context.get("channel_id", "")
            limit = context.get("limit", 50)
            
            if not channel_id:
                return {"success": False, "error": "Falta channel_id"}
            
            return discord_manager.get_channel_messages(channel_id, limit)
        
        elif action == "get_channels":
            guild_id = context.get("guild_id", "")
            
            if not guild_id:
                return {"success": False, "error": "Falta guild_id (ID del servidor)"}
            
            return discord_manager.get_guild_channels(guild_id)
        
        elif action == "create_dm":
            user_id = context.get("user_id", "")
            
            if not user_id:
                return {"success": False, "error": "Falta user_id"}
            
            return discord_manager.create_dm_channel(user_id)
        
        elif action == "get_user":
            user_id = context.get("user_id", "")
            
            if not user_id:
                return {"success": False, "error": "Falta user_id"}
            
            return discord_manager.get_user_info(user_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: send_message, get_messages, get_channels, create_dm, get_user"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Discord: {str(e)}"
        }
