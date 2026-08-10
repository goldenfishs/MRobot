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
    """OpenAI-compatible client with Responses and Chat Completions support.

    ``auto`` prefers the Responses API for new integrations, then falls back to
    Chat Completions only when an endpoint is clearly unavailable. A provider
    that ignores ``stream=true`` and returns ordinary JSON is also accepted.
    """

    PROTOCOLS = {"auto", "responses", "chat"}

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
        if config.protocol not in self.PROTOCOLS:
            raise AIClientError("接口协议必须是自动检测、Responses 或 Chat Completions")

    def _roots(self) -> tuple[str, ...]:
        root = self.base_url
        for suffix in ("/chat/completions", "/responses"):
            if root.endswith(suffix):
                root = root[: -len(suffix)]
                break
        values = [root]
        if not urlparse(root).path.rstrip("/"):
            values.append(f"{root}/v1")
        return tuple(dict.fromkeys(values))

    def _urls(self, endpoint: str) -> tuple[str, ...]:
        return tuple(f"{root}/{endpoint}" for root in self._roots())

    @property
    def chat_url(self) -> str:
        return self._urls("chat/completions")[0]

    @property
    def responses_url(self) -> str:
        return self._urls("responses")[0]

    @property
    def models_url(self) -> str:
        return self._urls("models")[0]

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json", "User-Agent": "MRobot-AI/2"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def list_models(self) -> tuple[str, ...]:
        last_error: Exception | None = None
        for url in self._urls("models"):
            try:
                response = self.session.get(url, headers=self._headers(), timeout=min(self.config.timeout, 20))
                response.raise_for_status()
                payload = response.json()
                values = payload.get("data", ()) if isinstance(payload, dict) else ()
                return tuple(sorted(str(item["id"]) for item in values if isinstance(item, dict) and item.get("id")))
            except requests.HTTPError as exc:
                last_error = exc
                if exc.response is not None and exc.response.status_code == 404:
                    continue
                break
            except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
                last_error = exc
                break
        assert last_error is not None
        raise self._friendly_error("读取模型列表失败", last_error) from last_error

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
        message_values = list(messages)
        tool_values = list(tools)
        attempts = ("responses", "chat") if self.config.protocol == "auto" else (self.config.protocol,)
        last_error: Exception | None = None

        for protocol_index, protocol in enumerate(attempts):
            payload = self._responses_payload(message_values, tool_values) if protocol == "responses" else self._chat_payload(message_values, tool_values)
            endpoint = "responses" if protocol == "responses" else "chat/completions"
            for url in self._urls(endpoint):
                try:
                    with self.session.post(
                        url,
                        headers=self._headers(),
                        json=payload,
                        stream=True,
                        timeout=(15, self.config.timeout),
                    ) as response:
                        response.raise_for_status()
                        return self._consume_response(response, protocol, on_text, cancelled)
                except AICancelled:
                    raise
                except requests.HTTPError as exc:
                    last_error = exc
                    status = exc.response.status_code if exc.response is not None else 0
                    if status in {404, 405}:
                        continue
                    if status == 400 and self.config.protocol == "auto" and protocol_index == 0:
                        break
                    raise self._friendly_error("AI 请求失败", exc) from exc
                except (requests.RequestException, ValueError, TypeError) as exc:
                    raise self._friendly_error("AI 请求失败", exc) from exc

        if last_error is not None:
            raise self._friendly_error("AI 请求失败", last_error) from last_error
        raise AIClientError("AI 请求失败：没有可用的接口协议")

    def _chat_payload(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, object]:
        payload: dict[str, object] = {
            "model": self.config.model,
            "messages": messages,
            "stream": True,
            "temperature": self.config.temperature,
        }
        if tools and self.config.enable_tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _responses_payload(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict[str, object]:
        instructions: list[str] = []
        input_items: list[dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role") or "")
            content = message.get("content")
            if role == "system":
                if content:
                    instructions.append(str(content))
                continue
            if role in {"user", "assistant"} and content:
                input_items.append({"role": role, "content": str(content)})
            if role == "assistant":
                for raw_call in message.get("tool_calls") or ():
                    if not isinstance(raw_call, dict):
                        continue
                    function = raw_call.get("function") or {}
                    if isinstance(function, dict) and function.get("name"):
                        input_items.append(
                            {
                                "type": "function_call",
                                "call_id": str(raw_call.get("id") or ""),
                                "name": str(function["name"]),
                                "arguments": str(function.get("arguments") or "{}"),
                            }
                        )
            if role == "tool":
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": str(message.get("tool_call_id") or ""),
                        "output": str(content or ""),
                    }
                )
        payload: dict[str, object] = {"model": self.config.model, "input": input_items, "stream": True}
        if instructions:
            payload["instructions"] = "\n\n".join(instructions)
        if tools and self.config.enable_tools:
            flattened: list[dict[str, Any]] = []
            for tool in tools:
                function = tool.get("function") if isinstance(tool, dict) else None
                if isinstance(function, dict):
                    flattened.append({"type": "function", **function})
            if flattened:
                payload["tools"] = flattened
                payload["tool_choice"] = "auto"
        return payload

    def _consume_response(
        self,
        response: requests.Response,
        protocol: str,
        on_text: Callable[[str], None] | None,
        cancelled: Callable[[], bool] | None,
    ) -> AssistantTurn:
        content_parts: list[str] = []
        calls: dict[int, dict[str, str]] = {}
        usage: dict[str, int] = {}
        plain_lines: list[str] = []
        saw_sse = False

        # Always decode SSE bytes ourselves. Some compatible gateways omit a
        # charset and requests then guesses ISO-8859-1, corrupting Chinese text.
        for raw_line in response.iter_lines(decode_unicode=False):
            if cancelled and cancelled():
                raise AICancelled("已停止生成")
            if not raw_line:
                continue
            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
            if line.startswith("event:"):
                saw_sse = True
                continue
            if not line.startswith("data:"):
                plain_lines.append(line)
                continue
            saw_sse = True
            data = line[5:].strip()
            if data == "[DONE]":
                break
            event = json.loads(data)
            if not isinstance(event, dict):
                continue
            self._consume_event(event, protocol, content_parts, calls, usage, on_text)

        if not saw_sse and plain_lines:
            payload = json.loads("\n".join(plain_lines))
            return self._consume_json(payload, protocol, on_text)

        turn = self._build_turn(content_parts, calls, usage)
        if not turn.content and not turn.tool_calls:
            raise AIClientError("AI 服务已连接，但没有返回可显示的文本或工具调用；请在模型设置中切换接口协议")
        return turn

    def _consume_event(
        self,
        event: dict[str, Any],
        protocol: str,
        content_parts: list[str],
        calls: dict[int, dict[str, str]],
        usage: dict[str, int],
        on_text: Callable[[str], None] | None,
    ) -> None:
        if isinstance(event.get("error"), dict) or str(event.get("type") or "").endswith(".error"):
            raise AIClientError("AI 服务返回错误，请检查模型权限、余额和接口参数")
        if protocol == "responses" or event.get("type"):
            event_type = str(event.get("type") or "")
            if event_type == "response.output_text.delta":
                self._append_text(str(event.get("delta") or ""), content_parts, on_text)
            elif event_type == "response.output_item.done":
                item = event.get("item") or {}
                if isinstance(item, dict) and item.get("type") == "function_call":
                    index = int(event.get("output_index", len(calls)))
                    calls[index] = {
                        "id": str(item.get("call_id") or item.get("id") or ""),
                        "name": str(item.get("name") or ""),
                        "arguments": str(item.get("arguments") or "{}"),
                    }
                elif isinstance(item, dict) and item.get("type") == "message" and not content_parts:
                    for part in item.get("content") or ():
                        if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                            self._append_text(part.get("text"), content_parts, on_text)
            elif event_type == "response.completed":
                response = event.get("response") or {}
                if isinstance(response, dict):
                    self._merge_usage(usage, response.get("usage"))
            if event_type:
                return

        self._merge_usage(usage, event.get("usage"))
        choices = event.get("choices") or []
        if not choices:
            return
        delta = choices[0].get("delta") or {}
        self._append_text(delta.get("content"), content_parts, on_text)
        message = choices[0].get("message") or {}
        if not delta and isinstance(message, dict):
            self._append_text(message.get("content"), content_parts, on_text)
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

    def _consume_json(
        self,
        payload: Any,
        protocol: str,
        on_text: Callable[[str], None] | None,
    ) -> AssistantTurn:
        if not isinstance(payload, dict):
            raise AIClientError("AI 服务返回的 JSON 格式不兼容")
        if isinstance(payload.get("error"), dict):
            raise AIClientError("AI 服务返回错误，请检查模型权限、余额和接口参数")
        content_parts: list[str] = []
        calls: dict[int, dict[str, str]] = {}
        usage: dict[str, int] = {}

        if protocol == "responses" or "output" in payload:
            self._merge_usage(usage, payload.get("usage"))
            has_output_text = isinstance(payload.get("output_text"), str) and bool(payload.get("output_text"))
            if has_output_text:
                self._append_text(payload["output_text"], content_parts, on_text)
            for index, item in enumerate(payload.get("output") or ()):
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "message" and not has_output_text:
                    for part in item.get("content") or ():
                        if isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                            self._append_text(part.get("text"), content_parts, on_text)
                elif item.get("type") == "function_call":
                    calls[index] = {
                        "id": str(item.get("call_id") or item.get("id") or ""),
                        "name": str(item.get("name") or ""),
                        "arguments": str(item.get("arguments") or "{}"),
                    }
        else:
            self._merge_usage(usage, payload.get("usage"))
            choices = payload.get("choices") or []
            message = choices[0].get("message") if choices and isinstance(choices[0], dict) else {}
            if isinstance(message, dict):
                self._append_text(message.get("content"), content_parts, on_text)
                for index, raw_call in enumerate(message.get("tool_calls") or ()):
                    if not isinstance(raw_call, dict):
                        continue
                    function = raw_call.get("function") or {}
                    if isinstance(function, dict) and function.get("name"):
                        calls[index] = {
                            "id": str(raw_call.get("id") or ""),
                            "name": str(function.get("name") or ""),
                            "arguments": str(function.get("arguments") or "{}"),
                        }
        turn = self._build_turn(content_parts, calls, usage)
        if not turn.content and not turn.tool_calls:
            raise AIClientError("AI 服务返回的 JSON 中没有可显示的文本或工具调用")
        return turn

    @staticmethod
    def _append_text(value: Any, content_parts: list[str], on_text: Callable[[str], None] | None) -> None:
        if isinstance(value, str) and value:
            content_parts.append(value)
            if on_text:
                on_text(value)

    @staticmethod
    def _merge_usage(target: dict[str, int], value: Any) -> None:
        if isinstance(value, dict):
            target.update({str(key): int(item) for key, item in value.items() if isinstance(item, (int, float))})

    @staticmethod
    def _build_turn(content_parts: list[str], calls: dict[int, dict[str, str]], usage: dict[str, int]) -> AssistantTurn:
        tool_calls = tuple(
            ToolCall(value["id"] or f"call_{index}", value["name"], value["arguments"] or "{}")
            for index, value in sorted(calls.items())
            if value["name"]
        )
        return AssistantTurn("".join(content_parts), tool_calls, usage)

    @staticmethod
    def _friendly_error(prefix: str, exc: Exception) -> AIClientError:
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            status = exc.response.status_code
            if status in {401, 403}:
                return AIClientError(f"{prefix}：API Key 无效或没有模型权限（HTTP {status}）")
            if status == 404:
                return AIClientError(f"{prefix}：未找到兼容接口，请检查 Base URL 是否包含 /v1（HTTP 404）")
            if status == 429:
                return AIClientError(f"{prefix}：服务限流或余额不足（HTTP 429）")
            return AIClientError(f"{prefix}：服务返回 HTTP {status}")
        if isinstance(exc, requests.Timeout):
            return AIClientError(f"{prefix}：连接或生成超时")
        if isinstance(exc, requests.ConnectionError):
            return AIClientError(f"{prefix}：无法连接服务，请检查 Base URL、网络或本地模型状态")
        return AIClientError(f"{prefix}：响应格式不兼容")
