"""
MININA v3.0 - AgentPool
Gestión de pools de agentes
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    CLEANING = "cleaning"


@dataclass
class Agent:
    """Agente ejecutor de skills"""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_skill: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    total_executions: int = 0
    

class AgentPool:
    """
    Pool de agentes pre-calentados
    Gestiona la creación, asignación y liberación de agentes
    """
    
    def __init__(self, agent_type: str, max_size: int = 4):
        self.agent_type = agent_type
        self.max_size = max_size
        self.agents: List[Agent] = []
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Inicializar pool con agentes"""
        for i in range(self.max_size):
            agent = Agent(
                agent_id=f"{self.agent_type}_{i}",
                agent_type=self.agent_type
            )
            self.agents.append(agent)
            
    async def acquire(self) -> Optional[Agent]:
        """Adquirir agente disponible"""
        async with self._lock:
            for agent in self.agents:
                if agent.status == AgentStatus.IDLE:
                    agent.status = AgentStatus.BUSY
                    agent.last_used = datetime.now()
                    return agent
            return None
            
    async def release(self, agent: Agent):
        """Liberar agente de vuelta al pool"""
        async with self._lock:
            agent.status = AgentStatus.IDLE
            agent.current_skill = None
            agent.last_used = datetime.now()
            
    async def scale_up(self, count: int):
        """Escalar pool agregando agentes"""
        async with self._lock:
            current_count = len(self.agents)
            for i in range(count):
                agent = Agent(
                    agent_id=f"{self.agent_type}_{current_count + i}",
                    agent_type=self.agent_type
                )
                self.agents.append(agent)
                
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del pool"""
        idle = sum(1 for a in self.agents if a.status == AgentStatus.IDLE)
        busy = sum(1 for a in self.agents if a.status == AgentStatus.BUSY)
        
        return {
            "total_agents": len(self.agents),
            "idle": idle,
            "busy": busy,
            "utilization": busy / len(self.agents) if self.agents else 0
        }
