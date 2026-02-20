# Changelog MININA v3.0.0

## [3.0.0] - 2026-02-19

### 🎉 Nuevo: Arquitectura de 4 Capas Orquestadas

#### Capa 1: Orquestador
- **OrchestratorAgent** - Procesa objetivos en lenguaje natural y descompone en tareas
- **TaskPlanner** - Planificación inteligente con dependencias
- **CortexBus** - Sistema de eventos asíncrono entre capas

#### Capa 2: Supervisor
- **ExecutionSupervisor** - Monitoreo en tiempo real de ejecuciones
- **ValidationResult** - Validación de resultados (SUCCESS, PARTIAL, FAILED)
- **Anomaly Detection** - Detección automática de loops y anomalías
- **Alert System** - Centro de alertas con niveles (Crítico, Advertencia, Info)

#### Capa 3: Controlador
- **PolicyController** - Sistema de reglas duras
- **RBAC** - Control de acceso basado en roles
- **Schedule Management** - Horarios de ejecución por skill
- **Rate Limiting** - Límites de ejecución por usuario

#### Capa 4: Manager
- **AgentResourceManager** - Gestión de pools de agentes
- **AgentPool** - Pools pre-calentados por tipo (CPU, IO, Network, General)
- **LoadBalancer** - Balanceo de carga con múltiples estrategias
- **AutoScaling** - Escalado automático basado en métricas

### 🖥️ Nuevo: UI Local PyQt6

#### 6 Vistas Completas
1. **OrchestratorView** - Chat inteligente + visualización DAG de planes
2. **ManagerView** - Pools de agentes, métricas, auto-scaling
3. **SupervisorView** - Centro de alertas + logs en tiempo real
4. **ControllerView** - Editor de reglas, horarios, permisos RBAC
5. **WorksView** - Archivos generados con preview y descargas nativas
6. **SkillsView** - Skill Studio: editor + chat IA + sandbox

#### Características UI
- **Navigation Rail** - Barra lateral con iconos intuitivos
- **QFileDialog** - Descargas nativas del sistema de archivos
- **Preview System** - Visualización de PDFs, imágenes, CSV, código
- **Dark Theme** - Soporte para tema oscuro en editores
- **System Tray** - Icono en bandeja del sistema

### 🔧 Base de Skills Mejorada

#### EnhancedSkill
- **Resource Profiles** - Clasificación por uso de recursos (CPU, IO, Network)
- **Metadata** - Versión, descripción, estimaciones de tiempo
- **Retry Policies** - Políticas de reintento configurables
- **Progress Reporting** - Reporte de progreso en tiempo real
- **Hooks** - on_success, on_failure para extensibilidad

### 🌐 Integración API

#### MININAApiClient
- **REST API** - Cliente para backend FastAPI (puerto 8897)
- **Skills API** - Listar, guardar, ejecutar skills
- **Works API** - Gestión de archivos generados
- **System API** - Estado del sistema y métricas
- **Error Handling** - Manejo robusto de errores de red

### 🧪 Testing

#### Tests de Integración
- **test_layers.py** - Tests de las 4 capas
- **test_ui_backend.py** - Tests UI-Backend
- **E2E Tests** - Tests end-to-end completos

### 📦 Estructura de Archivos

```
core/
├── orchestrator/
│   ├── orchestrator_agent.py
│   ├── task_planner.py
│   └── bus.py
├── supervisor/
│   └── execution_supervisor.py
├── controller/
│   └── policy_controller.py
├── manager/
│   ├── agent_resource_manager.py
│   ├── agent_pool.py
│   ├── load_balancer.py
│   └── auto_scaling.py
├── skills/
│   └── enhanced_skill.py
└── ui/
    ├── app.py
    ├── main_window.py
    ├── api_client.py
    └── views/
        ├── orchestrator_view.py
        ├── manager_view.py
        ├── supervisor_view.py
        ├── controller_view.py
        ├── works_view.py
        └── skills_view.py
```

### 🚀 Inicio Rápido

```bash
# Instalar dependencias UI
pip install PyQt5 qasync requests

# Iniciar aplicación
python launch_ui.py
```

### 🔄 Cambios desde v2.x

#### Mejoras
- **UI Local** - Reemplaza WebUI para experiencia nativa
- **4 Capas** - Arquitectura limpia con responsabilidades definidas
- **Descargas** - Sistema nativo con QFileDialog
- **Preview** - Visualización de archivos sin salir de la app
- **Skill Studio** - Entorno completo de desarrollo de skills

#### Deprecado
- WebUI movida a modo legacy (core/webui/)
- Descargas HTTP reemplazadas por sistema de archivos nativo
- Almacenamiento localStorage → Backend API

### 📝 Notas de Release

- **Breaking Changes**: Migración de WebUI a UI Local requiere PyQt6
- **Python**: Requiere Python 3.11+
- **Backend**: Puerto cambiado a 8897 (consolidado)

### 🤝 Contribuciones

Gracias a todos los contribuidores que hicieron posible v3.0.

---

**Full Changelog**: [v2.x...v3.0.0](https://github.com/minina/minina/compare/v2.x...v3.0.0)
