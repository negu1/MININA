"""
API Registry System
Sistema de registro y detección de APIs para el orquestador
"""
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class APIStatus(Enum):
    """Estado de una API"""
    CONFIGURED = "configured"
    MISSING = "missing"
    ERROR = "error"
    NOT_REQUIRED = "not_required"


@dataclass
class APIInfo:
    """Información de una API"""
    id: str
    name: str
    category: str
    required_for: List[str]  # Qué funcionalidades requieren esta API
    is_configured: bool
    status: APIStatus
    config: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class APIRegistry:
    """
    Registro central de APIs del sistema.
    Permite al orquestador detectar qué APIs están disponibles
    y notificar al usuario cuando falta alguna.
    """
    
    def __init__(self, config_path: str = 'data/api_config.json'):
        self.config_path = config_path
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración de APIs"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                print(f"Error cargando configuración de APIs: {e}")
                self._config = {}
    
    def reload(self):
        """Recargar configuración"""
        self._load_config()
    
    def get_all_apis(self) -> Dict[str, APIInfo]:
        """Obtener todas las APIs con su estado"""
        from core.ui.views.api_categories_structure import API_CATEGORIES
        
        apis = {}
        
        for cat_id, cat_data in API_CATEGORIES.items():
            if "subcategories" in cat_data:
                for sub_id, sub_data in cat_data["subcategories"].items():
                    for api_id, api_def in sub_data.get("apis", {}).items():
                        apis[api_id] = self._get_api_info(api_id, api_def, cat_id)
            else:
                for api_id, api_def in cat_data.get("apis", {}).items():
                    apis[api_id] = self._get_api_info(api_id, api_def, cat_id)
        
        return apis
    
    def _get_api_info(self, api_id: str, api_def: Dict, category: str) -> APIInfo:
        """Obtener información de una API específica"""
        # Buscar configuración
        config = None
        is_configured = False
        
        # 1. Buscar en formato antiguo (por categoría)
        if category in self._config:
            if api_id in self._config[category]:
                config = self._config[category][api_id]
                # Verificar que tenga al menos un campo requerido
                required_fields = [f["name"] for f in api_def.get("fields", []) if f.get("required", False)]
                is_configured = all(config.get(field) for field in required_fields)
        
        # 2. Buscar en formato nuevo (ai.*, apis.*, messaging.*)
        if not is_configured:
            # Formato: ai.groq.api_key
            if category == "ai" and "ai" in self._config:
                if api_id in self._config["ai"]:
                    api_data = self._config["ai"][api_id]
                    if isinstance(api_data, dict) and api_data.get("api_key"):
                        config = api_data
                        is_configured = True
            
            # Formato: apis.GroqAPI.key
            if category == "ai" and "apis" in self._config:
                api_key_map = {
                    "groq": ["Groq API", "groq"],
                    "openai": ["OpenAI API", "openai"],
                    "anthropic": ["Anthropic API", "anthropic"]
                }
                possible_names = api_key_map.get(api_id, [api_id])
                for name in possible_names:
                    if name in self._config["apis"]:
                        api_data = self._config["apis"][name]
                        if isinstance(api_data, dict) and api_data.get("key"):
                            config = {"api_key": api_data["key"], **api_data}
                            is_configured = api_data.get("enabled", True) and bool(api_data["key"])
                            break
            
            # Formato: messaging.TelegramBot.token
            if category == "messaging" and "messaging" in self._config:
                if api_id in self._config["messaging"]:
                    api_data = self._config["messaging"][api_id]
                    if isinstance(api_data, dict):
                        config = api_data
                        is_configured = api_data.get("enabled", False) and bool(api_data.get("token"))
        
        return APIInfo(
            id=api_id,
            name=api_def["name"],
            category=category,
            required_for=self._get_required_for(api_id),
            is_configured=is_configured,
            status=APIStatus.CONFIGURED if is_configured else APIStatus.MISSING,
            config=config
        )
    
    def _get_required_for(self, api_id: str) -> List[str]:
        """Obtener para qué funcionalidades se requiere esta API"""
        # Mapeo de APIs a funcionalidades
        requirements = {
            # AI APIs
            "openai": ["generación de texto", "chat", "análisis de código"],
            "groq": ["generación de texto rápida", "chat"],
            "anthropic": ["generación de texto", "análisis complejo"],
            
            # Bot APIs
            "telegram": ["notificaciones Telegram", "comandos remotos"],
            "whatsapp": ["notificaciones WhatsApp"],
            "discord": ["integración Discord"],
            "slack": ["integración Slack"],
            
            # Business APIs
            "salesforce": ["gestión de CRM", "automatización de ventas"],
            "quickbooks": ["contabilidad", "facturación"],
            "shopify": ["gestión de e-commerce"],
            "paypal": ["procesamiento de pagos"],
            "zendesk": ["soporte al cliente"],
            "clickup": ["gestión de proyectos"],
            "gitlab": ["gestión de código", "CI/CD"],
            "airtable": ["gestión de bases de datos"],
        }
        return requirements.get(api_id, [])
    
    def check_api_for_intent(self, intent: str) -> List[APIInfo]:
        """
        Verificar qué APIs se necesitan para un intent específico.
        Retorna lista de APIs que faltan.
        """
        required_apis = self._get_apis_for_intent(intent)
        missing = []
        
        for api_id in required_apis:
            api_info = self.get_api_info(api_id)
            if api_info and not api_info.is_configured:
                missing.append(api_info)
        
        return missing
    
    def _get_apis_for_intent(self, intent: str) -> List[str]:
        """Mapear intención a APIs requeridas"""
        intent_api_map = {
            # Intenciones de negocio
            "gestionar crm": ["salesforce", "pipedrive"],
            "facturación": ["quickbooks", "xero"],
            "procesar pago": ["paypal", "square"],
            "tienda online": ["shopify", "woocommerce"],
            "soporte cliente": ["zendesk", "freshdesk"],
            "gestión proyectos": ["clickup", "wrike"],
            "código": ["gitlab"],
            "base de datos": ["airtable"],
            
            # Intenciones de comunicación
            "notificar": ["telegram", "whatsapp", "discord", "slack"],
            "enviar mensaje": ["telegram", "whatsapp", "discord", "slack"],
            
            # Intenciones de IA (tienen fallback a modelos locales)
            "generar texto": ["openai", "groq", "anthropic"],
            "chat": ["openai", "groq", "anthropic"],
            "analizar": ["openai", "groq", "anthropic"],
        }
        
        # Buscar coincidencias parciales
        for key, apis in intent_api_map.items():
            if key in intent.lower():
                return apis
        
        return []
    
    def get_api_info(self, api_id: str) -> Optional[APIInfo]:
        """Obtener información de una API específica"""
        apis = self.get_all_apis()
        return apis.get(api_id)
    
    def get_configured_apis(self) -> Dict[str, Dict]:
        """Obtener solo las APIs configuradas"""
        configured = {}
        for cat_id, cat_apis in self._config.items():
            for api_id, api_config in cat_apis.items():
                if api_config:
                    configured[api_id] = api_config
        return configured
    
    def is_api_available(self, api_id: str) -> bool:
        """Verificar si una API específica está configurada y disponible"""
        api_info = self.get_api_info(api_id)
        return api_info.is_configured if api_info else False
    
    def validate_plan_requirements(self, plan: Dict) -> Dict:
        """
        Validar que un plan de ejecución tenga todas las APIs necesarias.
        Retorna dict con 'valid' y lista de APIs faltantes.
        """
        required = set()
        
        # Extraer APIs requeridas del plan
        for task in plan.get("tasks", []):
            task_api = task.get("required_api")
            if task_api:
                required.add(task_api)
            
            # Detectar por tipo de skill
            skill_name = task.get("skill", "").lower()
            detected = self._get_apis_for_intent(skill_name)
            required.update(detected)
        
        # Verificar cuáles faltan
        missing = []
        for api_id in required:
            api_info = self.get_api_info(api_id)
            if not api_info or not api_info.is_configured:
                missing.append(api_info or APIInfo(
                    id=api_id,
                    name=api_id,
                    category="unknown",
                    required_for=["plan execution"],
                    is_configured=False,
                    status=APIStatus.MISSING,
                    error_message=f"API {api_id} no está configurada"
                ))
        
        return {
            "valid": len(missing) == 0,
            "missing_apis": missing,
            "message": self._format_missing_message(missing) if missing else "Todas las APIs requeridas están configuradas"
        }
    
    def _format_missing_message(self, missing: List[APIInfo]) -> str:
        """Formatear mensaje de APIs faltantes"""
        lines = ["⚠️ Las siguientes APIs no están configuradas:"]
        for api in missing:
            lines.append(f"  • {api.name} ({', '.join(api.required_for)})")
        lines.append("\nConfigúralas en Settings > APIs")
        return "\n".join(lines)


# Singleton instance
_api_registry = None

def get_api_registry() -> APIRegistry:
    """Obtener instancia singleton del API Registry"""
    global _api_registry
    if _api_registry is None:
        _api_registry = APIRegistry()
    return _api_registry
