"""
MININA v3.0 - AutoScaling
Escalado automático de recursos
"""

from typing import Dict, Any
import asyncio


class AutoScalingPolicy:
    """Política de auto-scaling"""
    
    def __init__(self):
        self.scale_up_threshold = 10  # tareas en cola
        self.scale_down_threshold = 2
        self.max_agents = 20
        self.min_agents = 2
        self.cooldown_seconds = 60
        
    def should_scale_up(self, metrics: Dict[str, Any]) -> bool:
        """Determinar si escalar hacia arriba"""
        queue_depth = metrics.get("queue_depth", 0)
        current_agents = metrics.get("total_agents", 0)
        
        return (
            queue_depth > self.scale_up_threshold and
            current_agents < self.max_agents
        )
        
    def should_scale_down(self, metrics: Dict[str, Any]) -> bool:
        """Determinar si escalar hacia abajo"""
        idle_agents = metrics.get("idle", 0)
        current_agents = metrics.get("total_agents", 0)
        
        return (
            idle_agents > self.scale_down_threshold and
            current_agents > self.min_agents
        )
        
    def calculate_scale_amount(self, metrics: Dict[str, Any]) -> int:
        """Calcular cuántos agentes escalar"""
        queue_depth = metrics.get("queue_depth", 0)
        return min(queue_depth // 5, 5)  # Máximo 5 agentes por vez
