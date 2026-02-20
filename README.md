# MININA - Asistente Virtual

**MININA** es un asistente virtual inteligente con interfaz local PyQt5 moderna, soporte para skills personalizadas, integración con bots de Telegram/WhatsApp y múltiples proveedores de IA.

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno (opcional)
copy .env.example .env
# Editar .env con tus credenciales

# 3. Iniciar MININA UI Local
python iniciar_minina.py
```

**Se abrirá la interfaz gráfica PyQt5 automáticamente**

## 📁 Estructura

```
MININA/
├── core/              # Módulos principales
│   ├── ui/            # UI Local PyQt5 (única interfaz)
│   ├── SkillVault.py  # Gestión de skills
│   └── ...
├── tools/            # Herramientas de validación
├── assets/           # Recursos estáticos
├── skills_user/      # Skills del usuario
├── iniciar_minina.py # Launcher principal (UI Local)
└── requirements.txt  # Dependencias
```

## ✨ Características

- 🖥️ **UI Local PyQt5** - Interfaz nativa moderna (única interfaz, no hay duplicados)
- 🤖 **Skills** - Crea y ejecuta habilidades personalizadas
- 💬 **Chat IA** - Integración con múltiples LLMs
- 🔐 **Seguridad** - Sandbox para skills, validación AST
- 📱 **Bots** - Soporte para Telegram y WhatsApp
- 💾 **Backup** - Sistema de respaldo automático

## 🎯 Interfaz

MININA ahora usa **exclusivamente UI Local PyQt5**. No hay WebUI ni duplicación de interfaces. Todo tu trabajo, skills y configuración se manejan desde la interfaz local única.

## 🛠️ Herramientas de Desarrollo

```bash
# Validar estructura del proyecto
python tools/validate_webui.py

# Diagnóstico completo
python tools/webui_diagnostics.py
```

## 🗑️ Cambios Recientes

- **WebUI eliminada**: Ahora solo existe UI Local PyQt5
- **Standalone**: UI Local conecta directamente con managers, no usa HTTP
- **Sin duplicados**: Todo el trabajo se centraliza en una sola interfaz

## ⚙️ Configuración

Ver `.env.example` para opciones de configuración.

## 📄 Licencia

Proyecto personal - Uso libre

---
**Versión:** 1.0.0 | **Creado:** 2026
