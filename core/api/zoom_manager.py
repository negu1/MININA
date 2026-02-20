"""
MININA v3.0 - Zoom Manager
API para operaciones con Zoom (reuniones, webinars, usuarios)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class ZoomManager:
    """
    Manager de Zoom para MININA
    
    Requiere:
    - Account ID (para OAuth Server-to-Server)
    - Client ID
    - Client Secret
    
    Para obtener:
    1. Ve a https://marketplace.zoom.us/
    2. Crea una app "Server-to-Server OAuth"
    3. Copia Account ID, Client ID y Client Secret
    """
    
    API_BASE_URL = "https://api.zoom.us/v2"
    TOKEN_URL = "https://zoom.us/oauth/token"
    
    def __init__(self, config_path: str = "data/zoom_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.account_id: Optional[str] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.access_token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.account_id = data.get("account_id")
                    self.client_id = data.get("client_id")
                    self.client_secret = data.get("client_secret")
                    self.access_token = data.get("access_token")
            except Exception as e:
                print(f"Error cargando configuración Zoom: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "account_id": self.account_id,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "access_token": self.access_token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Zoom: {e}")
    
    def _get_access_token(self) -> Optional[str]:
        """Obtener access token usando Server-to-Server OAuth"""
        if not all([self.account_id, self.client_id, self.client_secret]):
            return None
        
        try:
            import base64
            credentials = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "account_credentials",
                "account_id": self.account_id
            }
            
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                self._save_config()
                return self.access_token
            else:
                print(f"Error obteniendo token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error en autenticación Zoom: {e}")
            return None
    
    def set_credentials(
        self,
        account_id: str,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """Configurar credenciales de Zoom"""
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._save_config()
        
        # Probar autenticación
        token = self._get_access_token()
        
        if token:
            return {
                "success": True,
                "message": "Credenciales de Zoom configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo autenticar con Zoom. Verifica las credenciales."
            }
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        if not self.access_token:
            self._get_access_token()
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.account_id and self.client_id and self.client_secret)
    
    def create_meeting(
        self,
        topic: str,
        start_time: str,
        duration: int = 60,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """Crear una reunión de Zoom"""
        if not self.is_configured():
            return {"success": False, "error": "Zoom no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/users/me/meetings"
            
            data = {
                "topic": topic,
                "type": 2,  # Scheduled meeting
                "start_time": start_time,
                "duration": duration,
                "timezone": timezone,
                "settings": {
                    "host_video": True,
                    "participant_video": True,
                    "join_before_host": False,
                    "mute_upon_entry": True,
                    "waiting_room": True
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "meeting_id": result.get("id"),
                    "topic": result.get("topic"),
                    "start_url": result.get("start_url"),
                    "join_url": result.get("join_url"),
                    "password": result.get("password"),
                    "created_at": result.get("created_at")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Eliminar una reunión"""
        if not self.is_configured():
            return {"success": False, "error": "Zoom no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/meetings/{meeting_id}"
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"Reunión {meeting_id} eliminada"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_meetings(self, type: str = "scheduled") -> Dict[str, Any]:
        """Listar reuniones del usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Zoom no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/users/me/meetings"
            params = {"type": type}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                meetings = result.get("meetings", [])
                return {
                    "success": True,
                    "meetings": [
                        {
                            "id": m["id"],
                            "topic": m["topic"],
                            "start_time": m.get("start_time"),
                            "duration": m.get("duration"),
                            "join_url": m.get("join_url")
                        }
                        for m in meetings
                    ],
                    "total": result.get("total_records", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_meeting_details(self, meeting_id: str) -> Dict[str, Any]:
        """Obtener detalles de una reunión"""
        if not self.is_configured():
            return {"success": False, "error": "Zoom no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/meetings/{meeting_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "meeting_id": result.get("id"),
                    "topic": result.get("topic"),
                    "status": result.get("status"),
                    "start_time": result.get("start_time"),
                    "duration": result.get("duration"),
                    "join_url": result.get("join_url"),
                    "start_url": result.get("start_url"),
                    "password": result.get("password"),
                    "participants_count": result.get("participants_count", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "account_id": "***" if self.account_id else None,
            "client_id": "***" if self.client_id else None
        }


# Singleton
zoom_manager = ZoomManager()
