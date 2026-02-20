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
        "color": "#6366f1",
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
        "color": "#22c55e",
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
                    {"name": "token", "label": "Bot Token", "type": "password", "placeholder": "MTAxMD...", "required": True}
                ]
            },
            "slack": {
                "name": "Slack Bot",
                "icon": "💼",
                "description": "Bot para Slack",
                "fields": [
                    {"name": "token", "label": "Bot Token", "type": "password", "placeholder": "xoxb-...", "required": True}
                ]
            }
        }
    },
    "business": {
        "name": "🏢 APIs Empresariales",
        "description": "Conecta con plataformas de negocio",
        "color": "#f59e0b",
        "subcategories": {
            "crm": {
                "name": "📊 CRM",
                "apis": {
                    "salesforce": {
                        "name": "Salesforce",
                        "icon": "☁️",
                        "description": "CRM líder en el mercado",
                        "fields": [
                            {"name": "username", "label": "Username", "type": "text", "placeholder": "email@ejemplo.com", "required": True},
                            {"name": "password", "label": "Password", "type": "password", "placeholder": "********", "required": True},
                            {"name": "security_token", "label": "Security Token", "type": "password", "placeholder": "token...", "required": True}
                        ]
                    },
                    "pipedrive": {
                        "name": "Pipedrive",
                        "icon": "🎯",
                        "description": "CRM de ventas visual",
                        "fields": [
                            {"name": "api_token", "label": "API Token", "type": "password", "placeholder": "token...", "required": True}
                        ]
                    }
                }
            },
            "finance": {
                "name": "💰 Finanzas",
                "apis": {
                    "quickbooks": {
                        "name": "QuickBooks",
                        "icon": "📗",
                        "description": "Contabilidad y finanzas",
                        "fields": [
                            {"name": "client_id", "label": "Client ID", "type": "text", "placeholder": "AB...", "required": True},
                            {"name": "client_secret", "label": "Client Secret", "type": "password", "placeholder": "secret...", "required": True},
                            {"name": "realm_id", "label": "Realm ID / Company ID", "type": "text", "placeholder": "12345", "required": True}
                        ]
                    },
                    "xero": {
                        "name": "Xero",
                        "icon": "📘",
                        "description": "Software de contabilidad",
                        "fields": [
                            {"name": "client_id", "label": "Client ID", "type": "text", "placeholder": "id...", "required": True},
                            {"name": "client_secret", "label": "Client Secret", "type": "password", "placeholder": "secret...", "required": True}
                        ]
                    },
                    "paypal": {
                        "name": "PayPal",
                        "icon": "💳",
                        "description": "Pagos en línea",
                        "fields": [
                            {"name": "client_id", "label": "Client ID", "type": "text", "placeholder": "Ae...", "required": True},
                            {"name": "client_secret", "label": "Client Secret", "type": "password", "placeholder": "secret...", "required": True}
                        ]
                    },
                    "square": {
                        "name": "Square",
                        "icon": "⬜",
                        "description": "Procesamiento de pagos",
                        "fields": [
                            {"name": "access_token", "label": "Access Token", "type": "password", "placeholder": "EAAA...", "required": True}
                        ]
                    }
                }
            },
            "ecommerce": {
                "name": "🛒 E-commerce",
                "apis": {
                    "shopify": {
                        "name": "Shopify",
                        "icon": "🛍️",
                        "description": "Plataforma de e-commerce",
                        "fields": [
                            {"name": "store_url", "label": "Store URL", "type": "text", "placeholder": "tu-tienda.myshopify.com", "required": True},
                            {"name": "access_token", "label": "Access Token", "type": "password", "placeholder": "shpat_...", "required": True}
                        ]
                    },
                    "woocommerce": {
                        "name": "WooCommerce",
                        "icon": "🛒",
                        "description": "Plugin de WordPress",
                        "fields": [
                            {"name": "store_url", "label": "Store URL", "type": "text", "placeholder": "https://tutienda.com", "required": True},
                            {"name": "consumer_key", "label": "Consumer Key", "type": "text", "placeholder": "ck_...", "required": True},
                            {"name": "consumer_secret", "label": "Consumer Secret", "type": "password", "placeholder": "cs_...", "required": True}
                        ]
                    }
                }
            },
            "support": {
                "name": "🎫 Soporte",
                "apis": {
                    "zendesk": {
                        "name": "Zendesk",
                        "icon": "🎫",
                        "description": "Soporte al cliente",
                        "fields": [
                            {"name": "subdomain", "label": "Subdomain", "type": "text", "placeholder": "tudominio", "required": True},
                            {"name": "email", "label": "Email", "type": "text", "placeholder": "tu@email.com", "required": True},
                            {"name": "api_token", "label": "API Token", "type": "password", "placeholder": "token...", "required": True}
                        ]
                    },
                    "freshdesk": {
                        "name": "Freshdesk",
                        "icon": "🆘",
                        "description": "Software de soporte",
                        "fields": [
                            {"name": "domain", "label": "Domain", "type": "text", "placeholder": "tudominio.freshdesk.com", "required": True},
                            {"name": "api_key", "label": "API Key", "type": "password", "placeholder": "key...", "required": True}
                        ]
                    }
                }
            },
            "project": {
                "name": "📋 Gestión de Proyectos",
                "apis": {
                    "clickup": {
                        "name": "ClickUp",
                        "icon": "☑️",
                        "description": "Gestión de tareas",
                        "fields": [
                            {"name": "api_token", "label": "API Token", "type": "password", "placeholder": "pk_...", "required": True}
                        ]
                    },
                    "wrike": {
                        "name": "Wrike",
                        "icon": "📊",
                        "description": "Gestión de proyectos",
                        "fields": [
                            {"name": "permanent_access_token", "label": "Access Token", "type": "password", "placeholder": "token...", "required": True}
                        ]
                    }
                }
            },
            "docs": {
                "name": "📄 Documentación",
                "apis": {
                    "gitlab": {
                        "name": "GitLab",
                        "icon": "🦊",
                        "description": "Repositorios Git",
                        "fields": [
                            {"name": "url", "label": "GitLab URL", "type": "text", "placeholder": "https://gitlab.com", "required": True},
                            {"name": "personal_access_token", "label": "Access Token", "type": "password", "placeholder": "glpat-...", "required": True}
                        ]
                    },
                    "airtable": {
                        "name": "Airtable",
                        "icon": "🗂️",
                        "description": "Base de datos flexible",
                        "fields": [
                            {"name": "personal_access_token", "label": "Access Token", "type": "password", "placeholder": "pat...", "required": True}
                        ]
                    },
                    "confluence": {
                        "name": "Confluence",
                        "icon": "📄",
                        "description": "Wiki empresarial",
                        "fields": [
                            {"name": "url", "label": "URL", "type": "text", "placeholder": "https://tudominio.atlassian.net/wiki", "required": True},
                            {"name": "email", "label": "Email", "type": "text", "placeholder": "tu@email.com", "required": True},
                            {"name": "api_token", "label": "API Token", "type": "password", "placeholder": "token...", "required": True}
                        ]
                    }
                }
            }
        }
    }
}
