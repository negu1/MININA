"""
MININA v3.0 - Stripe Manager
API para operaciones con Stripe (pagos, clientes, suscripciones)
"""

import requests
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
from datetime import datetime


class StripeManager:
    """
    Manager de Stripe para MININA
    
    Requiere:
    - Secret Key (sk_test_... o sk_live_...)
    
    Para obtener:
    1. Ve a https://dashboard.stripe.com/apikeys
    2. Crea una Secret Key o usa la existente
    3. Copia la clave (empieza con sk_test_ para pruebas o sk_live_ para producción)
    """
    
    API_BASE_URL = "https://api.stripe.com/v1"
    
    def __init__(self, config_path: str = "data/stripe_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.api_key: Optional[str] = None
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.api_key = data.get("api_key")
            except Exception as e:
                print(f"Error cargando configuración Stripe: {e}")
    
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
            print(f"Error guardando configuración Stripe: {e}")
    
    def set_api_key(self, api_key: str) -> Dict[str, Any]:
        """Configurar API Key de Stripe"""
        self.api_key = api_key
        self._save_config()
        
        # Verificar que funciona
        test_result = self._test_auth()
        
        if test_result:
            return {
                "success": True,
                "message": "API Key de Stripe configurada y verificada"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo verificar la API Key. Verifica que sea válida."
            }
    
    def _test_auth(self) -> bool:
        """Testear autenticación"""
        if not self.api_key:
            return False
        
        try:
            url = f"{self.API_BASE_URL}/account"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            return response.status_code == 200
        except:
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    
    def is_configured(self) -> bool:
        """Verificar si está configurado"""
        return bool(self.api_key)
    
    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear un Payment Intent (intención de pago)"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/payment_intents"
            
            data = {
                "amount": amount,  # En centavos (ej: 1000 = $10.00)
                "currency": currency.lower(),
                "automatic_payment_methods[enabled]": "true"
            }
            
            if customer_id:
                data["customer"] = customer_id
            if description:
                data["description"] = description
            
            response = requests.post(url, headers=self._get_headers(), data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "payment_intent_id": result.get("id"),
                    "client_secret": result.get("client_secret"),
                    "amount": result.get("amount"),
                    "currency": result.get("currency"),
                    "status": result.get("status")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear un cliente"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/customers"
            
            data = {"email": email}
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            
            response = requests.post(url, headers=self._get_headers(), data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "customer_id": result.get("id"),
                    "email": result.get("email"),
                    "name": result.get("name"),
                    "created": result.get("created")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Obtener información de un cliente"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/customers/{customer_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "customer_id": result.get("id"),
                    "email": result.get("email"),
                    "name": result.get("name"),
                    "description": result.get("description"),
                    "created": result.get("created"),
                    "balance": result.get("balance"),
                    "currency": result.get("currency")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def create_product(
        self,
        name: str,
        description: Optional[str] = None,
        price: Optional[int] = None,
        currency: str = "usd"
    ) -> Dict[str, Any]:
        """Crear un producto"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            # Crear producto
            url = f"{self.API_BASE_URL}/products"
            data = {"name": name}
            if description:
                data["description"] = description
            
            response = requests.post(url, headers=self._get_headers(), data=data, timeout=30)
            
            if response.status_code == 200:
                product = response.json()
                product_id = product.get("id")
                
                # Si se proporcionó precio, crear Price
                if price:
                    price_result = self._create_price(product_id, price, currency)
                    if price_result.get("success"):
                        return {
                            "success": True,
                            "product_id": product_id,
                            "price_id": price_result.get("price_id"),
                            "name": product.get("name"),
                            "description": product.get("description")
                        }
                
                return {
                    "success": True,
                    "product_id": product_id,
                    "name": product.get("name"),
                    "description": product.get("description")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def _create_price(self, product_id: str, amount: int, currency: str) -> Dict[str, Any]:
        """Crear un precio para un producto"""
        try:
            url = f"{self.API_BASE_URL}/prices"
            data = {
                "product": product_id,
                "unit_amount": amount,
                "currency": currency.lower()
            }
            
            response = requests.post(url, headers=self._get_headers(), data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "price_id": result.get("id"),
                    "unit_amount": result.get("unit_amount"),
                    "currency": result.get("currency")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def list_payments(self, limit: int = 10) -> Dict[str, Any]:
        """Listar pagos recientes"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/charges"
            params = {"limit": limit}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                charges = result.get("data", [])
                return {
                    "success": True,
                    "charges": [
                        {
                            "id": c["id"],
                            "amount": c["amount"],
                            "currency": c["currency"],
                            "status": c["status"],
                            "description": c.get("description"),
                            "customer": c.get("customer"),
                            "created": c["created"]
                        }
                        for c in charges
                    ],
                    "has_more": result.get("has_more", False)
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def refund_charge(self, charge_id: str, amount: Optional[int] = None) -> Dict[str, Any]:
        """Reembolsar un cargo"""
        if not self.is_configured():
            return {"success": False, "error": "Stripe no configurado"}
        
        try:
            url = f"{self.API_BASE_URL}/refunds"
            data = {"charge": charge_id}
            if amount:
                data["amount"] = amount
            
            response = requests.post(url, headers=self._get_headers(), data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "refund_id": result.get("id"),
                    "amount": result.get("amount"),
                    "status": result.get("status"),
                    "charge": result.get("charge")
                }
            else:
                return {"success": False, "error": f"Error HTTP {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    def get_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        return {
            "configured": self.is_configured(),
            "api_key": "***" if self.api_key else None,
            "mode": "live" if self.api_key and self.api_key.startswith("sk_live") else "test" if self.api_key else None
        }


# Singleton
stripe_manager = StripeManager()
