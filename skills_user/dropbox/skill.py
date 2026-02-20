"""
MININA v3.0 - Dropbox Skill
Skill para operaciones con Dropbox
"""

from core.api.dropbox_manager import dropbox_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Dropbox
    
    Args:
        context: {
            "action": str,           # list_files, upload_file, download_file, create_folder, delete_item, share
            "path": str,           # Ruta en Dropbox
            "local_path": str,     # Ruta local (para upload/download)
            "dropbox_path": str    # Ruta en Dropbox (para upload/download)
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
        
        # Verificar que Dropbox está configurado
        if not dropbox_manager.is_configured():
            return {
                "success": False,
                "error": "Dropbox no configurado. Ve a Configuración → Dropbox para agregar tu token."
            }
        
        if action == "list_files":
            path = context.get("path", "")
            recursive = context.get("recursive", False)
            return dropbox_manager.list_files(path, recursive)
        
        elif action == "upload_file":
            local_path = context.get("local_path", "")
            dropbox_path = context.get("dropbox_path", "")
            
            if not local_path or not dropbox_path:
                return {"success": False, "error": "Faltan local_path o dropbox_path"}
            
            return dropbox_manager.upload_file(local_path, dropbox_path)
        
        elif action == "download_file":
            dropbox_path = context.get("dropbox_path", "")
            local_path = context.get("local_path", "")
            
            if not dropbox_path or not local_path:
                return {"success": False, "error": "Faltan dropbox_path o local_path"}
            
            return dropbox_manager.download_file(dropbox_path, local_path)
        
        elif action == "create_folder":
            path = context.get("path", "")
            if not path:
                return {"success": False, "error": "Falta path"}
            return dropbox_manager.create_folder(path)
        
        elif action == "delete_item":
            path = context.get("path", "")
            if not path:
                return {"success": False, "error": "Falta path"}
            return dropbox_manager.delete_item(path)
        
        elif action == "share":
            path = context.get("path", "")
            if not path:
                return {"success": False, "error": "Falta path"}
            return dropbox_manager.create_shared_link(path)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_files, upload_file, download_file, create_folder, delete_item, share"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Dropbox: {str(e)}"
        }
