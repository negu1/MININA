"""
MININA v3.0 - AUDITORÍA EXHAUSTIVA GENERAL
Verificación completa de todos los sistemas
"""

import sys
import os
import traceback
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auditoria_general.log', mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AUDITORIA_GENERAL')

class AuditoriaResultado:
    """Resultado de auditoría"""
    def __init__(self, categoria: str, nombre: str, estado: str, 
                 detalles: str = None, error: str = None, criticidad: str = "ALTA"):
        self.categoria = categoria
        self.nombre = nombre
        self.estado = estado  # OK, WARNING, ERROR, INFO
        self.detalles = detalles
        self.error = error
        self.criticidad = criticidad
        
    def __str__(self):
        iconos = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌", "INFO": "ℹ️"}
        icono = iconos.get(self.estado, "?")
        return f"[{self.criticidad}] {icono} {self.categoria}/{self.nombre}: {self.estado}"

class AuditoriaGeneralMININA:
    """Auditoría exhaustiva del sistema MININA"""
    
    def __init__(self):
        self.resultados: List[AuditoriaResultado] = []
        self.stats = {"OK": 0, "WARNING": 0, "ERROR": 0, "INFO": 0}
        self.base_path = Path("c:/Users/wilso/Desktop/MININA")
        
    def ejecutar_auditoria_completa(self):
        """Ejecutar todas las auditorías"""
        logger.info("=" * 80)
        logger.info("AUDITORÍA EXHAUSTIVA GENERAL - MININA v3.0")
        logger.info("=" * 80)
        
        # 1. Sistema de Archivos
        self.auditar_sistema_archivos()
        
        # 2. Core System
        self.auditar_core_system()
        
        # 3. UI System
        self.auditar_ui_system()
        
        # 4. Skills System
        self.auditar_skills_system()
        
        # 5. Memory System
        self.auditar_memory_system()
        
        # 6. LLM Integration
        self.auditar_llm_system()
        
        # 7. API Connections
        self.auditar_api_connections()
        
        # 8. Messaging (Telegram/WhatsApp)
        self.auditar_messaging()
        
        # 9. Security & Backup
        self.auditar_security_backup()
        
        # 10. Dependencies
        self.auditar_dependencies()
        
        # Generar reporte y retornar resultados
        return self.generar_reporte_auditoria()
        
    def auditar_sistema_archivos(self):
        """Auditoría 1: Sistema de archivos"""
        logger.info("\n[1] AUDITANDO SISTEMA DE ARCHIVOS...")
        
        directorios_requeridos = [
            ("data", "Datos del sistema"),
            ("data/memory", "Memoria"),
            ("data/auditoria", "Auditoría"),
            ("data/output", "Output"),
            ("data/skills", "Skills del sistema"),
            ("skills_user", "Skills de usuario"),
            ("core/ui/views", "Vistas de UI"),
            ("core/manager", "Gestores"),
            ("core/orchestrator", "Orquestador"),
            ("tests", "Tests"),
        ]
        
        for dir_name, descripcion in directorios_requeridos:
            path = self.base_path / dir_name
            if path.exists():
                self.resultados.append(AuditoriaResultado(
                    "ARCHIVOS", f"Directorio {dir_name}", "OK",
                    f"{descripcion}: {len(list(path.iterdir()))} elementos",
                    criticidad="ALTA"
                ))
            else:
                self.resultados.append(AuditoriaResultado(
                    "ARCHIVOS", f"Directorio {dir_name}", "ERROR",
                    descripcion,
                    f"Directorio no existe: {path}",
                    criticidad="ALTA"
                ))
        
        # Verificar archivos críticos
        archivos_criticos = [
            "iniciar_minina.py",
            "core/ui/main_window.py",
            "core/ui/api_client.py",
            "core/MemoryCore.py",
            "core/SkillVault.py",
            "core/file_manager.py",
        ]
        
        for archivo in archivos_criticos:
            path = self.base_path / archivo
            if path.exists():
                size = path.stat().st_size
                self.resultados.append(AuditoriaResultado(
                    "ARCHIVOS", f"Archivo {archivo}", "OK",
                    f"Tamaño: {size} bytes",
                    criticidad="ALTA"
                ))
            else:
                self.resultados.append(AuditoriaResultado(
                    "ARCHIVOS", f"Archivo {archivo}", "ERROR",
                    None,
                    f"Archivo crítico no existe",
                    criticidad="CRITICA"
                ))
                
    def auditar_core_system(self):
        """Auditoría 2: Core System"""
        logger.info("\n[2] AUDITANDO CORE SYSTEM...")
        
        modulos_core = [
            "core.MemoryCore",
            "core.SkillVault",
            "core.file_manager",
            "core.LLMManager",
            "core.CortexBus",
            "core.AgentLifecycleManager",
            "core.orchestrator.orchestrator_agent",
            "core.orchestrator.task_planner",
            "core.manager.agent_pool",
            "core.manager.agent_resource_manager",
            "core.supervisor.execution_supervisor",
            "core.controller.policy_controller",
        ]
        
        for modulo in modulos_core:
            try:
                __import__(modulo)
                self.resultados.append(AuditoriaResultado(
                    "CORE", modulo, "OK",
                    "Módulo importado correctamente",
                    criticidad="ALTA"
                ))
            except Exception as e:
                self.resultados.append(AuditoriaResultado(
                    "CORE", modulo, "ERROR",
                    None,
                    str(e),
                    criticidad="CRITICA" if "orchestrator" in modulo or "MemoryCore" in modulo else "ALTA"
                ))
        
        # Verificar inicialización de core
        try:
            from core.MemoryCore import memory_core
            self.resultados.append(AuditoriaResultado(
                "CORE", "MemoryCore Inicializado", "OK",
                "Instancia memory_core disponible",
                criticidad="CRITICA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "CORE", "MemoryCore Inicializado", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
        try:
            from core.SkillVault import vault
            skills = vault.list_user_skills()
            self.resultados.append(AuditoriaResultado(
                "CORE", "SkillVault Inicializado", "OK",
                f"{len(skills)} skills disponibles",
                criticidad="CRITICA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "CORE", "SkillVault Inicializado", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
    def auditar_ui_system(self):
        """Auditoría 3: UI System"""
        logger.info("\n[3] AUDITANDO UI SYSTEM...")
        
        vistas_ui = [
            ("core.ui.views.orchestrator_view", "OrchestratorView"),
            ("core.ui.views.supervisor_view", "SupervisorView"),
            ("core.ui.views.controller_view", "ControllerView"),
            ("core.ui.views.manager_view", "ManagerView"),
            ("core.ui.views.works_view", "WorksView"),
            ("core.ui.views.skills_view", "SkillsView"),
            ("core.ui.views.settings_view", "SettingsView"),
        ]
        
        for modulo, clase in vistas_ui:
            try:
                mod = __import__(modulo, fromlist=[clase])
                cls = getattr(mod, clase)
                
                # Verificar métodos requeridos
                metodos_requeridos = ['_setup_ui', '_show_help_manual']
                metodos_faltantes = [m for m in metodos_requeridos if not hasattr(cls, m)]
                
                if metodos_faltantes:
                    self.resultados.append(AuditoriaResultado(
                        "UI", f"Vista {clase}", "WARNING",
                        None,
                        f"Métodos faltantes: {metodos_faltantes}",
                        criticidad="ALTA"
                    ))
                else:
                    self.resultados.append(AuditoriaResultado(
                        "UI", f"Vista {clase}", "OK",
                        "Todos los métodos requeridos presentes",
                        criticidad="ALTA"
                    ))
                    
            except Exception as e:
                self.resultados.append(AuditoriaResultado(
                    "UI", f"Vista {clase}", "ERROR",
                    None,
                    str(e),
                    criticidad="CRITICA"
                ))
        
        # Verificar MainWindow
        try:
            from core.ui.main_window import MainWindow
            self.resultados.append(AuditoriaResultado(
                "UI", "MainWindow", "OK",
                "Clase MainWindow importable",
                criticidad="CRITICA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "UI", "MainWindow", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
        # Verificar api_client
        try:
            from core.ui.api_client import api_client, MININAApiClient
            health = api_client.health_check()
            self.resultados.append(AuditoriaResultado(
                "UI", "API Client", "OK",
                f"Health check: {health}",
                criticidad="CRITICA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "UI", "API Client", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
    def auditar_skills_system(self):
        """Auditoría 4: Skills System"""
        logger.info("\n[4] AUDITANDO SKILLS SYSTEM...")
        
        # Verificar skills del sistema - usando métodos correctos
        try:
            from core.SkillVault import vault
            user_skills = vault.list_user_skills()
            
            self.resultados.append(AuditoriaResultado(
                "SKILLS", "SkillVault User", "OK",
                f"{len(user_skills)} skills de usuario",
                criticidad="ALTA"
            ))
            
            # Verificar que skills tienen execute
            for skill in user_skills[:3]:  # Verificar primeros 3
                if 'name' in skill:
                    self.resultados.append(AuditoriaResultado(
                        "SKILLS", f"Skill {skill['name']}", "INFO",
                        f"Tipo: {skill.get('type', 'desconocido')}",
                        criticidad="MEDIA"
                    ))
                    
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "SKILLS", "SkillVault", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
        # Verificar directorio skills_user
        skills_user_path = self.base_path / "skills_user"
        if skills_user_path.exists():
            skills_files = list(skills_user_path.glob("*.json"))
            self.resultados.append(AuditoriaResultado(
                "SKILLS", "Directorio skills_user", "OK",
                f"{len(skills_files)} archivos .json",
                criticidad="ALTA"
            ))
            
    def auditar_memory_system(self):
        """Auditoría 5: Memory System"""
        logger.info("\n[5] AUDITANDO MEMORY SYSTEM...")
        
        try:
            from core.MemoryCore import memory_core
            
            # Verificar bases de datos
            dbs = [
                "memory_vault.db",
                "stm_cache.json",
                "user_observability.db"
            ]
            
            data_memory = self.base_path / "data" / "memory"
            for db in dbs:
                db_path = data_memory / db
                if db_path.exists():
                    size = db_path.stat().st_size
                    self.resultados.append(AuditoriaResultado(
                        "MEMORY", f"DB {db}", "OK",
                        f"Tamaño: {size} bytes",
                        criticidad="ALTA"
                    ))
                else:
                    self.resultados.append(AuditoriaResultado(
                        "MEMORY", f"DB {db}", "WARNING",
                        None,
                        "Archivo no existe (se creará al usar)",
                        criticidad="MEDIA"
                    ))
                    
            # Probar guardar/recuperar memoria corto plazo - usando método correcto add_to_stm
            try:
                test_session = "auditoria_test"
                test_data = {"role": "user", "content": "test de auditoria", "timestamp": "2026-02-20"}
                memory_core.add_to_stm(test_session, "user", "test de auditoria", metadata={"test": True})
                retrieved = memory_core.get_stm_context(test_session, limit=1)
                
                if retrieved and len(retrieved) > 0:
                    self.resultados.append(AuditoriaResultado(
                        "MEMORY", "STM Read/Write", "OK",
                        "Memoria de corto plazo funcional",
                        criticidad="ALTA"
                    ))
                else:
                    self.resultados.append(AuditoriaResultado(
                        "MEMORY", "STM Read/Write", "ERROR",
                        None,
                        "No se recuperaron datos",
                        criticidad="CRITICA"
                    ))
            except Exception as e:
                self.resultados.append(AuditoriaResultado(
                    "MEMORY", "STM Read/Write", "ERROR",
                    None,
                    str(e),
                    criticidad="CRITICA"
                ))
                
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "MEMORY", "MemoryCore", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
    def auditar_llm_system(self):
        """Auditoría 6: LLM Integration"""
        logger.info("\n[6] AUDITANDO LLM SYSTEM...")
        
        try:
            from core.LLMManager import llm_manager
            
            # Verificar providers disponibles - usando método correcto
            providers = llm_manager.list_available_providers()
            self.resultados.append(AuditoriaResultado(
                "LLM", "Providers disponibles", "OK",
                f"{len(providers)} providers configurados",
                criticidad="ALTA"
            ))
            
            # Verificar provider default
            active = llm_manager.get_active_config()
            if active:
                self.resultados.append(AuditoriaResultado(
                    "LLM", "Provider activo", "OK",
                    f"Activo: {active.model}",
                    criticidad="ALTA"
                ))
            else:
                self.resultados.append(AuditoriaResultado(
                    "LLM", "Provider activo", "WARNING",
                    None,
                    "No hay provider activo configurado",
                    criticidad="ALTA"
                ))
                
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "LLM", "LLMManager", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
        # Verificar configuración LLM
        try:
            config_path = self.base_path / "data" / "llm_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.resultados.append(AuditoriaResultado(
                    "LLM", "Configuración LLM", "OK",
                    f"Providers configurados: {list(config.keys())}",
                    criticidad="ALTA"
                ))
            else:
                self.resultados.append(AuditoriaResultado(
                    "LLM", "Configuración LLM", "WARNING",
                    None,
                    "Archivo llm_config.json no existe",
                    criticidad="MEDIA"
                ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "LLM", "Configuración LLM", "ERROR",
                None,
                str(e),
                criticidad="ALTA"
            ))
            
    def auditar_api_connections(self):
        """Auditoría 7: API Connections"""
        logger.info("\n[7] AUDITANDO API CONNECTIONS...")
        
        # Probar backend local
        try:
            from core.ui.api_client import api_client
            
            endpoints = [
                ("health_check", []),
                ("get_skills", []),
                ("get_works", []),
            ]
            
            for endpoint, args in endpoints:
                try:
                    method = getattr(api_client, endpoint)
                    result = method(*args) if args else method()
                    self.resultados.append(AuditoriaResultado(
                        "API", f"Endpoint {endpoint}", "OK",
                        f"Respuesta: {result is not None}",
                        criticidad="ALTA"
                    ))
                except Exception as e:
                    self.resultados.append(AuditoriaResultado(
                        "API", f"Endpoint {endpoint}", "WARNING",
                        None,
                        str(e),
                        criticidad="MEDIA"
                    ))
                    
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "API", "API Client", "ERROR",
                None,
                str(e),
                criticidad="CRITICA"
            ))
            
        # Verificar APIs locales (Ollama, LM Studio, Jan)
        apis_locales = [
            ("Ollama", "http://localhost:11434", 11434),
            ("LM Studio", "http://localhost:1234", 1234),
            ("Jan", "http://localhost:1337", 1337),
        ]
        
        import socket
        for nombre, url, puerto in apis_locales:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', puerto))
                sock.close()
                
                if result == 0:
                    self.resultados.append(AuditoriaResultado(
                        "API", f"{nombre} (puerto {puerto})", "OK",
                        f"Puerto {puerto} abierto",
                        criticidad="MEDIA"
                    ))
                else:
                    self.resultados.append(AuditoriaResultado(
                        "API", f"{nombre} (puerto {puerto})", "INFO",
                        f"Puerto {puerto} cerrado (API no ejecutándose)",
                        criticidad="BAJA"
                    ))
            except Exception as e:
                self.resultados.append(AuditoriaResultado(
                    "API", f"{nombre} (puerto {puerto})", "ERROR",
                    None,
                    str(e),
                    criticidad="BAJA"
                ))
                
    def auditar_messaging(self):
        """Auditoría 8: Messaging (Telegram/WhatsApp)"""
        logger.info("\n[8] AUDITANDO MESSAGING SYSTEM...")
        
        # Telegram
        try:
            from core.TelegramBot import TelegramBot
            self.resultados.append(AuditoriaResultado(
                "MESSAGING", "TelegramBot", "OK",
                "Clase importable",
                criticidad="MEDIA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "MESSAGING", "TelegramBot", "WARNING",
                None,
                str(e),
                criticidad="MEDIA"
            ))
            
        # WhatsApp
        try:
            from core.WhatsAppBot import WhatsAppBot
            self.resultados.append(AuditoriaResultado(
                "MESSAGING", "WhatsAppBot", "OK",
                "Clase importable",
                criticidad="MEDIA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "MESSAGING", "WhatsAppBot", "WARNING",
                None,
                str(e),
                criticidad="MEDIA"
            ))
            
    def auditar_security_backup(self):
        """Auditoría 9: Security & Backup"""
        logger.info("\n[9] AUDITANDO SECURITY & BACKUP...")
        
        # Verificar sistema de backup
        try:
            from core.BackupManager import backup_manager
            self.resultados.append(AuditoriaResultado(
                "BACKUP", "BackupManager", "OK",
                "Backup manager disponible",
                criticidad="ALTA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "BACKUP", "BackupManager", "WARNING",
                None,
                str(e),
                criticidad="MEDIA"
            ))
            
        # Verificar credenciales seguras
        try:
            from core.SecureCredentials import credentials_store
            self.resultados.append(AuditoriaResultado(
                "SECURITY", "SecureCredentials", "OK",
                "Sistema de credenciales disponible",
                criticidad="ALTA"
            ))
        except Exception as e:
            self.resultados.append(AuditoriaResultado(
                "SECURITY", "SecureCredentials", "WARNING",
                None,
                str(e),
                criticidad="MEDIA"
            ))
            
        # Verificar directorio backups
        backups_path = self.base_path / "backups"
        if backups_path.exists():
            backup_files = list(backups_path.iterdir())
            self.resultados.append(AuditoriaResultado(
                "BACKUP", "Directorio backups", "OK",
                f"{len(backup_files)} backups disponibles",
                criticidad="MEDIA"
            ))
        else:
            self.resultados.append(AuditoriaResultado(
                "BACKUP", "Directorio backups", "INFO",
                "Directorio no existe (se creará al primer backup)",
                criticidad="BAJA"
            ))
            
    def auditar_dependencies(self):
        """Auditoría 10: Dependencies"""
        logger.info("\n[10] AUDITANDO DEPENDENCIAS...")
        
        dependencias_criticas = [
            "PyQt5",
            "fastapi",
            "uvicorn",
            "aiohttp",
            "python-dotenv",
            "psutil",
            "requests",
        ]
        
        for dep in dependencias_criticas:
            try:
                __import__(dep.lower().replace("-", "_"))
                self.resultados.append(AuditoriaResultado(
                    "DEPS", dep, "OK",
                    "Paquete instalado",
                    criticidad="ALTA" if dep in ["PyQt5", "fastapi"] else "MEDIA"
                ))
            except ImportError:
                self.resultados.append(AuditoriaResultado(
                    "DEPS", dep, "ERROR",
                    None,
                    "Paquete no instalado",
                    criticidad="ALTA" if dep in ["PyQt5", "fastapi"] else "MEDIA"
                ))
                
    def generar_reporte_auditoria(self):
        """Generar reporte final de auditoría"""
        logger.info("\n" + "=" * 80)
        logger.info("REPORTE DE AUDITORÍA EXHAUSTIVA")
        logger.info("=" * 80)
        
        # Contar por estado
        for r in self.resultados:
            self.stats[r.estado] = self.stats.get(r.estado, 0) + 1
            
        total = len(self.resultados)
        
        logger.info(f"\n📊 ESTADÍSTICAS:")
        logger.info(f"   Total checks: {total}")
        logger.info(f"   ✅ OK: {self.stats.get('OK', 0)}")
        logger.info(f"   ⚠️ WARNING: {self.stats.get('WARNING', 0)}")
        logger.info(f"   ❌ ERROR: {self.stats.get('ERROR', 0)}")
        logger.info(f"   ℹ️ INFO: {self.stats.get('INFO', 0)}")
        
        # Calcular salud del sistema
        errores_criticos = [r for r in self.resultados if r.estado == "ERROR" and r.criticidad == "CRITICA"]
        errores_altos = [r for r in self.resultados if r.estado == "ERROR" and r.criticidad == "ALTA"]
        
        if errores_criticos:
            salud = "CRÍTICA"
            logger.info(f"\n🚨 SALUD DEL SISTEMA: {salud}")
            logger.info(f"   Errores críticos: {len(errores_criticos)}")
        elif errores_altos:
            salud = "DEGRADADA"
            logger.info(f"\n⚠️ SALUD DEL SISTEMA: {salud}")
            logger.info(f"   Errores altos: {len(errores_altos)}")
        else:
            salud = "OPERATIVA"
            logger.info(f"\n✅ SALUD DEL SISTEMA: {salud}")
            
        # Mostrar errores
        if errores_criticos or errores_altos:
            logger.info("\n❌ ERRORES ENCONTRADOS:")
            for r in errores_criticos + errores_altos:
                logger.info(f"\n   [{r.criticidad}] {r.categoria}/{r.nombre}")
                if r.error:
                    logger.info(f"   Error: {r.error}")
                    
        # Guardar reporte detallado
        reporte_path = self.base_path / "AUDITORIA_GENERAL_2026-02-20.md"
        with open(reporte_path, 'w', encoding='utf-8') as f:
            f.write("# Auditoría General MININA v3.0\n\n")
            f.write(f"**Fecha:** 2026-02-20\n\n")
            f.write(f"**Estado:** {salud}\n\n")
            f.write("## Estadísticas\n\n")
            f.write(f"- Total checks: {total}\n")
            f.write(f"- OK: {self.stats.get('OK', 0)}\n")
            f.write(f"- WARNING: {self.stats.get('WARNING', 0)}\n")
            f.write(f"- ERROR: {self.stats.get('ERROR', 0)}\n")
            f.write(f"- INFO: {self.stats.get('INFO', 0)}\n\n")
            
            f.write("## Resultados Detallados\n\n")
            f.write("| Categoría | Componente | Estado | Criticidad | Detalles |\n")
            f.write("|-----------|------------|--------|------------|----------|\n")
            
            for r in self.resultados:
                detalles = (r.detalles or "").replace("|", "\\|").replace("\n", " ")
                f.write(f"| {r.categoria} | {r.nombre} | {r.estado} | {r.criticidad} | {detalles} |\n")
                
        logger.info(f"\n📄 Reporte guardado en: {reporte_path}")
        
        return salud, errores_criticos, errores_altos

if __name__ == "__main__":
    auditor = AuditoriaGeneralMININA()
    salud, errores_crit, errores_alt = auditor.ejecutar_auditoria_completa()
    
    # Exit code basado en salud
    if errores_crit:
        sys.exit(1)
    elif errores_alt:
        sys.exit(2)
    else:
        sys.exit(0)
