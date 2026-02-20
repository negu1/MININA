import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from core.CortexBus import bus

logger = logging.getLogger("UserObservabilityStore")


class UserObservabilityStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self._default_db_path()
        self._started = False

    def _default_db_path(self) -> Path:
        db_dir = Path(__file__).resolve().parents[1] / "data"
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / "user_observability.db"

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=10)

    def initialize(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS user_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    sender TEXT,
                    timestamp TEXT,
                    payload_json TEXT
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_events_topic ON user_events(topic)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_user_events_ts ON user_events(timestamp)")
            conn.commit()

    def get_recent_events(self, limit: int = 200) -> list[Dict[str, Any]]:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                rows = cur.execute(
                    "SELECT topic, sender, timestamp, payload_json FROM user_events ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()

            out: list[Dict[str, Any]] = []
            for topic, sender, ts, payload_json in rows:
                payload = None
                try:
                    payload = json.loads(payload_json) if payload_json else None
                except Exception:
                    payload = payload_json
                out.append({"topic": topic, "sender": sender, "timestamp": ts, "data": payload})
            return out
        except Exception:
            return []

    def get_pending_retries(self, scan_limit: int = 500) -> Dict[str, Dict[str, Any]]:
        events = self.get_recent_events(limit=scan_limit)
        last_available: Dict[str, Dict[str, Any]] = {}
        last_request: Dict[str, str] = {}

        for ev in reversed(events):
            topic = ev.get("topic")
            data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
            sid = (data or {}).get("session_id")
            if not sid:
                continue
            if topic == "skill.RETRY_AVAILABLE":
                last_available[sid] = data
            if topic == "skill.RETRY_REQUEST":
                last_request[sid] = ev.get("timestamp") or ""

        return {sid: payload for sid, payload in last_available.items() if sid not in last_request}

    async def rehydrate(self) -> None:
        pending = self.get_pending_retries(scan_limit=800)
        for _, payload in pending.items():
            try:
                await bus.publish("skill.RETRY_AVAILABLE", payload, sender="UserObservabilityStore")
            except Exception:
                pass

    async def start(self) -> None:
        if self._started:
            return
        self.initialize()
        bus.subscribe("*", self._on_any_event)
        self._started = True
        await self.rehydrate()

    async def _on_any_event(self, event: Dict[str, Any]) -> None:
        try:
            topic = event.get("topic")
            if topic not in {
                "user.SPEAK",
                "user.UI_MESSAGE",
                "user.PROGRESS",
                "skill.RETRY_AVAILABLE",
                "skill.RETRY_REQUEST",
                "agent.SPAWNED",
                "agent.RESULT",
            }:
                return

            payload_json = json.dumps(event.get("data"), ensure_ascii=False, default=str)
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO user_events (topic, sender, timestamp, payload_json) VALUES (?, ?, ?, ?)",
                    (topic, event.get("sender"), event.get("timestamp"), payload_json),
                )
                conn.commit()
        except Exception:
            pass


store = UserObservabilityStore()
