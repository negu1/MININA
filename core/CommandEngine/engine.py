from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ParsedCommand:
    raw: str
    intent: str
    skill_name: Optional[str] = None
    task: str = ""


class CommandEngine:
    def parse(self, text: str) -> Optional[ParsedCommand]:
        t = (text or "").strip()
        if not t:
            return None

        lower = t.lower()
        if lower in {"lista skills", "listar skills", "skills", "lista skill", "listar skill"}:
            return ParsedCommand(raw=t, intent="list_skills")

        if lower in {"estado", "status", "estado miia", "estado miia product"}:
            return ParsedCommand(raw=t, intent="status")

        if lower.startswith("usa skill "):
            rest = t[len("usa skill ") :].strip()
            parts = rest.split(" ", 1)
            skill = parts[0].strip()
            task = parts[1].strip() if len(parts) > 1 else ""
            return ParsedCommand(raw=t, intent="use_skill", skill_name=skill, task=task)

        return ParsedCommand(raw=t, intent="chat", task=t)

    def to_context(self, cmd: ParsedCommand, user_id: str = "anon") -> Dict[str, Any]:
        return {"task": cmd.task, "user_id": user_id}
