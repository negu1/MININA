"""
Universal Policy & Rules System
Sistema universal de reglas y políticas adaptable a cualquier tipo de trabajo
"""
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import os
from datetime import datetime


class RuleType(Enum):
    """Tipos de reglas universales"""
    RATE_LIMIT = "rate_limit"           # Límites de velocidad
    RESOURCE = "resource"                # Límites de recursos (CPU, RAM, storage)
    TIME = "time"                        # Restricciones de tiempo/horario
    NETWORK = "network"                  # Restricciones de red
    SECURITY = "security"                # Requisitos de seguridad
    PERMISSION = "permission"          # Permisos específicos
    APPROVAL = "approval"                # Requiere aprobación manual
    COST = "cost"                        # Límites de costo/presupuesto
    QUALITY = "quality"                  # Umbrales de calidad
    COMPLIANCE = "compliance"            # Cumplimiento normativo
    CUSTOM = "custom"                    # Reglas personalizadas


class ComparisonOp(Enum):
    """Operadores de comparación"""
    EQ = "eq"          # Igual
    NE = "ne"          # No igual
    GT = "gt"          # Mayor que
    GTE = "gte"        # Mayor o igual
    LT = "lt"          # Menor que
    LTE = "lte"        # Menor o igual
    IN = "in"          # Dentro de lista
    NOT_IN = "not_in"  # No en lista
    CONTAINS = "contains"  # Contiene substring
    REGEX = "regex"    # Match regex


@dataclass
class RuleCondition:
    """Condición para evaluar una regla"""
    field: str                          # Campo a evaluar (ej: "job.type", "resources.cpu")
    operator: ComparisonOp              # Operador de comparación
    value: Any                          # Valor a comparar
    description: str = ""               # Descripción legible


@dataclass
class RuleAction:
    """Acción a tomar cuando se viola una regla"""
    type: str                           # Tipo de acción: "block", "warn", "approve", "log", "notify"
    message: str = ""                   # Mensaje al usuario
    notify_channels: List[str] = field(default_factory=list)  # ui, telegram, whatsapp, email
    escalation_delay: int = 0           # Segundos antes de escalar
    auto_approve_after: int = 0         # Auto-aprobar después de X segundos si no hay respuesta


@dataclass
class UniversalRule:
    """Regla universal adaptable"""
    id: str                             # Identificador único
    name: str                           # Nombre legible
    description: str                    # Descripción
    type: RuleType                      # Tipo de regla
    category: str                       # Categoría para organización
    enabled: bool = True                # Está activa?
    
    # Condiciones de aplicabilidad (cuándo aplica esta regla)
    applies_to: List[str] = field(default_factory=list)  # Job types, skill categories, etc.
    conditions: List[RuleCondition] = field(default_factory=list)  # Condiciones específicas
    
    # Configuración de la regla
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Acciones cuando se viola
    on_violation: RuleAction = field(default_factory=lambda: RuleAction(type="block"))
    on_warning: Optional[RuleAction] = None
    
    # Metadatos
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: int = 100                 # Prioridad (menor = más importante)


@dataclass
class JobProfile:
    """Perfil de trabajo que define características y reglas aplicables"""
    id: str                             # ID del tipo de trabajo
    name: str                           # Nombre legible
    description: str                    # Descripción
    category: str                       # Categoría (ej: "data_processing", "communication", "automation")
    
    # Características del trabajo
    characteristics: Dict[str, Any] = field(default_factory=dict)
    
    # Reglas por defecto para este tipo
    default_rules: List[str] = field(default_factory=list)  # IDs de reglas
    
    # Recursos típicos necesarios
    typical_resources: Dict[str, Any] = field(default_factory=dict)
    
    # Permisos base
    base_permissions: List[str] = field(default_factory=list)
    
    # APIs típicamente necesarias
    typical_apis: List[str] = field(default_factory=list)
    
    # Riesgo base (0-100)
    base_risk_level: int = 50


@dataclass
class PermissionTemplate:
    """Template de permisos reutilizable"""
    id: str
    name: str
    description: str
    scope: str                          # "global", "job_type", "specific_job"
    permissions: Dict[str, bool] = field(default_factory=dict)  # permission_id -> granted
    applies_to: List[str] = field(default_factory=list)


