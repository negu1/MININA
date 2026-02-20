# AUDITORÍA TÉCNICA DE DEPENDENCIAS Y REQUISITOS DE MININA
## Todo lo necesario para funcionar al máximo: librerías, APIs gratuitas, configs y credenciales

---

## 📋 RESUMEN EJECUTIVO

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| **Librerías Python core** | 15+ | Instalación automática con pip |
| **APIs gratuitas** | 6+ | Requieren registro (free tier disponible) |
| **APIs de pago (opcionales)** | 4+ | Solo si se usan esas funciones |
| **Dependencias sistema** | 3 | Python 3.10+, Git, C++ build tools |
| **Variables de entorno** | 8+ | Tokens, credenciales, configuraciones |
| **Archivos de configuración** | 4+ | JSON, YAML, o en SecureCredentialStore |

---

## PARTE 1: DEPENDENCIAS DE SISTEMA (REQUISITOS PREVIOS)

### 1.1 Requisitos Mínimos del Sistema

| Componente | Versión Mínima | Recomendada | Notas |
|------------|----------------|-------------|-------|
| **Python** | 3.10 | 3.11+ | Async/await completo, mejor performance |
| **Sistema Operativo** | Windows 10 / Ubuntu 20.04 / macOS 11 | Windows 11 / Ubuntu 22.04 / macOS 13 | PyQt5 compatible con todos |
| **RAM** | 4 GB | 8 GB+ | Para múltiples agentes simultáneos |
| **Almacenamiento** | 2 GB libre | 5 GB+ | Skills, logs, archivos temporales |
| **Internet** | 1 Mbps | 5 Mbps+ | APIs de Telegram, LLMs, servicios externos |

### 1.2 Software de Sistema Necesario

```bash
# Windows
# - Visual C++ Build Tools 2019+ (para algunas librerías nativas)
# - Git for Windows
# - PowerShell 5.1+ o Windows Terminal

# Instalación recomendada (Chocolatey):
choco install python git visualstudio2019-workload-vctools

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev git build-essential

# macOS
brew install python@3.11 git
```

### 1.3 Puertos de Red Requeridos (Si hay Firewall)

| Puerto | Protocolo | Uso | Dirección |
|--------|-----------|-----|-----------|
| 443 | TCP HTTPS | Todas las APIs (Telegram, OpenAI, etc.) | Saliente |
| 80 | TCP HTTP | Fallback APIs | Saliente |
| 22 | TCP SSH | Git operations (opcional) | Saliente |

---

## PARTE 2: LIBRERÍAS PYTHON (REQUIREMENTS)

### 2.1 Core Dependencies (Esenciales)

```txt
# ==========================================
# MININA v3.0 - Core Dependencies
# ==========================================

# --- Telegram Bot ---
python-telegram-bot==20.7          # Bot framework asíncrono (v20+ requerido)

# --- UI Desktop ---
PyQt5==5.15.10                     # Interfaz gráfica de escritorio
PyQt5-Qt5==5.15.2                  # Binarios Qt para PyQt5

# --- Seguridad y Encriptación ---
cryptography==41.0.7               # SecureCredentialStore, hashing, AES
bcrypt==4.1.2                      # Alternativa para hashing (opcional)

# --- PDF y Documentos ---
fpdf2==2.7.6                      # Generación de PDFs (skill de ejemplo)
reportlab==4.0.7                   # PDF avanzado (opcional pero recomendado)

# --- Utilidades ---
python-dotenv==1.0.0               # Carga de .env (legacy, aún soportado)
requests==2.31.0                   # HTTP para APIs sin SDK
aiohttp==3.9.1                     # HTTP asíncrono
pathlib2==2.3.7.post1              # Compatibilidad Path (Python < 3.10)
psutil==5.9.6                      # Gestión de procesos (AgentLifecycleManager)

# --- Async y Concurrency ---
asyncio-mqtt==0.16.1               # MQTT async (futuro: IoT)
aiofiles==23.2.1                   # File I/O asíncrono

# --- Data y Configuración ---
pyyaml==6.0.1                      # Parsing de YAML (skills, config)
jsonschema==4.20.0                 # Validación de manifests
python-json-logger==2.0.7          # Logging estructurado

# --- Testing (Desarrollo) ---
pytest==7.4.3                      # Framework de testing
pytest-asyncio==0.21.1             # Soporte async para pytest
pytest-cov==4.1.0                  # Cobertura de tests
```

