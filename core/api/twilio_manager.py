"""
MININA v3.0 - Twilio Manager
API para operaciones con Twilio (SMS, llamadas, WhatsApp)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime
from requests.auth import HTTPBasicAuth


class TwilioManager:
    """
    Manager de Twilio para MININA
    
    Requiere:
    - Account SID (AC...)
    - Auth Token
    - From Number (número de Twilio para enviar SMS)
    
    Para obtener:
    1. Ve a https://www.twilio.com/console
    2. Copia Account SID y Auth Token del dashboard
    3. Obtén un número de teléfono de Twilio
    """
    
    API_BASE_URL = "https://api.twilio.com/2010-04-01"
    
    def __init__(self, config_path: str = "data/twilio_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.account_sid: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.from_number: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.account_sid = data.get("account_sid")
                    self.auth_token = data.get("auth_token")
                    self.from_number = data.get("from_number")
            except Exception as e:
                print(f"Error cargando configuración Twilio: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "updated_at": datetime.now().isoformat(),
                "account_sid": self.account_sid,
                "auth_token": self.auth_token,
                "from_number": self.from_number
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuración Twilio: {e}")
    
    def set_credentials(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str
    ) -> Dict[str, Any]:
        """Configurar credenciales de Twilio"""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self._save_config()
        
        # Verificar conexión
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "Credenciales de Twilio configuradas y verificadas"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo conectar con Twilio. Verifica Account SID y Auth Token."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not all([self.account_sid, self.auth_token]):
            return False
        
        try:
            url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}.json"
            response = requests.get(url, auth=HTTPBasicAuth(self.account_sid, self.auth_token), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.account_sid and self.auth_token and self.from_number)
    
    def send_sms(self, to_number: str, message: str) -> Dict[str, Any]:
        """Enviar SMS"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}/Messages.json"
            
            data = {
                "From": self.from_number,
                "To": to_number,
                "Body": message
            }
            
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                data=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "body": result.get("body"),
                    "status": result.get("status"),
                    "date_created": result.get("date_created"),
                    "price": result.get("price"),
                    "price_unit": result.get("price_unit")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def send_whatsapp(self, to_number: str, message: str) -> Dict[str, Any]:
        """Enviar mensaje de WhatsApp"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}/Messages.json"
            
            # Formato de número WhatsApp: whatsapp:+1234567890
            whatsapp_to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
            whatsapp_from = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
            
            data = {
                "From": whatsapp_from,
                "To": whatsapp_to,
                "Body": message
            }
            
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                data=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "body": result.get("body"),
                    "status": result.get("status"),
                    "date_created": result.get("date_created")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def make_call(self, to_number: str, url: str) -> Dict[str, Any]:
        """Realizar una llamada"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            call_url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}/Calls.json"
            
            data = {
                "From": self.from_number,
                "To": to_number,
                "Url": url  # URL con TwiML para manejar la llamada
            }
            
            response = requests.post(
                call_url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                data=data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "call_sid": result.get("sid"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "status": result.get("status"),
                    "direction": result.get("direction"),
                    "date_created": result.get("date_created"),
                    "price": result.get("price")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_message(self, message_sid: str) -> Dict[str, Any]:
        """Obtener información de un mensaje"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}/Messages/{message_sid}.json"
            response = requests.get(url, auth=HTTPBasicAuth(self.account_sid, self.auth_token), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid"),
                    "to": result.get("to"),
                    "from": result.get("from"),
                    "body": result.get("body"),
                    "status": result.get("status"),
                    "date_sent": result.get("date_sent"),
                    "price": result.get("price"),
                    "error_code": result.get("error_code"),
                    "error_message": result.get("error_message")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_messages(self, to_number: Optional[str] = None, from_number: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Listar mensajes"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/Accounts/{self.account_sid}/Messages.json"
            params = {"PageSize": limit}
            
            if to_number:
                params["To"] = to_number
            if from_number:
                params["From"] = from_number
            
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                messages = result.get("messages", [])
                return {
                    "success": True,
                    "messages": [
                        {
                            "sid": m["sid"],
                            "to": m["to"],
                            "from": m["from"],
                            "body": m["body"],
                            "status": m["status"],
                            "date_sent": m["date_sent"],
                            "price": m["price"]
                        }
                        for m in messages
                    ],
                    "total": len(messages)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def lookup_phone_number(self, phone_number: str) -> Dict[str, Any]:
        """Buscar información de un número de teléfono"""
        if not self.is_configured():
            return {"success": False, "error": "Twilio no configurado"}
        
        try:
            url = f"https://lookups.twilio.com/v1/PhoneNumbers/{phone_number}"
            params = {"Type": "carrier"}
            
            response = requests.get(
                url,
                auth=HTTPBasicAuth(self.account_sid, self.auth_token),
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                carrier = result.get("carrier", {})
                return {
                    "success": True,
                    "phone_number": result.get("phone_number"),
                    "national_format": result.get("national_format"),
                    "country_code": result.get("country_code"),
                    "carrier_name": carrier.get("name"),
                    "carrier_type": carrier.get("type"),
                    "mobile_country_code": carrier.get("mobile_country_code"),
                    "mobile_network_code": carrier.get("mobile_network_code")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "account_sid": self.account_sid[:10] + "***" if self.account_sid else None,
            "from_number": self.from_number
        }


# Singleton
twilio_manager = TwilioManager()