class UniversalPolicyEngine:
    """
    Motor de políticas universal que se adapta a cualquier tipo de trabajo.
    
    Características:
    - Reglas dinámicas por categoría
    - Perfiles de trabajo predefinidos
    - Evaluación contextual
    - Extensible sin modificar código
    """
    
    def __init__(self, config_path: str = 'data/universal_policies.json'):
        self.config_path = config_path
        self.rules: Dict[str, UniversalRule] = {}
        self.job_profiles: Dict[str, JobProfile] = {}
        self.permission_templates: Dict[str, PermissionTemplate] = {}
        self._subscribers: List[Callable] = []
        
        self._init_default_profiles()
        self._init_default_rules()
        self._load_config()
    
    def _init_default_profiles(self):
        """Inicializar perfiles de trabajo por defecto"""
        profiles = [
            JobProfile(
                id="data_processing",
                name="📊 Procesamiento de Datos",
                description="Trabajos que procesan, transforman o analizan datos",
                category="data",
                characteristics={"cpu_intensive": True, "io_intensive": True},
                default_rules=["resource_limits", "rate_limit_data", "storage_limit"],
                typical_resources={"cpu": 80, "ram": 4096, "storage": 1024},
                base_permissions=["read_data", "write_data", "transform_data"],
                typical_apis=["airtable", "postgresql", "aws_s3"],
                base_risk_level=30
            ),
            JobProfile(
                id="communication",
                name="💬 Comunicación",
                description="Envío de mensajes, notificaciones, comunicación con usuarios",
                category="communication",
                characteristics={"network_intensive": True, "external_apis": True},
                default_rules=["rate_limit_messages", "business_hours", "approval_external"],
                typical_resources={"cpu": 20, "ram": 512, "network": True},
                base_permissions=["send_message", "read_contacts"],
                typical_apis=["telegram", "whatsapp", "slack", "email"],
                base_risk_level=40
            ),
            JobProfile(
                id="automation",
                name="🤖 Automatización",
                description="Automatización de tareas repetitivas y flujos de trabajo",
                category="automation",
                characteristics={"scheduled": True, "repetitive": True},
                default_rules=["approval_automation", "rate_limit_auto", "log_all"],
                typical_resources={"cpu": 40, "ram": 1024},
                base_permissions=["execute_automation", "schedule_tasks", "trigger_events"],
                typical_apis=["webhooks", "zapier", "make"],
                base_risk_level=60
            ),
            JobProfile(
                id="content_generation",
                name="✍️ Generación de Contenido",
                description="Creación de texto, imágenes, código u otros contenidos con IA",
                category="ai",
                characteristics={"ai_intensive": True, "creative": True},
                default_rules=["cost_limit_ai", "rate_limit_ai", "content_quality"],
                typical_resources={"cpu": 60, "ram": 2048, "api_calls": True},
                base_permissions=["use_ai_models", "generate_content", "publish_content"],
                typical_apis=["openai", "groq", "anthropic", "stability"],
                base_risk_level=45
            ),
            JobProfile(
                id="business_operation",
                name="🏢 Operación de Negocio",
                description="Operaciones CRM, facturación, soporte, gestión de clientes",
                category="business",
                characteristics={"critical": True, "sensitive_data": True},
                default_rules=["approval_critical", "audit_log", "backup_required", "business_hours_only"],
                typical_resources={"cpu": 30, "ram": 1024, "secure": True},
                base_permissions=["access_crm", "modify_invoices", "customer_support"],
                typical_apis=["salesforce", "quickbooks", "zendesk", "pipedrive"],
                base_risk_level=70
            ),
            JobProfile(
                id="system_maintenance",
                name="🔧 Mantenimiento de Sistema",
                description="Tareas de mantenimiento, backups, limpieza, actualizaciones",
                category="system",
                characteristics={"maintenance": True, "low_priority": True},
                default_rules=["maintenance_window", "notify_before", "rollback_ready"],
                typical_resources={"cpu": 50, "ram": 2048, "disk_io": True},
                base_permissions=["system_access", "backup_restore", "update_system"],
                base_risk_level=35
            ),
            JobProfile(
                id="integration",
                name="🔗 Integración",
                description="Conexión entre sistemas, sincronización de datos",
                category="integration",
                characteristics={"api_intensive": True, "data_mapping": True},
                default_rules=["rate_limit_api", "error_handling", "retry_policy"],
                typical_resources={"cpu": 40, "ram": 1024, "network": True},
                base_permissions=["api_access", "data_transform", "webhook_manage"],
                typical_apis=["rest_apis", "graphql", "webhooks"],
                base_risk_level=50
            ),
            JobProfile(
                id="external_api_usage",
                name="🌐 Uso de APIs Externas",
                description="Consumo de servicios de terceros, APIs cloud",
                category="external",
                characteristics={"external_dependent": True, "cost_variable": True},
                default_rules=["cost_monitoring", "rate_limit_external", "timeout_handling", "api_key_rotation"],
                typical_resources={"network": True, "api_calls": True},
                base_permissions=["external_api_call", "manage_api_keys"],
                base_risk_level=55
            ),
        ]
        
        for profile in profiles:
            self.job_profiles[profile.id] = profile
    
    def _init_default_rules(self):
        """Inicializar reglas por defecto universales"""
        rules = [
            UniversalRule(
                id="resource_limits",
                name="🖥️ Límites de Recursos",
                description="Limita uso de CPU, RAM y storage",
                type=RuleType.RESOURCE,
                category="system",
                config={"max_cpu_percent": 80, "max_ram_mb": 4096, "max_storage_mb": 10240},
                on_violation=RuleAction(type="block", message="Límites de recursos excedidos")
            ),
            UniversalRule(
                id="rate_limit_global",
                name="⏱️ Rate Limit Global",
                description="Límite general de operaciones por minuto",
                type=RuleType.RATE_LIMIT,
                category="performance",
                config={"max_calls_per_min": 60, "burst_allowance": 10},
                on_violation=RuleAction(type="warn", message="Rate limit alcanzado, esperando...")
            ),
            UniversalRule(
                id="business_hours",
                name="🕐 Horario Laboral",
                description="Restringe operaciones críticas a horario laboral",
                type=RuleType.TIME,
                category="time",
                applies_to=["business_operation", "critical_operations"],
                conditions=[RuleCondition("time.is_business_hours", ComparisonOp.EQ, True)],
                config={"start": "09:00", "end": "18:00", "timezone": "local", "weekends": False},
                on_violation=RuleAction(
                    type="approve", 
                    message="Fuera de horario laboral. ¿Desea continuar?",
                    notify_channels=["ui"],
                    escalation_delay=300
                )
            ),
            UniversalRule(
                id="approval_network",
                name="🌐 Aprobación de Red",
                description="Requiere aprobación para operaciones de red",
                type=RuleType.NETWORK,
                category="security",
                applies_to=["external_api_usage", "integration"],
                config={"require_approval": True, "whitelist_domains": []},
                on_violation=RuleAction(
                    type="approve",
                    message="Operación de red detectada. Requiere aprobación.",
                    notify_channels=["ui", "telegram"],
                    escalation_delay=600
                )
            ),
            UniversalRule(
                id="approval_critical",
                name="⚠️ Aprobación Crítica",
                description="Requiere aprobación para operaciones de alto riesgo",
                type=RuleType.APPROVAL,
                category="security",
                applies_to=["business_operation"],
                conditions=[RuleCondition("job.risk_level", ComparisonOp.GTE, 70)],
                config={"require_dual_approval": False},
                on_violation=RuleAction(
                    type="approve",
                    message="Operación de alto riesgo detectada. Requiere aprobación manual.",
                    notify_channels=["ui", "telegram", "email"],
                    escalation_delay=3600
                )
            ),
            UniversalRule(
                id="cost_limit",
                name="💰 Límite de Costo",
                description="Limita gasto en APIs y servicios externos",
                type=RuleType.COST,
                category="financial",
                applies_to=["external_api_usage", "content_generation"],
                config={"max_cost_per_day": 10.0, "max_cost_per_month": 200.0, "currency": "USD"},
                on_violation=RuleAction(
                    type="block",
                    message="Límite de costo excedido. Contacte administrador.",
                    notify_channels=["ui", "telegram"]
                )
            ),
            UniversalRule(
                id="data_privacy",
                name="🔒 Privacidad de Datos",
                description="Protege datos sensibles según normativa",
                type=RuleType.COMPLIANCE,
                category="compliance",
                applies_to=["data_processing", "business_operation"],
                conditions=[RuleCondition("data.has_pii", ComparisonOp.EQ, True)],
                config={"encryption_required": True, "retention_days": 365, "gdpr_compliant": True},
                on_violation=RuleAction(
                    type="block",
                    message="Violación de política de privacidad detectada"
                )
            ),
            UniversalRule(
                id="audit_all",
                name="📝 Auditoría Completa",
                description="Registra todas las operaciones para auditoría",
                type=RuleType.SECURITY,
                category="audit",
                config={"log_level": "detailed", "retention_days": 90},
                on_violation=RuleAction(type="log", message="Evento registrado")
            ),
        ]
        
        for rule in rules:
            self.rules[rule.id] = rule
    
    def _load_config(self):
        """Cargar configuración guardada"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cargar reglas personalizadas
                for rule_data in data.get('custom_rules', []):
                    rule = UniversalRule(**rule_data)
                    self.rules[rule.id] = rule
                
                # Cargar perfiles personalizados
                for profile_data in data.get('custom_profiles', []):
                    profile = JobProfile(**profile_data)
                    self.job_profiles[profile.id] = profile
                    
            except Exception as e:
                print(f"Error cargando políticas: {e}")
    
    def save_config(self):
        """Guardar configuración"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            data = {
                'custom_rules': [asdict(r) for r in self.rules.values() if not r.id.startswith('_default')],
                'custom_profiles': [asdict(p) for p in self.job_profiles.values() if not p.id.startswith('_default')],
                'updated_at': datetime.now().isoformat()
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error guardando políticas: {e}")
    
    def get_rules_for_job(self, job_type: str, job_context: Optional[Dict] = None) -> List[UniversalRule]:
        """
        Obtener todas las reglas aplicables a un tipo de trabajo
        """
        applicable_rules = []
        job_context = job_context or {}
        
        # Obtener perfil del trabajo
        profile = self.job_profiles.get(job_type)
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Verificar si aplica por tipo
            if rule.applies_to and job_type not in rule.applies_to:
                continue
            
            # Verificar condiciones específicas
            if rule.conditions:
                all_match = True
                for condition in rule.conditions:
                    if not self._evaluate_condition(condition, job_context):
                        all_match = False
                        break
                if not all_match:
                    continue
            
            applicable_rules.append(rule)
        
        # Ordenar por prioridad
        applicable_rules.sort(key=lambda r: r.priority)
        
        return applicable_rules
    
    def _evaluate_condition(self, condition: RuleCondition, context: Dict) -> bool:
        """Evaluar una condición contra el contexto"""
        # Obtener valor del campo (soporta notación punto: "job.risk_level")
        field_path = condition.field.split('.')
        value = context
        for key in field_path:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        
        # Realizar comparación
        op = condition.operator
        target = condition.value
        
        if op == ComparisonOp.EQ:
            return value == target
        elif op == ComparisonOp.NE:
            return value != target
        elif op == ComparisonOp.GT:
            return value is not None and value > target
        elif op == ComparisonOp.GTE:
            return value is not None and value >= target
        elif op == ComparisonOp.LT:
            return value is not None and value < target
        elif op == ComparisonOp.LTE:
            return value is not None and value <= target
        elif op == ComparisonOp.IN:
            return value in target if isinstance(target, (list, set, tuple)) else False
        elif op == ComparisonOp.NOT_IN:
            return value not in target if isinstance(target, (list, set, tuple)) else True
        elif op == ComparisonOp.CONTAINS:
            return target in value if isinstance(value, str) else False
        
        return False
    
    def evaluate_job(self, job_type: str, job_context: Dict) -> Dict[str, Any]:
        """
        Evaluar un trabajo contra todas las reglas aplicables
        """
        rules = self.get_rules_for_job(job_type, job_context)
        violations = []
        warnings = []
        required_approvals = []
        
        for rule in rules:
            result = self._evaluate_rule(rule, job_context)
            
            if result == "violation":
                violations.append(rule)
                if rule.on_violation:
                    if rule.on_violation.type == "approve":
                        required_approvals.append(rule)
            elif result == "warning":
                warnings.append(rule)
        
        return {
            "can_execute": len(violations) == 0 or all(r.on_violation.type != "block" for r in violations),
            "violations": violations,
            "warnings": warnings,
            "requires_approval": len(required_approvals) > 0,
            "approval_rules": required_approvals,
            "applicable_rules": rules
        }
    
    def _evaluate_rule(self, rule: UniversalRule, context: Dict) -> str:
        """Evaluar una regla individual"""
        # Implementar lógica específica por tipo de regla
        if rule.type == RuleType.RESOURCE:
            return self._check_resource_rule(rule, context)
        elif rule.type == RuleType.RATE_LIMIT:
            return self._check_rate_limit_rule(rule, context)
        elif rule.type == RuleType.TIME:
            return self._check_time_rule(rule, context)
        elif rule.type == RuleType.COST:
            return self._check_cost_rule(rule, context)
        elif rule.type == RuleType.APPROVAL:
            return "needs_approval"  # Siempre requiere aprobación si aplica
        
        return "ok"
    
    def _check_resource_rule(self, rule: UniversalRule, context: Dict) -> str:
        """Verificar límites de recursos"""
        resources = context.get('resources', {})
        config = rule.config
        
        if resources.get('cpu', 0) > config.get('max_cpu_percent', 100):
            return "violation"
        if resources.get('ram', 0) > config.get('max_ram_mb', float('inf')):
            return "violation"
        
        return "ok"
    
    def _check_rate_limit_rule(self, rule: UniversalRule, context: Dict) -> str:
        """Verificar rate limits"""
        calls = context.get('metrics', {}).get('calls_per_min', 0)
        limit = rule.config.get('max_calls_per_min', float('inf'))
        
        if calls > limit:
            return "violation"
        elif calls > limit * 0.8:  # 80% del límite
            return "warning"
        
        return "ok"
    
    def _check_time_rule(self, rule: UniversalRule, context: Dict) -> str:
        """Verificar restricciones de tiempo"""
        from datetime import datetime
        
        now = datetime.now()
        config = rule.config
        
        # Verificar si es horario laboral
        if config.get('business_hours_only', False):
            hour = now.hour
            start_hour = int(config.get('start', '09:00').split(':')[0])
            end_hour = int(config.get('end', '18:00').split(':')[0])
            
            if hour < start_hour or hour >= end_hour:
                return "needs_approval"
        
        return "ok"
    
    def _check_cost_rule(self, rule: UniversalRule, context: Dict) -> str:
        """Verificar límites de costo"""
        current_cost = context.get('metrics', {}).get('cost_today', 0)
        limit = rule.config.get('max_cost_per_day', float('inf'))
        
        if current_cost > limit:
            return "violation"
        elif current_cost > limit * 0.9:  # 90% del límite
            return "warning"
        
        return "ok"
    
    def create_custom_rule(self, rule: UniversalRule) -> bool:
        """Crear una regla personalizada"""
        try:
            self.rules[rule.id] = rule
            self.save_config()
            self._notify_subscribers()
            return True
        except Exception as e:
            print(f"Error creando regla: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Eliminar una regla"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            self.save_config()
            self._notify_subscribers()
            return True
        return False
    
    def subscribe(self, callback: Callable):
        """Suscribirse a cambios"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Desuscribirse"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self):
        """Notificar cambios"""
        for cb in self._subscribers:
            try:
                cb(self)
            except:
                pass


# Singleton
_policy_engine = None

def get_policy_engine() -> UniversalPolicyEngine:
    """Obtener instancia singleton"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = UniversalPolicyEngine()
    return _policy_engine
