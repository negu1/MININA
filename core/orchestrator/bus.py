"""CortexBus v3.0 - Sistema de Eventos

Este módulo define el API tipado (`EventType`, `CortexEvent`) utilizado por la
arquitectura de 4 capas.

IMPORTANTE: Para evitar tener *dos buses distintos* en el runtime, este archivo
actúa como *adapter* sobre `core.CortexBus.bus` (topics string).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from core.CortexBus import bus as _topic_bus


class EventType(Enum):
    """Tipos de eventos del sistema"""

    # Orquestador
    PLAN_CREATED = "plan:created"
    PLAN_APPROVED = "plan:approved"
    PLAN_REJECTED = "plan:rejected"
    PLAN_EXECUTED = "plan:executed"

    # Manager
    SKILL_STARTED = "skill:started"
    SKILL_PROGRESS = "skill:progress"
    SKILL_COMPLETED = "skill:completed"

    # Supervisor
    SKILL_VALIDATED = "skill:validated"
    SKILL_FAILED = "skill:failed"
    ANOMALY_DETECTED = "anomaly:detected"
    ALERT_TRIGGERED = "alert:triggered"

    # Works
    WORK_SAVED = "work:saved"
    WORK_DELETED = "work:deleted"

    # UI
    UI_UPDATE = "ui:update"
    NOTIFICATION = "notification"


@dataclass
class CortexEvent:
    """Evento tipado del bus."""

    type: EventType
    source: str
    payload: Dict[str, Any]
    timestamp: Optional[datetime]
    event_id: str


class CortexBus:
    """Adapter tipado sobre `core.CortexBus.bus`.

    - `publish(CortexEvent)` publica a topic `event.type.value`.
    - `subscribe(EventType, cb)` suscribe a topic `event_type.value` y entrega un
      `CortexEvent` al callback.
    """

    def subscribe(self, event_type: EventType, callback: Callable[[CortexEvent], Any]) -> str:
        topic = event_type.value

        async def _async_wrapper(data: Any) -> None:
            ev = CortexEvent(
                type=event_type,
                source="cortexbus",
                payload=data if isinstance(data, dict) else {"data": data},
                timestamp=datetime.now(),
                event_id="",
            )
            res = callback(ev)
            if hasattr(res, "__await__"):
                await res  # type: ignore[misc]

        def _sync_wrapper(data: Any) -> None:
            ev = CortexEvent(
                type=event_type,
                source="cortexbus",
                payload=data if isinstance(data, dict) else {"data": data},
                timestamp=datetime.now(),
                event_id="",
            )
            callback(ev)

        wrapper: Callable[[Any], Any]
        if getattr(callback, "__call__", None) is None:
            wrapper = _sync_wrapper
        else:
            # `core.CortexBus` ya detecta coroutine functions en runtime y las
            # ejecuta como tareas/gather.
            wrapper = _async_wrapper

        return _topic_bus.subscribe(topic, wrapper)

    async def publish(self, event: CortexEvent) -> None:
        await _topic_bus.publish(
            topic=event.type.value,
            data=event.payload,
            sender=event.source or "Unknown",
        )

    async def start(self) -> None:
        # No-op: `core.CortexBus` entrega eventos directamente a subscribers.
        return


bus = CortexBus()
