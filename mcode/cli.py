from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import MCodeError
from .service import MCodeService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcode", description="MRobot 统一代码生成引擎")
    parser.add_argument("--version", action="version", version=f"MCode {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("init", "初始化 mrobot.yaml"),
        ("inspect", "解析 CubeMX 工程并输出统一模型"),
        ("plan", "预览生成变更，不写入文件"),
        ("generate", "按计划原子生成代码"),
        ("validate", "验证工程、包依赖与生成冲突"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("project", nargs="?", default=".", help="CubeMX 工程目录或 .ioc 文件")
        command.add_argument("--json", action="store_true", help="输出稳定的 JSON，供 GUI/插件/AI 使用")
        if name == "init":
            command.add_argument("--force", action="store_true", help="覆盖已有 mrobot.yaml")
    package = subparsers.add_parser("package", help="MRobot 包开发工具")
    package_commands = package.add_subparsers(dest="package_command", required=True)
    package_validate = package_commands.add_parser("validate", help="验证 mrobot-package.yaml")
    package_validate.add_argument("package", nargs="?", default=".", help="包目录或清单路径")
    package_validate.add_argument("--json", action="store_true", help="输出稳定 JSON")
    return parser


def _human_plan(data: dict[str, Any]) -> str:
    lines = [f"项目: {data['project_root']}"]
    summary = data["summary"]
    lines.append("变更: " + ", ".join(f"{key}={value}" for key, value in summary.items() if value))
    for change in data["changes"]:
        lines.append(f"  {change['action']:8} {change['path']}  ({change['reason']})")
    return "\n".join(lines)


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = MCodeService()
    try:
        if args.command == "package":
            diagnostics = service.validate_package(args.package)
            data = {"valid": not diagnostics, "diagnostics": [item.to_dict() for item in diagnostics]}
            human = "包清单验证通过" if data["valid"] else "\n".join(item.message for item in diagnostics)
        elif args.command == "init":
            target = service.initialize(args.project, args.force)
            data: Any = {"path": str(target), "created": True}
            human = f"已创建 {target}"
        elif args.command == "inspect":
            data = service.inspect(args.project).to_dict()
            human = json.dumps(data, ensure_ascii=False, indent=2)
        elif args.command == "plan":
            data = service.plan(args.project).to_dict()
            human = _human_plan(data)
        elif args.command == "generate":
            plan = service.generate(args.project)
            data = plan.to_dict()
            data["applied"] = True
            human = "生成完成\n" + _human_plan(data)
        else:
            diagnostics = service.validate(args.project)
            data = {"valid": not any(item.severity.value == "error" for item in diagnostics), "diagnostics": [item.to_dict() for item in diagnostics]}
            human = "验证通过" if data["valid"] else "\n".join(f"{item['severity']}: {item['message']}" for item in data["diagnostics"])
        print(json.dumps(data, ensure_ascii=False, indent=2) if args.json else human)
        if args.command in {"validate", "package"} and not data["valid"]:
            return 2
        if args.command == "plan" and data["has_errors"]:
            return 3
        return 0
    except MCodeError as exc:
        error = {"error": {"type": exc.__class__.__name__, "message": str(exc)}}
        print(json.dumps(error, ensure_ascii=False) if getattr(args, "json", False) else f"错误: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
