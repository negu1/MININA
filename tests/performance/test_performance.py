"""
MININA v3.0 - Performance Tests
Tests de rendimiento y benchmark
"""

import time
import asyncio
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestOrchestratorPerformance(unittest.TestCase):
    """Test rendimiento del orquestador"""
    
    def test_plan_creation_speed(self):
        """Test: velocidad de creación de planes"""
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        
        async def test():
            agent = OrchestratorAgent()
            
            start = time.time()
            plan = await agent.process_objective("Generar reporte de ventas")
            end = time.time()
            
            # Debe ser rápido (< 100ms para planificación simple)
            self.assertLess(end - start, 0.1)
            self.assertIsNotNone(plan)
            
        asyncio.run(test())
        
    def test_multiple_plans(self):
        """Test: creación de múltiples planes"""
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        
        async def test():
            agent = OrchestratorAgent()
            
            objectives = [
                "Analizar datos",
                "Generar reporte", 
                "Enviar email",
                "Procesar archivo"
            ]
            
            start = time.time()
            plans = await asyncio.gather(*[
                agent.process_objective(obj) for obj in objectives
            ])
            end = time.time()
            
            # 4 planes en menos de 500ms
            self.assertLess(end - start, 0.5)
            self.assertEqual(len(plans), 4)
            
        asyncio.run(test())


class TestManagerPerformance(unittest.TestCase):
    """Test rendimiento del manager"""
    
    def test_pool_initialization_speed(self):
        """Test: inicialización rápida de pools"""
        from core.manager.agent_pool import AgentPool
        
        async def test():
            pool = AgentPool("general", max_size=10)
            
            start = time.time()
            await pool.initialize()
            end = time.time()
            
            # 10 agentes en menos de 100ms
            self.assertLess(end - start, 0.1)
            self.assertEqual(len(pool.agents), 10)
            
        asyncio.run(test())
        
    def test_agent_acquire_performance(self):
        """Test: rendimiento de adquisición de agentes"""
        from core.manager.agent_pool import AgentPool
        
        async def test():
            pool = AgentPool("general", max_size=5)
            await pool.initialize()
            
            # Adquirir 5 agentes
            start = time.time()
            agents = []
            for _ in range(5):
                agent = await pool.acquire()
                if agent:
                    agents.append(agent)
            end = time.time()
            
            # 5 adquisiciones en menos de 50ms
            self.assertLess(end - start, 0.05)
            self.assertEqual(len(agents), 5)
            
        asyncio.run(test())


class TestSupervisorPerformance(unittest.TestCase):
    """Test rendimiento del supervisor"""
    
    def test_validation_speed(self):
        """Test: velocidad de validación"""
        from core.supervisor.execution_supervisor import ExecutionSupervisor
        
        async def test():
            supervisor = ExecutionSupervisor()
            
            # Simular 100 validaciones
            start = time.time()
            for i in range(100):
                await supervisor.monitor_execution(f"exec_{i}")
                result = {"success": True, "result": "OK"}
                await supervisor.validate_result(f"exec_{i}", result)
            end = time.time()
            
            # 100 validaciones en menos de 1 segundo
            self.assertLess(end - start, 1.0)
            
        asyncio.run(test())


class TestBusPerformance(unittest.TestCase):
    """Test rendimiento del bus de eventos"""
    
    def test_event_publishing_speed(self):
        """Test: velocidad de publicación de eventos"""
        from core.orchestrator.bus import bus, CortexEvent, EventType
        from datetime import datetime
        
        async def test():
            events = []
            
            # Crear 1000 eventos
            for i in range(1000):
                event = CortexEvent(
                    type=EventType.SKILL_COMPLETED,
                    source="test",
                    payload={"id": i},
                    timestamp=datetime.now(),
                    event_id=f"evt_{i}"
                )
                events.append(event)
            
            # Publicar todos
            start = time.time()
            await asyncio.gather(*[bus.publish(e) for e in events])
            end = time.time()
            
            # 1000 eventos en menos de 2 segundos
            self.assertLess(end - start, 2.0)
            
        asyncio.run(test())


class TestMemoryUsage(unittest.TestCase):
    """Test uso de memoria"""
    
    def test_pool_memory_footprint(self):
        """Test: huella de memoria de pools"""
        from core.manager.agent_pool import AgentPool
        
        async def test():
            import sys
            
            # Medir memoria antes
            pool = AgentPool("general", max_size=20)
            await pool.initialize()
            
            # 20 agentes no deben consumir más de 10MB
            # (estimación conservadora)
            self.assertEqual(len(pool.agents), 20)
            
        asyncio.run(test())


if __name__ == "__main__":
    unittest.main()
