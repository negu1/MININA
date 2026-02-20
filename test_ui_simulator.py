"""
MININA v3.0 - Simulador de Pruebas Exhaustivas de UI
Este script simula la interacción con todas las vistas para detectar fallos
"""

import sys
import traceback
from typing import List, Dict, Any, Tuple
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_simulation.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('UI_Simulator')

class TestResult:
    """Resultado de una prueba"""
    def __init__(self, name: str, passed: bool, error: str = None, details: str = None):
        self.name = name
        self.passed = passed
        self.error = error
        self.details = details
    
    def __str__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        result = f"{status}: {self.name}"
        if self.error:
            result += f"\n   Error: {self.error}"
        if self.details:
            result += f"\n   Details: {self.details}"
        return result

class MININAUISimulator:
    """Simulador de pruebas de UI"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.warnings: List[str] = []
        
    def run_all_tests(self):
        """Ejecutar todas las pruebas"""
        logger.info("=" * 80)
        logger.info("INICIANDO PRUEBAS EXHAUSTIVAS DE MININA UI v3.0")
        logger.info("=" * 80)
        
        # 1. Verificar imports
        self.test_imports()
        
        # 2. Probar creación de vistas
        self.test_view_instantiation()
        
        # 3. Verificar métodos de manuales
        self.test_help_manuals()
        
        # 4. Probar api_client
        self.test_api_client()
        
        # 5. Verificar conexiones backend
        self.test_backend_connections()
        
        # 6. Probar flujo Orquestador
        self.test_orchestrator_flow()
        
        # 7. Verificar Skill Studio
        self.test_skill_studio()
        
        # 8. Probar Works/Archivos
        self.test_works_view()
        
        # 9. Verificar Manager View
        self.test_manager_view()
        
        # 10. Probar Configuración
        self.test_settings_view()
        
        # Generar reporte
        self.generate_report()
        
    def test_imports(self):
        """Test 1: Verificar todos los imports"""
        logger.info("\n[Test 1] Verificando imports de vistas...")
        
        views_to_test = [
            ('core.ui.views.orchestrator_view', 'OrchestratorView'),
            ('core.ui.views.supervisor_view', 'SupervisorView'),
            ('core.ui.views.controller_view', 'ControllerView'),
            ('core.ui.views.manager_view', 'ManagerView'),
            ('core.ui.views.works_view', 'WorksView'),
            ('core.ui.views.skills_view', 'SkillsView'),
            ('core.ui.views.settings_view', 'SettingsView'),
            ('core.ui.api_client', 'MININAApiClient'),
            ('core.ui.main_window', 'MainWindow'),
        ]
        
        for module_name, class_name in views_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                self.results.append(TestResult(
                    f"Import {module_name}.{class_name}",
                    True,
                    details=f"Clase {class_name} cargada correctamente"
                ))
            except Exception as e:
                self.results.append(TestResult(
                    f"Import {module_name}.{class_name}",
                    False,
                    error=str(e),
                    details=traceback.format_exc()
                ))
                
    def test_view_instantiation(self):
        """Test 2: Probar creación de instancias"""
        logger.info("\n[Test 2] Probando creación de vistas...")
        
        # Nota: No podemos crear QWidgets sin QApplication, 
        # pero verificamos que las clases existen
        views = [
            ('core.ui.views.orchestrator_view', 'OrchestratorView'),
            ('core.ui.views.supervisor_view', 'SupervisorView'),
            ('core.ui.views.controller_view', 'ControllerView'),
            ('core.ui.views.manager_view', 'ManagerView'),
            ('core.ui.views.works_view', 'WorksView'),
            ('core.ui.views.skills_view', 'SkillsView'),
            ('core.ui.views.settings_view', 'SettingsView'),
        ]
        
        for module_name, class_name in views:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                
                # Verificar que tiene métodos esperados
                required_methods = ['_setup_ui']
                missing = [m for m in required_methods if not hasattr(cls, m)]
                
                if missing:
                    self.results.append(TestResult(
                        f"Vista {class_name} - métodos",
                        False,
                        error=f"Métodos faltantes: {missing}"
                    ))
                else:
                    self.results.append(TestResult(
                        f"Vista {class_name} - estructura",
                        True,
                        details=f"Métodos requeridos presentes"
                    ))
                    
            except Exception as e:
                self.results.append(TestResult(
                    f"Vista {class_name}",
                    False,
                    error=str(e)
                ))
                
    def test_help_manuals(self):
        """Test 3: Verificar métodos de manuales"""
        logger.info("\n[Test 3] Verificando manuales de ayuda...")
        
        views_with_manuals = [
            ('core.ui.views.orchestrator_view', 'OrchestratorView', '_show_help_manual'),
            ('core.ui.views.supervisor_view', 'SupervisorView', '_show_help_manual'),
            ('core.ui.views.controller_view', 'ControllerView', '_show_help_manual'),
            ('core.ui.views.manager_view', 'ManagerView', '_show_help_manual'),
            ('core.ui.views.works_view', 'WorksView', '_show_help_manual'),
            ('core.ui.views.skills_view', 'SkillsView', '_show_help_manual'),
            ('core.ui.views.settings_view', 'SettingsView', '_show_help_manual'),
        ]
        
        for module_name, class_name, method_name in views_with_manuals:
            try:
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
                
                if hasattr(cls, method_name):
                    method = getattr(cls, method_name)
                    # Verificar que es callable
                    if callable(method):
                        self.results.append(TestResult(
                            f"Manual {class_name}.{method_name}",
                            True,
                            details="Método existe y es callable"
                        ))
                    else:
                        self.results.append(TestResult(
                            f"Manual {class_name}.{method_name}",
                            False,
                            error="No es callable"
                        ))
                else:
                    self.results.append(TestResult(
                        f"Manual {class_name}.{method_name}",
                        False,
                        error="Método no encontrado"
                    ))
                    
            except Exception as e:
                self.results.append(TestResult(
                    f"Manual {class_name}",
                    False,
                    error=str(e)
                ))
                
    def test_api_client(self):
        """Test 4: Probar api_client"""
        logger.info("\n[Test 4] Probando API Client...")
        
        try:
            from core.ui.api_client import MININAApiClient
            
            # Verificar que se puede crear
            client = MININAApiClient()
            
            # Verificar métodos principales
            methods = [
                'health_check', 'get_skills', 'get_works', 
                'save_skill', 'delete_work', 'execute_skill'
            ]
            
            for method in methods:
                if hasattr(client, method):
                    self.results.append(TestResult(
                        f"API Client - {method}",
                        True
                    ))
                else:
                    self.results.append(TestResult(
                        f"API Client - {method}",
                        False,
                        error="Método no encontrado"
                    ))
                    
            # Probar health_check
            try:
                health = client.health_check()
                self.results.append(TestResult(
                    "API Client - health_check()",
                    True,
                    details=f"Retornó: {health}"
                ))
            except Exception as e:
                self.results.append(TestResult(
                    "API Client - health_check()",
                    False,
                    error=str(e)
                ))
                
        except Exception as e:
            self.results.append(TestResult(
                "API Client - Import/Creación",
                False,
                error=str(e),
                details=traceback.format_exc()
            ))
            
    def test_backend_connections(self):
        """Test 5: Verificar conexiones backend"""
        logger.info("\n[Test 5] Verificando conexiones backend...")
        
        # Verificar SkillVault
        try:
            from core.SkillVault import vault
            skills = vault.list_user_skills()
            self.results.append(TestResult(
                "Backend - SkillVault",
                True,
                details=f"{len(skills)} skills encontradas"
            ))
        except Exception as e:
            self.results.append(TestResult(
                "Backend - SkillVault",
                False,
                error=str(e)
            ))
            
        # Verificar WorksManager
        try:
            from core.file_manager import works_manager
            works = works_manager.get_all_works()
            self.results.append(TestResult(
                "Backend - WorksManager",
                True,
                details=f"{len(works)} works encontrados"
            ))
        except Exception as e:
            self.results.append(TestResult(
                "Backend - WorksManager",
                False,
                error=str(e)
            ))
            
        # Verificar MemoryCore
        try:
            from core.MemoryCore import memory_core
            self.results.append(TestResult(
                "Backend - MemoryCore",
                True,
                details="MemoryCore inicializado"
            ))
        except Exception as e:
            self.results.append(TestResult(
                "Backend - MemoryCore",
                False,
                error=str(e)
            ))
            
    def test_orchestrator_flow(self):
        """Test 6: Probar flujo del Orquestador"""
        logger.info("\n[Test 6] Probando flujo del Orquestador...")
        
        try:
            from core.orchestrator.orchestrator_agent import OrchestratorAgent
            
            orch = OrchestratorAgent()
            
            # Verificar que tiene el método process_objective
            if hasattr(orch, 'process_objective'):
                self.results.append(TestResult(
                    "Orquestador - process_objective",
                    True,
                    details="Método disponible"
                ))
            else:
                self.results.append(TestResult(
                    "Orquestador - process_objective",
                    False,
                    error="Método no encontrado"
                ))
                
            # Verificar métodos adicionales
            methods = ['_plan_tasks', '_execute_plan']
            for method in methods:
                if hasattr(orch, method):
                    self.results.append(TestResult(
                        f"Orquestador - {method}",
                        True
                    ))
                else:
                    self.warnings.append(f"Orquestador: método privado {method} no verificado")
                    
        except Exception as e:
            self.results.append(TestResult(
                "Orquestador - Inicialización",
                False,
                error=str(e),
                details=traceback.format_exc()
            ))
            
    def test_skill_studio(self):
        """Test 7: Verificar Skill Studio"""
        logger.info("\n[Test 7] Probando Skill Studio...")
        
        try:
            from core.ui.views.skills_view import SkillsView
            
            # Verificar métodos de generación
            methods = [
                '_create_new_skill', '_generate_skill_code', 
                '_save_skill_api', '_run_sandbox_api',
                '_send_chat_message', '_add_chat_message'
            ]
            
            for method in methods:
                if hasattr(SkillsView, method):
                    self.results.append(TestResult(
                        f"Skill Studio - {method}",
                        True
                    ))
                else:
                    self.results.append(TestResult(
                        f"Skill Studio - {method}",
                        False,
                        error="Método no encontrado"
                    ))
                    
        except Exception as e:
            self.results.append(TestResult(
                "Skill Studio - Import",
                False,
                error=str(e)
            ))
            
    def test_works_view(self):
        """Test 8: Probar Works View"""
        logger.info("\n[Test 8] Probando Works View...")
        
        try:
            from core.ui.views.works_view import WorksView
            
            methods = [
                '_load_works_from_api', '_on_work_selected',
                '_download_work', '_delete_work'
            ]
            
            for method in methods:
                if hasattr(WorksView, method):
                    self.results.append(TestResult(
                        f"Works - {method}",
                        True
                    ))
                else:
                    self.results.append(TestResult(
                        f"Works - {method}",
                        False,
                        error="Método no encontrado"
                    ))
                    
        except Exception as e:
            self.results.append(TestResult(
                "Works - Import",
                False,
                error=str(e)
            ))
            
    def test_manager_view(self):
        """Test 9: Verificar Manager View"""
        logger.info("\n[Test 9] Probando Manager View...")
        
        try:
            from core.ui.views.manager_view import ManagerView
            
            methods = [
                '_create_agents_panel', '_create_pools_panel',
                '_load_agents_table', '_create_pool_bar'
            ]
            
            for method in methods:
                if hasattr(ManagerView, method):
                    self.results.append(TestResult(
                        f"Manager - {method}",
                        True
                    ))
                else:
                    self.results.append(TestResult(
                        f"Manager - {method}",
                        False,
                        error="Método no encontrado"
                    ))
                    
        except Exception as e:
            self.results.append(TestResult(
                "Manager - Import",
                False,
                error=str(e)
            ))
            
    def test_settings_view(self):
        """Test 10: Probar Settings View"""
        logger.info("\n[Test 10] Probando Settings View...")
        
        try:
            from core.ui.views.settings_view import SettingsView
            
            methods = [
                '_create_section', '_create_local_api_card',
                '_create_api_card', '_create_status_card',
                '_create_messaging_card', '_show_install_guide',
                '_test_connections', '_save_settings'
            ]
            
            for method in methods:
                if hasattr(SettingsView, method):
                    self.results.append(TestResult(
                        f"Settings - {method}",
                        True
                    ))
                else:
                    self.results.append(TestResult(
                        f"Settings - {method}",
                        False,
                        error="Método no encontrado"
                    ))
                    
        except Exception as e:
            self.results.append(TestResult(
                "Settings - Import",
                False,
                error=str(e)
            ))
            
    def generate_report(self):
        """Generar reporte final"""
        logger.info("\n" + "=" * 80)
        logger.info("REPORTE FINAL DE PRUEBAS")
        logger.info("=" * 80)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        logger.info(f"\nTotal Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"📊 Success Rate: {passed/total*100:.1f}%")
        
        if self.warnings:
            logger.info(f"\n⚠️ Warnings: {len(self.warnings)}")
            for w in self.warnings:
                logger.info(f"  - {w}")
        
        logger.info("\n" + "-" * 80)
        logger.info("TESTS FALLIDOS:")
        logger.info("-" * 80)
        
        failed_tests = [r for r in self.results if not r.passed]
        if failed_tests:
            for test in failed_tests:
                logger.info(f"\n{test}")
        else:
            logger.info("✅ Ningún test falló!")
            
        logger.info("\n" + "=" * 80)
        
        # Guardar reporte detallado
        with open('simulation_report.txt', 'w', encoding='utf-8') as f:
            f.write("MININA UI v3.0 - Reporte de Simulación\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Success Rate: {passed/total*100:.1f}%\n\n")
            
            f.write("RESULTADOS DETALLADOS:\n")
            f.write("-" * 80 + "\n")
            for result in self.results:
                f.write(f"\n{result}\n")
                
        logger.info("\n📄 Reporte guardado en: simulation_report.txt")

if __name__ == "__main__":
    simulator = MININAUISimulator()
    simulator.run_all_tests()
