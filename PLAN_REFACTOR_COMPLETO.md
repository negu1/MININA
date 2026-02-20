# PLAN DE REFACTORIZACIÓN COMPLETA - MININA v3.0

**Checkpoint base:** `11a8f2a` - Estado estable antes de refactorización  
**Arquitectura:** UI PyQt5 Standalone (WebUI postergado)  
**Fecha:** 2026-02-20  

---

## 📋 ESTRUCTURA DEL PLAN

### **FASE 1: FUNDAMENTOS** (Prioridad Máxima)
| # | Área | Tarea | Archivos | Estimado |
|---|------|-------|----------|----------|
| 1.1 | Configuración | Unificar settings en settings_view_v2 | settings_view_v2.py, main_window.py | 2h |
| 1.2 | Configuración | Integrar 20 APIs con validación | business_apis.py, api_registry.py | 3h |
| 1.3 | Configuración | Crear wizard de configuración inicial | nuevo: config_wizard.py | 2h |
| 1.4 | Datos | Crear directorios data/ estructurados | config.py | 30m |
| 1.5 | Tests | Tests básicos de integración | tests/integration/ | 2h |

### **FASE 2: UI/UX** (Prioridad Alta)
| # | Área | Tarea | Archivos | Estimado |
|---|------|-------|----------|----------|
| 2.1 | Navegación | Simplificar menú principal | main_window.py | 1h |
| 2.2 | Skills | Mejorar Skill Studio (editor + sandbox) | skills_view.py | 2h |
| 2.3 | APIs | Panel de gestión de APIs con status | nuevo: apis_view.py | 2h |
| 2.4 | Dashboard | Vista de resumen del sistema | nuevo: dashboard_view.py | 2h |
| 2.5 | Notificaciones | Sistema de notificaciones en UI | nuevo: notifications_view.py | 1h |

