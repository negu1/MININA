# MININA — Perfil de Plataforma

> **Versión**: Beta de lanzamiento (recorte funcional)  
> **Tiempo de desarrollo**: 6 meses de trabajo activo  
> **Estado**: Módulo de automatización segura en fase de validación. La versión completa de MININA está en desarrollo y se lanzará en etapas.

---

## ¿Qué es MININA?

**MININA** es una plataforma de automatización inteligente con enfoque en **seguridad**, **agentes efímeros**, y **herramientas controladas (skills)**. Combina una interfaz local (UI) con integraciones remotas (como Telegram) para ejecutar tareas útiles del mundo real, manteniendo al usuario siempre en control de las acciones sensibles.

- **Enfoque principal**: ejecutar tareas prácticas con IA, sin convertir a la IA en un "superusuario" de tu máquina.
- **Modelo operativo**: "**capabilities mínimas + ejecución puntual + destrucción del agente**".
- **Propuesta**: un "sistema operativo de automatización", con un cerebro que decide, pero con **manos limitadas, auditables y de un solo uso**.

---

## ¿Para qué sirve?

MININA permite **delegar trabajo real** (técnico y administrativo) a un sistema que:

- Orquesta tareas mediante **skills** (módulos de herramientas).
- Integra APIs externas (negocio, productividad, comunicación).
- Ejecuta acciones localmente o en servicios conectados.
- Mantiene un **gate de seguridad** cuando hay riesgos (por ejemplo, escribir archivos en disco).

En términos simples: es un asistente que puede hacer cosas reales (crear archivos, enviar mensajes, gestionar tareas) pero **solo cuando tú lo apruebas** y **sin quedarse con privilegios permanentes**.

---

## Funciones principales

### 1) UI de control (operación local)
- Configuración de servicios y credenciales.
- Gestión de integraciones (Telegram, APIs de negocio).
- Control de ejecución y estado (inicio / apagado limpio).
- Paneles de monitoreo y logs seguros.

### 2) Bot de Telegram (interfaz remota segura)
- Permite ejecutar tareas por chat, desde cualquier lugar.
- Maneja flujos conversacionales (comandos + acciones).
- Incluye un **sistema de aprobación en dos pasos** para acciones sensibles.
- Puede enviar resultados (texto / archivos) cuando corresponde.

### 3) Skills (herramientas modulares)
- Cada skill define qué hace y qué permisos necesita en un `manifest.json`.
- Ejemplo real: una skill que crea un **PDF** requiere permiso `fs_write`.
- Las skills son:
  - Plug-and-play (copiar y listo).
  - Mínimamente privilegiadas.
  - Auditables por su manifest.

### 4) Agentes efímeros (use-and-kill)
MININA ejecuta tareas a través de agentes "de paso", diseñados para ser **de usar y tirar**:

- Se crean para ejecutar **un objetivo puntual**.
- Se les habilitan **solo las capacidades necesarias** (capability-based).
- Al finalizar:
  - Se limpia su entorno de ejecución (sandbox).
  - Se remueven credenciales temporales.
  - Se restaura el contexto del sistema.
  - El agente se destruye (no queda persistente con poder).

---

## Seguridad: pilares principales

### 1. Capability-Based Security (permisos mínimos)
Las acciones están gobernadas por un modelo de permisos por skill. Ejemplos:

- `fs_write`: escribir/crear archivos en disco (**alto riesgo**).
- Acceso a APIs externas (configurable por skill).

**Regla**: si no está declarado en el manifest, no se permite.

### 2. Doble confirmación para acciones HIGH
Para acciones sensibles, MININA aplica un flujo de aprobación:

1. **Confirmación explícita** (botón ✅/❌ en Telegram).
2. **PIN de administrador** (segunda barrera).

Esto evita que:
- Un mensaje ambiguo dispare acciones peligrosas.
- Una cuenta/telegram abierto ejecute cosas sin tu intención.
- Una inyección de prompt tenga vía libre.

### 3. PIN seguro (sin .env / sin logs / sin LLM)
El PIN no se guarda en texto plano:

- Almacenado como **hash con salt** (PBKDF2-HMAC-SHA256).
- Guardado en archivos dedicados (ej.: `data/admin_pin.json`).
- **Nunca** se envía a APIs.
- **Nunca** aparece en logs.
- **Nunca** se comparte con el modelo de lenguaje.

### 4. Manejo de secretos (SecureCredentialStore)
Credenciales como tokens de Telegram, chat_id, claves de APIs (Asana/Dropbox/etc.) se manejan mediante un **almacenamiento controlado** con encriptación.

**Objetivos**:
- No depender de `.env` para secretos críticos.
- Evitar filtrado accidental por logs o prompts.
- Permitir rotación y gestión centralizada.

### 5. Prevención de instancias múltiples
Al iniciar, MININA detecta y termina instancias previas para evitar:
- Conflictos de polling (ej.: error 409 de Telegram).
- Procesos huérfanos consumiendo recursos.

