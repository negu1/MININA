"""
MININA v3.0 - Twitter/X Skill
Skill para operaciones con Twitter/X
"""

from core.api.twitter_manager import twitter_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Twitter/X
    
    Args:
        context: {
            "action": str,           # search_tweets, post_tweet, get_timeline, delete_tweet
            "query": str,          # Búsqueda (para search_tweets)
            "text": str,           # Texto del tweet (para post_tweet)
            "user_id": str,        # ID de usuario (para timeline)
            "username": str,       # Username (para timeline)
            "tweet_id": str,       # ID del tweet (para delete)
            "max_results": int     # Máximo de resultados
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
        
        # Verificar que Twitter está configurado
        if not twitter_manager.is_configured():
            return {
                "success": False,
                "error": "Twitter no configurado. Ve a Configuración → Twitter/X para agregar tu Bearer Token."
            }
        
        if action == "search_tweets":
            query = context.get("query", "")
            max_results = context.get("max_results", 10)
            
            if not query:
                return {"success": False, "error": "Falta query"}
            
            return twitter_manager.search_tweets(query, max_results)
        
        elif action == "post_tweet":
            text = context.get("text", "")
            
            if not text:
                return {"success": False, "error": "Falta text"}
            
            if len(text) > 280:
                return {"success": False, "error": "El tweet excede 280 caracteres"}
            
            return twitter_manager.post_tweet(text)
        
        elif action == "get_timeline":
            user_id = context.get("user_id")
            username = context.get("username")
            max_results = context.get("max_results", 10)
            
            return twitter_manager.get_user_timeline(user_id, username, max_results)
        
        elif action == "delete_tweet":
            tweet_id = context.get("tweet_id", "")
            
            if not tweet_id:
                return {"success": False, "error": "Falta tweet_id"}
            
            return twitter_manager.delete_tweet(tweet_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: search_tweets, post_tweet, get_timeline, delete_tweet"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Twitter: {str(e)}"
        }
