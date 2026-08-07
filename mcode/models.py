from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    severity: Severity = Severity.ERROR
    path: str | None = None
    hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Pin:
    name: str
    signal: str = ""
    label: str = ""
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Peripheral:
    name: str
    kind: str
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectModel:
    project_root: str
    ioc_path: str
    name: str
    mcu: str
    family: str
    series: str
    freertos: bool
    peripherals: tuple[Peripheral, ...] = ()
    pins: tuple[Pin, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def capabilities(self) -> tuple[str, ...]:
        kinds = {peripheral.kind.lower() for peripheral in self.peripherals}
        capabilities = {f"bsp.{kind}" for kind in kinds}
        if kinds.intersection({"uart", "usart", "lpuart"}):
            capabilities.add("bsp.uart")
        if "fdcan" in kinds:
            capabilities.add("bsp.can")
        if "tim" in kinds and any(
            "PWM" in key.upper()
            for peripheral in self.peripherals
            if peripheral.kind.upper() == "TIM"
            for key in peripheral.attributes
        ):
            capabilities.add("bsp.pwm")
        if any(pin.signal.startswith(("GPIO_", "GPXTI")) for pin in self.pins):
            capabilities.add("bsp.gpio")
        if self.freertos:
            capabilities.add("os.freertos")
        capabilities.add("platform.stm32")
        capabilities.add("platform.stm32cubemx")
        if self.family:
            capabilities.add(f"mcu.{self.family.lower()}")
        return tuple(sorted(capabilities))

    def peripherals_of(self, *kinds: str) -> tuple[Peripheral, ...]:
        wanted = {kind.upper() for kind in kinds}
        return tuple(item for item in self.peripherals if item.kind.upper() in wanted)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = list(self.capabilities)
        return data


@dataclass(frozen=True)
class PackageDependency:
    package_id: str
    version: str = "*"
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PackageFile:
    source: str
    destination: str
    policy: str = "generated"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PackageManifest:
    package_id: str
    name: str
    package_type: str
    version: str
    root: str
    description: str = ""
    dependencies: tuple[PackageDependency, ...] = ()
    requires: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()
    files: tuple[PackageFile, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChangeAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"
    SKIP = "skip"
    CONFLICT = "conflict"


@dataclass(frozen=True)
class FileChange:
    path: str
    action: ChangeAction
    policy: str
    reason: str
    content: str | bytes | None = field(default=None, repr=False)
    previous_hash: str | None = None
    next_hash: str | None = None
    package_id: str | None = None

    def to_dict(self, include_content: bool = False) -> dict[str, Any]:
        data = asdict(self)
        data.pop("content", None)
        if include_content:
            data["content"] = self.content.decode("utf-8", errors="replace") if isinstance(self.content, bytes) else self.content
        return data


@dataclass(frozen=True)
class GenerationPlan:
    project_root: str
    changes: tuple[FileChange, ...]
    packages: tuple[PackageManifest, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def has_conflicts(self) -> bool:
        return any(change.action == ChangeAction.CONFLICT for change in self.changes)

    @property
    def has_errors(self) -> bool:
        return self.has_conflicts or any(item.severity == Severity.ERROR for item in self.diagnostics)

    @property
    def changed_count(self) -> int:
        return sum(change.action in (ChangeAction.CREATE, ChangeAction.UPDATE, ChangeAction.DELETE) for change in self.changes)

    def to_dict(self) -> dict[str, Any]:
        counts = {action.value: 0 for action in ChangeAction}
        for change in self.changes:
            counts[change.action.value] += 1
        return {
            "project_root": self.project_root,
            "summary": counts,
            "has_errors": self.has_errors,
            "changes": [change.to_dict() for change in self.changes],
            "packages": [package.to_dict() for package in self.packages],
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


def relative_posix(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()
