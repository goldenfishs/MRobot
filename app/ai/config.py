from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .models import AIProviderConfig, Conversation


def ai_data_directory() -> Path:
    override = os.environ.get("MROBOT_AI_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "MRobot" / "ai"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "MRobot" / "ai"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "MRobot" / "ai"


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class AIProfileStore:
    """Persist provider metadata without ever persisting an API key."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else ai_data_directory() / "profiles.json"

    def load(self) -> tuple[str, dict[str, AIProviderConfig]]:
        raw = _read_json(self.path, {})
        profiles: dict[str, AIProviderConfig] = {}
        if isinstance(raw, dict) and isinstance(raw.get("profiles"), dict):
            for name, value in raw["profiles"].items():
                if isinstance(name, str) and isinstance(value, dict):
                    profiles[name] = AIProviderConfig.from_dict({**value, "name": name})
        if not profiles:
            default = AIProviderConfig.from_preset("ollama")
            profiles[default.name] = default
        active = str(raw.get("active") or next(iter(profiles))) if isinstance(raw, dict) else next(iter(profiles))
        if active not in profiles:
            active = next(iter(profiles))
        return active, profiles

    def save(self, active: str, profiles: dict[str, AIProviderConfig]) -> None:
        if active not in profiles:
            raise ValueError("活动 AI 配置不存在")
        _atomic_write_json(
            self.path,
            {"schema_version": 1, "active": active, "profiles": {name: config.to_dict() for name, config in profiles.items()}},
        )


class AIConversationStore:
    def __init__(self, path: str | Path | None = None, limit: int = 50) -> None:
        self.path = Path(path) if path else ai_data_directory() / "conversations.json"
        self.limit = limit

    def load(self) -> list[Conversation]:
        raw = _read_json(self.path, {})
        items = raw.get("conversations") if isinstance(raw, dict) else []
        conversations = [Conversation.from_dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []
        return sorted(conversations, key=lambda item: item.updated_at, reverse=True)[: self.limit]

    def save_all(self, conversations: list[Conversation]) -> None:
        ordered = sorted(conversations, key=lambda item: item.updated_at, reverse=True)[: self.limit]
        _atomic_write_json(
            self.path,
            {"schema_version": 1, "conversations": [conversation.to_dict() for conversation in ordered]},
        )
