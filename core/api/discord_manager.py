"""
MININA v3.0 - Discord Manager
API para operaciones con Discord (mensajes, canales, usuarios)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class DiscordManager:
    """
    Manager de Discord para MININA
    
    Requiere:
    - Bot Token (de Discord Developer Portal)
    
    Para obtener:
    1. Ve a https://discord.com/developers/applications
    2. Crea una nueva aplicación
    3. Ve a "Bot" y copia el Token
    4. Invita el bot a tu servidor con permisos de bot
    """
    
    API_BASE_URL = "https://discord.com/api/v10"
    
    def __init__(self, config_path: str = "data/discord_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.bot_token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bot_token = data.get("bot_token")
            except Exception as e:
                print(f"Error cargando configuración Discord: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "bot_token": self.bot_token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Discord: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Discord"""
        self.bot_token = token
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Discord configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea un Bot Token válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.bot_token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}/users/@me"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.bot_token)
    
    def send_message(self, channel_id: str, content: str) -> Dict[str, Any]:
        """Enviar mensaje a un canal"""
        if not self.is_configured():
            return {"success": False, "error": "Discord no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/channels/{channel_id}/messages"
            data = {"content": content}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message_id": result.get("id"),
                    "channel_id": result.get("channel_id"),
                    "content": result.get("content"),
                    "timestamp": result.get("timestamp"),
                    "author": result.get("author", {}).get("username")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_channel_messages(self, channel_id: str, limit: int = 50) -> Dict[str, Any]:
        """Obtener mensajes de un canal"""
        if not self.is_configured():
            return {"success": False, "error": "Discord no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/channels/{channel_id}/messages"
            params = {"limit": min(limit, 100)}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "messages": [
                        {
                            "id": m["id"],
                            "content": m["content"],
                            "author": m["author"]["username"],
                            "timestamp": m["timestamp"],
                            "channel_id": m["channel_id"]
                        }
                        for m in result
                    ],
                    "count": len(result)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_guild_channels(self, guild_id: str) -> Dict[str, Any]:
        """Obtener canales de un servidor (guild)"""
        if not self.is_configured():
            return {"success": False, "error": "Discord no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/guilds/{guild_id}/channels"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "channels": [
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "type": c["type"],
                            "topic": c.get("topic"),
                            "nsfw": c.get("nsfw", False),
                            "parent_id": c.get("parent_id")
                        }
                        for c in result
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_dm_channel(self, user_id: str) -> Dict[str, Any]:
        """Crear canal DM (mensaje directo) con un usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Discord no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/users/@me/channels"
            data = {"recipient_id": user_id}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "channel_id": result.get("id"),
                    "type": result.get("type"),
                    "recipient": result.get("recipients", [{}])[0].get("username")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Obtener información de un usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Discord no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/users/{user_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get("id"),
                    "username": result.get("username"),
                    "discriminator": result.get("discriminator"),
                    "avatar": result.get("avatar"),
                    "bot": result.get("bot", False),
                    "created_at": self._get_user_creation_date(result.get("id"))
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def _get_user_creation_date(self, user_id: str) -> Optional[str]:
        """Calcular fecha de creación del usuario desde su ID (snowflake)"""
        try:
            if not user_id:
                return None
            timestamp = ((int(user_id) >> 22) + 1420070400000) / 1000
            return datetime.fromtimestamp(timestamp).isoformat()
        except:
            return None
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.bot_token else None
        }


# Singleton
discord_manager = DiscordManager()
