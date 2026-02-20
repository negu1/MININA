"""
MININA v3.0 - AgentResourceManager (Capa 4)
Gestión de agentes y pools de recursos
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

from core.orchestrator.bus import bus, EventType, CortexEvent


class AgentType(Enum):
    CPU_INTENSIVE = "cpu_intensive"
    IO_INTENSIVE = "io_intensive"
    NETWORK = "network"
    GENERAL = "general"


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class Agent:
    """Agente ejecutor"""
    agent_id: str
    agent_type: AgentType
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class AgentPool:
    """Pool de agentes pre-calentados"""
    
    def __init__(self, agent_type: AgentType, max_size: int = 4):
        self.agent_type = agent_type
        self.max_size = max_size
        self.agents: List[Agent] = []
        self.queue: asyncio.Queue = asyncio.Queue()
        
    async def initialize(self):
        """Inicializar pool con agentes"""
        for i in range(self.max_size):
            agent = Agent(
                agent_id=f"{self.agent_type.value}_{i}",
                agent_type=self.agent_type
            )
            self.agents.append(agent)
    
    async def acquire(self) -> Optional[Agent]:
        """Adquirir agente del pool"""
        for agent in self.agents:
            if agent.status == AgentStatus.IDLE:
                agent.status = AgentStatus.BUSY
                agent.last_activity = datetime.now()
                return agent
        return None
    
    async def release(self, agent: Agent):
        """Liberar agente al pool"""
        agent.status = AgentStatus.IDLE
        agent.current_task = None
        agent.last_activity = datetime.now()


class AgentResourceManager:
    """
    Manager de Recursos - Capa 4
    Gestiona pools de agentes y asignación de tareas
    """
    
    def __init__(self):
        self.pools: Dict[AgentType, AgentPool] = {
            AgentType.CPU_INTENSIVE: AgentPool(AgentType.CPU_INTENSIVE, 4),
            AgentType.IO_INTENSIVE: AgentPool(AgentType.IO_INTENSIVE, 8),
            AgentType.NETWORK: AgentPool(AgentType.NETWORK, 10),
            AgentType.GENERAL: AgentPool(AgentType.GENERAL, 6),
        }
        self.active_executions: Dict[str, str] = {}  # execution_id -> agent_id
        
    async def initialize(self):
        """Inicializar todos los pools"""
        for pool in self.pools.values():
            await pool.initialize()
    
    def classify_skill(self, skill_metadata: Dict[str, Any]) -> AgentType:
        """Clasificar skill según perfil de recursos"""
        resource_profile = skill_metadata.get("resource_profile", "general")
        
        type_mapping = {
            "cpu_intensive": AgentType.CPU_INTENSIVE,
            "io_intensive": AgentType.IO_INTENSIVE,
            "network": AgentType.NETWORK,
            "general": AgentType.GENERAL
        }
        
        return type_mapping.get(resource_profile, AgentType.GENERAL)
    
    async def execute_skill(self, skill_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecutar skill en agente apropiado"""
        # Determinar tipo de agente
        agent_type = self.classify_skill(context.get("skill_metadata", {}))
        pool = self.pools[agent_type]
        
        # Adquirir agente
        agent = await pool.acquire()
        if not agent:
            return {"success": False, "error": "No agents available"}
        
        try:
            # Publicar inicio
            execution_id = f"exec_{asyncio.get_event_loop().time()}"
            self.active_executions[execution_id] = agent.agent_id
            agent.current_task = skill_id
            
            await bus.publish(CortexEvent(
                type=EventType.SKILL_STARTED,
                source="manager",
                payload={
                    "execution_id": execution_id,
                    "skill_id": skill_id,
                    "agent_id": agent.agent_id
                },
                timestamp=datetime.now(),
                event_id=f"evt_{execution_id}_start"
            ))
            
            # TODO: Ejecutar skill real aquí
            # Por ahora simulamos
            await asyncio.sleep(1)
            
            result = {
                "success": True,
                "execution_id": execution_id,
                "result": f"Executed {skill_id}"
            }
            
            await bus.publish(CortexEvent(
                type=EventType.SKILL_COMPLETED,
                source="manager",
                payload={
                    "execution_id": execution_id,
                    "skill_id": skill_id,
                    "result": result
                },
                timestamp=datetime.now(),
                event_id=f"evt_{execution_id}_complete"
            ))
            
            return result
            
        finally:
            # Liberar agente
            await pool.release(agent)
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
