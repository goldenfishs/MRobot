from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcode.service import MCodeService


TEXT_SUFFIXES = {".c", ".h", ".cc", ".cpp", ".hpp", ".ioc", ".json", ".yaml", ".yml", ".md", ".txt", ".cmake", ".py"}
TEXT_NAMES = {"CMakeLists.txt", "Makefile", "Kconfig"}
IGNORED_DIRECTORIES = {".git", ".mrobot", ".venv", "build", "dist", "release-dist", "__pycache__"}
SENSITIVE_NAMES = {".env", ".env.local", "credentials.json", "secrets.json"}


class MRobotToolRegistry:
    """Read-only, project-scoped tools available to an AI model."""

    def __init__(self, project_root: str | Path | None, service: MCodeService | None = None) -> None:
        self.project_root = Path(project_root).expanduser().resolve() if project_root else None
        self.service = service or MCodeService()

    def definitions(self) -> tuple[dict[str, Any], ...]:
        if self.project_root is None:
            return ()
        return (
            self._definition("inspect_project", "读取 MCU、平台、外设、引脚和工程能力。", {}),
            self._definition("plan_generation", "预览 MCode 将创建、修改或冲突的文件；不会写入工程。", {}),
            self._definition("validate_project", "运行 MCode 工程与生成冲突诊断；不会写入工程。", {}),
            self._definition(
                "list_project_files",
                "列出工程内适合提供给 AI 的文本文件。",
                {"pattern": {"type": "string", "description": "可选的文件名包含过滤词"}},
            ),
            self._definition(
                "read_project_file",
                "读取工程目录内一个受支持的文本文件，最多 32 KiB。",
                {"path": {"type": "string", "description": "相对工程根目录的文件路径"}},
                required=("path",),
            ),
        )

    @staticmethod
    def _definition(name: str, description: str, properties: dict[str, Any], required: tuple[str, ...] = ()) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": list(required),
                    "additionalProperties": False,
                },
            },
        }

    def execute(self, name: str, arguments: dict[str, Any]) -> str:
        root = self._require_root()
        if name == "inspect_project":
            result: object = self.service.inspect(root).to_dict()
        elif name == "plan_generation":
            result = self.service.plan(root).to_dict()
            changes = result.get("changes", []) if isinstance(result, dict) else []
            if isinstance(changes, list) and len(changes) > 100:
                result["changes"] = changes[:100]
                result["truncated"] = True
                result["total_changes"] = len(changes)
        elif name == "validate_project":
            result = {"diagnostics": [item.to_dict() for item in self.service.validate(root)]}
        elif name == "list_project_files":
            result = {"files": self._list_files(str(arguments.get("pattern") or ""))}
        elif name == "read_project_file":
            result = self._read_file(str(arguments.get("path") or ""))
        else:
            raise ValueError(f"未知或未授权的 AI 工具：{name}")
        return json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    def _require_root(self) -> Path:
        if self.project_root is None or not self.project_root.is_dir():
            raise ValueError("请先选择有效的 MRobot 工程目录")
        return self.project_root

    def _safe_file(self, relative: str) -> Path:
        root = self._require_root()
        if not relative or Path(relative).is_absolute():
            raise ValueError("文件路径必须是工程内的相对路径")
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError("拒绝读取工程目录之外的文件") from exc
        if any(part in IGNORED_DIRECTORIES for part in target.relative_to(root).parts):
            raise ValueError("该目录不允许提供给 AI")
        if target.name.lower() in SENSITIVE_NAMES or target.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            raise ValueError("拒绝读取可能包含密钥的文件")
        if target.suffix.lower() not in TEXT_SUFFIXES and target.name not in TEXT_NAMES:
            raise ValueError("该文件类型不在 AI 文本上下文白名单中")
        if not target.is_file():
            raise ValueError("文件不存在")
        return target

    def _list_files(self, pattern: str) -> list[str]:
        root = self._require_root()
        needle = pattern.casefold()
        results: list[str] = []
        for target in sorted(root.rglob("*")):
            relative = target.relative_to(root)
            if any(part in IGNORED_DIRECTORIES for part in relative.parts):
                continue
            if not target.is_file() or (target.suffix.lower() not in TEXT_SUFFIXES and target.name not in TEXT_NAMES):
                continue
            if target.name.lower() in SENSITIVE_NAMES or target.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
                continue
            value = relative.as_posix()
            if not needle or needle in value.casefold():
                results.append(value)
            if len(results) >= 200:
                break
        return results

    def _read_file(self, relative: str) -> dict[str, object]:
        target = self._safe_file(relative)
        size = target.stat().st_size
        if size > 32 * 1024:
            raise ValueError(f"文件过大（{size} 字节），单次最多读取 32768 字节")
        return {
            "path": target.relative_to(self._require_root()).as_posix(),
            "size": size,
            "content": target.read_text(encoding="utf-8", errors="replace"),
        }
