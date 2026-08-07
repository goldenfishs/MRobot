from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import MCodeConfig, load_structured_file
from .errors import ConfigurationError, ResolutionError
from .models import PackageDependency, PackageFile, PackageManifest, ProjectModel


MANIFEST_NAME = "mrobot-package.yaml"
PACKAGE_TYPES = {"platform", "board", "bsp", "device", "component", "algorithm", "module", "task"}
FILE_POLICIES = {"generated", "scaffold"}


def _dependency(value: Any) -> PackageDependency:
    if isinstance(value, str):
        return PackageDependency(value)
    if isinstance(value, dict) and isinstance(value.get("id"), str):
        return PackageDependency(value["id"], str(value.get("version", "*")), bool(value.get("optional", False)))
    raise ConfigurationError("package.dependencies 项必须是包 id 或含 id 的对象")


def load_manifest(path: str | Path) -> PackageManifest:
    candidate = Path(path).resolve()
    manifest_path = candidate / MANIFEST_NAME if candidate.is_dir() else candidate
    if manifest_path.name != MANIFEST_NAME or not manifest_path.is_file():
        raise ConfigurationError(f"找不到包清单 {MANIFEST_NAME}: {candidate}")
    raw = load_structured_file(manifest_path)
    if raw.get("schema_version", 1) != 1:
        raise ConfigurationError(f"不支持的包清单版本: {manifest_path}")
    package = raw.get("package")
    if not isinstance(package, dict):
        raise ConfigurationError(f"package 必须是对象: {manifest_path}")
    package_id = package.get("id")
    package_type = package.get("type")
    version = package.get("version")
    if not all(isinstance(item, str) and item for item in (package_id, package_type, version)):
        raise ConfigurationError(f"package.id、package.type 和 package.version 均为必填字符串: {manifest_path}")
    if package_type not in PACKAGE_TYPES:
        raise ConfigurationError(f"未知 package.type '{package_type}': {manifest_path}")
    dependencies = tuple(_dependency(item) for item in (raw.get("dependencies") or []))
    requires = raw.get("requires") or []
    provides = raw.get("provides") or []
    if not isinstance(requires, list) or not isinstance(provides, list) or not all(isinstance(item, str) for item in requires + provides):
        raise ConfigurationError(f"requires/provides 必须是字符串数组: {manifest_path}")
    files: list[PackageFile] = []
    for item in raw.get("files") or []:
        if not isinstance(item, dict) or not isinstance(item.get("source"), str) or not isinstance(item.get("destination"), str):
            raise ConfigurationError(f"files 项必须包含 source 和 destination: {manifest_path}")
        policy = item.get("policy", "generated")
        if policy not in FILE_POLICIES:
            raise ConfigurationError(f"不支持的文件策略 '{policy}': {manifest_path}")
        source = (manifest_path.parent / item["source"]).resolve()
        try:
            source.relative_to(manifest_path.parent.resolve())
        except ValueError as exc:
            raise ConfigurationError(f"包文件不能位于仓库之外: {item['source']}") from exc
        if not source.is_file():
            raise ConfigurationError(f"包源文件不存在: {source}")
        files.append(PackageFile(item["source"], item["destination"], policy))
    return PackageManifest(
        package_id=package_id,
        name=str(package.get("name", package_id)),
        package_type=package_type,
        version=version,
        root=str(manifest_path.parent),
        description=str(package.get("description", "")),
        dependencies=dependencies,
        requires=tuple(requires),
        provides=tuple(provides),
        files=tuple(files),
    )


def _available_manifests(config: MCodeConfig) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for root_name in config.package_roots:
        root = (config.root / root_name).resolve()
        if not root.is_dir():
            continue
        for path in sorted(root.rglob(MANIFEST_NAME)):
            manifest = load_manifest(path)
            previous = result.get(manifest.package_id)
            if previous and previous != path:
                raise ResolutionError(f"包 id 重复: {manifest.package_id} ({previous}, {path})")
            result[manifest.package_id] = path
    return result


def resolve_packages(config: MCodeConfig, project: ProjectModel) -> tuple[PackageManifest, ...]:
    available = _available_manifests(config)
    selected: dict[str, PackageManifest] = {}
    for selection in config.packages:
        if not selection.enabled:
            continue
        path = (config.root / selection.path).resolve()
        manifest = load_manifest(path)
        if manifest.package_id in selected and selected[manifest.package_id].root != manifest.root:
            raise ResolutionError(f"包 id 重复: {manifest.package_id}")
        selected[manifest.package_id] = manifest
        available.setdefault(manifest.package_id, path)

    def include_dependencies(manifest: PackageManifest, stack: tuple[str, ...] = ()) -> None:
        for dependency in manifest.dependencies:
            if dependency.package_id in selected:
                continue
            path = available.get(dependency.package_id)
            if path is None:
                if dependency.optional:
                    continue
                chain = " -> ".join(stack + (manifest.package_id, dependency.package_id))
                raise ResolutionError(f"缺少依赖包 {dependency.package_id}（{chain}）")
            dependency_manifest = load_manifest(path)
            selected[dependency.package_id] = dependency_manifest
            include_dependencies(dependency_manifest, stack + (manifest.package_id,))

    for item in tuple(selected.values()):
        include_dependencies(item)

    ordered: list[PackageManifest] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(package_id: str) -> None:
        if package_id in visited:
            return
        if package_id in visiting:
            cycle = " -> ".join(visiting[visiting.index(package_id):] + [package_id])
            raise ResolutionError(f"包依赖存在循环: {cycle}")
        visiting.append(package_id)
        manifest = selected[package_id]
        for dependency in manifest.dependencies:
            if dependency.package_id in selected:
                visit(dependency.package_id)
        visiting.pop()
        visited.add(package_id)
        ordered.append(manifest)

    for package_id in sorted(selected):
        visit(package_id)

    capabilities = set(project.capabilities)
    for manifest in ordered:
        capabilities.update(manifest.provides)
    missing = sorted({requirement for manifest in ordered for requirement in manifest.requires if requirement not in capabilities})
    if missing:
        raise ResolutionError("当前 CubeMX 工程或包集合不满足能力要求: " + ", ".join(missing))
    return tuple(ordered)