### 2.2 LLM / AI Dependencies (Para funcionalidades de IA)

```txt
# --- LLM Providers ---
openai==1.6.1                      # OpenAI GPT-4, GPT-3.5, DALL-E
groq==0.4.2                        # Groq API (Llama 2/3, Mixtral)
anthropic==0.8.1                   # Claude API

tiktoken==0.5.2                    # Token counting para OpenAI

# --- Embeddings y Vector DBs (Futuro: RAG) ---
# pinecone-client==2.2.4           # Pinecone vector DB
# chromadb==0.4.18                 # Chroma local vector DB
# faiss-cpu==1.7.4                  # FAISS para embeddings local

# --- Hugging Face (Alternativa local) ---
# transformers==4.36.2             # Modelos Hugging Face
# torch==2.1.2                      # PyTorch (pesado, opcional)
# sentence-transformers==2.2.2       # Embeddings locales
```

### 2.3 Integraciones de APIs (Esenciales para funcionalidades específicas)

```txt
# --- Productividad ---
asana==3.2.1                       # API oficial de Asana
dropbox==11.36.2                   # SDK Dropbox

# --- Comunicación ---
discord.py==2.3.2                  # Bot de Discord

# --- Email ---
# yagmail==0.15.293                 # Email simplificado (opcional)
# keyring==24.3.0                  # Keyring sistema (opcional)

# --- Búsqueda y Datos ---
googlesearch-python==1.2.3         # Búsqueda Google (scraping)
# serpapi==0.1.5                    # SerpAPI oficial (requiere API key)

# --- Calendar (Futuro) ---
# google-api-python-client==2.111.0  # Google Calendar API
# google-auth-httplib2==0.2.0       # Auth Google
# google-auth-oauthlib==1.2.0       # OAuth Google

# --- Storage (Futuro) ---
# google-auth==2.25.2               # Auth Google Drive
# boto3==1.34.11                    # AWS S3 (opcional)
```

### 2.4 Dev / Debugging Dependencies

```txt
# --- Debugging y Profiling ---
# memory-profiler==0.61.0          # Profiling de memoria
# line-profiler==4.1.2             # Profiling línea por línea
# py-spy==0.3.14                   # Profiler de bajo overhead

# --- Linting y Formato ---
# black==23.12.1                   # Formato de código
# pylint==3.0.3                    # Linting
# mypy==1.7.1                      # Type checking

# --- Documentación ---
# sphinx==7.2.6                    # Generación docs
# sphinx-rtd-theme==2.0.0          # Tema ReadTheDocs
```

### 2.5 Lista Combinada (requirements.txt completo)

```txt
# ==========================================
# MININA v3.0 - Requirements Completos
# Generado: Auditoría Técnica
# ==========================================

# --- Core ---
python-telegram-bot==20.7
PyQt5==5.15.10
cryptography==41.0.7
fpdf2==2.7.6
python-dotenv==1.0.0
requests==2.31.0
aiohttp==3.9.1
psutil==5.9.6
pyyaml==6.0.1
jsonschema==4.20.0

# --- LLM / AI ---
openai==1.6.1
groq==0.4.2
anthropic==0.8.1
tiktoken==0.5.2

# --- Integraciones ---
asana==3.2.1
dropbox==11.36.2
discord.py==2.3.2

# --- Async Utils ---
aiofiles==23.2.1

# --- Testing ---
pytest==7.4.3
pytest-asyncio==0.21.1
```

---

## PARTE 3: APIS GRATUITAS (FREE TIER DISPONIBLE)

### 3.1 APIs Esenciales (Obligatorias para funcionamiento básico)

#### 1. Telegram Bot API
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://t.me/BotFather |
| **Costo** | 100% GRATIS |
| **Límites** | 30 mensajes/segundo, 20 mensajes/minuto a mismo chat |
| **Obtención** | Hablar con @BotFather en Telegram, /newbot |
| **Credenciales** | Bot Token (formato: `123456789:ABCdefGHI...`) |
| **Chat ID** | Usar @userinfobot o @raw_data_bot para obtener tu Chat ID |
| **Documentación** | https://core.telegram.org/bots/api |

