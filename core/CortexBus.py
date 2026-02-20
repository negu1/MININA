import asyncio
import concurrent.futures
import logging
from collections import defaultdict
from datetime import datetime
import inspect
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("CortexBus")


class CortexBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[Dict[str, Any]] = []
        self._max_history = 200
        self._event_stats = defaultdict(int)
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        return getattr(self, "_loop", None)

    def _callback_key(self, callback: Callable) -> Any:
        try:
            bound_self = getattr(callback, "__self__", None)
            bound_func = getattr(callback, "__func__", None)
            if bound_self is not None and bound_func is not None:
                return (id(bound_self), id(bound_func))
        except Exception:
            pass
        return id(callback)

    def subscribe(self, topic: str, callback: Callable) -> str:
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        try:
            new_key = self._callback_key(callback)
            for idx, existing_cb in enumerate(self._subscribers[topic]):
                if self._callback_key(existing_cb) == new_key:
                    return f"{topic}_{idx + 1}"
        except Exception:
            pass

        self._subscribers[topic].append(callback)
        return f"{topic}_{len(self._subscribers[topic])}"

    async def publish(self, topic: str, data: Any = None, sender: str = "Unknown"):
        event = {
            "topic": topic,
            "data": data,
            "sender": sender,
            "timestamp": datetime.now().isoformat(),
        }

        self._history.append(event)
        self._event_stats[topic] += 1
        if len(self._history) > self._max_history:
            self._history.pop(0)

        if topic in self._subscribers:
            await self._execute_callbacks(self._subscribers[topic], data, topic)
        if "*" in self._subscribers:
            await self._execute_callbacks(self._subscribers["*"], event, topic)

    def publish_sync(self, topic: str, data: Any = None, sender: str = "Unknown") -> None:
        # If we're already inside an async event loop in this thread, schedule the
        # coroutine without trying to start a new loop.
        try:
            running_loop = asyncio.get_running_loop()
            running_loop.create_task(self.publish(topic, data, sender))
            return
        except RuntimeError:
            pass

        try:
            loop = self.get_loop()
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(self.publish(topic, data, sender), loop)
                return
        except Exception:
            pass

        try:
            asyncio.run(self.publish(topic, data, sender))
        except RuntimeError:
            try:
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(self.publish(topic, data, sender))
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"publish_sync fallo {topic}: {e}")

    async def _execute_callbacks(self, callbacks: List[Callable], data: Any, topic: str):
        tasks = []
        for callback in callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    tasks.append(self._safe_async_call(callback, data, topic))
                else:
                    try:
                        loop = asyncio.get_event_loop()
                        tasks.append(loop.run_in_executor(None, callback, data))
                    except RuntimeError:
                        callback(data)
            except Exception as e:
                logger.error(f"Error callback {topic}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_async_call(self, coro_func: Callable, data: Any, topic: str):
        try:
            result = coro_func(data)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"Error callback async {topic}: {e}")


bus = CortexBus()
