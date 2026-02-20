"""
Test de integración de las 4 capas
"""

import asyncio
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.orchestrator.orchestrator_agent import OrchestratorAgent
from core.orchestrator.task_planner import TaskPlanner
from core.supervisor.execution_supervisor import ExecutionSupervisor, ValidationResult
from core.manager.agent_resource_manager import AgentResourceManager
from core.controller.policy_controller import PolicyController, RuleResult


class TestIntegration(unittest.TestCase):
    """Tests de integración de las 4 capas"""
    
    def test_orchestrator_creates_plan(self):
        """Test que el orquestador crea planes"""
        agent = OrchestratorAgent()
        
        async def test():
            plan = await agent.process_objective("Generar reporte de ventas")
            self.assertIsNotNone(plan)
            self.assertEqual(plan.objective, "Generar reporte de ventas")
            self.assertGreater(len(plan.tasks), 0)
        
        asyncio.run(test())
    
    def test_supervisor_validates(self):
        """Test que el supervisor valida resultados"""
        supervisor = ExecutionSupervisor()
        
        async def test():
            execution_id = "test_001"
            await supervisor.monitor_execution(execution_id)
            
            result = await supervisor.validate_result(
                execution_id,
                {"success": True, "result": "OK", "generated_files": []}
            )
            self.assertEqual(result, ValidationResult.SUCCESS)
        
        asyncio.run(test())
    
    def test_controller_allows_execution(self):
        """Test que el controlador permite ejecuciones"""
        controller = PolicyController()
        
        async def test():
            result = await controller.check_execution_allowed(
                "skill_test", "user_001", {}
            )
            self.assertEqual(result, RuleResult.ALLOW)
        
        asyncio.run(test())
    
    def test_manager_initializes(self):
        """Test que el manager inicializa correctamente"""
        manager = AgentResourceManager()
        
        async def test():
            await manager.initialize()
            self.assertEqual(len(manager.pools), 4)
        
        asyncio.run(test())


if __name__ == "__main__":
    unittest.main()
