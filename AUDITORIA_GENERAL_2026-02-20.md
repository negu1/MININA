# Auditoría General MININA v3.0

**Fecha:** 2026-02-20

**Estado:** DEGRADADA

## Estadísticas

- Total checks: 69
- OK: 58
- WARNING: 4
- ERROR: 2
- INFO: 5

## Resultados Detallados

| Categoría | Componente | Estado | Criticidad | Detalles |
|-----------|------------|--------|------------|----------|
| ARCHIVOS | Directorio data | OK | ALTA | Datos del sistema: 13 elementos |
| ARCHIVOS | Directorio data/memory | OK | ALTA | Memoria: 2 elementos |
| ARCHIVOS | Directorio data/auditoria | OK | ALTA | Auditoría: 2 elementos |
| ARCHIVOS | Directorio data/output | OK | ALTA | Output: 0 elementos |
| ARCHIVOS | Directorio data/skills | OK | ALTA | Skills del sistema: 0 elementos |
| ARCHIVOS | Directorio skills_user | OK | ALTA | Skills de usuario: 0 elementos |
| ARCHIVOS | Directorio core/ui/views | OK | ALTA | Vistas de UI: 8 elementos |
| ARCHIVOS | Directorio core/manager | OK | ALTA | Gestores: 6 elementos |
| ARCHIVOS | Directorio core/orchestrator | OK | ALTA | Orquestador: 5 elementos |
| ARCHIVOS | Directorio tests | OK | ALTA | Tests: 9 elementos |
| ARCHIVOS | Archivo iniciar_minina.py | OK | ALTA | Tamaño: 3395 bytes |
| ARCHIVOS | Archivo core/ui/main_window.py | OK | ALTA | Tamaño: 20278 bytes |
| ARCHIVOS | Archivo core/ui/api_client.py | OK | ALTA | Tamaño: 8552 bytes |
| ARCHIVOS | Archivo core/MemoryCore.py | OK | ALTA | Tamaño: 28362 bytes |
| ARCHIVOS | Archivo core/SkillVault.py | OK | ALTA | Tamaño: 12422 bytes |
| ARCHIVOS | Archivo core/file_manager.py | OK | ALTA | Tamaño: 12003 bytes |
| CORE | core.MemoryCore | OK | ALTA | Módulo importado correctamente |
| CORE | core.SkillVault | OK | ALTA | Módulo importado correctamente |
| CORE | core.file_manager | OK | ALTA | Módulo importado correctamente |
| CORE | core.LLMManager | OK | ALTA | Módulo importado correctamente |
| CORE | core.CortexBus | OK | ALTA | Módulo importado correctamente |
| CORE | core.AgentLifecycleManager | OK | ALTA | Módulo importado correctamente |
| CORE | core.orchestrator.orchestrator_agent | OK | ALTA | Módulo importado correctamente |
| CORE | core.orchestrator.task_planner | OK | ALTA | Módulo importado correctamente |
| CORE | core.manager.agent_pool | OK | ALTA | Módulo importado correctamente |
| CORE | core.manager.agent_resource_manager | OK | ALTA | Módulo importado correctamente |
| CORE | core.supervisor.execution_supervisor | OK | ALTA | Módulo importado correctamente |
| CORE | core.controller.policy_controller | OK | ALTA | Módulo importado correctamente |
| CORE | MemoryCore Inicializado | OK | CRITICA | Instancia memory_core disponible |
| CORE | SkillVault Inicializado | OK | CRITICA | 3 skills disponibles |
| UI | Vista OrchestratorView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista SupervisorView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista ControllerView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista ManagerView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista WorksView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista SkillsView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | Vista SettingsView | OK | ALTA | Todos los métodos requeridos presentes |
| UI | MainWindow | OK | CRITICA | Clase MainWindow importable |
| UI | API Client | OK | CRITICA | Health check: True |
| SKILLS | SkillVault User | OK | ALTA | 3 skills de usuario |
| SKILLS | Skill GHYU | INFO | MEDIA | Tipo: desconocido |
| SKILLS | Skill casa | INFO | MEDIA | Tipo: desconocido |
| SKILLS | Skill PN PRUENA | INFO | MEDIA | Tipo: desconocido |
| SKILLS | Directorio skills_user | OK | ALTA | 0 archivos .json |
| MEMORY | DB memory_vault.db | OK | ALTA | Tamaño: 49152 bytes |
| MEMORY | DB stm_cache.json | OK | ALTA | Tamaño: 11422 bytes |
| MEMORY | DB user_observability.db | WARNING | MEDIA |  |
| MEMORY | STM Read/Write | OK | ALTA | Memoria de corto plazo funcional |
| LLM | Providers disponibles | OK | ALTA | 7 providers configurados |
| LLM | Provider activo | OK | ALTA | Activo: llama-3.1-8b-instant |
| LLM | Configuración LLM | OK | ALTA | Providers configurados: ['providers', 'active_provider'] |
| API | Endpoint health_check | OK | ALTA | Respuesta: True |
| API | Endpoint get_skills | OK | ALTA | Respuesta: True |
| API | Endpoint get_works | OK | ALTA | Respuesta: True |
| API | Ollama (puerto 11434) | OK | MEDIA | Puerto 11434 abierto |
| API | LM Studio (puerto 1234) | INFO | BAJA | Puerto 1234 cerrado (API no ejecutándose) |
| API | Jan (puerto 1337) | INFO | BAJA | Puerto 1337 cerrado (API no ejecutándose) |
| MESSAGING | TelegramBot | WARNING | MEDIA |  |
| MESSAGING | WhatsAppBot | WARNING | MEDIA |  |
| BACKUP | BackupManager | OK | ALTA | Backup manager disponible |
| SECURITY | SecureCredentials | WARNING | MEDIA |  |
| BACKUP | Directorio backups | OK | MEDIA | 1 backups disponibles |
| DEPS | PyQt5 | ERROR | ALTA |  |
| DEPS | fastapi | OK | ALTA | Paquete instalado |
| DEPS | uvicorn | OK | MEDIA | Paquete instalado |
| DEPS | aiohttp | OK | MEDIA | Paquete instalado |
| DEPS | python-dotenv | ERROR | MEDIA |  |
| DEPS | psutil | OK | MEDIA | Paquete instalado |
| DEPS | requests | OK | MEDIA | Paquete instalado |
