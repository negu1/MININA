"""
Nuevo sistema de navegación por categorías para APIs
Estructura:
- SettingsView (main)
  - CategorySelectionScreen (selección de categoría)
    - AI APIs
    - Bot APIs  
    - Business APIs
  - APIListScreen (listado de APIs en categoría)
    - Muestra APIs de la categoría seleccionada
    - Indicador de configurado/no configurado
  - APIConfigScreen (configuración individual)
    - Formulario específico para cada API
    - Guardar/eliminar
    - Probar conexión
"""

API_CATEGORIES = {
    "ai": {
        "name": "🤖 APIs de Inteligencia Artificial",
        "description": "APIs para modelos de lenguaje y IA",
        "apis": {
            "openai": {
                "name": "OpenAI",
                "icon": "🤖",
                "description": "GPT-4, GPT-3.5, DALL-E, Whisper",
                "fields": [
                    {"name": "api_key", "label": "API Key", "type": "password", "placeholder": "sk-...", "required": True}
                ]
            },
            "groq": {
                "name": "Groq",
                "icon": "⚡",
                "description": "Inferencia ultrarrápida con LLMs",
                "fields": [
                    {"name": "api_key", "label": "API Key", "type": "password", "placeholder": "gsk_...", "required": True}
                ]
            },
            "anthropic": {
                "name": "Anthropic",
                "icon": "🧠",
                "description": "Claude AI - Modelos conversacionales",
                "fields": [
                    {"name": "api_key", "label": "API Key", "type": "password", "placeholder": "sk-ant-...", "required": True}
                ]
            }
        }
    },
    "bots": {
        "name": "💬 APIs de Bots y Mensajería",
        "description": "Conecta con plataformas de mensajería",
        "apis": {
            "telegram": {
                "name": "Telegram Bot",
                "icon": "🚀",
                "description": "Bot para Telegram",
                "fields": [
                    {"name": "token", "label": "Bot Token", "type": "password", "placeholder": "123456789:ABCdef...", "required": True},
                    {"name": "chat_id", "label": "Chat ID", "type": "text", "placeholder": "12345678 o -100...", "required": True}
                ]
            },
            "whatsapp": {
                "name": "WhatsApp Business",
                "icon": "💬",
                "description": "API de WhatsApp Business",
                "fields": [
                    {"name": "api_key", "label": "API Key / Token", "type": "password", "placeholder": "EAAxxxxx...", "required": True},
                    {"name": "phone_id", "label": "Phone Number ID", "type": "text", "placeholder": "123456789012345", "required": True}
                ]
            },
            "discord": {
                "name": "Discord Bot",
                "icon": "🎮",
                "description": "Bot para Discord",
                "fields": [
                    {"name": "token", "label": "Bot Token", "type": "password", "placeholder": "MTAxMD...
