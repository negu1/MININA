"""
MININA v3.0 - Mailchimp Manager
API para operaciones con Mailchimp (listas, campañas, suscriptores)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class MailchimpManager:
    """
    Manager de Mailchimp para MININA
    
    Requiere:
    - API Key (de Mailchimp Account)
    
    Para obtener:
    1. Ve a https://admin.mailchimp.com/account/api/
    2. Crea un API Key
    3. Copia el API Key (termina en -us1, -us2, etc. indicando el datacenter)
    """
    
    def __init__(self, config_path: str = "data/mailchimp_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_key: Optional[str] = None
        self.datacenter: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
                    # Extraer datacenter del API key (formato: key-us2)
                    if self.api_key and '-' in self.api_key:
                        self.datacenter = self.api_key.split('-')[-1]
            except Exception as e:
                print(f"Error cargando configuración Mailchimp: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "api_key": self.api_key
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Mailchimp: {e}")
    
    def set_api_key(self, api_key: str) -> Dict[str, Any]:
        """Configurar API Key de Mailchimp"""
        self.api_key = api_key
        # Extraer datacenter
        if '-' in api_key:
            self.datacenter = api_key.split('-')[-1]
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "API Key de Mailchimp configurada y verificada",
                "datacenter": self.datacenter
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar la API Key. Verifica que sea válida."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.api_key or not self.datacenter:
            return False
        
        try:
            url = f"https://{self.datacenter}.api.mailchimp.com/3.0/"
            response = requests.get(url, auth=("any", self.api_key), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def _get_url(self, endpoint: str) -> str:
        """Construir URL completa"""
        return f"https://{self.datacenter}.api.mailchimp.com/3.0{endpoint}"
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.api_key and self.datacenter)
    
    def get_lists(self) -> Dict[str, Any]:
        """Obtener listas (audiences)"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            url = self._get_url("/lists")
            response = requests.get(url, auth=("any", self.api_key), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                lists = result.get("lists", [])
                return {
                    "success": True,
                    "lists": [
                        {
                            "id": lst["id"],
                            "name": lst["name"],
                            "member_count": lst.get("stats", {}).get("member_count", 0),
                            "unsubscribe_count": lst.get("stats", {}).get("unsubscribe_count", 0),
                            "date_created": lst.get("date_created")
                        }
                        for lst in lists
                    ],
                    "total": result.get("total_items", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def add_subscriber(
        self,
        list_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        status: str = "subscribed"
    ) -> Dict[str, Any]:
        """Agregar suscriptor a una lista"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            url = self._get_url(f"/lists/{list_id}/members")
            
            data = {
                "email_address": email,
                "status": status,
                "merge_fields": {}
            }
            
            if first_name:
                data["merge_fields"]["FNAME"] = first_name
            if last_name:
                data["merge_fields"]["LNAME"] = last_name
            
            response = requests.post(
                url,
                auth=("any", self.api_key),
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "subscriber_id": result.get("id"),
                    "email": result.get("email_address"),
                    "status": result.get("status"),
                    "list_id": list_id
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def update_subscriber(
        self,
        list_id: str,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Actualizar suscriptor"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            # Convertir email a MD5 para el subscriber hash
            import hashlib
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            url = self._get_url(f"/lists/{list_id}/members/{subscriber_hash}")
            
            data = {}
            if first_name or last_name:
                data["merge_fields"] = {}
                if first_name:
                    data["merge_fields"]["FNAME"] = first_name
                if last_name:
                    data["merge_fields"]["LNAME"] = last_name
            
            if status:
                data["status"] = status
            
            response = requests.patch(
                url,
                auth=("any", self.api_key),
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "subscriber_id": result.get("id"),
                    "email": result.get("email_address"),
                    "status": result.get("status")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def remove_subscriber(self, list_id: str, email: str) -> Dict[str, Any]:
        """Eliminar suscriptor de una lista"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            import hashlib
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            url = self._get_url(f"/lists/{list_id}/members/{subscriber_hash}")
            
            response = requests.delete(url, auth=("any", self.api_key), timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"Suscriptor {email} eliminado de la lista"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_subscribers(self, list_id: str, count: int = 10) -> Dict[str, Any]:
        """Obtener suscriptores de una lista"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            url = self._get_url(f"/lists/{list_id}/members")
            params = {"count": count}
            
            response = requests.get(
                url,
                auth=("any", self.api_key),
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                members = result.get("members", [])
                return {
                    "success": True,
                    "members": [
                        {
                            "id": m["id"],
                            "email": m["email_address"],
                            "status": m["status"],
                            "first_name": m.get("merge_fields", {}).get("FNAME"),
                            "last_name": m.get("merge_fields", {}).get("LNAME"),
                            "last_changed": m.get("last_changed")
                        }
                        for m in members
                    ],
                    "total": result.get("total_items", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_campaigns(self, count: int = 10) -> Dict[str, Any]:
        """Obtener campañas"""
        if not self.is_configured():
            return {"success": False, "error": "Mailchimp no configurado"}
        
        try:
            url = self._get_url("/campaigns")
            params = {"count": count}
            
            response = requests.get(
                url,
                auth=("any", self.api_key),
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                campaigns = result.get("campaigns", [])
                return {
                    "success": True,
                    "campaigns": [
                        {
                            "id": c["id"],
                            "type": c["type"],
                            "status": c.get("status"),
                            "send_time": c.get("send_time"),
                            "emails_sent": c.get("emails_sent"),
                            "settings": {
                                "subject_line": c.get("settings", {}).get("subject_line"),
                                "title": c.get("settings", {}).get("title")
                            }
                        }
                        for c in campaigns
                    ],
                    "total": result.get("total_items", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "api_key": "***" + self.api_key[-4:] if self.api_key else None,
            "datacenter": self.datacenter
        }


# Singleton
mailchimp_manager = MailchimpManager()
