"""
MININA v3.0 - Notion Manager
API para operaciones con Notion (páginas, bases de datos, blocks)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class NotionPage:
    """Página de Notion"""
    id: str
    title: str
    url: str
    created_time: str
    last_edited_time: str


class NotionManager:
    """
    Manager de Notion para MININA
    
    Requiere:
    - Internal Integration Token
    
    Para obtener:
    1. Ve a https://www.notion.so/my-integrations
    2. Crea una nueva integración
    3. Copia el "Internal Integration Token"
    4. Comparte las páginas/bases de datos con la integración
    """
    
    API_BASE_URL = "https://api.notion.com/v1"
    API_VERSION = "2022-06-28"
    
    def __init__(self, config_path: str = "data/notion_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.token = data.get("token")
            except Exception as e:
                print(f"Error cargando configuración Notion: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "token": self.token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Notion: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Notion"""
        self.token = token
        self._save_config()
        
        # Verificar que funciona
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Notion configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea válido y tenga permisos."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.token:
            return False
        
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.API_BASE_URL}/users/me", headers=headers, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.token)
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.API_VERSION,
            "Content-Type": "application/json"
        }
    
    def search_pages(self, query: str = "") -> Dict[str, Any]:
        """Buscar páginas y bases de datos"""
        if not self.is_configured():
            return {"success": False, "error": "Notion no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/search"
            data = {"query": query} if query else {}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                pages = []
                databases = []
                
                for item in results:
                    item_type = item.get("object")
                    if item_type == "page":
                        title = self._extract_title(item)
                        pages.append({
                            "id": item["id"],
                            "title": title,
                            "url": item.get("url", ""),
                            "created_time": item.get("created_time", "")
                        })
                    elif item_type == "database":
                        title = self._extract_title(item)
                        databases.append({
                            "id": item["id"],
                            "title": title,
                            "url": item.get("url", "")
                        })
                
                return {
                    "success": True,
                    "pages": pages,
                    "databases": databases,
                    "total": len(results)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def _extract_title(self, item: dict) -> str:
        """Extraer título de un item de Notion"""
        try:
            properties = item.get("properties", {})
            title_prop = properties.get("title", {})
            
            if title_prop.get("title"):
                title_parts = [t.get("text", {}).get("content", "") for t in title_prop["title"]]
                return "".join(title_parts)
            
            # Para bases de datos
            if item.get("title"):
                title_parts = [t.get("text", {}).get("content", "") for t in item["title"]]
                return "".join(title_parts)
            
            return "Sin título"
        except:
            return "Sin título"
    
    def create_page(
        self,
        parent_id: str,
        title: str,
        content: str = ""
    ) -> Dict[str, Any]:
        """Crear nueva página"""
        if not self.is_configured():
            return {"success": False, "error": "Notion no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/pages"
            
            data = {
                "parent": {"page_id": parent_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                }
            }
            
            if content:
                data["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ]
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                page = response.json()
                return {
                    "success": True,
                    "page_id": page["id"],
                    "title": title,
                    "url": page.get("url", "")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def add_content_to_page(
        self,
        page_id: str,
        content: str,
        block_type: str = "paragraph"
    ) -> Dict[str, Any]:
        """Agregar contenido a una página"""
        if not self.is_configured():
            return {"success": False, "error": "Notion no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/blocks/{page_id}/children"
            
            data = {
                "children": [
                    {
                        "object": "block",
                        "type": block_type,
                        block_type: {
                            "rich_text": [{"type": "text", "text": {"content": content}}]
                        }
                    }
                ]
            }
            
            response = requests.patch(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Contenido agregado a la página {page_id}"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def query_database(
        self,
        database_id: str,
        filter_params: dict = None
    ) -> Dict[str, Any]:
        """Consultar base de datos"""
        if not self.is_configured():
            return {"success": False, "error": "Notion no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/databases/{database_id}/query"
            
            data = {}
            if filter_params:
                data["filter"] = filter_params
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                return {
                    "success": True,
                    "results": results,
                    "count": len(results)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.token else None
        }


# Singleton
notion_manager = NotionManager()
