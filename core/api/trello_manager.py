"""
MININA v3.0 - Trello Manager
API para operaciones con Trello (boards, lists, cards)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class TrelloCard:
    """Card de Trello"""
    id: str
    name: str
    desc: str
    url: str
    due: Optional[str]
    labels: List[str]


class TrelloManager:
    """
    Manager de Trello para MININA
    
    Requiere:
    - API Key
    - Token (obtenido al autorizar la aplicación)
    
    Para obtener:
    1. Ve a https://trello.com/app-key
    2. Copia tu API Key
    3. Genera un Token usando el link proporcionado
    """
    
    API_BASE_URL = "https://api.trello.com/1"
    
    def __init__(self, config_path: str = "data/trello_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_key: Optional[str] = None
        self.token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
                    self.token = data.get("token")
            except Exception as e:
                print(f"Error cargando configuración Trello: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "api_key": self.api_key,
                "token": self.token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Trello: {e}")
    
    def set_credentials(self, api_key: str, token: str) -> Dict[str, Any]:
        """Configurar credenciales de Trello"""
        self.api_key = api_key
        self.token = token
        self._save_config()
        
        # Verificar que funcionan
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Credenciales de Trello configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar las credenciales. Verifica API Key y Token."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.api_key or not self.token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}/members/me"
            params = {"key": self.api_key, "token": self.token}
            response = requests.get(url, params=params, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.api_key and self.token)
    
    def _get_auth_params(self) -> Dict[str, str]:
        """Obtener parámetros de autenticación"""
        return {
            "key": self.api_key,
            "token": self.token
        }
    
    def list_boards(self) -> Dict[str, Any]:
        """Listar boards del usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/members/me/boards"
            params = self._get_auth_params()
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                boards = response.json()
                return {
                    "success": True,
                    "boards": [
                        {
                            "id": b["id"],
                            "name": b["name"],
                            "url": b.get("url", ""),
                            "desc": b.get("desc", "")
                        }
                        for b in boards
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_board_lists(self, board_id: str) -> Dict[str, Any]:
        """Obtener listas de un board"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/boards/{board_id}/lists"
            params = self._get_auth_params()
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                lists = response.json()
                return {
                    "success": True,
                    "lists": [
                        {
                            "id": l["id"],
                            "name": l["name"],
                            "pos": l.get("pos", 0)
                        }
                        for l in lists
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_list_cards(self, list_id: str) -> Dict[str, Any]:
        """Obtener cards de una lista"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/lists/{list_id}/cards"
            params = self._get_auth_params()
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                cards = response.json()
                return {
                    "success": True,
                    "cards": [
                        {
                            "id": c["id"],
                            "name": c["name"],
                            "desc": c.get("desc", ""),
                            "url": c.get("url", ""),
                            "due": c.get("due"),
                            "labels": [l["name"] for l in c.get("labels", [])]
                        }
                        for c in cards
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str = "",
        due: Optional[str] = None,
        labels: List[str] = None
    ) -> Dict[str, Any]:
        """Crear card en una lista"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/cards"
            params = self._get_auth_params()
            params.update({
                "idList": list_id,
                "name": name,
                "desc": desc
            })
            
            if due:
                params["due"] = due
            
            response = requests.post(url, params=params, timeout=30)
            
            if response.status_code == 200:
                card = response.json()
                return {
                    "success": True,
                    "card_id": card["id"],
                    "name": card["name"],
                    "url": card.get("url", "")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_board(
        self,
        name: str,
        desc: str = "",
        default_lists: bool = True
    ) -> Dict[str, Any]:
        """Crear nuevo board"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/boards"
            params = self._get_auth_params()
            params.update({
                "name": name,
                "desc": desc,
                "defaultLists": str(default_lists).lower()
            })
            
            response = requests.post(url, params=params, timeout=30)
            
            if response.status_code == 200:
                board = response.json()
                return {
                    "success": True,
                    "board_id": board["id"],
                    "name": board["name"],
                    "url": board.get("url", "")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def move_card(self, card_id: str, list_id: str) -> Dict[str, Any]:
        """Mover card a otra lista"""
        if not self.is_configured():
            return {"success": False, "error": "Trello no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/cards/{card_id}"
            params = self._get_auth_params()
            params["idList"] = list_id
            
            response = requests.put(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Card movida a lista {list_id}"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "api_key": "***" if self.api_key else None,
            "token": "***" if self.token else None
        }


# Singleton
trello_manager = TrelloManager()
