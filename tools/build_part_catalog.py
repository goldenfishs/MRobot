#!/usr/bin/env python3
"""Build the static cloud part catalogue from an offline ZIP source."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.part_library import PartCatalog, extract_entries


DEFAULT_BASE_URL = "https://download.qutmrobot.cn/parts/v1/files/"


def build_catalog(
    source: Path,
    output: Path,
    *,
    base_url: str = DEFAULT_BASE_URL,
    collection: str = "机械",
) -> Path:
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"输出目录必须为空：{output}")
    output.mkdir(parents=True, exist_ok=True)
    files_root = output / "files"

    catalog = PartCatalog.load(source)
    entries = tuple(
        sorted(
            (entry for entry in catalog.entries if entry.collection == collection),
            key=lambda entry: entry.path,
        )
    )
    if not entries:
        raise RuntimeError(f"资料包中没有集合：{collection}")
    extract_entries(catalog.source, entries, files_root)

    decoded_by_archive_name = {entry.archive_name: entry.path for entry in catalog.entries}
    version_hash = hashlib.sha256()
    manifest_entries = []
    for entry in entries:
        version_hash.update(entry.path.encode("utf-8"))
        version_hash.update(str(entry.size).encode("ascii"))
        preview_path = decoded_by_archive_name.get(entry.preview_archive_name or "")
        manifest_entries.append(
            {
                "path": entry.path,
                "size": entry.size,
                **({"preview": preview_path} if preview_path else {}),
            }
        )

    payload = {
        "schema_version": 1,
        "version": version_hash.hexdigest()[:12],
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "base_url": base_url.rstrip("/") + "/",
        "file_count": len(entries),
        "model_count": sum(entry.is_model for entry in entries),
        "total_size": sum(entry.size for entry in entries),
        "entries": manifest_entries,
    }
    manifest_path = output / "catalog.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成 MRobot 云端零件库静态目录")
    parser.add_argument("--source", type=Path, required=True, help="源零件库 ZIP")
    parser.add_argument("--output", type=Path, required=True, help="空输出目录")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="云端文件基础 URL")
    parser.add_argument("--collection", default="机械", help="需要发布的顶层集合")
    args = parser.parse_args(argv)
    try:
        manifest = build_catalog(
            args.source,
            args.output,
            base_url=args.base_url,
            collection=args.collection,
        )
    except Exception as exc:
        print(f"构建失败：{exc}", file=sys.stderr)
        return 1
    print(manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
