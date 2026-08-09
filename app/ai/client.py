from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable
from typing import Any
from urllib.parse import urlparse

import requests

from .models import AIProviderConfig, AssistantTurn, ToolCall


class AIClientError(RuntimeError):
    pass


class AICancelled(AIClientError):
    pass


def validate_base_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise AIClientError("Base URL 必须是有效的 HTTP(S) 地址，且不能包含账号密码")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and parsed.hostname not in local_hosts:
        raise AIClientError("远程 AI 接口必须使用 HTTPS；HTTP 仅允许本机 Ollama 等服务")
    return normalized


class OpenAICompatibleClient:
    """Small dependency-free client for OpenAI-compatible Chat Completions APIs."""

    def __init__(
        self,
        config: AIProviderConfig,
        *,
        api_key: str = "",
        session: requests.Session | None = None,
    ) -> None:
        self.config = config
        self.base_url = validate_base_url(config.base_url)
        self.api_key = api_key.strip() or (os.environ.get(config.api_key_env, "") if config.api_key_env else "")
        self.session = session or requests.Session()

    @property
    def chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    @property
    def models_url(self) -> str:
        root = self.base_url.removesuffix("/chat/completions")
        return f"{root}/models"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "MRobot-AI/1"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def list_models(self) -> tuple[str, ...]:
        try:
            response = self.session.get(self.models_url, headers=self._headers(), timeout=min(self.config.timeout, 20))
            response.raise_for_status()
            payload = response.json()
            values = payload.get("data", ()) if isinstance(payload, dict) else ()
            return tuple(sorted(str(item["id"]) for item in values if isinstance(item, dict) and item.get("id")))
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise self._friendly_error("读取模型列表失败", exc) from exc

    def complete_turn(
        self,
        messages: Iterable[dict[str, Any]],
        *,
        tools: Iterable[dict[str, Any]] = (),
        on_text: Callable[[str], None] | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> AssistantTurn:
        if not self.config.model.strip():
            raise AIClientError("请先配置模型 ID")
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": list(messages),
            "stream": True,
            "temperature": self.config.temperature,
        }
        tool_values = list(tools)
        if tool_values and self.config.enable_tools:
            payload["tools"] = tool_values
            payload["tool_choice"] = "auto"
        try:
            with self.session.post(
                self.chat_url,
                headers=self._headers(),
                json=payload,
                stream=True,
                timeout=(15, self.config.timeout),
            ) as response:
                response.raise_for_status()
                return self._consume_stream(response, on_text, cancelled)
        except AICancelled:
            raise
        except (requests.RequestException, ValueError, TypeError) as exc:
            raise self._friendly_error("AI 请求失败", exc) from exc

    def _consume_stream(
        self,
        response: requests.Response,
        on_text: Callable[[str], None] | None,
        cancelled: Callable[[], bool] | None,
    ) -> AssistantTurn:
        content_parts: list[str] = []
        calls: dict[int, dict[str, str]] = {}
        usage: dict[str, int] = {}
        for raw_line in response.iter_lines(decode_unicode=True):
            if cancelled and cancelled():
                raise AICancelled("已停止生成")
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            if isinstance(event.get("error"), dict):
                raise AIClientError("AI 服务返回错误，请检查模型权限、余额和接口参数")
            if isinstance(event.get("usage"), dict):
                usage = {str(key): int(value) for key, value in event["usage"].items() if isinstance(value, (int, float))}
            choices = event.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            text = delta.get("content")
            if isinstance(text, str) and text:
                content_parts.append(text)
                if on_text:
                    on_text(text)
            for raw_call in delta.get("tool_calls") or ():
                if not isinstance(raw_call, dict):
                    continue
                index = int(raw_call.get("index", 0))
                current = calls.setdefault(index, {"id": "", "name": "", "arguments": ""})
                if raw_call.get("id"):
                    current["id"] += str(raw_call["id"])
                function = raw_call.get("function") or {}
                if isinstance(function, dict):
                    current["name"] += str(function.get("name") or "")
                    current["arguments"] += str(function.get("arguments") or "")
        tool_calls = tuple(
            ToolCall(value["id"] or f"call_{index}", value["name"], value["arguments"] or "{}")
            for index, value in sorted(calls.items())
            if value["name"]
        )
        if not content_parts and not tool_calls:
            raise AIClientError("AI 服务没有返回兼容的流式内容，请确认其支持 OpenAI Chat Completions SSE")
        return AssistantTurn("".join(content_parts), tool_calls, usage)

    @staticmethod
    def _friendly_error(prefix: str, exc: Exception) -> AIClientError:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            status = exc.response.status_code
            if status in {401, 403}:
                return AIClientError(f"{prefix}：API Key 无效或没有模型权限（HTTP {status}）")
            if status == 404:
                return AIClientError(f"{prefix}：接口地址或模型不存在（HTTP 404）")
            if status == 429:
                return AIClientError(f"{prefix}：服务限流或余额不足（HTTP 429）")
            return AIClientError(f"{prefix}：服务返回 HTTP {status}")
        if isinstance(exc, requests.Timeout):
            return AIClientError(f"{prefix}：连接或生成超时")
        if isinstance(exc, requests.ConnectionError):
            return AIClientError(f"{prefix}：无法连接服务，请检查 Base URL、网络或本地模型状态")
        return AIClientError(f"{prefix}：响应格式不兼容")
