"""Convert legacy MRobot assets into independently versioned package repositories.

The migration is deterministic and safe to rerun: existing non-empty repositories
are skipped unless --force is supplied. It does not publish or delete anything.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ALGORITHMS = {"ahrs", "filter", "kalman_filter", "limiter", "mixer", "pid", "user_math"}
IGNORED_INCLUDES = {"main", "cmsis_os", "cmsis_os2", "FreeRTOS", "task", "queue", "semphr", "timers", "stdint", "stddef", "stdbool", "string", "math", "stdlib", "stdio", "arm_math"}


@dataclass(frozen=True)
class LegacyPackage:
    category: str
    name: str
    source: Path

    @property
    def package_type(self) -> str:
        if self.category == "component" and self.name in ALGORITHMS:
            return "algorithm"
        return self.category

    @property
    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")

    @property
    def package_id(self) -> str:
        return f"mrobot.{self.package_type}.{self.slug}"

    @property
    def repository(self) -> str:
        return f"mrobot-{self.package_type}-{self.slug}"


def discover(assets: Path) -> list[LegacyPackage]:
    packages: list[LegacyPackage] = [
        LegacyPackage("bsp", "core", assets / "bsp/bsp.h"),
        LegacyPackage("device", "core", assets / "device/device.h"),
    ]
    for category in ("bsp", "component", "device"):
        for child in sorted((assets / category).iterdir()):
            if child.is_dir() and any(path.suffix.lower() in {".c", ".h"} for path in child.rglob("*")):
                if category == "device" and child.name == "bmi088":
                    continue
                packages.append(LegacyPackage(category, child.name.lower(), child))
    module_root = assets / "module"
    for header in sorted(module_root.rglob("*.h")):
        directory = header.parent
        if not any(path.suffix == ".c" for path in directory.iterdir()):
            continue
        relative = directory.relative_to(module_root)
        if relative == Path("."):
            name = "config"
        else:
            parts = list(relative.parts)
            leaf = parts[-1]
            if len(parts) > 1 and leaf.lower().startswith(parts[-2].lower() + "_"):
                leaf = leaf[len(parts[-2]) + 1:]
            parts[-1] = leaf
            name = "-".join(parts)
        item = LegacyPackage("module", name, directory)
        if item not in packages:
            packages.append(item)
    task_root = assets / "task" / "template_task"
    for source in sorted(task_root.glob("*.c")):
        packages.append(LegacyPackage("task", source.stem.replace("_", "-"), source))
    return packages


def include_stems(package: LegacyPackage) -> set[str]:
    if package.package_type == "module" and package.name == "config":
        sources = [package.source / "config.c", package.source / "config.h"]
    else:
        sources = [package.source] if package.source.is_file() else package.source.rglob("*")
    stems: set[str] = set()
    pattern = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]', re.MULTILINE)
    for source in sources:
        if not source.is_file() or source.suffix.lower() not in {".c", ".h"}:
            continue
        text = source.read_text(encoding="utf-8", errors="ignore")
        stems.update(Path(match).stem for match in pattern.findall(text))
    return stems - IGNORED_INCLUDES


def dependency_map(packages: Iterable[LegacyPackage]) -> dict[str, list[str]]:
    items = list(packages)
    owners: dict[str, list[LegacyPackage]] = {}
    for package in items:
        paths = [package.source] if package.source.is_file() else package.source.rglob("*")
        for path in paths:
            if path.is_file() and path.suffix.lower() == ".h":
                owners.setdefault(path.stem.lower(), []).append(package)
    result: dict[str, list[str]] = {}
    for package in items:
        dependencies: set[str] = set()
        for stem in include_stems(package):
            matches = owners.get(stem.lower(), [])
            if len(matches) == 1 and matches[0] != package:
                owner = matches[0]
                if owner.package_type != "bsp" or package.package_type == "bsp":
                    dependencies.add(owner.package_id)
        result[package.package_id] = sorted(dependencies)
    return result


def capabilities(package: LegacyPackage) -> tuple[list[str], list[str]]:
    if package.package_type == "bsp":
        return ([] if package.name == "core" else ["platform.stm32cubemx"]), [f"bsp.{package.slug}"]
    required = []
    for stem in sorted(include_stems(package)):
        normalized = stem.lower().removeprefix("bsp_")
        if normalized in {"can", "fdcan", "dwt", "flash", "gpio", "i2c", "mm", "pwm", "spi", "time", "uart"}:
            required.append(f"bsp.{normalized}")
    return sorted(set(required)), [f"{package.package_type}.{package.slug}"]


def destination_files(package: LegacyPackage) -> list[tuple[Path, str, str, str]]:
    if package.package_type == "module" and package.name == "config":
        sources = [package.source / "config.c", package.source / "config.h"]
    else:
        sources = [package.source] if package.source.is_file() else sorted(package.source.rglob("*"))
    result: list[tuple[Path, str, str, str]] = []
    for source in sources:
        if not source.is_file() or source.name.startswith("."):
            continue
        relative = Path(source.name) if package.source.is_file() else source.relative_to(package.source)
        repo_path = Path("src") / relative
        if package.package_type == "bsp":
            destination = Path("User/bsp") / relative
        elif package.package_type in {"component", "algorithm"}:
            destination = Path("User/component") / relative
        elif package.package_type == "device":
            destination = Path("User/device") / relative
        elif package.package_type == "task":
            destination = Path("User/task") / relative
        elif package.package_type == "module":
            module_root = package.source if package.source.name == "module" else next(parent for parent in package.source.parents if parent.name == "module")
            prefix = package.source.relative_to(module_root)
            destination = Path("User/module") / prefix / relative
        else:
            destination = Path("User/MRobot/packages") / package.repository / relative
        policy = "generated"
        if package.package_type == "module" and package.name == "config":
            destination = Path("User/MRobot/config") / relative
            policy = "scaffold"
        result.append((source, repo_path.as_posix(), destination.as_posix(), policy))
    return result


def write_package(package: LegacyPackage, output: Path, dependencies: dict[str, list[str]], force: bool) -> Path | None:
    root = output / package.repository
    if root.exists() and any(root.iterdir()):
        if not force:
            return None
        shutil.rmtree(root)
    root.mkdir(parents=True)
    requires, provides = capabilities(package)
    files = []
    for source, repo_path, destination, policy in destination_files(package):
        target = root / repo_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        files.append({"source": repo_path, "destination": destination, "policy": policy})
    manifest = {
        "$schema": "https://raw.githubusercontent.com/goldenfishs/MCode/main/schemas/package.schema.json",
        "schema_version": 1,
        "package": {
            "id": package.package_id,
            "name": f"MRobot {package.name}",
            "type": package.package_type,
            "version": "0.1.0",
            "description": f"Migrated MRobot {package.package_type} package",
            "repository": f"https://github.com/goldenfishs/{package.repository}",
        },
        "dependencies": [{"id": item, "version": "^0.1.0"} for item in dependencies[package.package_id]],
        "requires": requires,
        "provides": provides,
        "files": files,
    }
    (root / "mrobot-package.yaml").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (root / "README.md").write_text(
        f"# {package.repository}\n\n`{package.package_id}` extracted from the MRobot legacy asset tree. Install and generate it through MCode.\n",
        encoding="utf-8",
    )
    (root / "LICENSE").write_text((Path(__file__).resolve().parents[1] / "LICENSE").read_text(encoding="utf-8"), encoding="utf-8")
    (root / ".gitignore").write_text("build/\n.mrobot/\n", encoding="utf-8")
    workflow = root / ".github/workflows/validate.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "name: validate\non: [push, pull_request]\njobs:\n  manifest:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: python -m pip install \"mrobot-mcode @ git+https://github.com/goldenfishs/MCode.git\"\n      - run: mcode package validate .\n",
        encoding="utf-8",
    )
    return root


def update_manifest(package: LegacyPackage, output: Path, dependencies: dict[str, list[str]]) -> Path:
    root = output / package.repository
    manifest_path = root / "mrobot-package.yaml"
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    desired_dependencies = [{"id": item, "version": "^0.1.0"} for item in dependencies[package.package_id]]
    if value.get("dependencies", []) != desired_dependencies:
        version = value["package"]["version"].split(".")
        version[2] = str(int(version[2]) + 1)
        value["package"]["version"] = ".".join(version)
        value["dependencies"] = desired_dependencies
    value["files"] = [
        {"source": repo_path, "destination": destination, "policy": policy}
        for _, repo_path, destination, policy in destination_files(package)
    ]
    manifest_path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path(__file__).resolve().parents[1] / "assets/User_code")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[2] / "mrobot-packages-migrated")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--update-manifests", action="store_true", help="Update destinations/version in already migrated repositories")
    args = parser.parse_args()
    packages = discover(args.assets)
    dependencies = dependency_map(packages)
    if args.update_manifests:
        created = [update_manifest(package, args.output, dependencies) for package in packages]
    else:
        created = [path for package in packages if (path := write_package(package, args.output, dependencies, args.force))]
    print(json.dumps({"discovered": len(packages), "created": len(created), "output": str(args.output.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
