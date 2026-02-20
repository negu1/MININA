"""
MiIA LLM API Integration Module
Soporta: OpenAI, Gemini, Groq, Meta, Ollama (local), y modelos descargables (Qwen2.5, Phi-4)
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
from pathlib import Path

logger = logging.getLogger("LLMManager")

class ProviderType(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    GROQ = "groq"
    META = "meta"
    OLLAMA = "ollama"  # Local
    QWEN_LOCAL = "qwen_local"  # Descargado por usuario
    PHI4_LOCAL = "phi4_local"  # Descargado por usuario

@dataclass
class ProviderConfig:
    provider: ProviderType
    api_key: str = ""  # Encriptada en producción
    base_url: str = ""
    model: str = ""
    enabled: bool = False
    is_local: bool = False
    download_url: str = ""  # Para modelos locales que necesitan descarga
    description: str = ""

# Configuraciones por defecto de providers
DEFAULT_PROVIDERS = {
    ProviderType.OPENAI: ProviderConfig(
        provider=ProviderType.OPENAI,
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        description="OpenAI GPT-4o Mini (económico) o GPT-4o (premium)"
    ),
    ProviderType.GEMINI: ProviderConfig(
        provider=ProviderType.GEMINI,
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model="gemini-1.5-flash",
        description="Google Gemini 1.5 Flash (rápido) o Pro (avanzado)"
    ),
    ProviderType.GROQ: ProviderConfig(
        provider=ProviderType.GROQ,
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        description="Groq - Llama 3.1 8B (ultra rápido) o 70B (potente)"
    ),
    ProviderType.META: ProviderConfig(
        provider=ProviderType.META,
        base_url="https://api.meta.ai/v1",  # Ejemplo, ajustar según API real
        model="llama-3.1-8b",
        description="Meta Llama (via API oficial o partner)"
    ),
    ProviderType.OLLAMA: ProviderConfig(
        provider=ProviderType.OLLAMA,
        base_url="http://localhost:11434",
        model="llama3.1",
        is_local=True,
        download_url="https://ollama.com/download",
        description="Ollama - Ejecuta modelos localmente (Llama, Mistral, etc.)"
    ),
    ProviderType.QWEN_LOCAL: ProviderConfig(
        provider=ProviderType.QWEN_LOCAL,
        base_url="http://localhost:11434",  # Via Ollama o similar
        model="qwen2.5:7b",
        is_local=True,
        download_url="https://ollama.com/library/qwen2.5",
        description="Qwen 2.5 (Alibaba) - Modelo open source multilingüe"
    ),
    ProviderType.PHI4_LOCAL: ProviderConfig(
        provider=ProviderType.PHI4_LOCAL,
        base_url="http://localhost:11434",
        model="phi4:14b",
        is_local=True,
        download_url="https://ollama.com/library/phi4",
        description="Microsoft Phi-4 - Modelo eficiente y potente"
    ),
}

# Modelos disponibles por provider
AVAILABLE_MODELS = {
    ProviderType.OPENAI: [
        ("gpt-4o-mini", "GPT-4o Mini - Rápido y económico"),
        ("gpt-4o", "GPT-4o - Máxima calidad"),
        ("gpt-3.5-turbo", "GPT-3.5 Turbo - Legacy"),
    ],
    ProviderType.GEMINI: [
        ("gemini-1.5-flash", "Gemini 1.5 Flash - Rápido"),
        ("gemini-1.5-pro", "Gemini 1.5 Pro - Avanzado"),
        ("gemini-1.0-pro", "Gemini 1.0 Pro - Legacy"),
    ],
    ProviderType.GROQ: [
        ("llama-3.1-8b-instant", "Llama 3.1 8B - Ultra rápido"),
        ("llama-3.1-70b-versatile", "Llama 3.1 70B - Potente"),
        ("mixtral-8x7b-32768", "Mixtral 8x7B - Buen balance"),
        ("gemma-7b-it", "Gemma 7B - Google"),
    ],
    ProviderType.META: [
        ("llama-3.1-8b", "Llama 3.1 8B"),
        ("llama-3.1-70b", "Llama 3.1 70B"),
        ("llama-3-8b", "Llama 3 8B"),
    ],
    ProviderType.OLLAMA: [
        ("llama3.1", "Llama 3.1"),
        ("llama3", "Llama 3"),
        ("mistral", "Mistral"),
        ("codellama", "Code Llama"),
        ("neural-chat", "Neural Chat"),
    ],
    ProviderType.QWEN_LOCAL: [
        ("qwen2.5:0.5b", "Qwen 2.5 0.5B - Muy ligero"),
        ("qwen2.5:1.5b", "Qwen 2.5 1.5B - Ligero"),
        ("qwen2.5:7b", "Qwen 2.5 7B - Estándar"),
        ("qwen2.5:14b", "Qwen 2.5 14B - Potente"),
        ("qwen2.5:32b", "Qwen 2.5 32B - Máximo"),
    ],
    ProviderType.PHI4_LOCAL: [
        ("phi4:14b", "Phi-4 14B - Estándar"),
    ],
}

class LLMManager:
    """Gestor centralizado de conexiones LLM"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.config_path = Path("data/llm_config.json")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.providers: Dict[ProviderType, ProviderConfig] = {}
        self.active_provider: Optional[ProviderType] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        self._load_config()
    
    def _load_config(self):
        """Cargar configuración desde archivo"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Cargar providers
                for key, val in data.get("providers", {}).items():
                    try:
                        provider_type = ProviderType(key)
                        self.providers[provider_type] = ProviderConfig(**val)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error cargando provider {key}: {e}")
                
                # Provider activo
                active = data.get("active_provider")
                if active:
                    self.active_provider = ProviderType(active)
                    
            except Exception as e:
                logger.error(f"Error cargando config LLM: {e}")
        
        # Inicializar providers faltantes con defaults
        for ptype, default in DEFAULT_PROVIDERS.items():
            if ptype not in self.providers:
                self.providers[ptype] = default

        # Permitir override de URL local de Ollama vía env
        try:
            ollama_url = str(os.environ.get("MIIA_OLLAMA_URL") or os.environ.get("OLLAMA_BASE_URL") or "").strip()
            if ollama_url:
                self.providers[ProviderType.OLLAMA].base_url = ollama_url
        except Exception:
            pass

        # Si no hay provider activo configurado, preferir Ollama (local) por defecto.
        # Esto evita el estado "no conecta" cuando en realidad no hay provider seleccionado.
        if self.active_provider is None:
            self.active_provider = ProviderType.OLLAMA
            try:
                self._save_config()
            except Exception:
                pass
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            data = {
                "providers": {
                    k.value: asdict(v) for k, v in self.providers.items()
                },
                "active_provider": self.active_provider.value if self.active_provider else None,
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando config LLM: {e}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtener o crear sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120),
                headers={"User-Agent": "MiIA-Product-20/1.0"}
            )
        return self._session
    
    def set_api_key(self, provider: ProviderType, api_key: str) -> bool:
        """Configurar API key (en producción: encriptar)"""
        if provider not in self.providers:
            return False
        
        # TODO: Encriptar API key antes de guardar
        self.providers[provider].api_key = api_key
        self.providers[provider].enabled = bool(api_key)
        self._save_config()
        return True
    
    def set_model(self, provider: ProviderType, model: str) -> bool:
        """Cambiar modelo de un provider"""
        if provider not in self.providers:
            return False
        
        self.providers[provider].model = model
        self._save_config()
        return True
    
    def set_active_provider(self, provider: ProviderType) -> bool:
        """Cambiar provider activo"""
        if provider not in self.providers:
            return False
        
        config = self.providers[provider]
        
        # Verificar que esté configurado (API key o es local)
        if not config.is_local and not config.api_key:
            return False
        
        self.active_provider = provider
        self._save_config()
        return True
    
    def get_active_config(self) -> Optional[ProviderConfig]:
        """Obtener configuración del provider activo"""
        if self.active_provider:
            return self.providers.get(self.active_provider)
        return None
    
    def list_available_providers(self) -> List[Dict[str, Any]]:
        """Listar todos los providers con estado"""
        result = []
        for ptype, config in self.providers.items():
            result.append({
                "id": ptype.value,
                "name": ptype.name.replace("_", " ").title(),
                "enabled": config.enabled or config.is_local,
                "is_local": config.is_local,
                "model": config.model,
                "has_key": bool(config.api_key),
                "description": config.description,
                "download_url": config.download_url if config.is_local else None,
                "is_active": self.active_provider == ptype,
            })
        return result
    
    def get_models_for_provider(self, provider: ProviderType) -> List[tuple]:
        """Obtener modelos disponibles para un provider"""
        return AVAILABLE_MODELS.get(provider, [])
    
    async def check_local_provider(self, provider: ProviderType) -> Dict[str, Any]:
        """Verificar estado de provider local (Ollama, etc.)"""
        if provider not in self.providers:
            return {"available": False, "error": "Provider no configurado"}
        
        config = self.providers[provider]
        if not config.is_local:
            return {"available": False, "error": "No es un provider local"}
        
        # Verificar si Ollama está corriendo
        try:
            session = await self._get_session()
            async with session.get(f"{config.base_url}/api/tags", timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return {
                        "available": True,
                        "models": models,
                        "message": f"Ollama disponible con {len(models)} modelos"
                    }
                else:
                    return {"available": False, "error": f"HTTP {resp.status}"}
        except aiohttp.ClientConnectorError:
            return {
                "available": False,
                "error": "Ollama no está corriendo",
                "install_url": config.download_url,
                "setup_instructions": [
                    f"1. Descarga Ollama: {config.download_url}",
                    "2. Instala y ejecuta Ollama",
                    f"3. Descarga el modelo: ollama pull {config.model}",
                    "4. Listo para usar"
                ]
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """Generar texto con el provider activo"""
        
        if not self.active_provider:
            yield "Error: No hay provider LLM configurado. Configura uno en la configuración."
            return
        
        config = self.providers[self.active_provider]
        
        if config.is_local:
            async for chunk in self._generate_ollama(config, prompt, system, max_tokens, temperature, stream):
                yield chunk
        elif self.active_provider == ProviderType.OPENAI:
            async for chunk in self._generate_openai(config, prompt, system, max_tokens, temperature, stream):
                yield chunk
        elif self.active_provider == ProviderType.GEMINI:
            async for chunk in self._generate_gemini(config, prompt, system, max_tokens, temperature, stream):
                yield chunk
        elif self.active_provider == ProviderType.GROQ:
            async for chunk in self._generate_openai_compatible(config, prompt, system, max_tokens, temperature, stream):
                yield chunk
        else:
            yield f"Provider {config.provider.name} no implementado aún"
    
    async def _generate_openai(
        self, config: ProviderConfig, prompt: str, system: str,
        max_tokens: int, temperature: float, stream: bool
    ) -> AsyncGenerator[str, None]:
        """Generar con API OpenAI compatible"""
        try:
            session = await self._get_session()
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": config.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream,
            }
            
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            }
            
            async with session.post(
                f"{config.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    yield f"Error OpenAI: {resp.status} - {error}"
                    return
                
                if stream:
                    async for line in resp.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                if content:
                                    yield content
                            except:
                                pass
                else:
                    data = await resp.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    yield content
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def _generate_openai_compatible(
        self, config: ProviderConfig, prompt: str, system: str,
        max_tokens: int, temperature: float, stream: bool
    ) -> AsyncGenerator[str, None]:
        """APIs compatibles con OpenAI (Groq, etc.)"""
        # Mismo formato que OpenAI
        async for chunk in self._generate_openai(config, prompt, system, max_tokens, temperature, stream):
            yield chunk
    
    async def _generate_gemini(
        self, config: ProviderConfig, prompt: str, system: str,
        max_tokens: int, temperature: float, stream: bool
    ) -> AsyncGenerator[str, None]:
        """Generar con Google Gemini"""
        try:
            session = await self._get_session()
            
            url = f"{config.base_url}/models/{config.model}:generateContent?key={config.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": temperature,
                }
            }
            
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}
            
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    yield f"Error Gemini: {resp.status} - {error}"
                    return
                
                data = await resp.json()
                candidates = data.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    yield content
                else:
                    yield "Error: No se recibió respuesta de Gemini"
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    async def _generate_ollama(
        self, config: ProviderConfig, prompt: str, system: str,
        max_tokens: int, temperature: float, stream: bool
    ) -> AsyncGenerator[str, None]:
        """Generar con Ollama local"""
        try:
            session = await self._get_session()
            
            payload = {
                "model": config.model,
                "prompt": prompt,
                "system": system,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            async with session.post(
                f"{config.base_url}/api/generate",
                json=payload
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    yield f"Error Ollama: {resp.status} - {error}"
                    return
                
                if stream:
                    async for line in resp.content:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if not data.get('done'):
                                yield data.get('response', '')
                        except:
                            pass
                else:
                    # Ollama siempre stream, acumulamos
                    full_response = ""
                    async for line in resp.content:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            full_response += data.get('response', '')
                        except:
                            pass
                    yield full_response
                    
        except Exception as e:
            yield f"Error Ollama: {str(e)}. ¿Está Ollama corriendo?"
    
    async def close(self):
        """Cerrar sesiones"""
        if self._session and not self._session.closed:
            await self._session.close()


# Instancia global
llm_manager = LLMManager()