### **FASE 3: CORE MEJORAS** (Prioridad Media-Alta)
| # | Área | Tarea | Archivos | Estimado |
|---|------|-------|----------|----------|
| 3.1 | Seguridad | Integrar security dashboard | security/*.py, supervisor_view.py | 2h |
| 3.2 | Orquestador | Mejorar modo planning/execution | orchestrator_agent.py | 2h |
| 3.3 | LLM | Integrar configuración LLM en UI | LLMManager.py, settings_view_v2.py | 2h |
| 3.4 | Watchdog | Dashboard de monitoreo | SystemWatchdog.py, nuevo: monitoring_view.py | 2h |
| 3.5 | Memoria | Integrar MemoryCore visual | MemoryCore.py | 1h |

### **FASE 4: APIs & INTEGRACIONES** (Prioridad Media)
| # | Área | Tarea | Archivos | Estimado |
|---|------|-------|----------|----------|
| 4.1 | APIs | Validación automática de credenciales | api/*.py | 3h |
| 4.2 | Telegram | Integrar bot con UI | TelegramBot_v3.py | 2h |
| 4.3 | Notificaciones | Sistema de alertas multi-canal | api_notifications.py | 2h |
| 4.4 | Skills Externas | Mejorar evaluador | external_skills_view.py | 2h |

### **FASE 5: OPTIMIZACIÓN** (Prioridad Baja)
| # | Área | Tarea | Archivos | Estimado |
|---|------|-------|----------|----------|
| 5.1 | Performance | Optimizar carga de UI | main_window.py | 1h |
| 5.2 | Código | Eliminar archivos legacy | WebUI.legacy.py, archivos .bak | 30m |
| 5.3 | Docs | Documentación de uso | docs/USAGE.md | 1h |
| 5.4 | Tests | Cobertura completa | tests/ | 4h |

---

## 🎯 DETALLE DE TAREAS

### **FASE 1.1: Unificar Settings**
**Problema:** `settings_view.py` (137KB) es monolítico, `settings_view_v2.py` existe pero no se usa  
**Solución:** 
- Migrar funcionalidad esencial a `settings_view_v2.py`
- Integrar `business_apis.py` como sub-panel
- Actualizar `main_window.py` para usar `settings_view_v2`
- Eliminar `settings_view.py` legacy

**Criterios de éxito:**
- [ ] Settings v2 carga correctamente
- [ ] 20 APIs configurables desde UI
- [ ] Validación de campos requeridos
- [ ] Test de conexión por API

### **FASE 1.2: Integrar 20 APIs**
**Problema:** APIs existen como managers pero no integradas en UI  
**Solución:**
- Crear panel de APIs en settings_v2
- Usar `api_registry.py` para detectar estado
- Integrar `business_apis.py` como cards configurables
- Agregar botón "Test Connection" por API

**Criterios de éxito:**
- [ ] Lista de 20 APIs visible
- [ ] Configuración persistente en data/api_config.json
- [ ] Validación de credenciales
- [ ] Indicador visual: ✓ Configurado / ✗ Pendiente

### **FASE 2.4: Dashboard del Sistema**
**Nueva funcionalidad:**  
Vista de resumen mostrando:
- Skills activos/total
- APIs configuradas
- Works generados
- Estado del sistema (CPU, memoria)
- Últimas actividades
- Alertas pendientes

**Archivos:** nuevo `dashboard_view.py`, integrar en `main_window.py`

### **FASE 3.1: Security Dashboard**
**Problema:** 9 módulos de seguridad existen pero no visibles en UI  
**Solución:**
- Crear panel en `supervisor_view.py` o nueva vista
- Mostrar: análisis de skills, sandbox status, validaciones
- Alertas de seguridad destacadas

### **FASE 3.4: System Monitoring**
**Problema:** `SystemWatchdog` existe pero no visible  
**Solución:**
- Nueva vista `monitoring_view.py`
- Métricas en tiempo real: CPU, RAM, discos
- Estado de procesos de skills
- Logs del sistema

---

## 📊 PRIORIZACIÓN POR IMPACTO

```
Impacto Alto + Esfuerzo Bajo → PRIMERO
├── 1.1 Unificar settings (2h)
├── 1.2 Integrar APIs (3h)
├── 2.1 Simplificar navegación (1h)
└── 2.4 Dashboard básico (2h)

Impacto Alto + Esfuerzo Alto → SEGUNDO
├── 3.2 Mejorar orquestador (2h)
├── 4.1 Validación APIs (3h)
└── 2.3 Panel de APIs (2h)

Impacto Bajo + Esfuerzo Bajo → TERCERO
├── 5.2 Eliminar legacy (30m)
├── 1.4 Crear directorios (30m)
└── 5.1 Optimizar UI (1h)

Impacto Bajo + Esfuerzo Alto → ÚLTIMO
├── 5.4 Tests completos (4h)
└── 5.3 Documentación (1h)
```

---

## ⚡ ORDEN DE EJECUCIÓN RECOMENDADO

### **SPRINT 1: Fundamentos** (8 horas)
1. Unificar settings en v2
2. Integrar APIs con validación
3. Simplificar navegación
4. Crear directorios de datos

### **SPRINT 2: Dashboard & Visibilidad** (6 horas)
1. Dashboard del sistema
2. Security dashboard básico
3. System monitoring básico
4. Notificaciones en UI

### **SPRINT 3: Core & Integraciones** (10 horas)
1. Mejorar orquestador
2. Integrar LLM config
3. Validación automática APIs
4. Skills externas mejorado

### **SPRINT 4: Pulido** (6 horas)
1. Optimizaciones
2. Eliminar legacy
3. Tests críticos
4. Documentación mínima

---

## ✅ DEFINICIÓN DE "COMPLETO"

El sistema estará completo cuando:

1. **UI cohesiva:** Todas las vistas usan settings_v2, navegación simple
2. **20 APIs:** Todas configurables y testeables desde UI
3. **Dashboard:** Vista de resumen del sistema funcional
4. **Seguridad visible:** Panel de seguridad integrado
5. **Monitoreo:** Estado del sistema en tiempo real
6. **Tests básicos:** Flujo principal testeado (UI → Skill → Resultado)
7. **Sin errores:** No hay imports rotos, no hay referencias a archivos inexistentes

---

## 📁 ARCHIVOS A ELIMINAR/RENOMBRAR

### Eliminar:
- `core/WebUI.legacy.py` (302KB, no se usa)
- `core/ui/views/settings_view.py` (reemplazado por v2)
- `core/ui/views/orchestrator_view.py.bak`
- `core/ui/views/business_apis.py` (integrar en settings_v2)
- `core/ui/views/business_apis_extra.py` (integrar en settings_v2)
- Archivos scripts de migración (step1_add_sections.py, etc.)

### Mover a tools/ o docs/:
- `auditoria_general.py`
- `test_ui_simulator.py`
- `simulation_report.txt`
- `persistencia_apis_code.txt`

---

## 🔧 HERRAMIENTAS NECESARIAS

- PyQt5 (ya instalado)
- QPainter para dashboard visual
- psutil para métricas de sistema
- Tests con pytest-qt

---

**Próximo paso:** ¿Empezamos con Sprint 1 - Fundamentos?
