"""
MININA v3.0 - GitHub Skill
Skill para operaciones con GitHub
"""

from core.api.github_manager import github_manager


def execute(context: dict) -> dict:
    """
    Operaciones con GitHub
    
    Args:
        context: {
            "action": str,           # list_repos, list_issues, create_issue, create_pr, list_commits
            "owner": str,            # Owner del repo
            "repo": str,             # Nombre del repo
            "title": str,            # Título del issue/PR
            "body": str,             # Cuerpo del issue/PR
            "head": str,             # Branch origen (para PR)
            "base": str,             # Branch destino (para PR)
            "state": str,            # Estado de issues: open/closed/all
            "labels": list,          # Labels para issues
            "org": str               # Organización (opcional)
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
        
        # Verificar que GitHub está configurado
        if not github_manager.is_configured():
            return {
                "success": False,
                "error": "GitHub no configurado. Ve a Configuración → GitHub para agregar tu token."
            }
        
        if action == "list_repos":
            org = context.get("org")
            return github_manager.list_repos(org)
        
        elif action == "list_issues":
            owner = context.get("owner", "")
            repo = context.get("repo", "")
            state = context.get("state", "open")
            
            if not owner or not repo:
                return {"success": False, "error": "Faltan owner y repo"}
            
            return github_manager.list_issues(owner, repo, state)
        
        elif action == "create_issue":
            owner = context.get("owner", "")
            repo = context.get("repo", "")
            title = context.get("title", "")
            body = context.get("body", "")
            labels = context.get("labels", [])
            
            if not owner or not repo or not title:
                return {"success": False, "error": "Faltan owner, repo o title"}
            
            return github_manager.create_issue(owner, repo, title, body, labels)
        
        elif action == "create_pr" or action == "create_pull_request":
            owner = context.get("owner", "")
            repo = context.get("repo", "")
            title = context.get("title", "")
            head = context.get("head", "")
            base = context.get("base", "main")
            body = context.get("body", "")
            
            if not owner or not repo or not title or not head:
                return {"success": False, "error": "Faltan owner, repo, title o head"}
            
            return github_manager.create_pull_request(owner, repo, title, head, base, body)
        
        elif action == "list_commits":
            owner = context.get("owner", "")
            repo = context.get("repo", "")
            branch = context.get("branch", "main")
            
            if not owner or not repo:
                return {"success": False, "error": "Faltan owner y repo"}
            
            return github_manager.list_commits(owner, repo, branch)
        
        else:
            return {
                "success": False,
                "error": f"Acción '{action}' no válida. Usa: list_repos, list_issues, create_issue, create_pr, list_commits"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en skill de GitHub: {str(e)}"
        }
