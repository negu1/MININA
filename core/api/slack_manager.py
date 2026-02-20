"""
MININA v3.0 - Slack Manager
API para operaciones con Slack (mensajes, canales, usuarios)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class SlackMessage:
    """Mensaje de Slack"""
    ts: str
    text: str
    user: str
    channel: str
    thread_ts: Optional[str] = None


class SlackManager:
    """
    Manager de Slack para MININA
    
    Requiere:
    - Bot User OAuth Token (xoxb-...)
    
    Para obtener:
    1. Ve a https://api.slack.com/apps
    2. Crea una nueva app o usa una existente
    3. Ve a "OAuth & Permissions"
    4. Copia el "Bot User OAuth Token"
    5. Invita el bot a los canales con /invite @nombre_bot
    """
    
    API_BASE_URL = "https://slack.com/api"
    
    def __init__(self, config_path: str = "data/slack_config.json"):
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
                print(f"Error cargando configuración Slack: {e}")
    
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
            print(f"Error guardando configuración Slack: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Slack"""
        self.bot_token = token
        self._save_config()
        
        # Verificar que funciona
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Slack configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea un Bot User OAuth Token válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.bot_token:
            return False
        
        try:
            result = self._api_call("auth.test")
            return result.get("ok", False)
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.bot_token)
    
    def _api_call(self, method: str, params: dict = None) -> Dict[str, Any]:
        """Hacer llamada a la API de Slack"""
        if not self.bot_token:
            return {"ok": False, "error": "Not configured"}
        
        url = f"{self.API_BASE_URL}/{method}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        try:
            response = requests.post(url, headers=headers, json=params or {}, timeout=30)
            return response.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def list_channels(self, types: str = "public_channel,private_channel") -> Dict[str, Any]:
        """Listar canales del workspace"""
        if not self.is_configured():
            return {"success": False, "error": "Slack no configurado"}
        
        try:
            result = self._api_call("conversations.list", {"types": types})
            
            if result.get("ok"):
                channels = result.get("channels", [])
                return {
                    "success": True,
                    "channels": [
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "is_private": c.get("is_private", False),
                            "num_members": c.get("num_members", 0)
                        }
                        for c in channels
                    ]
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enviar mensaje a un canal"""
        if not self.is_configured():
            return {"success": False, "error": "Slack no configurado"}
        
        try:
            params = {
                "channel": channel,
                "text": text
            }
            if thread_ts:
                params["thread_ts"] = thread_ts
            
            result = self._api_call("chat.postMessage", params)
            
            if result.get("ok"):
                return {
                    "success": True,
                    "ts": result.get("ts"),
                    "channel": result.get("channel"),
                    "message": f"Mensaje enviado a #{channel}"
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_channel_history(
        self,
        channel: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Obtener historial de un canal"""
        if not self.is_configured():
            return {"success": False, "error": "Slack no configurado"}
        
        try:
            result = self._api_call("conversations.history", {
                "channel": channel,
                "limit": limit
            })
            
            if result.get("ok"):
                messages = result.get("messages", [])
                return {
                    "success": True,
                    "messages": [
                        {
                            "ts": m.get("ts"),
                            "text": m.get("text", ""),
                            "user": m.get("user", "bot"),
                            "type": m.get("type", "message")
                        }
                        for m in messages if m.get("type") == "message"
                    ],
                    "count": len(messages)
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def upload_file(
        self,
        channel: str,
        file_path: str,
        title: str = "",
        initial_comment: str = ""
    ) -> Dict[str, Any]:
        """Subir archivo a un canal"""
        if not self.is_configured():
            return {"success": False, "error": "Slack no configurado"}
        
        try:
            from pathlib import Path
            file = Path(file_path)
            
            if not file.exists():
                return {"success": False, "error": f"Archivo no encontrado: {file_path}"}
            
            # Para upload de archivos, necesitamos multipart/form-data
            url = f"{self.API_BASE_URL}/files.upload"
            
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'channels': channel,
                    'title': title or file.name,
                    'initial_comment': initial_comment
                }
                
                headers = {"Authorization": f"Bearer {self.bot_token}"}
                response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
                result = response.json()
            
            if result.get("ok"):
                return {
                    "success": True,
                    "file_id": result.get("file", {}).get("id"),
                    "permalink": result.get("file", {}).get("permalink"),
                    "message": f"Archivo subido a #{channel}"
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Obtener información de un usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Slack no configurado"}
        
        try:
            result = self._api_call("users.info", {"user": user_id})
            
            if result.get("ok"):
                user = result.get("user", {})
                return {
                    "success": True,
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": user.get("real_name"),
                    "email": user.get("profile", {}).get("email"),
                    "is_bot": user.get("is_bot", False)
                }
            else:
                return {"success": False, "error": result.get("error", "Unknown error")}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.bot_token else None
        }


# Singleton
slack_manager = SlackManager()
