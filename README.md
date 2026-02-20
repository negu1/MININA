# MININA - Asistente Virtual

**MININA** es un asistente virtual inteligente con interfaz web moderna, soporte para skills personalizadas, integración con bots de Telegram/WhatsApp y múltiples proveedores de IA.

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno (opcional)
copy .env.example .env
# Editar .env con tus credenciales

# 3. Iniciar MININA
python iniciar_minina.py
```

**Abre:** http://127.0.0.1:8897

## 📁 Estructura

```
MININA/
├── core/              # Módulos principales
│   ├── WebUI.py      # Interfaz web
│   ├── SkillVault.py # Gestión de skills
│   └── ...
├── tools/            # Herramientas de validación
├── assets/           # Recursos estáticos
├── skills_user/      # Skills del usuario
├── iniciar_minina.py # Launcher principal
└── requirements.txt  # Dependencias
```

## ✨ Características

- 🌐 **WebUI Moderna** - Interfaz responsive con Tailwind CSS
- 🤖 **Skills** - Crea y ejecuta habilidades personalizadas
- 💬 **Chat IA** - Integración con múltiples LLMs
- 🔐 **Seguridad** - Sandbox para skills, validación AST
- 📱 **Bots** - Soporte para Telegram y WhatsApp
- 💾 **Backup** - Sistema de respaldo automático

## 🛠️ Herramientas de Desarrollo

```bash
# Validar estructura WebUI
python tools/validate_webui.py

# Diagnóstico completo
python tools/webui_diagnostics.py
```

## ⚙️ Configuración

Ver `.env.example` para opciones de configuración.

## 📄 Licencia

Proyecto personal - Uso libre

---
**Versión:** 1.0.0 | **Creado:** 2026
