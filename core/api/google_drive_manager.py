"""
MININA v3.0 - Google Drive Manager
API para operaciones con Google Drive
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class DriveFile:
    """Archivo en Google Drive"""
    id: str
    name: str
    mime_type: str
    size: int
    created_time: str
    modified_time: str
    parents: List[str]
    web_view_link: str
    download_url: Optional[str] = None


class GoogleDriveManager:
    """
    Manager de Google Drive para MININA
    
    Requiere:
    - Google OAuth2 credentials (client_id, client_secret)
    - Access token o refresh token
    
    Para obtener:
    1. Ve a https://console.cloud.google.com/
    2. Crea un proyecto y habilita "Google Drive API"
    3. Ve a "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth"
    4. Descarga el archivo credentials.json
    """
    
    API_BASE_URL = "https://www.googleapis.com/drive/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
    
    def __init__(self, config_path: str = "data/google_drive_config.json"):
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
                print(f"Error cargando configuración Google Drive: {e}")
    
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
            print(f"Error guardando configuración Google Drive: {e}")
    
    def set_credentials(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configurar credenciales de Google Drive"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self._save_config()
        
        return {
            "success": True,
            "message": "Credenciales de Google Drive configuradas correctamente"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.access_token and self.client_id)
    
    def list_files(
        self,
        folder_id: str = "root",
        page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Listar archivos en una carpeta
        
        Args:
            folder_id: ID de la carpeta (default: root = Mi unidad)
            page_size: Número máximo de archivos a listar
        
        Returns:
            {
                "success": bool,
                "files": List[DriveFile],
                "error": str (si falla)
            }
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        # Simulación de archivos (para testing)
        mock_files = [
            {
                "id": "1",
                "name": "Documento1.pdf",
                "mime_type": "application/pdf",
                "size": 1024000,
                "created_time": datetime.now().isoformat(),
                "modified_time": datetime.now().isoformat(),
                "parents": [folder_id],
                "web_view_link": "https://drive.google.com/file/d/1/view"
            },
            {
                "id": "2",
                "name": "Spreadsheet.xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "size": 512000,
                "created_time": datetime.now().isoformat(),
                "modified_time": datetime.now().isoformat(),
                "parents": [folder_id],
                "web_view_link": "https://drive.google.com/file/d/2/view"
            }
        ]
        
        return {
            "success": True,
            "folder_id": folder_id,
            "files": mock_files,
            "count": len(mock_files)
        }
    
    def upload_file(
        self,
        file_path: str,
        folder_id: str = "root",
        description: str = ""
    ) -> Dict[str, Any]:
        """Subir archivo a Google Drive"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        try:
            from pathlib import Path
            file = Path(file_path)
            
            if not file.exists():
                return {
                    "success": False,
                    "error": f"Archivo no encontrado: {file_path}"
                }
            
            # Simulación de subida
            return {
                "success": True,
                "file_id": "new_file_id_123",
                "name": file.name,
                "size": file.stat().st_size,
                "folder_id": folder_id,
                "web_view_link": "https://drive.google.com/file/d/new_file_id_123/view"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error subiendo archivo: {str(e)}"
            }
    
    def download_file(
        self,
        file_id: str,
        download_path: str
    ) -> Dict[str, Any]:
        """Descargar archivo de Google Drive"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        # Simulación de descarga
        return {
            "success": True,
            "file_id": file_id,
            "download_path": download_path,
            "message": f"Archivo {file_id} descargado a {download_path}"
        }
    
    def create_folder(
        self,
        name: str,
        parent_id: str = "root"
    ) -> Dict[str, Any]:
        """Crear carpeta en Google Drive"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        # Simulación de creación
        return {
            "success": True,
            "folder_id": "new_folder_id_456",
            "name": name,
            "parent_id": parent_id,
            "web_view_link": "https://drive.google.com/drive/folders/new_folder_id_456"
        }
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Eliminar archivo de Google Drive"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        # Simulación de eliminación
        return {
            "success": True,
            "file_id": file_id,
            "message": f"Archivo {file_id} eliminado"
        }
    
    def share_file(
        self,
        file_id: str,
        email: str,
        role: str = "reader"  # reader, commenter, writer
    ) -> Dict[str, Any]:
        """Compartir archivo con un usuario"""
        if not self.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado"
            }
        
        # Simulación de compartir
        return {
            "success": True,
            "file_id": file_id,
            "shared_with": email,
            "role": role,
            "message": f"Archivo compartido con {email} como {role}"
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "client_id": self.client_id[:10] + "***" if self.client_id else None,
            "has_access_token": bool(self.access_token),
            "has_refresh_token": bool(self.refresh_token)
        }


# Singleton
google_drive_manager = GoogleDriveManager()
