"""
MININA v3.0 - Jira Skill
Skill para operaciones con Jira
"""

from core.api.jira_manager import jira_manager


def execute(context: dict) -> dict:
    """
    Operaciones con Jira
    
    Args:
        context: {
            "action": str,           # create_issue, get_issue, update_issue, add_comment, search_issues, list_projects
            "project_key": str,    # Clave del proyecto (para create)
            "summary": str,        # Título del issue
            "description": str,    # Descripción del issue
            "issue_type": str,     # Tipo (default: Task)
            "issue_key": str,      # KEY-123 (para get/update/comment)
            "comment": str,        # Texto del comentario
            "jql": str,           # Query JQL (para search)
            "max_results": int     # Máximo de resultados (default 50)
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
        
        # Verificar que Jira está configurado
        if not jira_manager.is_configured():
            return {
                "success": False,
                "error": "Jira no configurado. Ve a Configuración → Jira para agregar tus credenciales."
            }
        
        if action == "create_issue":
            project_key = context.get("project_key", "")
            summary = context.get("summary", "")
            description = context.get("description", "")
            issue_type = context.get("issue_type", "Task")
            
            if not project_key:
                return {"success": False, "error": "Falta project_key"}
            if not summary:
                return {"success": False, "error": "Falta summary"}
            
            return jira_manager.create_issue(project_key, summary, description, issue_type)
        
        elif action == "get_issue":
            issue_key = context.get("issue_key", "")
            if not issue_key:
                return {"success": False, "error": "Falta issue_key (ej: PROJ-123)"}
            return jira_manager.get_issue(issue_key)
        
        elif action == "update_issue":
            issue_key = context.get("issue_key", "")
            summary = context.get("summary")
            description = context.get("description")
            
            if not issue_key:
                return {"success": False, "error": "Falta issue_key"}
            if not summary and not description:
                return {"success": False, "error": "Debes proporcionar summary o description para actualizar"}
            
            return jira_manager.update_issue(issue_key, summary, description)
        
        elif action == "add_comment":
            issue_key = context.get("issue_key", "")
            comment = context.get("comment", "")
            
            if not issue_key:
                return {"success": False, "error": "Falta issue_key"}
            if not comment:
                return {"success": False, "error": "Falta comment"}
            
            return jira_manager.add_comment(issue_key, comment)
        
        elif action == "search_issues":
            jql = context.get("jql", "")
            max_results = context.get("max_results", 50)
            
            if not jql:
                return {"success": False, "error": "Falta jql (Jira Query Language)"}
            
            return jira_manager.search_issues(jql, max_results)
        
        elif action == "list_projects":
            return jira_manager.list_projects()
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: create_issue, get_issue, update_issue, add_comment, search_issues, list_projects"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de Jira: {str(e)}"
        }
