"""
MININA v3.0 - HubSpot Manager
API para operaciones con HubSpot (contactos, empresas, deals)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class HubSpotManager:
    """
    Manager de HubSpot para MININA
    
    Requiere:
    - Private App Token (de HubSpot Developer Portal)
    
    Para obtener:
    1. Ve a https://app.hubspot.com/private-apps
    2. Crea una Private App
    3. Copia el Access Token
    4. Configura los scopes necesarios (crm.objects.contacts.read, crm.objects.contacts.write, etc.)
    """
    
    API_BASE_URL = "https://api.hubapi.com/crm/v3"
    
    def __init__(self, config_path: str = "data/hubspot_config.json"):
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
                print(f"Error cargando configuración HubSpot: {e}")
    
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
            print(f"Error guardando configuración HubSpot: {e}")
    
    def set_token(self, token: str) -> Dict[str, Any]:
        """Configurar token de HubSpot"""
        self.access_token = token
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Token de HubSpot configurado y verificado"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar el token. Verifica que sea un Private App Token válido."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.access_token:
            return False
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts"
            params = {"limit": 1}
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
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
    
    def create_contact(
        self,
        email: str,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear un contacto en HubSpot"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts"
            
            properties = {"email": email}
            if firstname:
                properties["firstname"] = firstname
            if lastname:
                properties["lastname"] = lastname
            if phone:
                properties["phone"] = phone
            if company:
                properties["company"] = company
            
            data = {"properties": properties}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "contact_id": result.get("id"),
                    "email": email,
                    "created_at": result.get("createdAt")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """Obtener información de un contacto"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts/{contact_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                props = result.get("properties", {})
                return {
                    "success": True,
                    "contact_id": result.get("id"),
                    "email": props.get("email"),
                    "firstname": props.get("firstname"),
                    "lastname": props.get("lastname"),
                    "phone": props.get("phone"),
                    "company": props.get("company"),
                    "created_at": result.get("createdAt"),
                    "updated_at": result.get("updatedAt")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def search_contacts(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Buscar contactos"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts/search"
            
            data = {
                "query": query,
                "limit": limit
            }
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                contacts = result.get("results", [])
                return {
                    "success": True,
                    "contacts": [
                        {
                            "id": c["id"],
                            "email": c["properties"].get("email"),
                            "firstname": c["properties"].get("firstname"),
                            "lastname": c["properties"].get("lastname"),
                            "company": c["properties"].get("company")
                        }
                        for c in contacts
                    ],
                    "total": result.get("total", 0)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def update_contact(self, contact_id: str, properties: Dict[str, str]) -> Dict[str, Any]:
        """Actualizar un contacto"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts/{contact_id}"
            data = {"properties": properties}
            
            response = requests.patch(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "contact_id": result.get("id"),
                    "updated_at": result.get("updatedAt")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def delete_contact(self, contact_id: str) -> Dict[str, Any]:
        """Eliminar un contacto"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/contacts/{contact_id}"
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 204:
                return {
                    "success": True,
                    "message": f"Contacto {contact_id} eliminado"
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_deal(
        self,
        dealname: str,
        amount: Optional[float] = None,
        stage: Optional[str] = None,
        pipeline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear un deal (oportunidad)"""
        if not self.is_configured():
            return {"success": False, "error": "HubSpot no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/objects/deals"
            
            properties = {"dealname": dealname}
            if amount is not None:
                properties["amount"] = str(amount)
            if stage:
                properties["dealstage"] = stage
            if pipeline:
                properties["pipeline"] = pipeline
            
            data = {"properties": properties}
            
            response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "deal_id": result.get("id"),
                    "dealname": dealname,
                    "created_at": result.get("createdAt")
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
hubspot_manager = HubSpotManager()
