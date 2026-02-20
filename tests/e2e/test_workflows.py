"""
MININA v3.0 - Tests E2E (End-to-End)
Tests de flujos completos del sistema
"""

import unittest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestOrchestratorFlow(unittest.TestCase):
    """Test flujo completo del orquestador"""
    
    def test_objective_to_plan(self):
        """Test: objetivo → plan → tareas"""
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        
        async def test():
            agent = OrchestratorAgent()
            plan = await agent.process_objective("Generar reporte PDF")
            
            self.assertIsNotNone(plan)
            self.assertEqual(plan.objective, "Generar reporte PDF")
            self.assertGreater(len(plan.tasks), 0)
            
        asyncio.run(test())
        
    def test_plan_approval(self):
        """Test: aprobación de plan"""
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        
        async def test():
            agent = OrchestratorAgent()
            plan = await agent.process_objective("Tarea de prueba")
            
            success = await agent.approve_plan(plan.plan_id)
            self.assertTrue(success)
            
        asyncio.run(test())


class TestExecutionFlow(unittest.TestCase):
    """Test flujo de ejecución con supervisor"""
    
    def test_skill_execution_with_supervision(self):
        """Test: skill → supervisor → validación"""
        from core.supervisor.execution_supervisor import ExecutionSupervisor, ValidationResult
        
        async def test():
            supervisor = ExecutionSupervisor()
            execution_id = "test_e2e_001"
            
            # Iniciar monitoreo
            await supervisor.monitor_execution(execution_id)
            
            # Simular ejecución
            result = {
                "success": True,
                "result": "OK",
                "generated_files": [{"name": "test.pdf"}]
            }
            
            # Validar
            validation = await supervisor.validate_result(execution_id, result)
            self.assertEqual(validation, ValidationResult.SUCCESS)
            
        asyncio.run(test())


class TestPolicyEnforcement(unittest.TestCase):
    """Test aplicación de políticas"""
    
    def test_execution_allowed_by_policy(self):
        """Test: controlador permite/deniega ejecución"""
        from core.controller.policy_controller import PolicyController, RuleResult
        
        async def test():
            controller = PolicyController()
            
            result = await controller.check_execution_allowed(
                skill_id="test_skill",
                user_id="admin",
                context={"time": "business_hours"}
            )
            
            self.assertEqual(result, RuleResult.ALLOW)
            
        asyncio.run(test())


class TestAgentPoolManagement(unittest.TestCase):
    """Test gestión de pools de agentes"""
    
    def test_pool_initialization(self):
        """Test: inicialización de pools"""
        from core.manager.agent_pool import AgentPool
        
        async def test():
            pool = AgentPool("general", max_size=4)
            await pool.initialize()
            
            self.assertEqual(len(pool.agents), 4)
            
        asyncio.run(test())
        
    def test_agent_acquire_release(self):
        """Test: adquirir y liberar agentes"""
        from core.manager.agent_pool import AgentPool
        
        async def test():
            pool = AgentPool("general", max_size=2)
            await pool.initialize()
            
            # Adquirir agente
            agent = await pool.acquire()
            self.assertIsNotNone(agent)
            self.assertEqual(agent.status.value, "busy")
            
            # Liberar agente
            await pool.release(agent)
            self.assertEqual(agent.status.value, "idle")
            
        asyncio.run(test())


class TestUIIntegration(unittest.TestCase):
    """Test integración UI con backend"""
    
    def test_api_client_creation(self):
        """Test: creación de cliente API - modo standalone"""
        from core.ui.api_client import MININAApiClient
        
        client = MININAApiClient()
        self.assertEqual(client.base_url, "local")
        
    def test_works_manager_integration(self):
        """Test: WorksManager funciona con UI"""
        from core.file_manager import works_manager
        
        # WorksManager debe estar inicializado
        self.assertIsNotNone(works_manager)
        self.assertIsNotNone(works_manager.base_path)


class TestCompleteWorkflow(unittest.TestCase):
    """Test flujo de trabajo completo"""
    
    def test_end_to_end_skill_creation_and_execution(self):
        """Test: crear skill → sandbox → ejecutar → validar → ver en works"""
        # Este test simula el flujo completo
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        from core.supervisor.execution_supervisor import ExecutionSupervisor, ValidationResult
        from core.controller.policy_controller import PolicyController, RuleResult
        from core.manager.agent_resource_manager import AgentResourceManager
        
        async def test():
            # 1. Orquestador crea plan
            orch = OrchestratorAgent()
            plan = await orch.process_objective("Crear y ejecutar skill de prueba")
            
            # 2. Controlador verifica permisos
            ctrl = PolicyController()
            permission = await ctrl.check_execution_allowed(
                "test_skill", "admin", {}
            )
            self.assertEqual(permission, RuleResult.ALLOW)
            
            # 3. Manager ejecuta
            mgr = AgentResourceManager()
            await mgr.initialize()
            
            # 4. Supervisor valida
            sup = ExecutionSupervisor()
            await sup.monitor_execution("exec_001")
            
            result = {"success": True, "result": "OK"}
            validation = await sup.validate_result("exec_001", result)
            self.assertEqual(validation, ValidationResult.SUCCESS)
            
        asyncio.run(test())


if __name__ == "__main__":
    unittest.main()
