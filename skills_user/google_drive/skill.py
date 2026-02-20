"""
MININA v3.0 - Google Drive Skill
Skill para operaciones con Google Drive
"""

from core.api.google_drive_manager import google_drive_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Google Drive
    
    Args:
        context: {
            "action": str,           # list_files, upload_file, download_file, create_folder
            "folder_id": str,        # Para listar archivos (default: root)
            "file_path": str,        # Para subir archivo
            "file_id": str,          # Para descargar/eliminar archivo
            "download_path": str,    # Para descargar archivo
            "folder_name": str,      # Para crear carpeta
            "description": str       # Descripción opcional
        }
    
    Returns:
        {
            "success": bool,
            "result": dict,
            "error": str (si falla)
        }
    """
    try:
        action = context.get("action", "")
        
        # Verificar que Drive está configurado
        if not google_drive_manager.is_configured():
            return {
                "success": False,
                "error": "Google Drive no configurado. Ve a Configuración → Google Drive."
            }
        
        if action == "list_files":
            folder_id = context.get("folder_id", "root")
            return google_drive_manager.list_files(folder_id)
        
        elif action == "upload_file":
            file_path = context.get("file_path", "")
            folder_id = context.get("folder_id", "root")
            description = context.get("description", "")
            
            if not file_path:
                return {"success": False, "error": "Falta file_path"}
            
            return google_drive_manager.upload_file(file_path, folder_id, description)
        
        elif action == "download_file":
            file_id = context.get("file_id", "")
            download_path = context.get("download_path", "")
            
            if not file_id or not download_path:
                return {"success": False, "error": "Faltan file_id o download_path"}
            
            return google_drive_manager.download_file(file_id, download_path)
        
        elif action == "create_folder":
            name = context.get("folder_name", "")
            parent_id = context.get("parent_id", "root")
            
            if not name:
                return {"success": False, "error": "Falta folder_name"}
            
            return google_drive_manager.create_folder(name, parent_id)
        
        elif action == "delete_file":
            file_id = context.get("file_id", "")
            
            if not file_id:
                return {"success": False, "error": "Falta file_id"}
            
            return google_drive_manager.delete_file(file_id)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_files, upload_file, download_file, create_folder, delete_file"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Drive: {str(e)}"
        }
