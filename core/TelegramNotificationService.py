"""
MININA v3.0 - Sistema de Notificaciones Telegram
Servicio de notificaciones configurables y modo "espejo"
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from datetime import datetime

from core.CortexBus import bus
from core.ui.api_client import api_client

logger = logging.getLogger("TelegramNotifications")


@dataclass
class NotificationConfig:
    """Configuración de notificaciones para un usuario"""
    chat_id: int
    enabled: bool = True
    
    # Tipos de notificaciones
    notify_works_completed: bool = True  # Works terminados
    notify_skills_executed: bool = False  # Skills ejecutadas
    notify_errors: bool = True  # Errores
    notify_auto_send_works: bool = False  # Enviar works automáticamente
    
    # Filtros
    only_important: bool = False  # Solo notificaciones importantes
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NotificationConfig':
        return cls(**data)


class TelegramNotificationService:
    """
    Servicio de notificaciones de MININA v3.0
    Modo 'espejo': el usuario trabaja en UI, Telegram recibe avisos
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Configuraciones por chat_id
        self._configs: Dict[int, NotificationConfig] = {}
        
        # Referencia al bot (se asigna desde TelegramBotService)
        self._bot = None
        
        # Works ya notificados (para evitar duplicados)
        self._notified_works: Set[str] = set()
        
        # Archivo de configuración
        self._config_path = Path("data/telegram_notifications.json")
        self._load_configs()
        
        # Suscribirse a eventos
        self._subscribe_events()
        
        # Iniciar loop de verificación
        self._check_task = None
        
    def set_bot(self, bot) -> None:
        """Asignar referencia al bot de Telegram"""
        self._bot = bot
        
    def _subscribe_events(self) -> None:
        """Suscribirse a eventos del CortexBus"""
        bus.subscribe("work.COMPLETED", self._on_work_completed)
        bus.subscribe("skill.EXECUTED", self._on_skill_executed)
        bus.subscribe("skill.ERROR", self._on_skill_error)
        bus.subscribe("orchestrator.COMPLETED", self._on_orchestrator_completed)
        
    def _load_configs(self) -> None:
        """Cargar configuraciones desde archivo"""
        if self._config_path.exists():
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for chat_id_str, config_dict in data.get("configs", {}).items():
                        chat_id = int(chat_id_str)
                        self._configs[chat_id] = NotificationConfig.from_dict(config_dict)
                logger.info(f"Cargadas {len(self._configs)} configuraciones de notificaciones")
            except Exception as e:
                logger.error(f"Error cargando configuraciones: {e}")
    
    def _save_configs(self) -> None:
        """Guardar configuraciones a archivo"""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "configs": {
                    str(k): v.to_dict() for k, v in self._configs.items()
                }
            }
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando configuraciones: {e}")
    
    def get_or_create_config(self, chat_id: int) -> NotificationConfig:
        """Obtener o crear configuración para un chat"""
        if chat_id not in self._configs:
            self._configs[chat_id] = NotificationConfig(chat_id=chat_id)
            self._save_configs()
        return self._configs[chat_id]
    
    def update_config(self, chat_id: int, **kwargs) -> NotificationConfig:
        """Actualizar configuración de un chat"""
        config = self.get_or_create_config(chat_id)
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self._save_configs()
        return config
    
    def disable_notifications(self, chat_id: int) -> None:
        """Deshabilitar todas las notificaciones para un chat"""
        config = self.get_or_create_config(chat_id)
        config.enabled = False
        self._save_configs()
    
    def enable_notifications(self, chat_id: int) -> None:
        """Habilitar notificaciones para un chat"""
        config = self.get_or_create_config(chat_id)
        config.enabled = True
        self._save_configs()
    
    # =========================================================================
    # HANDLERS DE EVENTOS
    # =========================================================================
    
    async def _on_work_completed(self, data: Dict[str, Any]) -> None:
        """Handler para cuando se completa un work"""
        if not self._bot:
            return
            
        work_id = data.get("work_id")
        work_name = data.get("work_name", "Archivo")
        
        if work_id in self._notified_works:
            return
        self._notified_works.add(work_id)
        
        # Notificar a todos los chats configurados
        for chat_id, config in self._configs.items():
            if not config.enabled:
                continue
            
            if config.notify_works_completed:
                try:
                    await self._bot.send_message(
                        chat_id=chat_id,
                        text=f"📄 *Work completado:*\n_{work_name}_",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error notificando work a {chat_id}: {e}")
            
            # Enviar archivo automáticamente si está configurado
            if config.notify_auto_send_works:
                await self._send_work_to_chat(chat_id, work_id)
    
    async def _on_skill_executed(self, data: Dict[str, Any]) -> None:
        """Handler para cuando se ejecuta una skill"""
        if not self._bot:
            return
            
        skill_name = data.get("skill_name", "unknown")
        
        for chat_id, config in self._configs.items():
            if not config.enabled or not config.notify_skills_executed:
                continue
            
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=f"⚡ Skill ejecutada: *{skill_name}*",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error notificando skill a {chat_id}: {e}")
    
    async def _on_skill_error(self, data: Dict[str, Any]) -> None:
        """Handler para errores de skills"""
        if not self._bot:
            return
            
        skill_name = data.get("skill_name", "unknown")
        error = data.get("error", "Error desconocido")
        
        for chat_id, config in self._configs.items():
            if not config.enabled or not config.notify_errors:
                continue
            
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ *Error en skill {skill_name}:*\n{error[:200]}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error notificando error a {chat_id}: {e}")
    
    async def _on_orchestrator_completed(self, data: Dict[str, Any]) -> None:
        """Handler para cuando completa el orquestador"""
        if not self._bot:
            return
            
        objective = data.get("objective", "Objetivo")
        success = data.get("success", False)
        works = data.get("works", [])
        
        for chat_id, config in self._configs.items():
            if not config.enabled:
                continue
            
            status = "✅ Completado" if success else "❌ Fallido"
            
            try:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=f"🎯 *Orquestador:* {status}\n_{objective[:100]}_",
                    parse_mode="Markdown"
                )
                
                # Enviar works si está configurado
                if success and config.notify_auto_send_works:
                    for work_id in works:
                        await self._send_work_to_chat(chat_id, work_id)
                        
            except Exception as e:
                logger.error(f"Error notificando orquestador a {chat_id}: {e}")
    
    async def _send_work_to_chat(self, chat_id: int, work_id: str) -> None:
        """Enviar un work específico a un chat"""
        if not self._bot:
            return
            
        try:
            # Obtener info del work
            works = api_client.get_works()
            work = None
            for w in works:
                if w.get('id') == work_id:
                    work = w
                    break
            
            if not work:
                return
            
            # Descargar archivo temporalmente
            import tempfile
            tmp_path = Path(tempfile.gettempdir()) / work.get('original_name', 'file')
            
            if api_client.download_work(work_id, tmp_path):
                # Enviar archivo
                with open(tmp_path, "rb") as f:
                    await self._bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        caption=f"📄 {work.get('original_name')}"
                    )
                
                # Limpiar
                tmp_path.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Error enviando work {work_id} a {chat_id}: {e}")
    
    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================
    
    async def send_notification(self, chat_id: int, message: str, important: bool = False) -> bool:
        """Enviar notificación manual a un chat"""
        if not self._bot:
            return False
            
        config = self.get_or_create_config(chat_id)
        
        if not config.enabled:
            return False
        
        if config.only_important and not important:
            return False
        
        try:
            await self._bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            logger.error(f"Error enviando notificación a {chat_id}: {e}")
            return False
    
    def broadcast(self, message: str, important: bool = False) -> None:
        """Enviar notificación a todos los chats habilitados"""
        if not self._bot:
            return
            
        for chat_id, config in self._configs.items():
            if not config.enabled:
                continue
            
            if config.only_important and not important:
                continue
            
            try:
                asyncio.create_task(
                    self._bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                )
            except Exception as e:
                logger.error(f"Error en broadcast a {chat_id}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio"""
        total = len(self._configs)
        enabled = sum(1 for c in self._configs.values() if c.enabled)
        auto_send = sum(1 for c in self._configs.values() if c.notify_auto_send_works)
        
        return {
            "total_chats": total,
            "enabled": enabled,
            "auto_send_works": auto_send,
            "works_notified": len(self._notified_works)
        }


# Instancia global
notification_service = TelegramNotificationService()