### 6. Shutdown limpio
Al cerrar la UI, MININA:
- Detiene el polling del bot de Telegram.
- Limpia hilos y procesos pendientes.
- Cierra recursos de forma ordenada.

---

## APIs e integraciones implementadas

### Productividad / Gestión
- **Asana**: gestión de tareas, proyectos, asignaciones y estados.

### Comunicación
- **Discord**: mensajería automatizada, gestión de canales.
- **Telegram**: bot completo con comandos, aprobaciones y envío de archivos.
- **Email**: envío de correos automatizados.

### Almacenamiento / Archivos
- **Dropbox**: operaciones de archivos en la nube.
- **Google Drive**: gestión de archivos y carpetas.

### Financieras / Datos
- **SerpAPI**: búsqueda en la web (SEO, datos de mercado).
- APIs de negocio adicionales (extensible mediante skills).

---

## Arquitectura: agentes y seguridad

```
Usuario (Telegram/UI)
        │
        ▼
┌─────────────────┐
│   MININA Core   │  ← orquestador principal
│  (Policy Engine)│
└─────────────────┘
        │
        ├──────────────┐
        ▼              ▼
   ┌─────────┐    ┌──────────┐
   │  Skill  │    │  Agent   │  ← agente efímero
   │ Manifest│    │ Spawner  │    (use-and-kill)
   └─────────┘    └──────────┘
                        │
                        ▼
                 ┌─────────────┐
                 │   Sandbox   │  ← entorno aislado
                 │  Ejecución  │
                 └─────────────┘
```

Flujo de una acción HIGH (ejemplo: crear PDF):

1. Usuario solicita ejecutar skill con `fs_write`.
2. MININA detecta permiso HIGH → **bloquea y pide aprobación**.
3. Usuario confirma con botón ✅ en Telegram.
4. MININA pide **PIN** (segunda barrera).
5. PIN verificado → se lanza agente efímero con **solo** permiso `fs_write`.
6. Skill se ejecuta en sandbox aislado.
7. Resultado copiado a ruta segura.
8. **Agente destruido**, credenciales limpiadas, contexto restaurado.
9. Archivo enviado al usuario por Telegram.

---

## Requisitos para instalar

### Sistema
- Windows 10/11, Linux o macOS.
- Python 3.10 o superior.
- Git (para clonar).

### Dependencias principales
- `python-telegram-bot` 20+ (bot asíncrono)
- `PyQt5` (interfaz gráfica)
- `cryptography` (almacenamiento seguro)
- `fpdf2` (generación de PDFs)
- `python-dotenv` (configuración base)
- `requests` (APIs externas)

### Credenciales necesarias
Para usar todas las funciones, necesitarás:
- **Token de Telegram Bot** (de @BotFather).
- **Chat ID** de Telegram (para notificaciones).
- Credenciales de APIs de negocio que quieras usar (Asana, Dropbox, etc.).

---

## Instalación rápida

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd MININA

# 2. Crear entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar
python iniciar_minina.py
```

---

## Uso básico

### Iniciar MININA
```bash
python iniciar_minina.py
```
- Abre la UI automáticamente.
- Si hay credenciales de Telegram guardadas, inicia el bot.
- Mata instancias previas para evitar conflictos.

### Configurar Telegram
1. Ve a **Configuración → Telegram Bot** en la UI.
2. Ingresa tu **Token** y **Chat ID**.
3. Guarda (se almacenan encriptados).
4. Activa el toggle para iniciar el bot.

### Ejecutar una skill segura
En Telegram (o UI):
```
usa skill hola_mundo ejecutar
```

### Ejecutar una skill HIGH (requiere aprobación)
```
usa skill crear_pdf crear
```

Flujo:
1. Aparece botón de confirmación.
2. Luego pide PIN.
3. Finalmente ejecuta y envía resultado.

---

## Roadmap y estado

### ✅ Disponible ahora
- UI funcional con PyQt5.
- Bot de Telegram completo (comandos + aprobaciones + envío de archivos).
- Sistema de skills con manifests y permisos.
- Almacenamiento seguro de credenciales (hash + encriptación).
- Agentes efímeros con sandbox.
- Integraciones: Asana, Discord, Dropbox, Email, SerpAPI, Telegram.

### 🔄 En desarrollo (versión completa de MININA)
- Motor de orquestación avanzado.
- Más integraciones empresariales.
- Dashboard web.
- Multi-usuario con roles.
- API REST propia.
- Plugins de terceros.

---

## Licencia y uso

MININA es un proyecto en desarrollo activo. La versión actual es funcional para automatización personal y pequeños equipos.

**Importante**: este es un recorte de la plataforma completa. Se comparte para validación y feedback, pero no representa la totalidad del sistema que se está construyendo.

---

## Contacto / Comunidad

- Issues: [GitHub Issues URL]
- Discusiones: [Discord/Forum URL]
- Contacto directo: [email]

---

*Documento generado para la versión beta de lanzamiento de MININA.*
*Proyecto en desarrollo desde hace 6 meses. Versión completa en progreso.*
