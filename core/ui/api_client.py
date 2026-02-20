"""
MININA v3.0 - API Client
Cliente para conectar UI Local con backend FastAPI
"""

import requests
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


class MININAApiClient:
    """
    Cliente API para comunicación UI-Backend
    Conecta con el servidor FastAPI existente
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8897"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """Verificar si el servidor está activo"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def get_skills(self) -> List[Dict[str, Any]]:
        """Obtener lista de skills del usuario"""
        try:
            response = self.session.get(f"{self.base_url}/api/skills/list")
            if response.status_code == 200:
                data = response.json()
                return data.get("skills", [])
            return []
        except Exception as e:
            print(f"Error obteniendo skills: {e}")
            return []
            
    def save_skill(self, name: str, code: str, skill_id: Optional[str] = None) -> bool:
        """Guardar una skill"""
        try:
            payload = {
                "name": name,
                "code": code,
                "description": ""
            }
            if skill_id:
                payload["id"] = skill_id
                
            response = self.session.post(
                f"{self.base_url}/api/skills/save",
                json=payload
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error guardando skill: {e}")
            return False
            
    def execute_skill(self, skill_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar una skill"""
        try:
            payload = {
                "skill_name": skill_name,
                "context": context
            }
            response = self.session.post(
                f"{self.base_url}/api/skills/execute",
                json=payload
            )
            return response.json() if response.status_code == 200 else {"success": False, "error": "Execution failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    def get_works(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener lista de works/archivos"""
        try:
            url = f"{self.base_url}/api/works/list"
            if category:
                url += f"?category={category}"
                
            response = self.session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("works", [])
            return []
        except Exception as e:
            print(f"Error obteniendo works: {e}")
            return []
            
    def download_work(self, work_id: str, destination: Path) -> bool:
        """Descargar un work"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/works/{work_id}/download",
                stream=True
            )
            if response.status_code == 200:
                with open(destination, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            return False
        except Exception as e:
            print(f"Error descargando work: {e}")
            return False
            
    def delete_work(self, work_id: str) -> bool:
        """Eliminar un work"""
        try:
            response = self.session.delete(f"{self.base_url}/api/works/{work_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error eliminando work: {e}")
            return False
            
    def get_system_status(self) -> Dict[str, Any]:
        """Obtener estado del sistema"""
        try:
            response = self.session.get(f"{self.base_url}/api/system/status")
            return response.json() if response.status_code == 200 else {}
        except:
            return {}


# Instancia global del cliente
api_client = MININAApiClient()
