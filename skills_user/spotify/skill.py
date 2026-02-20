"""
MININA v3.0 - Spotify Skill
Skill para operaciones con Spotify
"""

from core.api.spotify_manager import spotify_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Spotify
    
    Args:
        context: {
            "action": str,           # search, play_track, pause, get_playback, get_playlists, play_playlist
            "query": str,          # Búsqueda
            "search_type": str,    # track, artist, album, playlist
            "track_uri": str,      # URI de canción (para play_track)
            "playlist_uri": str    # URI de playlist (para play_playlist)
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
        
        # Verificar que Spotify está configurado
        if not spotify_manager.is_configured():
            return {
                "success": False,
                "error": "Spotify no configurado. Ve a Configuración → Spotify para agregar tus credenciales."
            }
        
        if action == "search":
            query = context.get("query", "")
            search_type = context.get("search_type", "track")
            limit = context.get("limit", 10)
            
            if not query:
                return {"success": False, "error": "Falta query"}
            
            return spotify_manager.search(query, search_type, limit)
        
        elif action == "play_track":
            track_uri = context.get("track_uri", "")
            if not track_uri:
                return {"success": False, "error": "Falta track_uri"}
            return spotify_manager.play_track(track_uri)
        
        elif action == "pause":
            return spotify_manager.pause_playback()
        
        elif action == "get_playback":
            return spotify_manager.get_current_playback()
        
        elif action == "get_playlists":
            limit = context.get("limit", 20)
            return spotify_manager.get_user_playlists(limit)
        
        elif action == "play_playlist":
            playlist_uri = context.get("playlist_uri", "")
            if not playlist_uri:
                return {"success": False, "error": "Falta playlist_uri"}
            return spotify_manager.play_playlist(playlist_uri)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: search, play_track, pause, get_playback, get_playlists, play_playlist"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Spotify: {str(e)}"
        }
