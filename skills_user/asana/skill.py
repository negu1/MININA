"""
MININA v3.0 - Asana Skill
Skill para operaciones con Asana
"""

from core.api.asana_manager import asana_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Asana
    
    Args:
        context: {
            "action": str,           # get_workspaces, get_projects, create_task, get_task, update_task, delete_task, get_project_tasks, get_my_tasks
            "workspace_id": str,   # ID del workspace (para get_projects, create_task)
            "project_id": str,     # ID del proyecto (para get_projects_tasks)
            "task_id": str,        # ID de la tarea (para get/update/delete)
            "name": str,          # Nombre de la tarea (para create)
            "assignee": str,      # ID del asignado (opcional)
            "due_date": str,      # Fecha de vencimiento YYYY-MM-DD (opcional)
            "notes": str,         # Notas/descripción (opcional)
            "completed": bool    # Estado de completado (para update)
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
        
        # Verificar que Asana está configurado
        if not asana_manager.is_configured():
            return {
                "success": False,
                "error": "Asana no configurado. Ve a Configuración → Asana para agregar tu Personal Access Token."
            }
        
        if action == "get_workspaces":
            return asana_manager.get_workspaces()
        
        elif action == "get_projects":
            workspace_id = context.get("workspace_id")
            return asana_manager.get_projects(workspace_id)
        
        elif action == "create_task":
            name = context.get("name", "")
            workspace_id = context.get("workspace_id", "")
            project_id = context.get("project_id")
            assignee = context.get("assignee")
            due_date = context.get("due_date")
            notes = context.get("notes")
            
            if not name:
                return {"success": False, "error": "Falta name"}
            if not workspace_id:
                return {"success": False, "error": "Falta workspace_id"}
            
            return asana_manager.create_task(name, workspace_id, project_id, assignee, due_date, notes)
        
        elif action == "get_task":
            task_id = context.get("task_id", "")
            
            if not task_id:
                return {"success": False, "error": "Falta task_id"}
            
            return asana_manager.get_task(task_id)
        
        elif action == "update_task":
            task_id = context.get("task_id", "")
            name = context.get("name")
            assignee = context.get("assignee")
            due_date = context.get("due_date")
            notes = context.get("notes")
            completed = context.get("completed")
            
            if not task_id:
                return {"success": False, "error": "Falta task_id"}
            
            return asana_manager.update_task(task_id, name, assignee, due_date, notes, completed)
        
        elif action == "delete_task":
            task_id = context.get("task_id", "")
            
            if not task_id:
                return {"success": False, "error": "Falta task_id"}
            
            return asana_manager.delete_task(task_id)
        
        elif action == "get_project_tasks":
            project_id = context.get("project_id", "")
            
            if not project_id:
                return {"success": False, "error": "Falta project_id"}
            
            return asana_manager.get_project_tasks(project_id)
        
        elif action == "get_my_tasks":
            return asana_manager.get_user_tasks("me")
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: get_workspaces, get_projects, create_task, get_task, update_task, delete_task, get_project_tasks, get_my_tasks"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Asana: {str(e)}"
        }
