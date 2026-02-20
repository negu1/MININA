"""
MININA v3.0 - GitHub Manager
API para operaciones con GitHub (repos, issues, PRs, commits)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


@dataclass
class GitHubIssue:
    """Issue de GitHub"""
    number: int
    title: str
    state: str
    body: str
    created_at: str
    updated_at: str
    url: str


class GitHubManager:
    """
    Manager de GitHub para MININA
    
    Requiere:
    - Personal Access Token (classic) o Fine-grained token
    
    Para obtener:
    1. Ve a https://github.com/settings/tokens
    2. Genera un nuevo token
    3. Guarda el token de forma segura
    """
    
    API_BASE_URL = "https://api.github.com"
    
    def __init__(self, config_path: str = "data/github_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.token: Optional[str] = None
        self.username: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.token = data.get("token")
                    self.username = data.get("username")
            except Exception as e:
                print(f"Error cargando configuración GitHub: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "token": self.token,
                "username": self.username
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración GitHub: {e}")
    
    def set_credentials(self, token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Configurar credenciales de GitHub"""
        self.token = token
        self.username = username
        self._save_config()
        
        # Verificar que funcionan
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Credenciales de GitHub configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.token:
            return False
        
        try:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(f"{self.API_BASE_URL}/user", headers=headers, timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.token)
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MININA-App"
        }
    
    def list_repos(self, org: Optional[str] = None) -> Dict[str, Any]:
        """Listar repositorios"""
        if not self.is_configured():
            return {"success": False, "error": "GitHub no configurado"}
        
        try:
            if org:
                url = f"{self.API_BASE_URL}/orgs/{org}/repos"
            else:
                url = f"{self.API_BASE_URL}/user/repos"
            
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                repos = response.json()
                return {
                    "success": True,
                    "repos": [{"name": r["name"], "full_name": r["full_name"], "url": r["html_url"]} for r in repos]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_issues(self, owner: str, repo: str, state: str = "open") -> Dict[str, Any]:
        """Listar issues de un repositorio"""
        if not self.is_configured():
            return {"success": False, "error": "GitHub no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/issues?state={state}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                issues = response.json()
                return {
                    "success": True,
                    "issues": [
                        {
                            "number": i["number"],
                            "title": i["title"],
                            "state": i["state"],
                            "url": i["html_url"]
                        }
                        for i in issues
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: List[str] = None
    ) -> Dict[str, Any]:
        """Crear issue"""
        if not self.is_configured():
            return {"success": False, "error": "GitHub no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/issues"
            data = {
                "title": title,
                "body": body
            }
            if labels:
                data["labels"] = labels
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                issue = response.json()
                return {
                    "success": True,
                    "issue_number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = ""
    ) -> Dict[str, Any]:
        """Crear pull request"""
        if not self.is_configured():
            return {"success": False, "error": "GitHub no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/pulls"
            data = {
                "title": title,
                "head": head,
                "base": base,
                "body": body
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                pr = response.json()
                return {
                    "success": True,
                    "pr_number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_commits(self, owner: str, repo: str, branch: str = "main") -> Dict[str, Any]:
        """Listar commits"""
        if not self.is_configured():
            return {"success": False, "error": "GitHub no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/repos/{owner}/{repo}/commits?sha={branch}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                commits = response.json()
                return {
                    "success": True,
                    "commits": [
                        {
                            "sha": c["sha"][:7],
                            "message": c["commit"]["message"],
                            "author": c["commit"]["author"]["name"],
                            "date": c["commit"]["author"]["date"]
                        }
                        for c in commits[:10]
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "username": self.username,
            "token": "***" if self.token else None
        }


# Singleton
github_manager = GitHubManager()
