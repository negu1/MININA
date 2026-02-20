"""
Test básico de la UI Local
"""

import sys
import unittest
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt5.QtWidgets import QApplication
from core.ui.main_window import MainWindow


class TestMainWindow(unittest.TestCase):
    """Tests de la ventana principal"""
    
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
    
    def test_window_creation(self):
        """Test creación de ventana"""
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertTrue(window.windowTitle().startswith("MININA v3.0"))

    def test_views_exist(self):
        """Test que las vistas existen"""
        window = MainWindow()
        self.assertIsNotNone(getattr(window, "content_area", None))
        self.assertTrue(hasattr(window, "nav_rail"))


class TestCortexBus(unittest.TestCase):
    """Tests del bus de eventos"""
    
    def test_typed_bus_adapter_publish_subscribe(self):
        """Test básico: el bus tipado (adapter) publica y entrega eventos."""
        from core.orchestrator.bus import bus, EventType, CortexEvent

        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.PLAN_CREATED, handler)

        async def run():
            await bus.publish(CortexEvent(type=EventType.PLAN_CREATED, source="test", payload={"ok": True}, timestamp=None, event_id=""))
            await asyncio.sleep(0.01)

        asyncio.run(run())
        self.assertGreaterEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
