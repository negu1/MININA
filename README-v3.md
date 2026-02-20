# MININA v3.0.0 - Sistema Operativo de Automatización Inteligente

MININA es un sistema de automatización con arquitectura de 4 capas orquestadas (Orquestador, Supervisor, Controlador, Manager) y UI Local nativa en PyQt5.

---

## 🚀 Características Principales v3.0

### Arquitectura de 4 Capas
- **🧠 Orquestador (Capa 1)** - IA que descompone objetivos en planes ejecutables
- **👁️ Supervisor (Capa 2)** - Monitoreo, validación y detección de anomalías  
- **📜 Controlador (Capa 3)** - Reglas duras, horarios y permisos RBAC
- **⚙️ Manager (Capa 4)** - Pools de agentes, balanceo de carga, auto-scaling

### UI Local PyQt5 (Nuevo en v3.0)
- **🤖 Orquestador** - Chat inteligente + visualización de planes
- **⚡ Agentes** - Gestión de pools y métricas en tiempo real
- **🛡️ Alertas** - Centro de supervisión con logs
- **📜 Reglas** - Editor de políticas y horarios
- **📦 Works** - Archivos generados con preview y descargas nativas
- **📚 Skills** - Creador con editor + chat IA + sandbox de testing

---

## 📦 Instalación

### Requisitos
- Python 3.11+
- PyQt5
- Backend FastAPI (puerto 8897)

### Instalación Rápida
```bash
# 1. Instalar dependencias UI
pip install -r requirements-ui.txt

# 2. Iniciar UI Local
python launch_ui.py
```

---

## 🏗️ Estructura del Proyecto v3.0

```
MININA/
├── core/
│   ├── orchestrator/          # Capa 1: Orquestación
│   │   ├── orchestrator_agent.py
│   │   ├── task_planner.py
│   │   └── bus.py
│   ├── supervisor/            # Capa 2: Supervisión
│   │   └── execution_supervisor.py
│   ├── controller/            # Capa 3: Control
│   │   └── policy_controller.py
│   ├── manager/               # Capa 4: Recursos
│   │   ├── agent_resource_manager.py
│   │   ├── agent_pool.py
│   │   ├── load_balancer.py
│   │   └── auto_scaling.py
│   ├── skills/               # Base para skills
│   │   └── enhanced_skill.py
│   ├── webui/                # WebUI FastAPI (legado)
│   └── ui/                   # UI Local PyQt5 (nuevo v3.0)
│       ├── app.py
│       ├── main_window.py
│       ├── api_client.py
│       └── views/
│           ├── orchestrator_view.py
│           ├── manager_view.py
│           ├── supervisor_view.py
│           ├── controller_view.py
│           ├── works_view.py
│           └── skills_view.py
├── tests/
│   ├── unit/
│   └── integration/
├── launch_ui.py              # Launcher UI v3.0
├── iniciar_minina.py         # Launcher WebUI (legado)
└── requirements-ui.txt       # Dependencias UI
```

---

## 🔧 Uso

### UI Local (Recomendado v3.0)
```bash
python launch_ui.py
```

### WebUI (Legado - aún disponible)
```bash
python iniciar_minina.py
# Abre: http://127.0.0.1:8897
```

---

## 🧪 Testing

```bash
# Tests unitarios
python -m pytest tests/unit/ -v

# Tests de integración  
python -m pytest tests/integration/ -v
```

---

## 📚 Documentación

- [Guía de Usuario](docs/GUIDE.md)
- [Changelog](docs/CHANGELOG.md)
- [API Reference](docs/API.md)

---

## 📄 Licencia

Proyecto personal - Uso libre

---

**Versión:** 3.0.0 | **Actualizado:** Febrero 2026
