"""
MiIA-Product-20 LLM Extension
Versión simplificada para el producto standalone
Gestión de credenciales y providers LLM
"""
import os
import json
import base64
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger("LLMExtension")

# Intentar importar Fernet para encriptación
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logging.warning("cryptography no disponible, usando almacenamiento básico")


class SecureCredentialStore:
    """Almacenamiento seguro de credenciales API para MiIA-Product-20"""
    
    def __init__(self, app_name: str = "miia-product-20"):
        self.app_name = app_name
        self.config_dir = Path.home() / ".config" / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.creds_file = self.config_dir / "credentials.enc"
        self._key = None
        self._fernet = None
        self._credentials = {}
        
        if CRYPTO_AVAILABLE:
            self._init_encryption()
        else:
            logger.warning("cryptography no disponible, usando almacenamiento sin encriptar")
        
        self._load_credentials()
    
    def _get_machine_id(self) -> str:
        """Obtener ID único de la máquina"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                r"SOFTWARE\Microsoft\Cryptography") as key:
                return winreg.QueryValueEx(key, "MachineGuid")[0]
        except:
            return f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
    
    def _init_encryption(self):
        """Inicializar encriptación"""
        key_file = self.config_dir / ".key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                self._key = f.read()
        else:
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=machine_id.encode(),
                iterations=480000,
            )
            self._key = base64.urlsafe_b64encode(kdf.derive(b"miia-secret-v1"))
            
            with open(key_file, 'wb') as f:
                f.write(self._key)
        
        self._fernet = Fernet(self._key)
    
    def _load_credentials(self):
        """Cargar credenciales"""
        if not self.creds_file.exists():
            return
        
        try:
            if CRYPTO_AVAILABLE and self._fernet:
                with open(self.creds_file, 'rb') as f:
                    encrypted = f.read()
                decrypted = self._fernet.decrypt(encrypted)
                self._credentials = json.loads(decrypted.decode('utf-8'))
            else:
                # Sin encriptación
                with open(self.creds_file, 'r', encoding='utf-8') as f:
                    self._credentials = json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando credenciales: {e}")
            self._credentials = {}
    
    def _save_credentials(self):
        """Guardar credenciales"""
        try:
            data = json.dumps(self._credentials).encode('utf-8')
            
            if CRYPTO_AVAILABLE and self._fernet:
                encrypted = self._fernet.encrypt(data)
                with open(self.creds_file, 'wb') as f:
                    f.write(encrypted)
            else:
                with open(self.creds_file, 'w', encoding='utf-8') as f:
                    json.dump(self._credentials, f)
            return True
        except Exception as e:
            logger.error(f"Error guardando credenciales: {e}")
            return False
    
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """Guardar API key"""
        if provider not in self._credentials:
            self._credentials[provider] = {}
        
        self._credentials[provider]['api_key'] = api_key
        self._credentials[provider]['updated_at'] = json.dumps({})
        return self._save_credentials()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Obtener API key"""
        return self._credentials.get(provider, {}).get('api_key')
    
    def delete_api_key(self, provider: str) -> bool:
        """Eliminar API key"""
        if provider in self._credentials:
            del self._credentials[provider]
            return self._save_credentials()
        return False
    
    def has_key(self, provider: str) -> bool:
        """Verificar si existe API key"""
        return bool(self.get_api_key(provider))
    
    def list_providers(self) -> List[str]:
        """Listar providers con credenciales"""
        return [k for k, v in self._credentials.items() if v.get('api_key')]


# Instancia global
credential_store = SecureCredentialStore()


# Providers disponibles para MiIA-Product-20
AVAILABLE_PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'description': 'GPT-4o, GPT-4o Mini',
        'models': ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
        'docs_url': 'https://platform.openai.com/api-keys',
    },
    'groq': {
        'name': 'Groq',
        'description': 'Ultra rápido - Llama, Mixtral',
        'models': ['llama-3.1-8b-instant', 'llama-3.1-70b-versatile', 'mixtral-8x7b'],
        'docs_url': 'https://console.groq.com/keys',
    },
    'anthropic': {
        'name': 'Anthropic',
        'description': 'Claude 3 Opus, Sonnet, Haiku',
        'models': ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
        'docs_url': 'https://console.anthropic.com/settings/keys',
    },
    'gemini': {
        'name': 'Google Gemini',
        'description': 'Gemini 1.5 Flash y Pro',
        'models': ['gemini-1.5-flash', 'gemini-1.5-pro'],
        'docs_url': 'https://aistudio.google.com/app/apikey',
    },
    'deepseek': {
        'name': 'DeepSeek',
        'description': 'Económico y capaz',
        'models': ['deepseek-chat', 'deepseek-coder'],
        'docs_url': 'https://platform.deepseek.com/api_keys',
    },
}


# Modelos locales (Ollama)
LOCAL_MODELS = {
    'ollama': {
        'name': 'Ollama',
        'description': 'Plataforma para ejecutar LLMs localmente',
        'download_url': 'https://ollama.com/download',
        'models': {
            'llama3.1': 'Meta Llama 3.1',
            'llama3': 'Meta Llama 3',
            'mistral': 'Mistral',
            'codellama': 'Code Llama',
            'qwen2.5': 'Qwen 2.5 (Alibaba)',
            'phi4': 'Microsoft Phi-4',
        }
    }
}


class LLMConfigurator:
    """Helper para configurar y gestionar providers LLM"""
    
    def __init__(self):
        self.credential_store = credential_store
    
    def get_available_providers(self) -> Dict[str, Dict]:
        """Obtener lista de providers disponibles con estado"""
        providers = {
            'paid': {},
            'local': {}
        }
        
        # APIs Pagas
        for key, info in AVAILABLE_PROVIDERS.items():
            providers['paid'][key] = {
                'name': info['name'],
                'description': info['description'],
                'has_key': self.credential_store.has_key(key),
                'models': info['models'],
                'docs_url': info['docs_url'],
            }
        
        # APIs Locales
        for key, info in LOCAL_MODELS.items():
            providers['local'][key] = {
                'name': info['name'],
                'description': info['description'],
                'is_local': True,
                'download_url': info['download_url'],
                'models': list(info['models'].keys()),
            }
        
        return providers
    
    def configure_provider(self, provider: str, api_key: str) -> bool:
        """Configurar provider con API key"""
        return self.credential_store.set_api_key(provider, api_key)
    
    def remove_provider(self, provider: str) -> bool:
        """Eliminar configuración de provider"""
        return self.credential_store.delete_api_key(provider)
    
    def get_setup_instructions(self, provider: str) -> List[str]:
        """Obtener instrucciones de configuración"""
        info = AVAILABLE_PROVIDERS.get(provider, {})
        docs_url = info.get('docs_url', '')
        
        return [
            f"1. Ve a {docs_url}",
            "2. Crea una nueva API key",
            "3. Copia la key",
            "4. Pégala aquí cuando se te pida"
        ]


# Instancia global
llm_configurator = LLMConfigurator()
