from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.ai.client import AIClientError, OpenAICompatibleClient, validate_base_url
from app.ai.config import AIConversationStore, AIProfileStore
from app.ai.models import AIProviderConfig, AssistantTurn, Conversation, ToolCall
from app.ai.service import MRobotAssistant
from app.ai.tools import MRobotToolRegistry
from tests.helpers import write_config, write_ioc


class StreamResponse:
    def __init__(self, lines: list[str], status: int = 200):
        self.lines = lines
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            response = requests.Response()
            response.status_code = self.status_code
            raise requests.HTTPError(response=response)

    def iter_lines(self, decode_unicode: bool = False):
        yield from self.lines

    def json(self):
        return {"data": [{"id": "demo-model"}]}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeSession:
    def __init__(self, responses: list[StreamResponse]):
        self.responses = list(responses)
        self.requests = []

    def post(self, url, **kwargs):
        self.requests.append(("POST", url, kwargs))
        return self.responses.pop(0)

    def get(self, url, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return self.responses.pop(0)


def config(**overrides) -> AIProviderConfig:
    values = {
        "name": "测试模型",
        "base_url": "https://ai.example.com/v1",
        "model": "demo-model",
        "api_key_env": "TEST_AI_KEY",
    }
    values.update(overrides)
    return AIProviderConfig(**values)


def sse(value: dict) -> str:
    return "data: " + json.dumps(value)


def test_provider_url_rejects_insecure_remote_and_credentials() -> None:
    assert validate_base_url("http://127.0.0.1:11434/v1/") == "http://127.0.0.1:11434/v1"
    assert validate_base_url("https://ai.example.com/v1") == "https://ai.example.com/v1"
    with pytest.raises(AIClientError, match="HTTPS"):
        validate_base_url("http://ai.example.com/v1")
    with pytest.raises(AIClientError, match="账号密码"):
        validate_base_url("https://user:secret@ai.example.com/v1")


def test_openai_compatible_stream_collects_text_usage_and_fragmented_tool_calls() -> None:
    response = StreamResponse(
        [
            sse({"choices": [{"delta": {"content": "正在"}}]}),
            sse({"choices": [{"delta": {"content": "检查"}}]}),
            sse({"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "function": {"name": "inspect_", "arguments": "{"}}]}}]}),
            sse({"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"name": "project", "arguments": "}"}}]}}]}),
            sse({"choices": [], "usage": {"prompt_tokens": 12, "completion_tokens": 4}}),
            "data: [DONE]",
        ]
    )
    session = FakeSession([response])
    chunks: list[str] = []
    client = OpenAICompatibleClient(config(), api_key="secret", session=session)
    result = client.complete_turn([{"role": "user", "content": "检查工程"}], on_text=chunks.append)
    assert result.content == "正在检查"
    assert chunks == ["正在", "检查"]
    assert result.tool_calls == (ToolCall("call_1", "inspect_project", "{}"),)
    assert result.usage["prompt_tokens"] == 12
    method, url, request = session.requests[0]
    assert method == "POST"
    assert url == "https://ai.example.com/v1/chat/completions"
    assert request["headers"]["Authorization"] == "Bearer secret"
    assert "secret" not in json.dumps(request["json"])


def test_model_listing_uses_models_endpoint() -> None:
    session = FakeSession([StreamResponse([])])
    client = OpenAICompatibleClient(config(), session=session)
    assert client.list_models() == ("demo-model",)
    assert session.requests[0][1] == "https://ai.example.com/v1/models"


def test_profiles_never_persist_api_key(tmp_path: Path) -> None:
    target = tmp_path / "profiles.json"
    store = AIProfileStore(target)
    provider = config()
    store.save(provider.name, {provider.name: provider})
    text = target.read_text(encoding="utf-8")
    assert "api_key_env" in text
    assert "actual-secret" not in text
    active, profiles = store.load()
    assert active == provider.name
    assert profiles[active] == provider


def test_conversations_are_local_and_bounded(tmp_path: Path) -> None:
    store = AIConversationStore(tmp_path / "conversations.json", limit=2)
    conversations = [Conversation.create("测试模型") for _ in range(3)]
    for index, conversation in enumerate(conversations):
        conversation.title = f"对话 {index}"
        conversation.updated_at = f"2026-08-09T00:00:0{index}+00:00"
    store.save_all(conversations)
    loaded = store.load()
    assert [item.title for item in loaded] == ["对话 2", "对话 1"]


def test_project_tools_are_read_only_and_block_path_escape_and_secrets(tmp_path: Path) -> None:
    write_ioc(tmp_path)
    write_config(tmp_path)
    (tmp_path / "Core").mkdir()
    (tmp_path / "Core" / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    tools = MRobotToolRegistry(tmp_path)

    definitions = tools.definitions()
    assert {item["function"]["name"] for item in definitions} == {
        "inspect_project",
        "plan_generation",
        "validate_project",
        "list_project_files",
        "read_project_file",
    }
    files = json.loads(tools.execute("list_project_files", {}))["files"]
    assert "Core/main.c" in files
    assert ".env" not in files
    result = json.loads(tools.execute("read_project_file", {"path": "Core/main.c"}))
    assert "int main" in result["content"]
    inspected = json.loads(tools.execute("inspect_project", {}))
    assert inspected["mcu"] == "STM32F407IGHx"
    with pytest.raises(ValueError, match="之外"):
        tools.execute("read_project_file", {"path": "../outside.txt"})
    with pytest.raises(ValueError, match="密钥"):
        tools.execute("read_project_file", {"path": ".env"})
    with pytest.raises(ValueError, match="未授权"):
        tools.execute("generate_project", {})


def test_assistant_executes_tool_then_returns_final_answer() -> None:
    class FakeClient:
        config = SimpleNamespace(enable_tools=True)

        def __init__(self):
            self.turns = [
                AssistantTurn("", (ToolCall("call_1", "inspect_project", "{}"),)),
                AssistantTurn("工程使用 STM32F4。"),
            ]

        def complete_turn(self, messages, **_kwargs):
            assert messages[0]["role"] == "system"
            return self.turns.pop(0)

    class FakeTools:
        project_root = Path("/tmp/demo")

        def definitions(self):
            return ({"type": "function", "function": {"name": "inspect_project"}},)

        def execute(self, name, arguments):
            assert name == "inspect_project"
            assert arguments == {}
            return '{"mcu":"STM32F407"}'

    result = MRobotAssistant(FakeClient(), FakeTools()).run([{"role": "user", "content": "什么 MCU？"}])
    assert result.text == "工程使用 STM32F4。"
    assert len(result.tool_events) == 1
    assert [message["role"] for message in result.messages] == ["user", "assistant", "tool", "assistant"]


def test_main_navigation_exposes_ai_workbench() -> None:
    source = (Path(__file__).resolve().parents[1] / "app" / "main_window.py").read_text(encoding="utf-8")
    assert "self.aiInterface = AIInterface" in source
    assert "self.addSubInterface(self.aiInterface, FIF.ROBOT" in source
