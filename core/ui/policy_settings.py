import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, List


@dataclass
class PolicySettingsData:
    rate_limit_per_min: int = 5
    storage_mb_per_day: int = 100

    business_hours_enabled: bool = True
    business_hours_start: str = "09:00"
    business_hours_end: str = "18:00"

    network_requires_approval: bool = True


class PolicySettings:
    _data = PolicySettingsData()
    _subscribers: List[Callable[[PolicySettingsData], None]] = []

    @classmethod
    def _settings_path(cls) -> Path:
        root = Path(__file__).parent.parent.parent
        data_dir = root / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "policy_settings.json"

    @classmethod
    def load(cls) -> None:
        p = cls._settings_path()
        if not p.exists():
            return
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cls._data = PolicySettingsData(
                    rate_limit_per_min=int(raw.get("rate_limit_per_min", cls._data.rate_limit_per_min)),
                    storage_mb_per_day=int(raw.get("storage_mb_per_day", cls._data.storage_mb_per_day)),
                    business_hours_enabled=bool(raw.get("business_hours_enabled", cls._data.business_hours_enabled)),
                    business_hours_start=str(raw.get("business_hours_start", cls._data.business_hours_start)),
                    business_hours_end=str(raw.get("business_hours_end", cls._data.business_hours_end)),
                    network_requires_approval=bool(raw.get("network_requires_approval", cls._data.network_requires_approval)),
                )
        except Exception:
            return

    @classmethod
    def save(cls) -> None:
        p = cls._settings_path()
        try:
            p.write_text(json.dumps(asdict(cls._data), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @classmethod
    def get(cls) -> PolicySettingsData:
        return cls._data

    @classmethod
    def subscribe(cls, cb: Callable[[PolicySettingsData], None]) -> None:
        if cb not in cls._subscribers:
            cls._subscribers.append(cb)

    @classmethod
    def unsubscribe(cls, cb: Callable[[PolicySettingsData], None]) -> None:
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

    @classmethod
    def set_rate_limit_per_min(cls, value: int) -> None:
        v = int(value)
        if v < 1:
            v = 1
        if v > 120:
            v = 120
        cls._data.rate_limit_per_min = v
        cls.save()
        cls._notify()

    @classmethod
    def set_storage_mb_per_day(cls, value: int) -> None:
        v = int(value)
        if v < 1:
            v = 1
        if v > 10240:
            v = 10240
        cls._data.storage_mb_per_day = v
        cls.save()
        cls._notify()

    @classmethod
    def set_business_hours_enabled(cls, enabled: bool) -> None:
        cls._data.business_hours_enabled = bool(enabled)
        cls.save()
        cls._notify()

    @classmethod
    def set_business_hours_start(cls, hhmm: str) -> None:
        cls._data.business_hours_start = str(hhmm)
        cls.save()
        cls._notify()

    @classmethod
    def set_business_hours_end(cls, hhmm: str) -> None:
        cls._data.business_hours_end = str(hhmm)
        cls.save()
        cls._notify()

    @classmethod
    def set_network_requires_approval(cls, enabled: bool) -> None:
        cls._data.network_requires_approval = bool(enabled)
        cls.save()
        cls._notify()


PolicySettings.load()
