"""
MININA v3.0 - Dropbox Manager
API para operaciones con Dropbox (archivos, carpetas, compartir)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class DropboxFile:
    """Archivo en Dropbox"""
    id: str
    name: str
    path: str
    size: int
    modified: str
    is_folder: bool
    shared_link: Optional[str] = None


class DropboxManager:
    """
    Manager de Dropbox para MININA
    
    Requiere:
    - Access Token (OAuth2)
    
    Para obtener:
    1. Ve a https://www.dropbox.com/developers/apps
    2. Crea una nueva app
    3. Genera Access Token
    """
    
    API_BASE_URL = "https://api.dropboxapi.com/2"
    CONTENT_URL = "https://content.dropboxapi.com/2"
    
    def __init__(self, config_path: str = "data/dropbox_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.access_token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
            except Exception as e:
                print(f"Error cargando configuración Dropbox: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "access_token": self.access_token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Dropbox: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Dropbox"""
        self.access_token = token
        self._save_config()
        
        # Verificar que funciona
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Dropbox configurado y verificado"
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
            headers = self._get_headers()
            response = requests.post(
                f"{self.API_BASE_URL}/users/get_current_account",
                headers=headers,
                timeout=30
            )
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.access_token)
    
    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Obtener headers para requests"""
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers
    
    def list_files(
        self,
        path: str = "",
        recursive: bool = False
    ) -> Dict[str, Any]:
        """Listar archivos en una carpeta"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/files/list_folder"
            data = {
                "path": path,
                "recursive": recursive
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                entries = result.get("entries", [])
                
                files = []
                for entry in entries:
                    files.append({
                        "id": entry.get("id", ""),
                        "name": entry.get("name", ""),
                        "path": entry.get("path_display", ""),
                        "size": entry.get("size", 0) if entry.get(".tag") == "file" else 0,
                        "modified": entry.get("server_modified", ""),
                        "is_folder": entry.get(".tag") == "folder"
                    })
                
                return {
                    "success": True,
                    "path": path or "root",
                    "files": files,
                    "count": len(files)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def upload_file(
        self,
        local_path: str,
        dropbox_path: str
    ) -> Dict[str, Any]:
        """Subir archivo a Dropbox"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            from pathlib import Path
            file_path = Path(local_path)
            
            if not file_path.exists():
                return {"success": False, "error": f"Archivo no encontrado: {local_path}"}
            
            # Leer archivo
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Subir
            url = f"{self.CONTENT_URL}/files/upload"
            headers = self._get_headers(content_type="application/octet-stream")
            headers["Dropbox-API-Arg"] = json.dumps({
                "path": dropbox_path,
                "mode": "add",
                "autorename": True
            })
            
            response = requests.post(url, headers=headers, data=file_data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "file_id": result.get("id", ""),
                    "name": result.get("name", ""),
                    "path": result.get("path_display", ""),
                    "size": result.get("size", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def download_file(
        self,
        dropbox_path: str,
        local_path: str
    ) -> Dict[str, Any]:
        """Descargar archivo de Dropbox"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            url = f"{self.CONTENT_URL}/files/download"
            headers = self._get_headers(content_type=None)
            headers["Dropbox-API-Arg"] = json.dumps({"path": dropbox_path})
            
            response = requests.post(url, headers=headers, timeout=60)
            
            if response.status_code == 200:
                # Guardar archivo
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "path": dropbox_path,
                    "local_path": local_path,
                    "size": len(response.content)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_folder(self, path: str) -> Dict[str, Any]:
        """Crear carpeta en Dropbox"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/files/create_folder_v2"
            data = {"path": path, "autorename": False}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                metadata = result.get("metadata", {})
                return {
                    "success": True,
                    "id": metadata.get("id", ""),
                    "name": metadata.get("name", ""),
                    "path": metadata.get("path_display", "")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_item(self, path: str) -> Dict[str, Any]:
        """Eliminar archivo o carpeta"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/files/delete_v2"
            data = {"path": path}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Item eliminado: {path}"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_shared_link(self, path: str) -> Dict[str, Any]:
        """Crear link compartido"""
        if not self.is_configured():
            return {"success": False, "error": "Dropbox no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/sharing/create_shared_link_with_settings"
            data = {
                "path": path,
                "settings": {
                    "requested_visibility": "public"
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "url": result.get("url", ""),
                    "path": path
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.access_token else None
        }


# Singleton
dropbox_manager = DropboxManager()
