"""
SkillCredentialVault - Sistema de credenciales temporales y seguras para skills

Este módulo gestiona credenciales sensibles (contraseñas, tokens, API keys) que las skills
necesitan para operar. Las credenciales:
- NUNCA se almacenan en disco
- Se inyectan temporalmente en memoria durante la ejecución
- Se limpian automáticamente después de cada uso
- Están aisladas por skill y por sesión
"""

import os
import time
import secrets
import hashlib
import threading
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("SkillCredentialVault")


@dataclass
class CredentialSet:
    """Conjunto de credenciales temporales para una skill"""
    skill_id: str
    session_id: str
    credentials: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 300)  # 5 minutos default
    used: bool = False
    auto_cleaned: bool = False
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def mask_value(self, key: str, value: str) -> str:
        """Enmascara un valor para logging seguro"""
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]


class SkillCredentialVault:
    """
    Vault de credenciales temporales para skills
    
    Características de seguridad:
    1. Memoria únicamente - nunca toca disco
    2. Auto-expiración (TTL configurable)
    3. Limpieza segura de memoria (sobrescritura con ceros)
    4. Aislamiento por sesión y skill
    5. Auditoría de acceso
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._vault: Dict[str, CredentialSet] = {}
        self._access_log: List[Dict] = []
        self._failed_attempts: Dict[str, int] = {}  # Contador de intentos fallidos por session
        self._max_failed_attempts = 3  # Máximo intentos fallidos antes de bloquear
        self._access_count: Dict[str, int] = {}  # Contador de accesos exitosos
        self._max_access_count = 10  # Máximo accesos permitidos por sesión
        self._cleanup_interval = 60  # segundos
        self._max_ttl = 600  # 10 minutos máximo
        self._lock = threading.RLock()
        
        # Iniciar thread de limpieza automática
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        
        self._initialized = True
        logger.info("SkillCredentialVault inicializado")
    
    def _generate_session_id(self, skill_id: str) -> str:
        """Genera un ID de sesión único"""
        timestamp = str(int(time.time() * 1000))
        random_part = secrets.token_hex(8)
        return f"{skill_id}_{timestamp}_{random_part}"
    
    def store_credentials(
        self, 
        skill_id: str, 
        credentials: Dict[str, str],
        ttl_seconds: int = 300
    ) -> str:
        """
        Almacena credenciales temporales para una skill
        
        Args:
            skill_id: Identificador de la skill
            credentials: Dict con credenciales (ej: {"username": "user", "password": "pass"})
            ttl_seconds: Tiempo de vida en segundos (default 5 min, max 10 min)
        
        Returns:
            session_id: ID único de sesión para recuperar las credenciales
        """
        with self._lock:
            # Limitar TTL
            ttl = min(ttl_seconds, self._max_ttl)
            
            session_id = self._generate_session_id(skill_id)
            
            cred_set = CredentialSet(
                skill_id=skill_id,
                session_id=session_id,
                credentials=credentials.copy(),
                created_at=time.time(),
                expires_at=time.time() + ttl,
                used=False,
                auto_cleaned=False
            )
            
            self._vault[session_id] = cred_set
            
            # Log seguro (sin valores reales)
            safe_creds = {k: cred_set.mask_value(k, v) for k, v in credentials.items()}
            logger.info(f"Credenciales almacenadas para skill '{skill_id}', session '{session_id[:20]}...', campos: {list(safe_creds.keys())}")
            
            return session_id
    
    def get_credentials(self, session_id: str, skill_id: str, user_id: str = "unknown") -> Optional[Dict[str, str]]:
        """
        Recupera credenciales para una sesión y skill específica
        
        Args:
            session_id: ID de sesión devuelto por store_credentials
            skill_id: Debe coincidir con el skill_id original
            user_id: ID del usuario para notificaciones
        
        Returns:
            Dict con credenciales o None si no existe/expiró/bloqueado
        """
        with self._lock:
            # Verificar intentos fallidos
            failed_count = self._failed_attempts.get(session_id, 0)
            if failed_count >= self._max_failed_attempts:
                logger.error(f"Session {session_id[:20]}... BLOQUEADA por {failed_count} intentos fallidos")
                self._notify_user(user_id, skill_id, "blocked", f"Bloqueado por {failed_count} intentos fallidos")
                return None
            
            cred_set = self._vault.get(session_id)
            
            if not cred_set:
                self._failed_attempts[session_id] = failed_count + 1
                logger.warning(f"Intento de acceso a credenciales inexistentes: {session_id[:20]}... (intento {failed_count + 1}/{self._max_failed_attempts})")
                self._notify_user(user_id, skill_id, "failed", f"Intento de acceso a credenciales inexistentes ({failed_count + 1}/{self._max_failed_attempts})")
                return None
            
            if cred_set.skill_id != skill_id:
                self._failed_attempts[session_id] = failed_count + 1
                logger.error(f"Skill ID no coincide! Esperado: {cred_set.skill_id}, Recibido: {skill_id} (intento {failed_count + 1}/{self._max_failed_attempts})")
                self._notify_user(user_id, skill_id, "failed", f"Skill ID no coincide ({failed_count + 1}/{self._max_failed_attempts})")
                return None
            
            if cred_set.is_expired():
                logger.warning(f"Credenciales expiradas para session {session_id[:20]}...")
                self._secure_delete(session_id)
                self._notify_user(user_id, skill_id, "expired", "Credenciales expiradas")
                return None
            
            # Verificar límite de accesos
            access_count = self._access_count.get(session_id, 0)
            if access_count >= self._max_access_count:
                logger.error(f"Session {session_id[:20]}... alcanzó límite de {self._max_access_count} accesos")
                self._secure_delete(session_id)
                self._notify_user(user_id, skill_id, "limit_reached", f"Límite de {self._max_access_count} accesos alcanzado")
                return None
            
            # Marcar como usada y contar acceso
            cred_set.used = True
            self._access_count[session_id] = access_count + 1
            
            # Log de acceso
            self._access_log.append({
                "timestamp": time.time(),
                "skill_id": skill_id,
                "session_id": session_id[:20] + "...",
                "user_id": user_id,
                "action": "access",
                "access_number": access_count + 1
            })
            
            # Notificar al usuario del acceso
            self._notify_user(user_id, skill_id, "access", f"Acceso #{access_count + 1} a credenciales")
            
            logger.info(f"Credenciales accedidas por skill '{skill_id}' (acceso {access_count + 1}/{self._max_access_count})")
            
            return cred_set.credentials.copy()
    
    def _notify_user(self, user_id: str, skill_id: str, event_type: str, message: str):
        """
        Notifica al usuario sobre eventos de credenciales vía CortexBus
        """
        try:
            from core.CortexBus import bus
            bus.publish_sync(
                "user.CREDENTIAL_EVENT",
                {
                    "user_id": user_id,
                    "skill_id": skill_id,
                    "event_type": event_type,  # access, failed, blocked, expired, limit_reached
                    "message": message,
                    "timestamp": time.time()
                },
                sender="SkillCredentialVault"
            )
        except Exception as e:
            logger.error(f"Error notificando a usuario: {e}")
    
    def release_credentials(self, session_id: str) -> bool:
        """
        Libera y limpia credenciales de forma segura después del uso
        
        Args:
            session_id: ID de sesión
        
        Returns:
            True si se limpiaron correctamente
        """
        with self._lock:
            return self._secure_delete(session_id)
    
    def _secure_delete(self, session_id: str) -> bool:
        """
        Elimina credenciales de forma segura sobrescribiendo memoria
        """
        cred_set = self._vault.get(session_id)
        if not cred_set:
            return False
        
        try:
            # Sobrescribir valores con patrones aleatorios antes de eliminar
            for key in cred_set.credentials:
                original_len = len(cred_set.credentials[key])
                # Sobrescribir con caracteres aleatorios
                cred_set.credentials[key] = secrets.token_hex(original_len)
                # Luego con ceros
                cred_set.credentials[key] = "0" * original_len
            
            # Marcar como limpiado
            cred_set.auto_cleaned = True
            cred_set.credentials.clear()
            
            # Eliminar del vault
            del self._vault[session_id]
            
            logger.info(f"Credenciales eliminadas de forma segura: {session_id[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error en limpieza segura: {e}")
            # Forzar eliminación incluso si falla la sobrescritura
            self._vault.pop(session_id, None)
            return False
    
    def _cleanup_loop(self):
        """Thread de limpieza automática de credenciales expiradas"""
        while True:
            try:
                time.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except Exception as e:
                logger.error(f"Error en cleanup loop: {e}")
    
    def _cleanup_expired(self):
        """Limpia credenciales expiradas"""
        with self._lock:
            expired_sessions = [
                sid for sid, cred in self._vault.items() 
                if cred.is_expired()
            ]
            
            for session_id in expired_sessions:
                logger.info(f"Auto-limpieza de credenciales expiradas: {session_id[:20]}...")
                self._secure_delete(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del vault (para monitoreo)"""
        with self._lock:
            active = len(self._vault)
            expired = sum(1 for c in self._vault.values() if c.is_expired())
            
            return {
                "active_sessions": active,
                "expired_sessions": expired,
                "total_access_logged": len(self._access_log),
                "failed_attempts_total": sum(self._failed_attempts.values()),
                "blocked_sessions": sum(1 for s, c in self._failed_attempts.items() if c >= self._max_failed_attempts),
                "max_failed_attempts": self._max_failed_attempts,
                "max_access_count": self._max_access_count,
                "cleanup_interval": self._cleanup_interval,
                "max_ttl": self._max_ttl
            }
    
    def validate_skill_credential_request(self, skill_id: str, requested_permissions: List[str]) -> Dict[str, Any]:
        """
        Valida si una skill puede solicitar credenciales basado en sus permisos
        
        Returns:
            Dict con 'allowed' (bool) y 'required_fields' (list)
        """
        # Skills con permiso 'network' o 'sensitive_data' pueden solicitar credenciales
        can_request = any(p in requested_permissions for p in ['network', 'sensitive_data', 'credentials'])
        
        if not can_request:
            return {
                "allowed": False,
                "reason": "La skill no tiene permisos para acceder a credenciales sensibles",
                "required_permissions": ["network", "sensitive_data", "credentials"]
            }
        
        return {
            "allowed": True,
            "required_fields": ["username", "password", "api_key", "token"],
            "security_notice": "Las credenciales se proporcionarán temporalmente y se eliminarán automáticamente después del uso"
        }


# Instancia global
credential_vault = SkillCredentialVault()


def get_credential_vault() -> SkillCredentialVault:
    """Retorna la instancia global del vault"""
    return credential_vault


# Funciones de conveniencia para integración con skills
def prepare_skill_with_credentials(skill_id: str, user_provided_creds: Dict[str, str]) -> str:
    """
    Prepara una skill con credenciales de usuario
    
    Uso:
        session_id = prepare_skill_with_credentials("facebook_bot", {
            "username": "user@example.com",
            "password": "secret123"
        })
        
        # Ejecutar skill pasando session_id en el contexto
        result = run_skill("facebook_bot", task="postear", credential_session=session_id)
    """
    return credential_vault.store_credentials(skill_id, user_provided_creds)


def cleanup_after_skill(session_id: str):
    """Limpia credenciales después de que la skill termina"""
    credential_vault.release_credentials(session_id)
