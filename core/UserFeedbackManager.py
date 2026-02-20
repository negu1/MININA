import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

from core.CortexBus import bus

logger = logging.getLogger("UserFeedbackManager")


class UserFeedbackManager:
    def __init__(self):
        self._last_interaction = datetime.now()
        self._idle_check_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._retry_callbacks: Dict[str, Callable] = {}

        bus.subscribe("agent.SPAWNED", self._on_skill_spawned)
        bus.subscribe("agent.RESULT", self._on_skill_result)
        bus.subscribe("skill.RETRY_REQUEST", self._on_retry_request)
        bus.subscribe("user.INTERACTION", self._on_user_interaction)

    async def start(self):
        if not self._is_running:
            self._is_running = True
            self._idle_check_task = asyncio.create_task(self._idle_status_loop())

    async def _idle_status_loop(self):
        while self._is_running:
            await asyncio.sleep(30)
            idle_time = datetime.now() - self._last_interaction
            if idle_time > timedelta(minutes=5):
                if int(idle_time.total_seconds()) % 300 < 30:
                    await self.speak_async("Estoy activa. Di un comando tipo: 'usa skill web_browser example.com'", priority="low")

    def _on_user_interaction(self, event: Dict[str, Any]):
        self._last_interaction = datetime.now()

    async def _on_skill_spawned(self, event: Dict[str, Any]):
        await self.speak_async(f"Iniciando {event.get('skill_name','skill')}...")

    async def _on_skill_result(self, event: Dict[str, Any]):
        skill = event.get("skill", "skill")
        success = bool(event.get("success"))
        if success:
            res = event.get("result")
            msg = str(res)
            if len(msg) > 100:
                msg = msg[:100] + "..."
            await self.speak_async(f"✅ {skill} completado: {msg}")
        else:
            err = event.get("error", "Error desconocido")
            await self.speak_async(f"❌ {skill} falló: {err}. Si quieres, puedo reintentar.")
            sid = event.get("session_id")
            if sid:
                await bus.publish("skill.RETRY_AVAILABLE", {"session_id": sid, "skill": skill, "original_error": err, "timestamp": datetime.now().isoformat()}, sender="UserFeedbackManager")

    async def speak_async(self, message: str, priority: str = "normal"):
        await bus.publish("user.SPEAK", {"message": message, "priority": priority, "timestamp": datetime.now().isoformat()}, sender="UserFeedbackManager")
        await bus.publish("user.UI_MESSAGE", {"message": message, "priority": priority, "type": "feedback"}, sender="UserFeedbackManager")

    def register_retry_callback(self, session_id: str, callback: Callable):
        self._retry_callbacks[session_id] = callback

    def unregister_retry_callback(self, session_id: str) -> None:
        try:
            self._retry_callbacks.pop(session_id, None)
        except Exception:
            pass

    async def request_retry(self, session_id: str) -> Any:
        if session_id in self._retry_callbacks:
            try:
                result = await self._retry_callbacks[session_id]()
                self.unregister_retry_callback(session_id)
                return result
            except Exception as e:
                return {"success": False, "error": str(e), "session_id": session_id}
        return {"success": False, "error": "No hay reintento disponible", "session_id": session_id}

    async def _on_retry_request(self, event: Dict[str, Any]):
        session_id = (event or {}).get("session_id")
        if not session_id:
            await self.speak_async("❌ Falta session_id para reintento", priority="high")
            return

        await self.speak_async("🔁 Reintentando...", priority="normal")
        result = await self.request_retry(session_id)
        try:
            success = bool((result or {}).get("success")) if isinstance(result, dict) else bool(result)
        except Exception:
            success = False

        if success:
            await self.speak_async("✅ Reintento completado. ¿Siguiente comando?", priority="normal")
        else:
            err = result.get("error") if isinstance(result, dict) else None
            await self.speak_async(f"❌ Reintento falló: {err or 'Error desconocido'}. ¿Probamos otra cosa?", priority="high")


feedback_manager = UserFeedbackManager()
