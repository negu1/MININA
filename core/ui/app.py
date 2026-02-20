"""
MININA v3.0 - Sistema Operativo de Automatización Inteligente
Entry point de la aplicación UI Local
"""

import sys
import asyncio
from pathlib import Path

# Añadir root al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.ui.main_window import MainWindow


def main():
    """Punto de entrada principal de MININA v3.0"""
    
    # Configurar aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("MININA")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("MININA")
    
    # Configurar estilo y tema
    app.setStyle("Fusion")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
