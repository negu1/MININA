"""
MININA v3.0 - Jira Manager
API para operaciones con Jira (issues, proyectos, comentarios)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime
import base64


class JiraManager:
    """
    Manager de Jira para MININA
    
    Requiere:
    - Jira URL (ej: https://tudominio.atlassian.net)
    - Email del usuario
    - API Token
    
    Para obtener API Token:
    1. Ve a https://id.atlassian.com/manage-profile/security/api-tokens
    2. Crea un nuevo token
    3. Copia el token generado
    """
    
    def __init__(self, config_path: str = "data/jira_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.jira_url: Optional[str] = None
        self.email: Optional[str] = None
        self.api_token: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.jira_url = data.get("jira_url")
                    self.email = data.get("email")
                    self.api_token = data.get("api_token")
            except Exception as e:
                print(f"Error cargando configuración Jira: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "jira_url": self.jira_url,
                "email": self.email,
                "api_token": self.api_token
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Jira: {e}")
    
    def set_credentials(
        self,
        jira_url: str,
        email: str,
        api_token: str
    ) -> Dict[str, Any]:
        """Configurar credenciales de Jira"""
        # Normalizar URL
        if not jira_url.startswith(('http://', 'https://')):
            jira_url = f"https://{jira_url}"
        
        self.jira_url = jira_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Credenciales de Jira configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo conectar con Jira. Verifica la URL, email y API token."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not all([self.jira_url, self.email, self.api_token]):
            return False
        
        try:
            url = f"{self.jira_url}/rest/api/3/myself"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        credentials = base64.b64encode(
            f"{self.email}:{self.api_token}".encode()
        ).decode()
        
        return {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.jira_url and self.email and self.api_token)
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task"
    ) -> Dict[str, Any]:
        """Crear un issue en Jira"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue"
            
            data = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": description}]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "issue_id": result.get("id"),
                    "issue_key": result.get("key"),
                    "self": result.get("self"),
                    "url": f"{self.jira_url}/browse/{result.get('key')}"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Obtener detalles de un issue"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                fields = result.get("fields", {})
                return {
                    "success": True,
                    "issue_id": result.get("id"),
                    "issue_key": result.get("key"),
                    "summary": fields.get("summary"),
                    "description": self._extract_description(fields.get("description")),
                    "status": fields.get("status", {}).get("name"),
                    "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
                    "reporter": fields.get("reporter", {}).get("displayName"),
                    "created": fields.get("created"),
                    "updated": fields.get("updated"),
                    "priority": fields.get("priority", {}).get("name"),
                    "issue_type": fields.get("issuetype", {}).get("name")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def _extract_description(self, description: Any) -> Optional[str]:
        """Extraer texto de descripción en formato ADF"""
        if not description:
            return None
        
        try:
            if isinstance(description, dict):
                content = description.get("content", [])
                texts = []
                for item in content:
                    if item.get("type") == "paragraph":
                        for text_item in item.get("content", []):
                            if text_item.get("type") == "text":
                                texts.append(text_item.get("text", ""))
                return " ".join(texts) if texts else None
            else:
                return str(description)
        except:
            return str(description)
    
    def update_issue(self, issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Actualizar un issue"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            
            data = {"fields": {}}
            
            if summary:
                data["fields"]["summary"] = summary
            
            if description:
                data["fields"]["description"] = {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}]
                        }
                    ]
                }
            
            response = requests.put(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"Issue {issue_key} actualizado"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Agregar comentario a un issue"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/comment"
            
            data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": comment}]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "comment_id": result.get("id"),
                    "created": result.get("created")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def search_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Buscar issues usando JQL"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                "jql": jql,
                "maxResults": max_results
            }
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                issues = result.get("issues", [])
                return {
                    "success": True,
                    "total": result.get("total", 0),
                    "issues": [
                        {
                            "key": issue["key"],
                            "summary": issue["fields"].get("summary"),
                            "status": issue["fields"].get("status", {}).get("name"),
                            "assignee": issue["fields"].get("assignee", {}).get("displayName") if issue["fields"].get("assignee") else None,
                            "created": issue["fields"].get("created"),
                            "updated": issue["fields"].get("updated")
                        }
                        for issue in issues
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_projects(self) -> Dict[str, Any]:
        """Listar proyectos disponibles"""
        if not self.is_configured():
            return {"success": False, "error": "Jira no configurado"}
        
        try:
            url = f"{self.jira_url}/rest/api/3/project"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "projects": [
                        {
                            "id": project["id"],
                            "key": project["key"],
                            "name": project["name"],
                            "projectTypeKey": project.get("projectTypeKey"),
                            "url": f"{self.jira_url}/browse/{project['key']}"
                        }
                        for project in result
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
            "jira_url": self.jira_url,
            "email": self.email[:3] + "***" if self.email else None
        }


# Singleton
jira_manager = JiraManager()
