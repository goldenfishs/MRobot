from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigurationError


CONFIG_NAME = "mrobot.yaml"


def load_structured_file(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(f"无法读取配置文件 {path}: {exc}") from exc

    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ConfigurationError(
                f"{path} 使用 YAML 语法；请安装 mrobot-mcode[yaml]，或使用 JSON 兼容的 YAML"
            ) from exc
        try:
            value = yaml.safe_load(text)
        except Exception as exc:
            raise ConfigurationError(f"配置文件格式错误 {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise ConfigurationError(f"配置文件根节点必须是对象: {path}")
    return value


def write_json_yaml(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class PackageSelection:
    path: str
    enabled: bool = True


@dataclass(frozen=True)
class MCodeConfig:
    root: Path
    ioc: str | None = None
    generated_root: str = "User/MRobot/generated"
    package_roots: tuple[str, ...] = ("mrobot-packages",)
    packages: tuple[PackageSelection, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def defaults(cls, root: Path) -> "MCodeConfig":
        return cls(root=root.resolve())

    @classmethod
    def load(cls, root: Path) -> "MCodeConfig":
        root = root.resolve()
        path = root / CONFIG_NAME
        if not path.exists():
            return cls.defaults(root)
        raw = load_structured_file(path)
        schema_version = raw.get("schema_version", 1)
        if schema_version != 1:
            raise ConfigurationError(f"不支持的 mrobot.yaml schema_version: {schema_version}")
        project = raw.get("project") or {}
        output = raw.get("output") or {}
        if not isinstance(project, dict) or not isinstance(output, dict):
            raise ConfigurationError("project 和 output 必须是对象")
        platform = project.get("platform", "stm32cubemx")
        if platform != "stm32cubemx":
            raise ConfigurationError(f"当前版本只支持 project.platform=stm32cubemx，收到: {platform}")
        package_items = raw.get("packages") or []
        if not isinstance(package_items, list):
            raise ConfigurationError("packages 必须是数组")
        packages: list[PackageSelection] = []
        for item in package_items:
            if isinstance(item, str):
                packages.append(PackageSelection(item))
            elif isinstance(item, dict) and isinstance(item.get("path"), str):
                packages.append(PackageSelection(item["path"], bool(item.get("enabled", True))))
            else:
                raise ConfigurationError("packages 项必须是路径字符串或含 path 的对象")
        roots = raw.get("package_roots", ["mrobot-packages"])
        if not isinstance(roots, list) or not all(isinstance(item, str) for item in roots):
            raise ConfigurationError("package_roots 必须是字符串数组")
        return cls(
            root=root,
            ioc=project.get("ioc"),
            generated_root=output.get("generated_root", "User/MRobot/generated"),
            package_roots=tuple(roots),
            packages=tuple(packages),
            raw=raw,
        )

    def template(self, ioc: str | None = None) -> dict[str, Any]:
        return {
            "$schema": "https://raw.githubusercontent.com/goldenfishs/MCode/main/mcode/schemas/mrobot.schema.json",
            "schema_version": 1,
            "project": {"ioc": ioc or "project.ioc", "platform": "stm32cubemx"},
            "output": {"generated_root": self.generated_root},
            "package_roots": list(self.package_roots),
            "packages": [],
        }
