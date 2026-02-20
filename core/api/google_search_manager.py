"""
MININA v3.0 - Google Search Manager
API para búsquedas web usando Google Custom Search API
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class SearchResult:
    """Resultado de búsqueda"""
    title: str
    link: str
    snippet: str
    display_url: str


class GoogleSearchManager:
    """
    Manager de búsqueda Google para MININA
    
    Requiere:
    - Google API Key
    - Custom Search Engine ID (cx)
    
    Para obtener:
    1. Ve a https://console.cloud.google.com/
    2. Crea un proyecto y habilita "Custom Search API"
    3. Obtén API Key desde "Credenciales"
    4. Ve a https://programmablesearchengine.google.com/
    5. Crea un motor de búsqueda y copia el ID (cx)
    """
    
    API_BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, config_path: str = "data/google_search_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_key: Optional[str] = None
        self.cx: Optional[str] = None  # Custom Search Engine ID
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
                    self.cx = data.get("cx")
            except Exception as e:
                print(f"Error cargando configuración Google Search: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "api_key": self.api_key,
                "cx": self.cx
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Google Search: {e}")
    
    def set_credentials(self, api_key: str, cx: str) -> Dict[str, Any]:
        """Configurar credenciales de Google Search"""
        self.api_key = api_key
        self.cx = cx
        self._save_config()
        
        # Verificar que funcionan
        test_result = self.search("test", num_results=1)
        
        if test_result.get("success"):
            return {
                "success": True,
                "message": "Credenciales configuradas y verificadas correctamente"
            }
        else:
            return {
                "success": False,
                "error": test_result.get("error", "Error verificando credenciales")
            }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.api_key and self.cx)
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        start: int = 1,
        safe: str = "active"
    ) -> Dict[str, Any]:
        """
        Realizar búsqueda en Google
        
        Args:
            query: Término de búsqueda
            num_results: Número de resultados (max 10)
            start: Índice del primer resultado
            safe: Filtro de contenido seguro (active/off)
        
        Returns:
            {
                "success": bool,
                "query": str,
                "total_results": int,
                "results": List[SearchResult],
                "error": str (si falla)
            }
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Search no configurado. Ve a Configuración para agregar API Key y CX."
            }
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": min(num_results, 10),
                "start": start,
                "safe": safe
            }
            
            response = requests.get(self.API_BASE_URL, params=params, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"Error HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"Error en API de Google: {error_msg}"
                }
            
            data = response.json()
            
            # Extraer información de búsqueda
            search_info = data.get("searchInformation", {})
            total_results = search_info.get("totalResults", "0")
            
            # Extraer resultados
            items = data.get("items", [])
            results = []
            
            for item in items:
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_url": item.get("displayLink", "")
                })
            
            return {
                "success": True,
                "query": query,
                "total_results": int(total_results.replace(",", "")) if total_results else 0,
                "results": results,
                "search_time": search_info.get("searchTime", 0)
            }
            
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout esperando respuesta de Google Search API"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en búsqueda: {str(e)}"
            }
    
    def search_images(
        self,
        query: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """Buscar imágenes"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Search no configurado"
            }
        
        try:
            params = {
                "key": self.api_key,
                "cx": self.cx,
                "q": query,
                "num": min(num_results, 10),
                "searchType": "image"
            }
            
            response = requests.get(self.API_BASE_URL, params=params, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"Error HTTP {response.status_code}")
                return {
                    "success": False,
                    "error": f"Error en API: {error_msg}"
                }
            
            data = response.json()
            items = data.get("items", [])
            
            results = []
            for item in items:
                image_data = item.get("image", {})
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "thumbnail": image_data.get("thumbnailLink", ""),
                    "width": image_data.get("width", 0),
                    "height": image_data.get("height", 0),
                    "context": item.get("image", {}).get("contextLink", "")
                })
            
            return {
                "success": True,
                "query": query,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error buscando imágenes: {str(e)}"
            }
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "api_key": "***" if self.api_key else None,
            "cx": self.cx
        }


# Singleton
google_search_manager = GoogleSearchManager()
