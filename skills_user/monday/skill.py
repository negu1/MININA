"""
MININA v3.0 - Monday.com Skill
Skill para operaciones con Monday.com
"""

from core.api.monday_manager import monday_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Monday.com
    
    Args:
        context: {
            "action": str,           # list_boards, get_items, create_item, update_item, delete_item
            "board_id": str,       # ID del board (para items)
            "item_id": str,        # ID del item (para update/delete)
            "item_name": str,      # Nombre del item (para create)
            "column_values": dict, # Valores de columnas (para create/update)
            "limit": int           # Límite de resultados
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
        
        # Verificar que Monday.com está configurado
        if not monday_manager.is_configured():
            return {
                "success": False,
                "error": "Monday.com no configurado. Ve a Configuración → Monday.com para agregar tu API Token."
            }
        
        if action == "list_boards":
            limit = context.get("limit", 25)
            return monday_manager.list_boards(limit)
        
        elif action == "get_items":
            board_id = context.get("board_id", "")
            limit = context.get("limit", 25)
            
            if not board_id:
                return {"success": False, "error": "Falta board_id"}
            
            return monday_manager.get_board_items(board_id, limit)
        
        elif action == "create_item":
            board_id = context.get("board_id", "")
            item_name = context.get("item_name", "")
            column_values = context.get("column_values", {})
            
            if not board_id:
                return {"success": False, "error": "Falta board_id"}
            if not item_name:
                return {"success": False, "error": "Falta item_name"}
            
            return monday_manager.create_item(board_id, item_name, column_values)
        
        elif action == "update_item":
            item_id = context.get("item_id", "")
            column_values = context.get("column_values", {})
            
            if not item_id:
                return {"success": False, "error": "Falta item_id"}
            if not column_values:
                return {"success": False, "error": "Falta column_values"}
            
            return monday_manager.update_item(item_id, column_values)
        
        elif action == "delete_item":
            item_id = context.get("item_id", "")
            
            if not item_id:
                return {"success": False, "error": "Falta item_id"}
            
            return monday_manager.delete_item(item_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_boards, get_items, create_item, update_item, delete_item"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Monday.com: {str(e)}"
        }
