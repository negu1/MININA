"""
MININA v3.0 - OrchestratorAgent (Capa 1) con Modo Planning y Ejecución
IA Orquestadora para descomposición de objetivos con dos modos de operación
SEGURIDAD: Integrado con Guardian y Recovery
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from datetime import datetime

from core.orchestrator.bus import bus, EventType, CortexEvent
from core.orchestrator.task_planner import TaskPlanner
from core.orchestrator.guardian import guardian, ActionType, RiskLevel
from core.orchestrator.recovery import recovery
from core.api_registry import get_api_registry
from core.api_notifications import get_notification_manager


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestratorMode(Enum):
    """Modos de operación del orquestador"""
    PLANNING = "planning"      # Modo asistente: solo conversa, aclara, planifica
    EXECUTION = "execution"    # Modo ejecución: ejecuta skills


@dataclass
class ExecutionPlan:
    """Plan de ejecución generado"""
    plan_id: str
    objective: str
    tasks: List[Dict[str, Any]]
    status: ExecutionStatus
    created_at: str
    context_questions: List[str] = field(default_factory=list)
    clarifications: Dict[str, str] = field(default_factory=dict)
    is_approved: bool = False


@dataclass
class PlanningResponse:
    """Respuesta del modo planning"""
    type: str  # 'question', 'plan_ready', 'clarification', 'suggestion'
    message: str
    plan: Optional[ExecutionPlan] = None
    questions: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class OrchestratorAgent:
    """
    Agente Orquestador - Capa 1 con dos modos:
    
    1. MODO PLANNING (Asistente):
       - NO ejecuta skills
       - Hace preguntas para entender qué quiere el usuario
       - Propone planes detallados
       - Espera aprobación explícita
       - Guía al usuario hasta que el plan esté claro
       - DESCUBRE skills relevantes para el objetivo
    
    2. MODO EJECUCIÓN:
       - Ejecuta el plan aprobado
       - Coordina skills por categorías
       - Entrega resultados
    """
    
    def __init__(self):
        self.planner = TaskPlanner()
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.mode: OrchestratorMode = OrchestratorMode.PLANNING  # Por defecto en planning
        self.current_conversation: List[Dict[str, str]] = []  # Historial de conversación planning
        self._skill_catalog: Dict[str, List[Dict]] = {}  # Catálogo de skills por categoría
        self._refresh_skill_catalog()
        
    def _refresh_skill_catalog(self):
        """Actualizar catálogo de skills organizado por categorías"""
        try:
            from core.SkillVault import vault
            result = vault.list_skills_by_category()
            if result.get("success"):
                self._skill_catalog = result.get("categories", {})
        except Exception as e:
            print(f"Error cargando catálogo de skills: {e}")
            
    def get_available_skills_by_category(self) -> Dict[str, List[str]]:
        """Obtener lista de skills disponibles organizadas por categoría"""
        self._refresh_skill_catalog()
        return {
            category: [skill.get("id", "") for skill in skills]
            for category, skills in self._skill_catalog.items()
        }
        
    def discover_skills_for_objective(self, objective: str) -> List[Dict]:
        """Descubrir skills relevantes para un objetivo"""
        try:
            from core.SkillVault import vault
            return vault.discover_skills_for_objective(objective)
        except Exception as e:
            print(f"Error descubriendo skills: {e}")
            return []
            
    def get_skill_info(self, skill_id: str) -> Dict:
        """Obtener información completa de una skill"""
        try:
            from core.SkillVault import vault
            return vault.get_skill_manifest(skill_id)
        except Exception as e:
            return {"id": skill_id, "name": skill_id, "category": "unknown"}
            
    async def chat_in_planning_mode(self, user_input: str, context: Optional[Dict] = None) -> PlanningResponse:
        """
        Modo PLANNING: Conversar con el usuario para entender su objetivo
        Sin ejecutar nada, solo aclarar y proponer planes
        SEGURIDAD: Valida input del usuario antes de procesar
        """
        # 0. VALIDAR INPUT DEL USUARIO (Seguridad)
        is_valid, validation_msg, risk_level = guardian.validate_user_input(user_input)
        if not is_valid:
            # Auditar intento de input peligroso
            guardian.audit_action(
                action=ActionType.ERROR_DETECTED,
                user_input=user_input,
                result=f"Input rechazado: {validation_msg}",
                risk_level=risk_level,
                details={"validation_error": validation_msg}
            )
            return PlanningResponse(
                type="error",
                message=f"⚠️ No puedo procesar esta solicitud: {validation_msg}",
                suggestions=["Reformula tu solicitud con lenguaje más específico y seguro"]
            )
        
        # Auditar acción del usuario
        guardian.audit_action(
            action=ActionType.PLAN_CREATED,
            user_input=user_input,
            result="Input validado, iniciando planning",
            risk_level=risk_level
        )
        
        # Guardar en historial
        self.current_conversation.append({"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()})
        
        # 1. Analizar intención y detectar si hay ambigüedad
        intent_analysis = await self._analyze_intent_deep(user_input)
        
        # 2. Si es ambiguo o poco claro, hacer preguntas
        if intent_analysis.get("needs_clarification", False):
            questions = self._generate_context_questions(intent_analysis)
            response = PlanningResponse(
                type="question",
                message="Necesito entender mejor qué quieres hacer. ¿Podrías aclararme lo siguiente?",
                questions=questions
            )
            self.current_conversation.append({"role": "assistant", "content": response.message, "timestamp": datetime.now().isoformat()})
            return response
        
        # 3. Si hay suficiente contexto, proponer un plan
        if intent_analysis.get("ready_for_planning", False):
            # Crear plan detallado
            plan = await self._create_detailed_plan(intent_analysis, context)
            
            # VALIDAR PLAN ANTES DE PRESENTARLO (Seguridad)
            is_plan_valid, plan_validation_msg = guardian.validate_plan_creation(plan.__dict__)
            if not is_plan_valid:
                guardian.audit_action(
                    action=ActionType.ERROR_DETECTED,
                    plan_id=plan.plan_id,
                    user_input=user_input,
                    result=f"Plan rechazado: {plan_validation_msg}",
                    risk_level=RiskLevel.HIGH,
                    details={"plan_validation_error": plan_validation_msg}
                )
                return PlanningResponse(
                    type="error",
                    message=f"⚠️ El plan generado no cumple con los criterios de seguridad: {plan_validation_msg}",
                    suggestions=["Intenta con un objetivo más específico o menos complejo"]
                )
            
            # Verificar límites de recursos
            resources_ok, resources_msg = guardian.check_resource_limits(plan.plan_id)
            if not resources_ok:
                return PlanningResponse(
                    type="error",
                    message=f"⚠️ {resources_msg}",
                    suggestions=["Espera a que terminen otros planes en ejecución"]
                )
            
            # Auditar plan creado
            guardian.audit_action(
                action=ActionType.PLAN_CREATED,
                plan_id=plan.plan_id,
                user_input=user_input,
                result=f"Plan creado con {len(plan.tasks)} tareas",
                risk_level=RiskLevel.LOW,
                details={"task_count": len(plan.tasks), "skills_required": list(set(t.get('required_skill', '') for t in plan.tasks))}
            )
            
            # Generar explicación del plan
            plan_explanation = self._explain_plan(plan)
            
            response = PlanningResponse(
                type="plan_ready",
                message=f"He preparado un plan para: **{plan.objective}**\n\n{plan_explanation}\n\n¿Estás de acuerdo con este plan? Cuando estés listo, dime **'ejecutar plan'** o presiona el botón de acción.",
                plan=plan,
                suggestions=["ejecutar plan", "modificar plan", "agregar paso", "quitar paso"]
            )
            
            self.active_plans[plan.plan_id] = plan
            self.current_conversation.append({"role": "assistant", "content": response.message, "timestamp": datetime.now().isoformat()})
            return response
        
        # 4. Si no está listo ni ambiguo, dar sugerencias
        suggestions = self._generate_suggestions(intent_analysis)
        response = PlanningResponse(
            type="suggestion",
            message=f"Entiendo que quieres: **{intent_analysis.get('objective', 'hacer algo')}**. ¿Podrías darme más detalles sobre:\n\n" + "\n".join([f"• {s}" for s in suggestions]),
            suggestions=suggestions
        )
        self.current_conversation.append({"role": "assistant", "content": response.message, "timestamp": datetime.now().isoformat()})
        return response
    
    async def process_objective(self, user_input: str, context: Optional[Dict] = None) -> ExecutionPlan:
        """
        Procesar un objetivo del usuario (modo ejecución directa)
        Este método se usa cuando ya estamos en modo ejecución
        """
        # 1. Analizar intención
        intent = await self._analyze_intent(user_input)
        
        # 2. Descomponer en tareas
        tasks = await self.planner.decompose(intent, context)
        
        # 3. Crear plan
        plan = ExecutionPlan(
            plan_id=f"plan_{asyncio.get_event_loop().time()}",
            objective=user_input,
            tasks=tasks,
            status=ExecutionStatus.PENDING,
            created_at=str(asyncio.get_event_loop().time())
        )
        
        # 4. Publicar evento
        await bus.publish(CortexEvent(
            type=EventType.PLAN_CREATED,
            source="orchestrator",
            payload={"plan_id": plan.plan_id, "tasks_count": len(tasks)},
            timestamp=None,
            event_id=""
        ))
        
        self.active_plans[plan.plan_id] = plan
        return plan
    
    async def switch_to_execution_mode(self, plan_id: str) -> bool:
        """
        Cambiar del modo planning al modo ejecución para un plan específico
        SEGURIDAD: Auditar transición y verificar límites
        """
        if plan_id not in self.active_plans:
            guardian.audit_action(
                action=ActionType.ERROR_DETECTED,
                plan_id=plan_id,
                result="Intento de aprobar plan inexistente",
                risk_level=RiskLevel.MEDIUM
            )
            return False
        
        plan = self.active_plans[plan_id]
        plan.is_approved = True
        plan.status = ExecutionStatus.RUNNING
        self.mode = OrchestratorMode.EXECUTION
        
        # Iniciar monitoreo del plan en Guardian
        guardian.start_plan(plan_id, {
            "objective": plan.objective,
            "task_count": len(plan.tasks),
            "skills": list(set(t.get('required_skill', '') for t in plan.tasks))
        })
        
        # Crear checkpoint inicial para rollback
        guardian.create_checkpoint(plan_id, 0, {"status": "started", "completed_tasks": []})
        
        # Auditar aprobación
        guardian.audit_action(
            action=ActionType.PLAN_APPROVED,
            plan_id=plan_id,
            result="Plan aprobado, pasando a modo ejecución",
            risk_level=RiskLevel.MEDIUM
        )
        
        # Publicar evento de cambio de modo
        await bus.publish(CortexEvent(
            type=EventType.PLAN_APPROVED,
            source="orchestrator",
            payload={"plan_id": plan_id, "mode": "execution"},
            timestamp=None,
            event_id=""
        ))
        
        return True
    
    async def _analyze_intent_deep(self, user_input: str) -> Dict[str, Any]:
        """
        Análisis profundo de intención para modo planning
        Detecta ambigüedad y necesidad de aclaración
        """
        objective_lower = user_input.lower()
        
        # Detectar si es vago o ambiguo
        vague_terms = ['algo', 'cosa', 'ayuda', 'hacer', 'tarea', 'trabajo']
        is_vague = any(term in objective_lower for term in vague_terms)
        
        # Detectar si tiene contexto suficiente
        has_context = len(user_input.split()) > 5
        
        # Detectar tipo de tarea
        task_types = {
            'email': ['email', 'correo', 'mail', 'gmail', 'outlook'],
            'file': ['archivo', 'file', 'documento', 'pdf', 'excel', 'csv'],
            'web': ['web', 'internet', 'descargar', 'buscar', 'navegar'],
            'automation': ['automático', 'automatic', 'script', 'programa', 'código'],
            'admin': ['administrar', 'gestionar', 'organizar', 'limpiar', 'configurar']
        }
        
        detected_type = "general"
        for task_type, keywords in task_types.items():
            if any(kw in objective_lower for kw in keywords):
                detected_type = task_type
                break
        
        return {
            "objective": user_input,
            "intent_type": detected_type,
            "priority": "normal",
            "needs_clarification": is_vague or not has_context,
            "ready_for_planning": has_context and not is_vague,
            "vagueness_score": 0.7 if is_vague else 0.2,
            "context_score": 0.8 if has_context else 0.3
        }
    
    def _generate_context_questions(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Generar preguntas para aclarar el contexto según el tipo de tarea"""
        task_type = intent_analysis.get("intent_type", "general")
        
        questions_by_type = {
            "email": [
                "¿Qué tipo de administración de email necesitas? (organizar, responder, enviar, limpiar)",
                "¿Qué cuenta de email usas? (Gmail, Outlook, etc.)",
                "¿Hay algún criterio específico para organizar los emails? (remitente, fecha, asunto)"
            ],
            "file": [
                "¿Qué tipo de archivo necesitas trabajar? (PDF, Excel, Word, imágenes)",
                "¿Dónde están ubicados los archivos? (carpeta específica, descargas, escritorio)",
                "¿Qué operación quieres hacer? (organizar, renombrar, convertir, analizar)"
            ],
            "web": [
                "¿Qué sitio web necesitas visitar o qué información buscas?",
                "¿Necesitas descargar algo específico o solo obtener información?",
                "¿Hay algún login o credencial necesaria para acceder?"
            ],
            "automation": [
                "¿Qué proceso específico quieres automatizar?",
                "¿Con qué frecuencia necesitas que se ejecute esta automatización?",
                "¿Hay algún archivo de configuración o template que deba usar?"
            ],
            "admin": [
                "¿Qué sistema o área necesitas administrar?",
                "¿Cuál es el objetivo final de esta administración? (organizar, limpiar, reportar)",
                "¿Hay algún criterio específico que deba seguir?"
            ]
        }
        
        return questions_by_type.get(task_type, [
            "¿Podrías describir con más detalle qué quieres lograr?",
            "¿Cuál es el resultado esperado al finalizar esta tarea?",
            "¿Hay algún paso específico que ya tengas en mente?"
        ])
    
    def _generate_suggestions(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Generar sugerencias para guiar al usuario"""
        task_type = intent_analysis.get("intent_type", "general")
        
        suggestions_by_type = {
            "email": [
                "Especificar qué tipo de acción (organizar, enviar, responder, limpiar)",
                "Mencionar el proveedor de email (Gmail, Outlook, Yahoo)",
                "Definir criterios de organización (remitentes, fechas, etiquetas)"
            ],
            "file": [
                "Especificar el tipo de archivo (PDF, Excel, imágenes, etc.)",
                "Indicar la ubicación de los archivos",
                "Mencionar la operación deseada (organizar, renombrar, convertir)"
            ],
            "web": [
                "Proporcionar la URL del sitio web",
                "Especificar qué información o archivos necesitas",
                "Indicar si requiere login o credenciales"
            ],
            "automation": [
                "Describir el paso a paso manual actual",
                "Especificar los archivos de entrada y salida",
                "Indicar la frecuencia de ejecución deseada"
            ],
            "admin": [
                "Definir el alcance de la administración",
                "Especificar los criterios de organización",
                "Mencionar cualquier restricción o preferencia"
            ]
        }
        
        return suggestions_by_type.get(task_type, [
            "Describe el objetivo final que quieres lograr",
            "Menciona cualquier paso específico que ya tengas en mente",
            "Indica si hay alguna restricción o preferencia especial"
        ])
    
    async def _create_detailed_plan(self, intent_analysis: Dict[str, Any], context: Optional[Dict] = None) -> ExecutionPlan:
        """Crear un plan detallado basado en el análisis de intención"""
        
        # 1. VERIFICAR APIs REQUERIDAS ANTES DE CREAR EL PLAN
        objective = intent_analysis.get("objective", "")
        registry = get_api_registry()
        missing_apis = registry.check_api_for_intent(objective)
        
        if missing_apis:
            # Notificar al usuario sobre APIs faltantes
            notifier = get_notification_manager()
            await notifier.notify_missing_apis(missing_apis, f"Crear plan para: {objective}")
            
            # Crear plan con advertencia
            plan = ExecutionPlan(
                plan_id=f"plan_{asyncio.get_event_loop().time()}",
                objective=objective,
                tasks=[{
                    "name": "api_configuration_required",
                    "description": f"Configurar APIs requeridas: {', '.join([api.name for api in missing_apis])}",
                    "required_skill": "api_setup",
                    "step_number": 1,
                    "step_description": "Paso 1: Configurar APIs necesarias",
                    "user_friendly_name": "⚠️ Configuración de APIs requerida",
                    "expected_outcome": "APIs configuradas correctamente",
                    "missing_apis": [api.id for api in missing_apis]
                }],
                status=ExecutionStatus.PENDING,
                created_at=datetime.now().isoformat(),
                is_approved=False,
                context_questions=[
                    f"Las siguientes APIs no están configuradas: {', '.join([api.name for api in missing_apis])}",
                    "Por favor, configúralas en Settings > APIs antes de continuar"
                ]
            )
            return plan
        
        # 2. Crear plan normal si todas las APIs están disponibles
        tasks = await self.planner.decompose(intent_analysis, context)
        
        # Enriquecer tareas con más detalle
        enriched_tasks = []
        for i, task in enumerate(tasks, 1):
            enriched_task = {
                **task,
                "step_number": i,
                "step_description": f"Paso {i}: {task.get('description', 'Tarea')}",
                "user_friendly_name": self._make_user_friendly(task.get('name', f'Tarea {i}')),
                "expected_outcome": self._generate_expected_outcome(task)
            }
            enriched_tasks.append(enriched_task)
        
        plan = ExecutionPlan(
            plan_id=f"plan_{asyncio.get_event_loop().time()}",
            objective=intent_analysis.get("objective", "Objetivo del usuario"),
            tasks=enriched_tasks,
            status=ExecutionStatus.PENDING,
            created_at=datetime.now().isoformat(),
            is_approved=False
        )
        
        return plan
    
    def _explain_plan(self, plan: ExecutionPlan) -> str:
        """Generar una explicación amigable del plan"""
        explanation = f"📋 **Plan de ejecución:**\n\n"
        explanation += f"🎯 **Objetivo:** {plan.objective}\n\n"
        explanation += "📝 **Pasos a seguir:**\n\n"
        
        for task in plan.tasks:
            step_num = task.get('step_number', '?')
            name = task.get('user_friendly_name', task.get('name', 'Paso'))
            desc = task.get('description', '')
            skill = task.get('required_skill', 'skill')
            outcome = task.get('expected_outcome', '')
            
            explanation += f"**{step_num}.** {name}\n"
            explanation += f"   📝 {desc}\n"
            explanation += f"   🤖 Skill: `{skill}`\n"
            if outcome:
                explanation += f"   ✅ Resultado: {outcome}\n"
            explanation += "\n"
        
        total_steps = len(plan.tasks)
        explanation += f"📊 **Total:** {total_steps} paso{'s' if total_steps > 1 else ''}\n\n"
        explanation += "💡 Una vez aprobado, ejecutaré estos pasos automáticamente."
        
        return explanation
    
    def _make_user_friendly(self, task_name: str) -> str:
        """Convertir nombres técnicos a nombres amigables"""
        friendly_names = {
            "analysis": "Análisis del contexto",
            "analyzer": "Análisis de requisitos",
            "execution": "Ejecución de la tarea",
            "executor": "Procesamiento principal",
            "validation": "Validación de resultados",
            "report": "Generación de reporte",
            "download": "Descarga de archivos",
            "upload": "Carga de información",
            "organize": "Organización de archivos",
            "clean": "Limpieza de datos"
        }
        return friendly_names.get(task_name.lower(), task_name)
    
    def _generate_expected_outcome(self, task: Dict[str, Any]) -> str:
        """Generar descripción del resultado esperado de una tarea"""
        skill = task.get('required_skill', '').lower()
        name = task.get('name', '').lower()
        
        if 'anal' in skill or 'anal' in name:
            return "Entenderemos exactamente qué necesitas y cómo hacerlo"
        elif 'download' in skill or 'download' in name:
            return "Archivos descargados en la ubicación especificada"
        elif 'organize' in skill or 'organize' in name:
            return "Archivos organizados según los criterios definidos"
        elif 'report' in skill or 'report' in name:
            return "Reporte generado con toda la información requerida"
        elif 'email' in skill or 'mail' in name:
            return "Emails procesados según las instrucciones"
        elif 'execute' in skill or 'process' in name:
            return "Tarea principal completada con éxito"
        else:
            return "Resultado esperado obtenido"
    
    async def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Analizar la intención del usuario (versión simple para ejecución)"""
        return {
            "objective": user_input,
            "intent_type": "automation",
            "priority": "normal"
        }
    
    async def approve_plan(self, plan_id: str) -> bool:
        """Aprobar un plan para ejecución"""
        return await self.switch_to_execution_mode(plan_id)
    
    def reset_conversation(self):
        """Resetear la conversación de planning"""
        self.current_conversation = []
        self.mode = OrchestratorMode.PLANNING
        
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Obtener historial de conversación"""
        return self.current_conversation.copy()
