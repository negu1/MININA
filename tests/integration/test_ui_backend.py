"""
Test de integración UI-Backend
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestAPIClient(unittest.TestCase):
    """Tests del cliente API"""
    
    def test_client_creation(self):
        """Test creación del cliente - ahora modo standalone"""
        from core.ui.api_client import MININAApiClient
        client = MININAApiClient()
        self.assertEqual(client.base_url, "local")
        
    def test_health_check_standalone(self):
        """Test health check en modo standalone - siempre True si managers disponibles"""
        from core.ui.api_client import MININAApiClient
        client = MININAApiClient()
        result = client.health_check()
        self.assertTrue(result)  # En standalone, verifica que managers estén disponibles


class TestViewsIntegration(unittest.TestCase):
    """Tests de integración de vistas"""
    
    def test_works_view_import(self):
        """Test import de WorksView"""
        from core.ui.views.works_view import WorksView
        from core.file_manager import works_manager
        self.assertIsNotNone(WorksView)
        self.assertIsNotNone(works_manager)
        
    def test_orchestrator_view_import(self):
        """Test import de OrchestratorView"""
        from core.ui.views.orchestrator_view import OrchestratorView
        from core.orchestrator.orchestrator_agent import OrchestratorAgent
        self.assertIsNotNone(OrchestratorView)
        self.assertIsNotNone(OrchestratorAgent)


if __name__ == "__main__":
    unittest.main()
