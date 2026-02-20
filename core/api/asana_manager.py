"""
MININA v3.0 - Asana Manager
API para operaciones con Asana (tareas, proyectos, workspaces)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class AsanaManager:
    """
    Manager de Asana para MININA
    
    Requiere:
    - Personal Access Token (de Asana Developer Console)
    
    Para obtener:
    1. Ve a https://app.asana.com/0/developer-console
    2. Crea un nuevo "Personal Access Token"
    3. Copia el token generado
    """
    
    API_BASE_URL = "https://app.asana.com/api/1.0"
    
    def __init__(self, config_path: str = "data/asana_config.json"):
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
                print(f"Error cargando configuración Asana: {e}")
    
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
            print(f"Error guardando configuración Asana: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de Asana"""
        self.access_token = token
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de Asana configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea un Personal Access Token válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.access_token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}/users/me"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.access_token)
    
    def get_workspaces(self) -> Dict[str, Any]:
        """Obtener workspaces del usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/workspaces"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                workspaces = result.get("data", [])
                return {
                    "success": True,
                    "workspaces": [
                        {
                            "id": w["gid"],
                            "name": w["name"],
                            "is_organization": w.get("is_organization", False)
                        }
                        for w in workspaces
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_projects(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Obtener proyectos"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            if workspace_id:
                url = f"{self.API_BASE_URL}/workspaces/{workspace_id}/projects"
            else:
                url = f"{self.API_BASE_URL}/projects"
            
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                projects = result.get("data", [])
                return {
                    "success": True,
                    "projects": [
                        {
                            "id": p["gid"],
                            "name": p["name"],
                            "archived": p.get("archived", False),
                            "color": p.get("color"),
                            "notes": p.get("notes", "")[:100]  # Primeros 100 caracteres
                        }
                        for p in projects
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_task(
        self,
        name: str,
        workspace_id: str,
        project_id: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear una tarea"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/tasks"
            
            data = {
                "data": {
                    "name": name,
                    "workspace": workspace_id
                }
            }
            
            if project_id:
                data["data"]["projects"] = [project_id]
            if assignee:
                data["data"]["assignee"] = assignee
            if due_date:
                data["data"]["due_on"] = due_date
            if notes:
                data["data"]["notes"] = notes
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                task = result.get("data", {})
                return {
                    "success": True,
                    "task_id": task.get("gid"),
                    "name": task.get("name"),
                    "created_at": task.get("created_at")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """Obtener información de una tarea"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/tasks/{task_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                task = result.get("data", {})
                return {
                    "success": True,
                    "task_id": task.get("gid"),
                    "name": task.get("name"),
                    "notes": task.get("notes", ""),
                    "completed": task.get("completed", False),
                    "due_on": task.get("due_on"),
                    "assignee": task.get("assignee", {}).get("name") if task.get("assignee") else None,
                    "created_at": task.get("created_at"),
                    "modified_at": task.get("modified_at")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Actualizar una tarea"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/tasks/{task_id}"
            
            data = {"data": {}}
            
            if name:
                data["data"]["name"] = name
            if assignee:
                data["data"]["assignee"] = assignee
            if due_date:
                data["data"]["due_on"] = due_date
            if notes:
                data["data"]["notes"] = notes
            if completed is not None:
                data["data"]["completed"] = completed
            
            response = requests.put(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                task = result.get("data", {})
                return {
                    "success": True,
                    "task_id": task.get("gid"),
                    "name": task.get("name"),
                    "modified_at": task.get("modified_at")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """Eliminar una tarea"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/tasks/{task_id}"
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Tarea {task_id} eliminada"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_project_tasks(self, project_id: str) -> Dict[str, Any]:
        """Obtener tareas de un proyecto"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/projects/{project_id}/tasks"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tasks = result.get("data", [])
                return {
                    "success": True,
                    "tasks": [
                        {
                            "id": t["gid"],
                            "name": t["name"],
                            "completed": t.get("completed", False),
                            "due_on": t.get("due_on")
                        }
                        for t in tasks
                    ]
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_user_tasks(self, user_id: str = "me") -> Dict[str, Any]:
        """Obtener tareas asignadas a un usuario"""
        if not self.is_configured():
            return {"success": False, "error": "Asana no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/users/{user_id}/tasks"
            params = {"opt_fields": "name,completed,due_on,projects.name"}
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                tasks = result.get("data", [])
                return {
                    "success": True,
                    "tasks": [
                        {
                            "id": t["gid"],
                            "name": t["name"],
                            "completed": t.get("completed", False),
                            "due_on": t.get("due_on")
                        }
                        for t in tasks
                    ],
                    "total": len(tasks)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "token": "***" if self.access_token else None
        }


# Singleton
asana_manager = AsanaManager()
