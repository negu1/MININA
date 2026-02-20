"""
MININA v3.0 - Spotify Manager
API para operaciones con Spotify (reproducción, playlists, búsqueda)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class SpotifyTrack:
    """Track de Spotify"""
    id: str
    name: str
    artist: str
    album: str
    duration_ms: int
    uri: str


class SpotifyManager:
    """
    Manager de Spotify para MININA
    
    Requiere:
    - Access Token (OAuth2)
    
    Para obtener:
    1. Ve a https://developer.spotify.com/dashboard
    2. Crea una app
    3. Obtén Client ID y Client Secret
    4. Autoriza y obtén Access Token
    """
    
    API_BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/api/token"
    
    def __init__(self, config_path: str = "data/spotify_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.client_id = data.get("client_id")
                    self.client_secret = data.get("client_secret")
            except Exception as e:
                print(f"Error cargando configuración Spotify: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Spotify: {e}")
    
    def set_credentials(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configurar credenciales de Spotify"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._save_config()
        
        # Verificar que funcionan
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Credenciales de Spotify configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.access_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.API_BASE_URL}/me",
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.access_token)
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def search(
        self,
        query: str,
        search_type: str = "track",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Buscar canciones, artistas, álbumes o playlists"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/search"
            params = {
                "q": query,
                "type": search_type,
                "limit": limit
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if search_type == "track":
                    tracks = result.get("tracks", {}).get("items", [])
                    return {
                        "success": True,
                        "tracks": [
                            {
                                "id": t["id"],
                                "name": t["name"],
                                "artist": t["artists"][0]["name"] if t["artists"] else "Desconocido",
                                "album": t["album"]["name"],
                                "duration_ms": t["duration_ms"],
                                "uri": t["uri"]
                            }
                            for t in tracks
                        ]
                    }
                else:
                    return {"success": True, "results": result}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def play_track(self, track_uri: str) -> Dict[str, Any]:
        """Reproducir una canción"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/me/player/play"
            data = {"uris": [track_uri]}
            
            response = requests.put(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code in [200, 204]:
                return {"success": True, "message": "Reproduciendo canción"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def pause_playback(self) -> Dict[str, Any]:
        """Pausar reproducción"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/me/player/pause"
            response = requests.put(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code in [200, 204]:
                return {"success": True, "message": "Reproducción pausada"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_current_playback(self) -> Dict[str, Any]:
        """Obtener estado actual de reproducción"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/me/player/currently-playing"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                track = data.get("item", {})
                return {
                    "success": True,
                    "is_playing": data.get("is_playing", False),
                    "track": {
                        "name": track.get("name", ""),
                        "artist": track["artists"][0]["name"] if track.get("artists") else "",
                        "album": track.get("album", {}).get("name", "")
                    } if track else None
                }
            elif response.status_code == 204:
                return {"success": True, "is_playing": False, "track": None}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_user_playlists(self, limit: int = 20) -> Dict[str, Any]:
        """Obtener playlists del usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/me/playlists"
            params = {"limit": limit}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                playlists = result.get("items", [])
                return {
                    "success": True,
                    "playlists": [
                        {
                            "id": p["id"],
                            "name": p["name"],
                            "tracks_count": p["tracks"]["total"],
                            "uri": p["uri"]
                        }
                        for p in playlists
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def play_playlist(self, playlist_uri: str) -> Dict[str, Any]:
        """Reproducir una playlist"""
        if not self.is_configured():
            return {"success": False, "error": "Spotify no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/me/player/play"
            data = {"context_uri": playlist_uri}
            
            response = requests.put(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code in [200, 204]:
                return {"success": True, "message": "Reproduciendo playlist"}
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "client_id": "***" if self.client_id else None,
            "has_access_token": bool(self.access_token)
        }


# Singleton
spotify_manager = SpotifyManager()
