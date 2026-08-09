"""Command-line frontend for the shared MRobot desktop update service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .update_service import UpdateError, UpdateService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mrobot-update", description="MRobot 桌面更新工具")
    parser.add_argument("--json", action="store_true", help="输出稳定 JSON，供插件或 AI 调用")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="检查当前平台是否有更新")
    subparsers.add_parser("download", help="下载并校验当前平台更新包")
    install = subparsers.add_parser("install", help="下载、安装并重新启动 MRobot")
    install.add_argument(
        "--desktop-path",
        type=Path,
        help="源码模式下指定已安装的 MRobot.app 或 MRobot 可执行文件",
    )
    return parser


def _print(data: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if not data.get("available"):
        print("当前已是最新版本")
    elif data.get("installing"):
        print(f"已启动 MRobot {data['version']} 安装程序")
    elif data.get("downloaded"):
        print(f"已下载并校验：{data['path']}")
    else:
        print(f"发现 MRobot {data['version']}：{data['asset_name']}")


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        executable = args.desktop_path if args.command == "install" else None
        service = UpdateService(
            __version__,
            executable=executable,
            frozen=True if executable else None,
        )
        update = service.check()
        if update is None:
            _print({"available": False, "current_version": __version__}, args.json)
            return 0
        if args.command == "check":
            data = update.to_dict()
            data["available"] = True
            _print(data, args.json)
            return 0

        def progress(downloaded: int, total: int) -> None:
            if not args.json and total:
                print(f"\r下载 {downloaded * 100 / total:5.1f}%", end="", file=sys.stderr)

        downloaded = service.download(update, progress)
        if not args.json:
            print(file=sys.stderr)
        data: dict[str, object] = {
            "available": True,
            "version": update.version,
            "downloaded": True,
            "path": str(downloaded.path),
            "sha256": update.asset.sha256,
        }
        if args.command == "download":
            _print(data, args.json)
            return 0
        plan = service.prepare_install(downloaded)
        service.launch_install(plan)
        data["installing"] = True
        _print(data, args.json)
        return 0
    except UpdateError as exc:
        error = {"error": {"type": exc.__class__.__name__, "message": str(exc)}}
        print(json.dumps(error, ensure_ascii=False) if args.json else f"错误：{exc}", file=sys.stderr)
        return 2


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
