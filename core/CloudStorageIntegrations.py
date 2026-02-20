"""
MiIA Cloud Storage Integrations
Integraciones reales con Google Drive, Dropbox, OneDrive para backup
- Verificación de conexión automática
- Flujo: MiIA guía → Usuario configura → MiIA verifica
"""
import os
import json
import logging
import aiohttp
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("MiIACloudStorage")


class GoogleDriveIntegration:
    """
    Integración con Google Drive
    Flujo:
    1. MiIA muestra URL de Google Cloud Console
    2. Usuario crea proyecto y credenciales
    3. Usuario pega JSON de credenciales en MiIA
    4. MiIA verifica la conexión
    """
    
    AUTH_URL = "https://console.cloud.google.com/apis/credentials"
    DRIVE_API_URL = "https://www.googleapis.com/drive/v3"
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Instrucciones paso a paso para el usuario"""
        return {
            "title": "Configurar Google Drive",
            "steps": [
                {
                    "number": 1,
                    "action": "Ir a Google Cloud Console",
                    "url": "https://console.cloud.google.com/apis/credentials",
                    "description": "Crea un nuevo proyecto (o usa uno existente)"
                },
                {
                    "number": 2,
                    "action": "Habilitar Google Drive API",
                    "description": "Busca 'Google Drive API' y haz clic en 'Habilitar'"
                },
                {
                    "number": 3,
                    "action": "Crear credenciales",
                    "description": "Tipo: 'Cuenta de servicio', formato: JSON"
                },
                {
                    "number": 4,
                    "action": "Compartir carpeta de Drive",
                    "description": "Crea una carpeta en Drive y compártela con el email de la cuenta de servicio"
                },
n                {
                    "number": 5,
                    "action": "Pegar credenciales en MiIA",
                    "description": "Copia el contenido del archivo JSON descargado y pégalo aquí"
                }
            ],
            "required_scopes": [
                "https://www.googleapis.com/auth/drive.file"
            ],
            "help_url": "https://developers.google.com/drive/api/v3/quickstart/python"
        }
    
    @staticmethod
    async def verify_connection(credentials_json: str) -> Dict[str, Any]:
        """
        Verificar que las credenciales de Google Drive funcionan
        """
        try:
            import base64
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            # Parsear credenciales
            creds_data = json.loads(credentials_json)
            
            # Crear credenciales de servicio
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            # Crear servicio
            service = build('drive', 'v3', credentials=credentials)
            
            # Intentar listar archivos (verificación simple)
            results = service.files().list(pageSize=1).execute()
            
            return {
                "success": True,
                "message": "✅ Conexión con Google Drive verificada correctamente",
                "account_email": creds_data.get("client_email", "unknown"),
                "project_id": creds_data.get("project_id", "unknown"),
                "files_accessible": len(results.get('files', []))
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": "❌ El JSON de credenciales no es válido",
                "details": str(e)
            }
        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg:
                return {
                    "success": False,
                    "error": "❌ Las credenciales han expirado o son inválidas",
                    "details": "Crea nuevas credenciales en Google Cloud Console"
                }
            elif "insufficient_permissions" in error_msg:
                return {
                    "success": False,
                    "error": "❌ Permisos insuficientes",
                    "details": "Asegúrate de compartir la carpeta de Drive con la cuenta de servicio"
                }
            else:
                return {
                    "success": False,
                    "error": f"❌ Error de conexión: {error_msg}",
                    "details": "Verifica tu conexión a internet y las credenciales"
                }
    
    @staticmethod
    async def upload_file(credentials_json: str, file_path: Path, folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Subir archivo a Google Drive"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            
            creds_data = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            service = build('drive', 'v3', credentials=credentials)
            
            file_metadata = {
                'name': file_path.name,
                'mimeType': 'application/zip'
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='application/zip',
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                "success": True,
                "file_id": file.get('id'),
                "file_name": file.get('name'),
                "web_link": file.get('webViewLink'),
                "message": f"✅ Archivo subido a Google Drive: {file.get('name')}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error subiendo archivo: {str(e)}"
            }


class DropboxIntegration:
    """
    Integración con Dropbox
    Flujo:
    1. MiIA muestra URL de Dropbox App Console
    2. Usuario crea app y genera token de acceso
    3. Usuario pega token en MiIA
    4. MiIA verifica la conexión
    """
    
    APP_CONSOLE_URL = "https://www.dropbox.com/developers/apps"
    API_URL = "https://api.dropboxapi.com/2"
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Instrucciones paso a paso para el usuario"""
        return {
            "title": "Configurar Dropbox",
            "steps": [
                {
                    "number": 1,
                    "action": "Ir a Dropbox App Console",
                    "url": "https://www.dropbox.com/developers/apps",
                    "description": "Inicia sesión con tu cuenta de Dropbox"
                },
                {
                    "number": 2,
                    "action": "Crear nueva app",
                    "description": "Tipo: 'Scoped access', Acceso: 'Full Dropbox' o 'App folder'"
                },
                {
                    "number": 3,
                    "action": "Configurar permisos",
                    "description": "En 'Permissions', activa: files.content.write, files.content.read"
                },
                {
                    "number": 4,
                    "action": "Generar token de acceso",
                    "description": "En 'Settings' → 'OAuth 2' → 'Generate access token'"
                },
                {
                    "number": 5,
                    "action": "Copiar y pegar token",
                    "description": "Pega el token generado en el campo de abajo"
                }
            ],
            "required_permissions": [
                "files.content.write",
                "files.content.read"
            ],
            "help_url": "https://www.dropbox.com/developers/documentation"
        }
    
    @staticmethod
    async def verify_connection(access_token: str) -> Dict[str, Any]:
        """
        Verificar que el token de Dropbox funciona
        """
        try:
            import dropbox
            from dropbox.exceptions import AuthError
            
            # Crear cliente Dropbox
            dbx = dropbox.Dropbox(access_token)
            
            # Verificar token obteniendo info de la cuenta
            account_info = dbx.users_get_current_account()
            
            # Verificar espacio disponible
            space_usage = dbx.users_get_space_usage()
            
            used_bytes = space_usage.used
            allocation = space_usage.allocation
            if isinstance(allocation, dropbox.users.SpaceAllocation.individual):
                total_bytes = allocation.get_individual().allocated
            else:
                total_bytes = 0  # Equipo, no se puede determinar fácilmente
            
            return {
                "success": True,
                "message": "✅ Conexión con Dropbox verificada correctamente",
                "account_name": account_info.name.display_name,
                "account_email": account_info.email,
                "space_used_gb": round(used_bytes / (1024**3), 2),
                "space_total_gb": round(total_bytes / (1024**3), 2) if total_bytes > 0 else "Ilimitado (equipo)"
            }
            
        except AuthError as e:
            return {
                "success": False,
                "error": "❌ Token de Dropbox inválido o expirado",
                "details": "Genera un nuevo token en Dropbox App Console"
            }
        except ImportError:
            return {
                "success": False,
                "error": "❌ Biblioteca de Dropbox no instalada",
                "details": "Ejecuta: pip install dropbox"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ Error de conexión: {str(e)}",
                "details": "Verifica tu conexión a internet y el token"
            }
    
    @staticmethod
    async def upload_file(access_token: str, file_path: Path, folder_path: str = "/MiIA-Backups") -> Dict[str, Any]:
        """Subir archivo a Dropbox"""
        try:
            import dropbox
            from dropbox.files import WriteMode
            
            dbx = dropbox.Dropbox(access_token)
            
            # Crear carpeta si no existe
            try:
                dbx.files_create_folder_v2(folder_path)
            except dropbox.exceptions.ApiError as e:
                if e.error.is_path() and e.error.get_path().is_conflict():
                    pass  # Carpeta ya existe
                else:
                    raise
            
            # Subir archivo
            dest_path = f"{folder_path}/{file_path.name}"
            
            with open(file_path, 'rb') as f:
                file_size = os.path.getsize(file_path)
                
                if file_size <= 150 * 1024 * 1024:  # 150 MB
                    # Upload simple
                    dbx.files_upload(f.read(), dest_path, mode=WriteMode.overwrite)
                else:
                    # Upload por sesiones (archivos grandes)
                    upload_session_start_result = dbx.files_upload_session_start(f.read(1024*1024*100))
                    cursor = dropbox.files.UploadSessionCursor(
                        session_id=upload_session_start_result.session_id,
                        offset=f.tell()
                    )
                    commit = dropbox.files.CommitInfo(path=dest_path, mode=WriteMode.overwrite)
                    
                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= 1024*1024*100:
                            dbx.files_upload_session_finish(f.read(1024*1024*100), cursor, commit)
                        else:
                            dbx.files_upload_session_append_v2(f.read(1024*1024*100), cursor)
                            cursor.offset = f.tell()
            
            # Obtener link compartido
            try:
                shared_link = dbx.sharing_create_shared_link_with_settings(dest_path)
                link_url = shared_link.url
            except:
                link_url = None
            
            return {
                "success": True,
                "file_path": dest_path,
                "file_size": file_size,
                "shared_link": link_url,
                "message": f"✅ Archivo subido a Dropbox: {file_path.name}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error subiendo archivo: {str(e)}"
            }


