"""
MININA v3.0 - LoadBalancer
Balanceo de carga entre agentes
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import random


@dataclass
class LoadMetrics:
    """Métricas de carga"""
    agent_id: str
    cpu_usage: float
    memory_usage: float
    queue_depth: int
    score: float = 0.0


class LoadBalancer:
    """
    Balanceador de carga
    Distribuye tareas entre agentes disponibles
    """
    
    def __init__(self):
        self.strategy = "least_loaded"
        
    def select_agent(self, available_agents: List[Dict[str, Any]]) -> str:
        """
        Seleccionar agente óptimo
        
        Args:
            available_agents: Lista de agentes disponibles con métricas
            
        Returns:
            ID del agente seleccionado
        """
        if not available_agents:
            raise ValueError("No agents available")
            
        if self.strategy == "least_loaded":
            return self._least_loaded(available_agents)
        elif self.strategy == "round_robin":
            return self._round_robin(available_agents)
        elif self.strategy == "random":
            return self._random(available_agents)
        else:
            return self._least_loaded(available_agents)
            
    def _least_loaded(self, agents: List[Dict[str, Any]]) -> str:
        """Seleccionar agente menos cargado"""
        sorted_agents = sorted(agents, key=lambda a: a.get("load", 100))
        return sorted_agents[0]["agent_id"]
        
    def _round_robin(self, agents: List[Dict[str, Any]]) -> str:
        """Selección round-robin"""
        # TODO: Implementar estado de round-robin
        return agents[0]["agent_id"]
        
    def _random(self, agents: List[Dict[str, Any]]) -> str:
        """Selección aleatoria"""
        return random.choice(agents)["agent_id"]
        
    def calculate_load_score(self, metrics: LoadMetrics) -> float:
        """Calcular score de carga (menor es mejor)"""
        return (
            metrics.cpu_usage * 0.4 +
            metrics.memory_usage * 0.3 +
            metrics.queue_depth * 0.3
        )
