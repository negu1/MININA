"""
MININA v3.0 - Trello Skill
Skill para operaciones con Trello
"""

from core.api.trello_manager import trello_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Trello
    
    Args:
        context: {
            "action": str,           # list_boards, get_board_lists, get_list_cards, create_card, create_board, move_card
            "board_id": str,         # ID del board
            "list_id": str,          # ID de la lista
            "card_id": str,          # ID de la card (para move)
            "name": str,             # Nombre de card/board
            "desc": str,             # Descripción
            "due": str,              # Fecha de vencimiento (ISO format)
            "labels": list           # Lista de labels
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
        
        # Verificar que Trello está configurado
        if not trello_manager.is_configured():
            return {
                "success": False,
                "error": "Trello no configurado. Ve a Configuración → Trello para agregar API Key y Token."
            }
        
        if action == "list_boards":
            return trello_manager.list_boards()
        
        elif action == "get_board_lists":
            board_id = context.get("board_id", "")
            if not board_id:
                return {"success": False, "error": "Falta board_id"}
            return trello_manager.get_board_lists(board_id)
        
        elif action == "get_list_cards":
            list_id = context.get("list_id", "")
            if not list_id:
                return {"success": False, "error": "Falta list_id"}
            return trello_manager.get_list_cards(list_id)
        
        elif action == "create_card":
            list_id = context.get("list_id", "")
            name = context.get("name", "")
            desc = context.get("desc", "")
            due = context.get("due")
            labels = context.get("labels", [])
            
            if not list_id or not name:
                return {"success": False, "error": "Faltan list_id o name"}
            
            return trello_manager.create_card(list_id, name, desc, due, labels)
        
        elif action == "create_board":
            name = context.get("name", "")
            desc = context.get("desc", "")
            default_lists = context.get("default_lists", True)
            
            if not name:
                return {"success": False, "error": "Falta name"}
            
            return trello_manager.create_board(name, desc, default_lists)
        
        elif action == "move_card":
            card_id = context.get("card_id", "")
            list_id = context.get("list_id", "")
            
            if not card_id or not list_id:
                return {"success": False, "error": "Faltan card_id o list_id"}
            
            return trello_manager.move_card(card_id, list_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_boards, get_board_lists, get_list_cards, create_card, create_board, move_card"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Trello: {str(e)}"
        }
