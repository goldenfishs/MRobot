"""Create the rate-limit-free update.json published with desktop releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


ARTIFACT = re.compile(
    r"^MRobot-v(?P<version>[^-]+)-(?P<system>macos|windows|linux)-(?P<arch>[^-.]+).+"
)


def create_manifest(directory: Path, repository: str, tag: str, base_url: str | None = None) -> Path:
    version = tag.removeprefix("v")
    assets: list[dict[str, object]] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name.endswith(".sha256") or path.name == "update.json":
            continue
        match = ARTIFACT.match(path.name)
        if not match or match.group("version") != version:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        download_root = (
            base_url.rstrip("/")
            if base_url
            else f"https://github.com/{repository}/releases/download/{quote(tag)}"
        )
        assets.append(
            {
                "name": path.name,
                "system": match.group("system"),
                "architecture": match.group("arch"),
                "size": path.stat().st_size,
                "sha256": digest,
                "url": f"{download_root}/{quote(path.name)}",
            }
        )
    required = {"macos", "windows", "linux"}
    present = {str(asset["system"]) for asset in assets}
    if present != required:
        raise SystemExit(f"update manifest requires {sorted(required)}, found {sorted(present)}")
    manifest = {
        "schema_version": 1,
        "version": version,
        "channel": "stable",
        "published_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "release_url": f"https://github.com/{repository}/releases/tag/{quote(tag)}",
        "release_notes": "完整更新说明请查看 Release 页面。",
        "assets": assets,
    }
    target = directory / "update.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    (directory / "update.json.sha256").write_text(f"{checksum}  update.json\n", encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--base-url", help="Override asset download root for a mirror manifest")
    args = parser.parse_args()
    print(create_manifest(args.directory, args.repository, args.tag, args.base_url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
