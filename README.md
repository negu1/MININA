# MININA

**Sistema de automatización segura con autonomía operativa controlada**

---

## ¿Qué es MININA?

MININA es una plataforma de automatización *local-first* diseñada para ejecutar tareas complejas de forma confiable, segura y controlada. Combina agentes efímeros, un sistema de skills declarativas y múltiples canales de comunicación (como Telegram o Email) para operar procesos reales sin exponer al usuario a riesgos de agencia libre.

MININA **no es una IA que decide sola**. Es un sistema que **ejecuta por el humano**, bajo reglas explícitas, permisos declarados y aprobaciones claras.

---

## Modelo de Autonomía

MININA implementa un modelo de **autonomía operativa, no decisional**:

* ❌ No define objetivos propios

* ❌ No redefine prioridades

* ❌ No actúa fuera de flujos aprobados

* ✅ Ejecuta tareas automáticamente

* ✅ Puede operar por eventos o schedules

* ✅ Encadena skills bajo planes definidos

* ✅ Trabaja sin supervisión constante, pero **con control humano**

**Los humanos deciden el qué y el por qué.**
**MININA ejecuta el cómo y el cuándo.**

---

## Arquitectura (alto nivel)

```
Humano
  ↓
Agente (razona dentro de límites)
  ↓
Orchestrator (define el flujo)
  ↓
Skills (ejecutan acciones concretas)
  ↓
Supervisor (valida y audita)
```

* Los agentes son **efímeros** (nacen, trabajan y mueren)
* Las skills **no piensan**, solo ejecutan
* Toda acción sensible pasa por **gates de aprobación**

---

## Principios Clave

* 🔐 Seguridad por diseño (sandbox, permisos, doble confirmación)
* 🧩 Extensibilidad mediante skills en Python
* 🧠 Separación clara entre decisión y ejecución
* 📴 Control total: todo es auditable, reversible y apagable
* 🏠 Local-first: tus datos, tu máquina, tus reglas

---

## Casos de Uso

* Automatización de tareas administrativas
* Reportes diarios/semanales
* Gestión de proyectos (Asana, Notion, etc.)
* Envío de correos, archivos y notificaciones
* Operación de pequeñoso grandes emprresas y negocios (stock, pedidos, cierres ect ect)

---

## ¿Para quién es?

* Usuarios avanzados que quieren automatizar sin perder control
* Pequeños negocios que necesitan ejecutar procesos diarios grandes negocios que necesitas mas control 
* Desarrolladores que buscan una base segura para automatización
* Equipos que no pueden usar soluciones cloud cerradas ect ect

---

## Estado del Proyecto

* Versión: **v0.9 – Beta funcional**
* Arquitectura core: ✅ estable
* Seguridad base: ✅ implementada
* Integraciones iniciales: Telegram, Email, Asana, Dropbox

El proyecto está en evolución activa.

---

## Colaboración y Propuestas

Este proyecto está en fase abierta de exploración y crecimiento.

👉 **Estoy dispuesto a escuchar propuestas**, colaboraciones técnicas, ideas de integración o conversaciones estratégicas.

**Autor:** Daniel Mora
**Contacto:** vía GitHub / repositorio / DANIMOR985@GMAIL.COM /TELEGRAM @DANIDANIP1

---

## Filosofía Final

> Mientras otras herramientas te dan poder sin freno,
> **MININA te da poder con garantías.**

Automatización real, sin perder el control humano.