#### 2. Groq (LLM ultra-rápido)
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://console.groq.com |
| **Costo** | FREE tier: 1,000,000 tokens/minuto |
| **Modelos gratis** | Llama 3.1 70B, Mixtral 8x7B, Gemma 2, etc. |
| **Credenciales** | API Key (formato: `gsk_...`) |
| **Rate limit** | 20 requests/minuto (free) |
| **Documentación** | https://console.groq.com/docs |

### 3.2 APIs Opcionales (Gratuitas con límites)

#### 3. SerpAPI (Búsquedas Google)
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://serpapi.com |
| **Costo** | 100 búsquedas/mes GRATIS |
| **Credenciales** | API Key (formato: `...`) |
| **Alternativa gratis** | `googlesearch-python` (scraping, sin API key) |
| **Documentación** | https://serpapi.com/docs |

#### 4. Asana API
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://app.asana.com/-/developer_console |
| **Costo** | FREE (hasta ciertos límites de uso) |
| **Credenciales** | Personal Access Token |
| **Scopes** | `default`, `oidc`, `profile`, `email` |
| **Documentación** | https://developers.asana.com |

#### 5. Dropbox API
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://www.dropbox.com/developers/apps |
| **Costo** | FREE (hasta 500 usuarios + 15GB storage) |
| **Credenciales** | Access Token (OAuth 2.0) |
| **Permisos** | `files.content.write`, `files.content.read` |
| **Documentación** | https://www.dropbox.com/developers/documentation |

#### 6. Discord Developer Portal
| Aspecto | Detalle |
|---------|---------|
| **URL registro** | https://discord.com/developers/applications |
| **Costo** | 100% GRATIS |
| **Credenciales** | Bot Token |
| **Intents** | `message_content`, `guild_messages`, `direct_messages` |
| **Documentación** | https://discord.com/developers/docs |

### 3.3 APIs de Pago (Opcionales, para features avanzadas)

| API | Costo | Uso | URL |
|-----|-------|-----|-----|
| **OpenAI** | ~$0.01/1K tokens | GPT-4, GPT-3.5, DALL-E | https://platform.openai.com |
| **Anthropic Claude** | ~$0.008/1K tokens | Claude 3 Opus/Sonnet | https://console.anthropic.com |
| **WhatsApp Business** | ~$0.005/mensaje | WhatsApp oficial | https://business.facebook.com |
| **Pinecone** | ~$70/mes (starter) | Vector DB | https://www.pinecone.io |

### 3.4 Tabla de APIs por Prioridad

| Prioridad | API | Free Tier | Requiere Tarjeta | Setup Time |
|-----------|-----|-----------|------------------|------------|
| 🔴 **Obligatoria** | Telegram Bot | ✅ Ilimitado | ❌ No | 2 min |
| 🔴 **Obligatoria** | Groq LLM | ✅ 1M tokens/min | ❌ No | 3 min |
| 🟡 **Recomendada** | SerpAPI | ✅ 100/mes | ❌ No | 5 min |
| 🟡 **Recomendada** | Asana | ✅ Generoso | ❌ No | 10 min |
| 🟢 **Opcional** | Dropbox | ✅ 15GB | ❌ No | 10 min |
| 🟢 **Opcional** | Discord | ✅ Ilimitado | ❌ No | 5 min |
| ⚪ **Futura** | OpenAI | ❌ Pago | ✅ Sí | 5 min |
| ⚪ **Futura** | WhatsApp | ❌ Pago | ✅ Sí | 30 min (verificación) |

---

## PARTE 4: VARIABLES DE ENTORNO Y CONFIGURACIÓN

### 4.1 Variables de Entorno (Legacy - aún soportadas)

```bash
# --- Core ---
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_CHAT_ID=123456789

# --- LLM ---
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# --- Integraciones ---
ASANA_ACCESS_TOKEN=...
DROPBOX_ACCESS_TOKEN=...
DISCORD_BOT_TOKEN=...
SERPAPI_API_KEY=...

# --- Email ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tuemail@gmail.com
SMTP_PASSWORD=tu_app_password
```

