"""
MININA v3.0 - Twitter/X Manager
API para operaciones con Twitter/X (posts, timeline, búsqueda)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class Tweet:
    """Tweet de Twitter/X"""
    id: str
    text: str
    author_id: str
    author_name: str
    created_at: str
    public_metrics: dict


class TwitterManager:
    """
    Manager de Twitter/X para MININA
    
    Requiere:
    - Bearer Token (API v2)
    - Opcional: API Key, API Secret, Access Token, Access Secret (para posting)
    
    Para obtener:
    1. Ve a https://developer.twitter.com/en/portal/dashboard
    2. Crea un proyecto y app
    3. Genera Bearer Token y/o User Authentication tokens
    """
    
    API_BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, config_path: str = "data/twitter_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.bearer_token: Optional[str] = None
        self.api_key: Optional[str] = None
        self.api_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self.access_secret: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bearer_token = data.get("bearer_token")
                    self.api_key = data.get("api_key")
                    self.api_secret = data.get("api_secret")
                    self.access_token = data.get("access_token")
                    self.access_secret = data.get("access_secret")
            except Exception as e:
                print(f"Error cargando configuración Twitter: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "bearer_token": self.bearer_token,
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "access_token": self.access_token,
                "access_secret": self.access_secret
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Twitter: {e}")
    
    def set_bearer_token(self, token: str) -> Dict[str, Any]:
        """Configurar Bearer Token para lectura"""
        self.bearer_token = token
        self._save_config()
        
        # Verificar que funciona
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Bearer Token configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea válido."
            }
    
    def set_user_credentials(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str
    ) -> Dict[str, Any]:
        """Configurar credenciales de usuario para posting"""
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self._save_config()
        
        return {
            "success": True,
            "message": "Credenciales de usuario configuradas"
        }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.bearer_token:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            response = requests.get(
                f"{self.API_BASE_URL}/users/me",
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self, for_posting: bool = False) -> bool:
        """Verificar si está configurado"""
        if for_posting:
            return bool(
                self.api_key and self.api_secret and 
                self.access_token and self.access_secret
            )
        return bool(self.bearer_token)
    
    def _get_headers(self, user_auth: bool = False) -> Dict[str, str]:
        """Obtener headers para requests"""
        if user_auth and self.access_token:
            # Para operaciones de usuario (posting)
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        # Para lectura
        return {"Authorization": f"Bearer {self.bearer_token}"}
    
    def search_tweets(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Buscar tweets"""
        if not self.is_configured():
            return {"success": False, "error": "Twitter no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/tweets/search/recent"
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics,author_id"
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tweets = result.get("data", [])
                
                # Obtener info de autores
                users = {u["id"]: u for u in result.get("includes", {}).get("users", [])}
                
                return {
                    "success": True,
                    "tweets": [
                        {
                            "id": t["id"],
                            "text": t["text"],
                            "author_id": t["author_id"],
                            "author_name": users.get(t["author_id"], {}).get("username", "Unknown"),
                            "created_at": t.get("created_at", ""),
                            "metrics": t.get("public_metrics", {})
                        }
                        for t in tweets
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def post_tweet(self, text: str) -> Dict[str, Any]:
        """Publicar tweet"""
        if not self.is_configured(for_posting=True):
            return {"success": False, "error": "Twitter no configurado para posting"}
        
        try:
            url = f"{self.API_BASE_URL}/tweets"
            headers = self._get_headers(user_auth=True)
            data = {"text": text}
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                tweet = result.get("data", {})
                return {
                    "success": True,
                    "tweet_id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "url": f"https://twitter.com/i/web/status/{tweet.get('id')}"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_user_timeline(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """Obtener timeline de un usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Twitter no configurado"}
        
        try:
            # Si no se proporciona user_id, usar el usuario autenticado
            if not user_id:
                if not username:
                    # Timeline del usuario autenticado
                    url = f"{self.API_BASE_URL}/users/me/tweets"
                else:
                    # Buscar usuario por username
                    user_url = f"{self.API_BASE_URL}/users/by/username/{username}"
                    user_response = requests.get(user_url, headers=self._get_headers(), timeout=30)
                    if user_response.status_code == 200:
                        user_id = user_response.json().get("data", {}).get("id")
                        url = f"{self.API_BASE_URL}/users/{user_id}/tweets"
                    else:
                        return {"success": False, "error": "Usuario no encontrado"}
            else:
                url = f"{self.API_BASE_URL}/users/{user_id}/tweets"
            
            params = {
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,public_metrics"
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tweets = result.get("data", [])
                return {
                    "success": True,
                    "tweets": [
                        {
                            "id": t["id"],
                            "text": t["text"],
                            "created_at": t.get("created_at", ""),
                            "metrics": t.get("public_metrics", {})
                        }
                        for t in tweets
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Eliminar tweet"""
        if not self.is_configured(for_posting=True):
            return {"success": False, "error": "Twitter no configurado para posting"}
        
        try:
            url = f"{self.API_BASE_URL}/tweets/{tweet_id}"
            headers = self._get_headers(user_auth=True)
            
            response = requests.delete(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Tweet {tweet_id} eliminado"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "configured_for_posting": self.is_configured(for_posting=True),
            "has_bearer_token": bool(self.bearer_token),
            "has_user_credentials": bool(self.api_key and self.access_token)
        }


# Singleton
twitter_manager = TwitterManager()
