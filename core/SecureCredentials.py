"""
Secure Credential Storage for API Keys
Encriptación simple para almacenamiento local de credenciales
"""
import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureCredentialStore:
    """Almacenamiento seguro de credenciales con encriptación"""
    
    def __init__(self, app_name: str = "miia-product-20"):
        self.app_name = app_name
        self.config_dir = Path.home() / ".config" / app_name
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.key_file = self.config_dir / ".key"
        self.creds_file = self.config_dir / "credentials.enc"
        
        self._key = None
        self._fernet = None
        self._credentials = {}
        
        self._init_encryption()
        self._load_credentials()
    
    def _init_encryption(self):
        """Inicializar o cargar clave de encriptación"""
        if self.key_file.exists():
            # Cargar clave existente
            with open(self.key_file, 'rb') as f:
                self._key = f.read()
        else:
            # Generar nueva clave basada en machine-id (única por PC)
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=machine_id.encode(),
                iterations=480000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b"miia-secret-v1"))
            self._key = key
            
            # Guardar clave (esto es seguro porque está vinculada al machine-id)
            with open(self.key_file, 'wb') as f:
                f.write(key)
        
        self._fernet = Fernet(self._key)
    
    def _get_machine_id(self) -> str:
        """Obtener identificador único de la máquina"""
        # En Windows, usar MachineGuid del registro
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                r"SOFTWARE\Microsoft\Cryptography") as key:
                return winreg.QueryValueEx(key, "MachineGuid")[0]
        except:
            # Fallback: usar nombre de equipo + usuario
            return f"{os.environ.get('COMPUTERNAME', 'unknown')}-{os.environ.get('USERNAME', 'user')}"
    
    def _load_credentials(self):
        """Cargar credenciales encriptadas"""
        if self.creds_file.exists():
            try:
                with open(self.creds_file, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted = self._fernet.decrypt(encrypted_data)
                self._credentials = json.loads(decrypted.decode('utf-8'))
            except Exception as e:
                print(f"Advertencia: No se pudieron cargar credenciales: {e}")
                self._credentials = {}
    
    def _save_credentials(self):
        """Guardar credenciales encriptadas"""
        try:
            data = json.dumps(self._credentials).encode('utf-8')
            encrypted = self._fernet.encrypt(data)
            
            with open(self.creds_file, 'wb') as f:
                f.write(encrypted)
            return True
        except Exception as e:
            print(f"Error guardando credenciales: {e}")
            return False
    
    def set_credential(self, service: str, key: str, value: str) -> bool:
        """Guardar credencial"""
        if service not in self._credentials:
            self._credentials[service] = {}
        
        self._credentials[service][key] = value
        return self._save_credentials()
    
    def get_credential(self, service: str, key: str) -> Optional[str]:
        """Obtener credencial"""
        return self._credentials.get(service, {}).get(key)
    
    def delete_credential(self, service: str, key: str) -> bool:
        """Eliminar credencial"""
        if service in self._credentials and key in self._credentials[service]:
            del self._credentials[service][key]
            return self._save_credentials()
        return False
    
    def delete_service(self, service: str) -> bool:
        """Eliminar todas las credenciales de un servicio"""
        if service in self._credentials:
            del self._credentials[service]
            return self._save_credentials()
        return False
    
    def list_services(self) -> list:
        """Listar servicios con credenciales"""
        return list(self._credentials.keys())


# Instancia global
credential_store = SecureCredentialStore()