### 4.2 SecureCredentialStore (Recomendado)

```python
# Las credenciales se almacenan encriptadas en:
# - Windows: %APPDATA%/MININA/credentials/
# - Linux: ~/.config/MININA/credentials/
# - macOS: ~/Library/Application Support/MININA/credentials/

# Se gestionan vía UI (Configuración → APIs) o vía código:
from core.llm_extension import credential_store
credential_store.set_api_key("telegram_bot_token", "123456789:...")
credential_store.set_api_key("groq_api_key", "gsk_...")
```

### 4.3 Archivos de Configuración JSON

```json
// data/telegram_bot_config.json
{
  "token": "123456789:ABC...",
  "chat_id": "123456789",
  "webhook_url": "",
  "notifications": {
    "works": true,
    "skills": false,
    "errors": true,
    "orchestrator": false
  }
}

// data/admin_pin.json
{
  "pin_hash": "pbkdf2_sha256$...",
  "salt": "...",
  "created_at": "2024-02-20T12:00:00"
}
```

---

## PARTE 5: CHECKLIST DE SETUP COMPLETO

### 5.1 Setup Básico (Mínimo funcional)

```bash
# 1. Clonar repo
git clone <repo-url>
cd MININA

# 2. Crear entorno virtual
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Obtener credenciales
# - Ir a @BotFather en Telegram → /newbot → copiar token
# - Ir a console.groq.com → Create API Key → copiar key

# 5. Configurar credenciales (opción A: UI)
python iniciar_minina.py
# → Configuración → Telegram Bot → pegar token
# → Configuración → LLM → pegar Groq key

# 6. O configurar vía archivo (opción B: legacy)
echo "TELEGRAM_BOT_TOKEN=tu_token" > .env
echo "GROQ_API_KEY=tu_key" >> .env

# 7. Iniciar
python iniciar_minina.py
```

### 5.2 Setup Completo (Máximo potencial)

```bash
# --- APIs a registrar ---
# 1. Telegram Bot (@BotFather) ✅
# 2. Groq (console.groq.com) ✅
# 3. SerpAPI (serpapi.com) - opcional
# 4. Asana (app.asana.com/-/developer_console) - opcional
# 5. Dropbox (dropbox.com/developers/apps) - opcional
# 6. Discord (discord.com/developers/applications) - opcional
# 7. OpenAI (platform.openai.com) - opcional, de pago

# --- Instalación completa ---
# 1. Dependencias core
pip install python-telegram-bot PyQt5 cryptography fpdf2 requests aiohttp psutil pyyaml

# 2. Dependencias LLM
pip install openai groq anthropic tiktoken

# 3. Dependencias integraciones
pip install asana dropbox discord.py

# 4. Dependencias testing
pip install pytest pytest-asyncio

# 5. Iniciar y configurar vía UI
python iniciar_minina.py
```

---

## PARTE 6: SOLUCIÓN DE PROBLEMAS COMUNES

### 6.1 Errores de Instalación

| Error | Causa | Solución |
|-------|-------|----------|
| `error: Microsoft Visual C++ 14.0` | Falta compilador C++ | `pip install --upgrade pip setuptools wheel` + instalar Build Tools |
| `No module named 'PyQt5'` | PyQt5 no instalado | `pip install PyQt5` o usar `pip install -r requirements-ui.txt` |
| `ImportError: cannot import name 'QtWidgets'` | PyQt5 incompleto | `pip uninstall PyQt5 && pip install PyQt5==5.15.10` |
| `ModuleNotFoundError: telegram` | python-telegram-bot faltante | `pip install python-telegram-bot==20.7` |

### 6.2 Errores de API

| Error | Causa | Solución |
|-------|-------|----------|
| `401 Unauthorized` | Token inválido/expirado | Verificar token en BotFather / regenerar |
| `409 Conflict` | Dos bots con mismo token | Matar procesos previos: `taskkill /f /im python.exe` |
| `429 Too Many Requests` | Rate limit | Esperar 1 minuto o reducir frecuencia |
| `groq error 401` | API Key inválida | Verificar key en console.groq.com |

