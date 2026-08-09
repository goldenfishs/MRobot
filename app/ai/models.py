from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


PROVIDER_PRESETS: dict[str, dict[str, object]] = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-terra",
        "api_key_env": "OPENAI_API_KEY",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "api_key_env": "DEEPSEEK_API_KEY",
    },
    "siliconflow": {
        "label": "硅基流动",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2",
        "api_key_env": "SILICONFLOW_API_KEY",
    },
    "dashscope": {
        "label": "阿里云百炼",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3-max",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-5.4-mini",
        "api_key_env": "OPENROUTER_API_KEY",
    },
    "ollama": {
        "label": "Ollama 本地",
        "base_url": "http://127.0.0.1:11434/v1",
        "model": "qwen3:0.6b",
        "api_key_env": "",
    },
    "custom": {
        "label": "自定义 OpenAI 兼容接口",
        "base_url": "https://example.com/v1",
        "model": "",
        "api_key_env": "MROBOT_AI_API_KEY",
    },
}


@dataclass(frozen=True)
class AIProviderConfig:
    name: str
    base_url: str
    model: str
    api_key_env: str = ""
    temperature: float = 0.2
    timeout: int = 120
    enable_tools: bool = True

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "AIProviderConfig":
        return cls(
            name=str(value.get("name") or "自定义模型"),
            base_url=str(value.get("base_url") or ""),
            model=str(value.get("model") or ""),
            api_key_env=str(value.get("api_key_env") or ""),
            temperature=float(value.get("temperature", 0.2)),
            timeout=int(value.get("timeout", 120)),
            enable_tools=bool(value.get("enable_tools", True)),
        )

    @classmethod
    def from_preset(cls, preset_id: str, name: str | None = None) -> "AIProviderConfig":
        preset = PROVIDER_PRESETS[preset_id]
        return cls(
            name=name or str(preset["label"]),
            base_url=str(preset["base_url"]),
            model=str(preset["model"]),
            api_key_env=str(preset["api_key_env"]),
            enable_tools=True,
        )


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: str

    def to_openai(self) -> dict[str, object]:
        return {
            "id": self.call_id,
            "type": "function",
            "function": {"name": self.name, "arguments": self.arguments},
        }


@dataclass(frozen=True)
class AssistantTurn:
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    usage: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolEvent:
    name: str
    arguments: dict[str, object]
    result: str


@dataclass(frozen=True)
class AssistantResult:
    text: str
    messages: tuple[dict[str, Any], ...]
    tool_events: tuple[ToolEvent, ...] = ()
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class Conversation:
    conversation_id: str
    title: str
    provider: str
    project_root: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def create(cls, provider: str, project_root: str = "") -> "Conversation":
        return cls(uuid4().hex, "新对话", provider, project_root)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "Conversation":
        raw_messages = value.get("messages")
        messages = [item for item in raw_messages if isinstance(item, dict)] if isinstance(raw_messages, list) else []
        return cls(
            conversation_id=str(value.get("conversation_id") or uuid4().hex),
            title=str(value.get("title") or "新对话"),
            provider=str(value.get("provider") or "Ollama 本地"),
            project_root=str(value.get("project_root") or ""),
            messages=messages,
            created_at=str(value.get("created_at") or datetime.now(timezone.utc).isoformat()),
            updated_at=str(value.get("updated_at") or datetime.now(timezone.utc).isoformat()),
        )
