"""
MININA v3.0 - OrchestratorAgent (Capa 1)
IA Orquestadora para descomposición de objetivos
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

from core.orchestrator.bus import bus, EventType, CortexEvent
from core.orchestrator.task_planner import TaskPlanner


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionPlan:
    """Plan de ejecución generado"""
    plan_id: str
    objective: str
    tasks: List[Dict[str, Any]]
    status: ExecutionStatus
    created_at: str


class OrchestratorAgent:
    """
    Agente Orquestador - Capa 1
    Recibe objetivos en lenguaje natural y los descompone en tareas ejecutables
    """
    
    def __init__(self):
        self.planner = TaskPlanner()
        self.active_plans: Dict[str, ExecutionPlan] = {}
        
    async def process_objective(self, user_input: str, context: Optional[Dict] = None) -> ExecutionPlan:
        """
        Procesar un objetivo del usuario
        
        Args:
            user_input: Objetivo en lenguaje natural
            context: Contexto adicional (opcional)
            
        Returns:
            ExecutionPlan: Plan de ejecución generado
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
    
    async def _analyze_intent(self, user_input: str) -> Dict[str, Any]:
        """Analizar la intención del usuario"""
        # TODO: Integrar con LLMManager para análisis real
        return {
            "objective": user_input,
            "intent_type": "automation",
            "priority": "normal"
        }
    
    async def approve_plan(self, plan_id: str) -> bool:
        """Aprobar un plan para ejecución"""
        if plan_id not in self.active_plans:
            return False
            
        plan = self.active_plans[plan_id]
        plan.status = ExecutionStatus.RUNNING
        
        # Publicar evento de aprobación
        await bus.publish(CortexEvent(
            type=EventType.PLAN_APPROVED,
            source="orchestrator",
            payload={"plan_id": plan_id},
            timestamp=None,
            event_id=""
        ))
        
        return True
