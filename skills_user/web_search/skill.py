"""
MININA v3.0 - Web Search Skill
Skill para realizar búsquedas web usando Google Custom Search API
"""

from core.api.google_search_manager import google_search_manager


def execute(context: dict) -> dict:
    """
    Realizar búsqueda web
    
    Args:
        context: {
            "query": str,              # Término de búsqueda (requerido)
            "num_results": int,        # Número de resultados (default: 10)
            "search_type": str         # "web" o "images" (default: "web")
        }
    
    Returns:
        {
            "success": bool,
            "query": str,
            "total_results": int,
            "results": list,
            "error": str (si falla)
        }
    """
    try:
        # Extraer parámetros
        query = context.get("query", "")
        num_results = context.get("num_results", 10)
        search_type = context.get("search_type", "web")
        
        # Validaciones
        if not query:
            return {
                "success": False,
                "error": "Falta término de búsqueda (parámetro 'query')"
            }
        
        # Verificar que Google Search está configurado
        if not google_search_manager.is_configured():
            return {
                "success": False,
                "error": "Google Search no configurado. Ve a Configuración → Búsqueda Web para agregar API Key y CX."
            }
        
        # Realizar búsqueda
        if search_type == "images":
            result = google_search_manager.search_images(query, num_results=num_results)
        else:
            result = google_search_manager.search(query, num_results=num_results)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de búsqueda: {str(e)}"
        }
