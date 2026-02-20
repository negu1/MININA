"""
MiIA Secure LLM Gateway
Arquitectura de seguridad para uso de APIs LLM en chat
- Opt-in explícito por usuario
- Validación de intención
- Logs de auditoría completa
- Límites de uso y presupuesto
"""
import json
import logging
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger("SecureLLMGateway")

class APIRiskLevel(Enum):
    """Niveles de riesgo para APIs"""
    SAFE = "safe"           # Gratis, local, sin costo
    LOW = "low"             # Muy económico (< $0.001 por consulta)
    MEDIUM = "medium"       # Económico ($0.001 - $0.01)
    HIGH = "high"           # Costoso (>$0.01)

@dataclass
class APIUsageRecord:
    """Registro de uso de API para auditoría"""
    timestamp: str
    user_id: str
    provider: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    query_hash: str  # Hash de la consulta (privacidad)
    approved_by_user: bool
    session_id: str

class SecureLLMGateway:
    """
    Gateway seguro para APIs LLM
    Principios:
    1. OPT-IN: APIs pagas NUNCA se usan sin consentimiento explícito
    2. TRANSPARENCIA: El usuario siempre sabe cuándo y qué API se usa
    3. CONTROL: El usuario puede desactivar en cualquier momento
    4. AUDITORÍA: Todo uso queda registrado
    5. LÍMITES: Presupuestos y límites de uso
    """
    
    def __init__(self):
        self.config_path = Path("data/secure_llm_config.json")
        self.audit_log_path = Path("data/llm_audit.log")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuración por usuario
        self.user_configs: Dict[str, Dict] = {}
        
        # Estado de consentimiento temporal
        self.pending_approvals: Dict[str, Dict] = {}  # session_id -> approval_data
        
        # Límites de uso
        self.daily_limits = {
            APIRiskLevel.SAFE: float('inf'),
            APIRiskLevel.LOW: 100,      # 100 consultas/día
            APIRiskLevel.MEDIUM: 20,    # 20 consultas/día
            APIRiskLevel.HIGH: 5,       # 5 consultas/día
        }
        
        # Costos estimados por 1K tokens (USD)
        self.pricing = {
            'openai-gpt4o': {'input': 0.005, 'output': 0.015, 'risk': APIRiskLevel.MEDIUM},
            'openai-gpt4o-mini': {'input': 0.00015, 'output': 0.0006, 'risk': APIRiskLevel.LOW},
            'groq-llama3': {'input': 0.00005, 'output': 0.00008, 'risk': APIRiskLevel.LOW},
            'ollama-local': {'input': 0, 'output': 0, 'risk': APIRiskLevel.SAFE},
        }
        
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración de usuarios"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.user_configs = json.load(f)
            except Exception as e:
                logger.error(f"Error cargando config: {e}")
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_configs, f, indent=2)
        except Exception as e:
            logger.error(f"Error guardando config: {e}")
    
    def _log_audit(self, record: APIUsageRecord):
        """Registrar uso en log de auditoría"""
        try:
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(record), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Error en auditoría: {e}")
    
    def get_user_api_status(self, user_id: str) -> Dict[str, Any]:
        """Obtener estado de APIs para un usuario"""
        config = self.user_configs.get(user_id, {})
        
        return {
            'apis_enabled': config.get('apis_enabled', False),
            'approved_providers': config.get('approved_providers', []),
            'daily_budget_usd': config.get('daily_budget_usd', 1.0),
            'today_usage_usd': self._get_today_usage(user_id),
            'today_queries': self._get_today_queries(user_id),
            'risk_preferences': config.get('risk_preferences', {
                'allow_safe': True,
                'allow_low': False,
                'allow_medium': False,
                'allow_high': False,
            })
        }
    
    def _get_today_usage(self, user_id: str) -> float:
        """Calcular uso de hoy en USD"""
        today = datetime.now().strftime('%Y-%m-%d')
        total = 0.0
        
        if not self.audit_log_path.exists():
            return total
        
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record['user_id'] == user_id and record['timestamp'].startswith(today):
                            total += record['cost_usd']
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error calculando uso: {e}")
        
        return round(total, 4)
    
    def _get_today_queries(self, user_id: str) -> Dict[str, int]:
        """Contar consultas de hoy por nivel de riesgo"""
        today = datetime.now().strftime('%Y-%m-%d')
        counts = {level: 0 for level in APIRiskLevel}
        
        if not self.audit_log_path.exists():
            return counts
        
        try:
            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record['user_id'] == user_id and record['timestamp'].startswith(today):
                            risk = record.get('risk_level', 'SAFE')
                            counts[risk] = counts.get(risk, 0) + 1
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error contando consultas: {e}")
        
        return counts
    
    async def request_api_access(self, user_id: str, provider: str, 
                                  query_preview: str = "") -> Dict[str, Any]:
        """
        Solicitar acceso a API para una consulta específica
        Retorna: {'approved': True/False, 'message': str, 'session_id': str}
        """
        config = self.user_configs.get(user_id, {})
        
        # Si el usuario no ha habilitado APIs pagas
        if not config.get('apis_enabled', False):
            return {
                'approved': False,
                'message': (
                    "🔒 Las APIs pagas están desactivadas.\n\n"
                    "Para usar IA avanzada (GPT-4, Claude, etc.):\n"
                    "1. Ve a Configuración → IA\n"
                    "2. Activa 'Permitir APIs pagas'\n"
                    "3. Configura tu presupuesto diario\n\n"
                    "O usa Ollama (gratis) para modelos locales."
                ),
                'session_id': None
            }
        
        # Verificar si el provider está aprobado
        approved_providers = config.get('approved_providers', [])
        if provider not in approved_providers:
            return {
                'approved': False,
                'message': f"🔒 Provider '{provider}' no está en tu lista de APIs aprobadas.",
                'session_id': None
            }
        
        # Calcular riesgo y costo estimado
        risk = self._get_provider_risk(provider)
        estimated_cost = self._estimate_cost(provider, query_preview)
        
        # Verificar límites diarios
        today_queries = self._get_today_queries(user_id)
        if today_queries.get(risk.name, 0) >= self.daily_limits[risk]:
            return {
                'approved': False,
                'message': (
                    f"⛔ Has alcanzado el límite diario para APIs de riesgo {risk.name}.\n"
                    f"Límite: {self.daily_limits[risk]} consultas/día\n\n"
                    f"Vuelve a intentar mañana o usa una API local (Ollama)."
                ),
                'session_id': None
            }
        
        # Verificar presupuesto
        today_usage = self._get_today_usage(user_id)
        daily_budget = config.get('daily_budget_usd', 1.0)
        if today_usage + estimated_cost > daily_budget:
            return {
                'approved': False,
                'message': (
                    f"💰 Esto excedería tu presupuesto diario (${daily_budget}).\n"
                    f"Uso hoy: ${today_usage:.4f}\n"
                    f"Estimado: ${estimated_cost:.4f}\n\n"
                    f"Aumenta tu presupuesto o espera a mañana."
                ),
                'session_id': None
            }
        
        # Generar sesión de aprobación
        session_id = hashlib.sha256(f"{user_id}:{provider}:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Guardar aprobación pendiente
        self.pending_approvals[session_id] = {
            'user_id': user_id,
            'provider': provider,
            'risk': risk.name,
            'estimated_cost': estimated_cost,
            'query_preview': query_preview[:100],  # Solo preview
            'timestamp': datetime.now().isoformat(),
            'approved': False
        }
        
        return {
            'approved': False,  # Requiere confirmación explícita
            'requires_approval': True,
            'message': (
                f"🔐 Solicitud de uso de API\n\n"
                f"Provider: {provider}\n"
                f"Riesgo: {risk.name}\n"
                f"Costo estimado: ${estimated_cost:.4f}\n"
                f"Presupuesto restante: ${daily_budget - today_usage:.4f}\n\n"
                f"¿Deseas continuar?\n"
                f"Responde: 'sí usar {session_id}' para aprobar"
            ),
            'session_id': session_id
        }
    
    async def approve_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Aprobar una sesión pendiente"""
        if session_id not in self.pending_approvals:
            return {'success': False, 'error': 'Sesión no encontrada o expirada'}
        
        approval = self.pending_approvals[session_id]
        
        if approval['user_id'] != user_id:
            return {'success': False, 'error': 'No autorizado'}
        
        approval['approved'] = True
        approval['approved_at'] = datetime.now().isoformat()
        
        return {
            'success': True,
            'message': f"✅ Aprobado. Puedes hacer tu consulta ahora.",
            'provider': approval['provider'],
            'session_id': session_id
        }
    
    async def execute_with_api(self, user_id: str, session_id: str, 
                                query: str, provider: str) -> Dict[str, Any]:
        """Ejecutar consulta con API aprobada"""
        # Verificar sesión aprobada
        if session_id not in self.pending_approvals:
            return {'success': False, 'error': 'Sesión no aprobada o expirada'}
        
        approval = self.pending_approvals[session_id]
        if not approval.get('approved', False):
            return {'success': False, 'error': 'Sesión no aprobada'}
        
        # Aquí iría la llamada real a la API
        # Por ahora simulamos
        tokens_input = len(query.split()) * 2  # Estimación simple
        tokens_output = 100  # Estimación
        actual_cost = self._calculate_actual_cost(provider, tokens_input, tokens_output)
        
        # Registrar auditoría
        record = APIUsageRecord(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            provider=provider,
            model=approval.get('model', 'unknown'),
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=actual_cost,
            query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
            approved_by_user=True,
            session_id=session_id
        )
        self._log_audit(record)
        
        # Limpiar sesión usada
        del self.pending_approvals[session_id]
        
        return {
            'success': True,
            'cost': actual_cost,
            'total_today': self._get_today_usage(user_id),
            'budget_remaining': self.user_configs.get(user_id, {}).get('daily_budget_usd', 1.0) - self._get_today_usage(user_id)
        }
    
    def _get_user_configured_apis(self, user_id: str) -> List[Dict[str, Any]]:
        """Obtener lista de APIs configuradas por el usuario"""
        try:
            from core.llm_extension import credential_store
            
            configured_apis = []
            available_providers = ['openai', 'groq', 'anthropic', 'gemini', 'deepseek']
            
            for provider in available_providers:
                if credential_store.has_key(provider):
                    # Obtener info del provider
                    provider_info = self._get_provider_info(provider)
                    configured_apis.append({
                        'id': provider,
                        'name': provider_info.get('name', provider.title()),
                        'description': provider_info.get('description', ''),
                        'risk': provider_info.get('risk', 'MEDIUM'),
                        'has_key': True
                    })
            
            return configured_apis
        except Exception as e:
            logger.error(f"Error obteniendo APIs configuradas: {e}")
            return []
    
    def _get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Obtener información de un provider"""
        providers_info = {
            'openai': {
                'name': 'OpenAI',
                'description': 'GPT-4o, GPT-4o Mini',
                'risk': 'MEDIUM',
                'models': ['gpt-4o-mini', 'gpt-4o']
            },
            'groq': {
                'name': 'Groq',
                'description': 'Ultra rápido - Llama 3.1, Mixtral',
                'risk': 'LOW',
                'models': ['llama-3.1-8b-instant', 'llama-3.1-70b-versatile']
            },
            'anthropic': {
                'name': 'Anthropic',
                'description': 'Claude 3 Opus, Sonnet, Haiku',
                'risk': 'MEDIUM',
                'models': ['claude-3-opus', 'claude-3-sonnet']
            },
            'gemini': {
                'name': 'Google Gemini',
                'description': 'Gemini 1.5 Flash y Pro',
                'risk': 'LOW',
                'models': ['gemini-1.5-flash', 'gemini-1.5-pro']
            },
            'deepseek': {
                'name': 'DeepSeek',
                'description': 'Económico y capaz',
                'risk': 'LOW',
                'models': ['deepseek-chat', 'deepseek-coder']
            }
        }
        return providers_info.get(provider, {
            'name': provider.title(),
            'description': 'Provider de IA',
            'risk': 'MEDIUM',
            'models': []
        })
    
    async def request_api_menu(self, user_id: str, query_preview: str = "") -> Dict[str, Any]:
        """
        Mostrar menú de APIs configuradas para que el usuario elija
        Retorna menú con opciones o mensaje si no hay APIs configuradas
        """
        config = self.user_configs.get(user_id, {})
        
        # Si el usuario no ha habilitado APIs pagas
        if not config.get('apis_enabled', False):
            return {
                'menu_available': False,
                'message': (
                    "🔒 Las APIs pagas están desactivadas.\n\n"
                    "Para usar IA avanzada:\n"
                    "1. Ve a Configuración → IA\n"
                    "2. Activa 'Permitir APIs pagas'\n"
                    "3. Configura al menos una API (OpenAI, Groq, etc.)\n\n"
                    "O usa Ollama (gratis) para modelos locales."
                )
            }
        
        # Obtener APIs configuradas
        configured_apis = self._get_user_configured_apis(user_id)
        
        if not configured_apis:
            return {
                'menu_available': False,
                'message': (
                    "⚠️ No tienes APIs configuradas.\n\n"
                    "Ve a Configuración → IA para agregar:\n"
                    "• OpenAI (GPT-4o)\n"
                    "• Groq (Ultra rápido)\n"
                    "• Google Gemini\n\n"
                    "O usa Ollama gratis."
                )
            }
        
        # Verificar presupuesto
        today_usage = self._get_today_usage(user_id)
        daily_budget = config.get('daily_budget_usd', 1.0)
        remaining = daily_budget - today_usage
        
        if remaining <= 0:
            return {
                'menu_available': False,
                'message': (
                    f"💰 Has alcanzado tu presupuesto diario (${daily_budget}).\n"
                    f"Espera a mañana o aumenta tu presupuesto."
                )
            }
        
        # Generar sesión para este menú
        session_id = hashlib.sha256(f"{user_id}:menu:{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        # Guardar opciones disponibles
        self.pending_approvals[session_id] = {
            'user_id': user_id,
            'type': 'api_selection_menu',
            'query_preview': query_preview[:100],
            'available_apis': configured_apis,
            'timestamp': datetime.now().isoformat(),
            'selected_provider': None,
            'approved': False
        }
        
        # Construir mensaje del menú
        menu_text = (
            f"🤖 Necesito usar una API de pago para responder.\n\n"
            f"💰 Presupuesto restante: ${remaining:.4f}\n"
            f"📊 APIs configuradas disponibles:\n\n"
        )
        
        for i, api in enumerate(configured_apis, 1):
            menu_text += f"  {i}. {api['name']} - {api['description']}\n"
        
        menu_text += (
            f"\n¿Cuál quieres usar?\n"
            f"• Por voz: Di 'usar la número X' o 'usar {configured_apis[0]['id']}'\n"
            f"• Por clic: Presiona el botón correspondiente\n"
            f"• Di 'cancelar' o presiona ❌ para no usar API"
        )
        
        return {
            'menu_available': True,
            'session_id': session_id,
            'message': menu_text,
            'options': [
                {
                    'id': api['id'],
                    'name': api['name'],
                    'description': api['description'],
                    'risk': api['risk'],
                    'number': i
                }
                for i, api in enumerate(configured_apis, 1)
            ],
            'voice_commands': [
                f"usar la número {i}" for i in range(1, len(configured_apis) + 1)
            ] + [f"usar {api['id']}" for api in configured_apis] + ["cancelar", "no usar api"]
        }
    
    async def select_api_from_menu(self, user_id: str, session_id: str, 
                                    selection: str) -> Dict[str, Any]:
        """
        Procesar selección del menú de APIs
        selection puede ser: número ("1", "2") o nombre ("openai", "groq")
        """
        if session_id not in self.pending_approvals:
            return {'success': False, 'error': 'Sesión de menú expirada'}
        
        menu_data = self.pending_approvals[session_id]
        
        if menu_data['user_id'] != user_id:
            return {'success': False, 'error': 'No autorizado'}
        
        if menu_data.get('type') != 'api_selection_menu':
            return {'success': False, 'error': 'Tipo de sesión inválido'}
        
        available_apis = menu_data['available_apis']
        selected_provider = None
        
        # Intentar parsear como número
        try:
            num = int(selection.strip())
            if 1 <= num <= len(available_apis):
                selected_provider = available_apis[num - 1]['id']
        except ValueError:
            # No es número, buscar por nombre
            selection_lower = selection.lower().strip()
            for api in available_apis:
                if api['id'] in selection_lower or api['name'].lower() in selection_lower:
                    selected_provider = api['id']
                    break
        
        if not selected_provider:
            return {
                'success': False,
                'error': f"No entendí '{selection}'. Di el número o el nombre de la API.",
                'available_options': [api['id'] for api in available_apis]
            }
        
        # Verificar límites y costos para el provider seleccionado
        risk = self._get_provider_risk(selected_provider)
        estimated_cost = self._estimate_cost(selected_provider, menu_data['query_preview'])
        
        today_queries = self._get_today_queries(user_id)
        if today_queries.get(risk.name, 0) >= self.daily_limits[risk]:
            return {
                'success': False,
                'error': f"Has alcanzado el límite para APIs {risk.name}. Intenta con otra o espera a mañana."
            }
        
        # Actualizar sesión con selección
        menu_data['selected_provider'] = selected_provider
        menu_data['approved'] = True
        menu_data['risk'] = risk.name
        menu_data['estimated_cost'] = estimated_cost
        
        # Crear nueva sesión de ejecución
        exec_session_id = hashlib.sha256(
            f"{user_id}:{selected_provider}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        self.pending_approvals[exec_session_id] = {
            'user_id': user_id,
            'provider': selected_provider,
            'risk': risk.name,
            'estimated_cost': estimated_cost,
            'query_preview': menu_data['query_preview'],
            'timestamp': datetime.now().isoformat(),
            'approved': True,  # Ya aprobado por selección
            'menu_session': session_id
        }
        
        return {
            'success': True,
            'provider': selected_provider,
            'provider_name': self._get_provider_info(selected_provider)['name'],
            'estimated_cost': estimated_cost,
            'session_id': exec_session_id,
            'message': f"✅ Usarás {self._get_provider_info(selected_provider)['name']}. Procediendo..."
        }
    
    def _estimate_cost(self, provider: str, query: str) -> float:
        """Estimar costo de una consulta"""
        for key, data in self.pricing.items():
            if provider.lower() in key.lower():
                tokens = len(query.split()) * 2  # Estimación
                return (tokens / 1000) * data['input']
        return 0.001  # Default
    
    def _calculate_actual_cost(self, provider: str, tokens_in: int, tokens_out: int) -> float:
        """Calcular costo real"""
        for key, data in self.pricing.items():
            if provider.lower() in key.lower():
                cost_in = (tokens_in / 1000) * data['input']
                cost_out = (tokens_out / 1000) * data['output']
                return cost_in + cost_out
        return 0.001


# Instancia global
secure_gateway = SecureLLMGateway()