### 6.3 Errores de UI

| Error | Causa | Solución |
|-------|-------|----------|
| `This application failed to start` | Qt platform plugin | `pip install PyQt5-Qt5` o variable `QT_QPA_PLATFORM=windows` |
| `No X11 display` | Intentando UI en servidor | Usar SSH con X11 forwarding o modo headless |
| `QFontDatabase: Cannot find font` | Fuentes faltantes | Instalar fuentes del sistema o ignorar (cosmético) |

---

## PARTE 7: ARQUITECTURA DE DIRECTORIOS IMPORTANTES

```
MININA/
├── 📁 core/                          # Código fuente principal
│   ├── TelegramBot.py               # Bot de Telegram
│   ├── AgentLifecycleManager.py     # Gestión de agentes
│   ├── ui/                          # Interfaz gráfica
│   │   └── views/telegram_bot_view.py
│   └── ...
├── 📁 data/                         # Datos persistentes (gitignore)
│   ├── telegram_bot_config.json    # Config Telegram
│   ├── admin_pin.json              # PIN hasheado
│   ├── SecureCredentialStore/      # Credenciales encriptadas
│   ├── skills/                      # Skills del sistema
│   ├── skills_user/                 # Skills del usuario
│   └── temp_sandbox/                # Sandbox temporal
├── 📁 skills_user/                  # Skills personalizadas (gitignore)
├── 📁 docs/                         # Documentación
│   ├── MININA_PROFILE.md
│   └── AUDITORIA_GENERAL_MININA.md
├── 📁 tests/                        # Tests
├── 📄 requirements.txt               # Dependencias (gitignore)
├── 📄 requirements-ui.txt            # UI deps (gitignore)
├── 📄 .gitignore                    # Excluye data/, secrets
└── 📄 iniciar_minina.py             # Entry point
```

---

## PARTE 8: MANTENIMIENTO Y ACTUALIZACIONES

### 8.1 Actualizar Dependencias

```bash
# Actualizar todas las librerías
pip install --upgrade -r requirements.txt

# Actualizar librería específica
pip install --upgrade python-telegram-bot

# Verificar versiones instaladas
pip list --outdated
```

### 8.2 Rotación de Credenciales

| Credencial | Frecuencia rotación | Cómo rotar |
|------------|---------------------|------------|
| Telegram Bot Token | Si se filtra | @BotFather → /revoke → /newbot |
| Groq API Key | Cada 6 meses | console.groq.com → Delete → Create new |
| Asana Token | Cada 3 meses | Developer Console → Revoke → New |
| PIN Admin | Cada 6 meses | /setadminpin en Telegram |

### 8.3 Backup de Configuración

```bash
# Backup manual
cp -r data/ backup_$(date +%Y%m%d)/

# O excluir datos sensibles
tar -czvf minina_config_backup.tar.gz data/*.json data/skills_user/
```

---

## CONCLUSIÓN

### Resumen de Requisitos

Para que MININA funcione al **máximo potencial**, necesitas:

1. **Python 3.10+** instalado
2. **15+ librerías** (instalables con `pip install -r requirements.txt`)
3. **2 APIs gratuitas obligatorias**: Telegram Bot + Groq LLM
4. **4+ APIs gratuitas opcionales**: SerpAPI, Asana, Dropbox, Discord
5. **Credenciales configuradas** vía UI (SecureCredentialStore) o .env

### Setup Rápido (5 minutos)

```bash
# 1. Clonar e instalar
git clone <repo>
cd MININA && python -m venv venv && venv\Scripts\activate
pip install python-telegram-bot PyQt5 cryptography fpdf2 requests aiohttp psutil pyyaml groq

# 2. Obtener tokens (2 min en Telegram, 2 min en Groq)
# @BotFather → /newbot → copiar token
# console.groq.com → Create API Key → copiar key

# 3. Iniciar y configurar
python iniciar_minina.py
# → Configuración → Telegram Bot → pegar token
# → Configuración → LLM → pegar Groq key

# 4. ¡Listo! Usar desde Telegram
```

---

*Auditoría Técnica generada para MININA v3.0*  
*Estado: Base técnica completa, 6 meses de desarrollo, 25+ integraciones posibles*
