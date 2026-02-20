"""
MININA v3.0 - Notion Skill
Skill para operaciones con Notion
"""

from core.api.notion_manager import notion_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Notion
    
    Args:
        context: {
            "action": str,           # search_pages, create_page, add_content, query_database
            "query": str,            # Búsqueda (para search_pages)
            "parent_id": str,        # ID de página padre (para create_page)
            "title": str,            # Título de página
            "content": str,          # Contenido
            "page_id": str,          # ID de página (para add_content)
            "database_id": str,      # ID de base de datos (para query_database)
            "block_type": str        # Tipo de bloque (paragraph, heading_1, etc.)
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
        
        # Verificar que Notion está configurado
        if not notion_manager.is_configured():
            return {
                "success": False,
                "error": "Notion no configurado. Ve a Configuración → Notion para agregar tu token."
            }
        
        if action == "search_pages":
            query = context.get("query", "")
            return notion_manager.search_pages(query)
        
        elif action == "create_page":
            parent_id = context.get("parent_id", "")
            title = context.get("title", "")
            content = context.get("content", "")
            
            if not parent_id or not title:
                return {"success": False, "error": "Faltan parent_id o title"}
            
            return notion_manager.create_page(parent_id, title, content)
        
        elif action == "add_content":
            page_id = context.get("page_id", "")
            content = context.get("content", "")
            block_type = context.get("block_type", "paragraph")
            
            if not page_id or not content:
                return {"success": False, "error": "Faltan page_id o content"}
            
            return notion_manager.add_content_to_page(page_id, content, block_type)
        
        elif action == "query_database":
            database_id = context.get("database_id", "")
            
            if not database_id:
                return {"success": False, "error": "Falta database_id"}
            
            return notion_manager.query_database(database_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: search_pages, create_page, add_content, query_database"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Notion: {str(e)}"
        }