class OneDriveIntegration:
    """
    Integración con Microsoft OneDrive
    Flujo:
    1. MiIA muestra URL de Azure Portal
    2. Usuario registra aplicación y obtiene credenciales
    3. Usuario autoriza a través de OAuth
    4. MiIA verifica la conexión
    """
    
    AZURE_PORTAL_URL = "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
    
    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Instrucciones paso a paso para el usuario"""
        return {
            "title": "Configurar OneDrive",
            "steps": [
                {
                    "number": 1,
                    "action": "Ir a Azure Portal",
                    "url": "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade",
                    "description": "Inicia sesión con tu cuenta de Microsoft"
                },
                {
                    "number": 2,
                    "action": "Registrar nueva aplicación",
                    "description": "Haz clic en 'New registration', nombre: 'MiIA-Backup'"
                },
                {
                    "number": 3,
                    "action": "Configurar permisos",
                    "description": "API permissions → Microsoft Graph → Delegated permissions: Files.ReadWrite"
                },
                {
                    "number": 4,
                    "action": "Obtener credenciales",
                    "description": "Copia Application (client) ID y crea un nuevo 'client secret'"
                },
                {
                    "number": 5,
                    "action": "Pegar credenciales en MiIA",
                    "description": "Ingresa el Client ID, Client Secret y tu Tenant ID"
                }
            ],
            "required_permissions": [
                "Files.ReadWrite"
            ],
            "help_url": "https://docs.microsoft.com/en-us/graph/onedrive-concept-overview"
        }
    
    @staticmethod
    async def verify_connection(client_id: str, client_secret: str, tenant_id: str) -> Dict[str, Any]:
        """
        Verificar conexión con OneDrive mediante Microsoft Graph API
        """
        try:
            # Obtener token de acceso
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            
            token_data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=token_data) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        return {
                            "success": False,
                            "error": "❌ Error de autenticación",
                            "details": error_data.get("error_description", "Credenciales inválidas")
                        }
                    
                    token_result = await response.json()
                    access_token = token_result.get("access_token")
                    
                    # Verificar acceso a OneDrive
                    graph_url = "https://graph.microsoft.com/v1.0/me/drive"
                    headers = {"Authorization": f"Bearer {access_token}"}
                    
                    async with session.get(graph_url, headers=headers) as drive_response:
                        if drive_response.status == 200:
                            drive_info = await drive_response.json()
                            return {
                                "success": True,
                                "message": "✅ Conexión con OneDrive verificada correctamente",
                                "drive_id": drive_info.get("id"),
                                "drive_type": drive_info.get("driveType"),
                                "owner": drive_info.get("owner", {}).get("user", {}).get("displayName", "Unknown")
                            }
                        else:
                            error_text = await drive_response.text()
                            return {
                                "success": False,
                                "error": "❌ No se pudo acceder a OneDrive",
                                "details": error_text
                            }
                            
        except Exception as e:
            return {
                "success": False,
                "error": f"❌ Error de conexión: {str(e)}",
                "details": "Verifica tus credenciales de Azure AD"
            }
    
    @staticmethod
    async def upload_file(client_id: str, client_secret: str, tenant_id: str, 
                         file_path: Path, folder_path: str = "MiIA-Backups") -> Dict[str, Any]:
        """Subir archivo a OneDrive"""
        try:
            # Obtener token (reutilizar lógica anterior)
            token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
            token_data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=token_data) as response:
                    token_result = await response.json()
                    access_token = token_result.get("access_token")
                
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/octet-stream"
                }
                
                # Crear/verificar carpeta
                folder_url = f"https://graph.microsoft.com/v1.0/me/drive/root/children"
                folder_payload = {
                    "name": folder_path,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
                
                async with session.post(folder_url, headers={"Authorization": f"Bearer {access_token}", 
                                                             "Content-Type": "application/json"}, 
                                       json=folder_payload) as folder_response:
                    folder_result = await folder_response.json()
                    folder_id = folder_result.get("id")
                
                # Subir archivo
                upload_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}:/{file_path.name}:/content"
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                async with session.put(upload_url, headers=headers, data=file_content) as upload_response:
                    if upload_response.status in [200, 201]:
                        file_info = await upload_response.json()
                        return {
                            "success": True,
                            "file_id": file_info.get("id"),
                            "file_name": file_info.get("name"),
                            "web_url": file_info.get("webUrl"),
                            "message": f"✅ Archivo subido a OneDrive: {file_info.get('name')}"
                        }
                    else:
                        error_text = await upload_response.text()
                        return {
                            "success": False,
                            "error": f"Error subiendo archivo: {error_text}"
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }


# ============ FUNCIONES DE VERIFICACIÓN UNIFICADAS ============

async def verify_cloud_connection(provider: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verificar conexión con proveedor de nube seleccionado
    
    Args:
        provider: 'google_drive', 'dropbox', 'onedrive'
        credentials: Diccionario con credenciales específicas del proveedor
    
    Returns:
        Dict con resultado de verificación
    """
    try:
        if provider == "google_drive":
            return await GoogleDriveIntegration.verify_connection(
                credentials.get("credentials_json", "")
            )
        elif provider == "dropbox":
            return await DropboxIntegration.verify_connection(
                credentials.get("access_token", "")
            )
        elif provider == "onedrive":
            return await OneDriveIntegration.verify_connection(
                credentials.get("client_id", ""),
                credentials.get("client_secret", ""),
                credentials.get("tenant_id", "")
            )
        else:
            return {
                "success": False,
                "error": f"Proveedor no soportado: {provider}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error verificando conexión: {str(e)}"
        }


def get_provider_instructions(provider: str) -> Dict[str, Any]:
    """Obtener instrucciones de configuración para un proveedor"""
    if provider == "google_drive":
        return GoogleDriveIntegration.get_setup_instructions()
    elif provider == "dropbox":
        return DropboxIntegration.get_setup_instructions()
    elif provider == "onedrive":
        return OneDriveIntegration.get_setup_instructions()
    else:
        return {
            "error": f"Proveedor no soportado: {provider}"
        }


# ============ EXPORTAR FUNCIONES ============

__all__ = [
    "GoogleDriveIntegration",
    "DropboxIntegration", 
    "OneDriveIntegration",
    "verify_cloud_connection",
    "get_provider_instructions"
]
