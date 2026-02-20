from dataclasses import dataclass
from typing import Callable, List


@dataclass
class UiSettingsData:
    chat_history_limit: int = 20


class UiSettings:
    _data = UiSettingsData()
    _subscribers: List[Callable[[UiSettingsData], None]] = []

    @classmethod
    def get(cls) -> UiSettingsData:
        return cls._data

    @classmethod
    def set_chat_history_limit(cls, value: int) -> None:
        v = int(value)
        if v < 5:
            v = 5
        if v > 200:
            v = 200
        cls._data.chat_history_limit = v
        cls._notify()

    @classmethod
    def subscribe(cls, cb: Callable[[UiSettingsData], None]) -> None:
        if cb not in cls._subscribers:
            cls._subscribers.append(cb)

    @classmethod
    def unsubscribe(cls, cb: Callable[[UiSettingsData], None]) -> None:
        try:
            cls._subscribers.remove(cb)
        except ValueError:
            pass

    @classmethod
    def _notify(cls) -> None:
        for cb in list(cls._subscribers):
            try:
                cb(cls._data)
            except Exception:
                pass
