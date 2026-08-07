from __future__ import annotations

import re
from pathlib import Path

from ..errors import ConfigurationError
from ..models import Peripheral, Pin, ProjectModel


_IP_KIND = re.compile(r"^(FDCAN|CAN|USART|UART|LPUART|I2C|SPI|TIM|ADC|DAC|USB|SDMMC|ETH|QUADSPI|OCTOSPI)(\d*)")
_PIN_NAME = re.compile(r"^P[A-Z][0-9]+$")
_MCU_IP_KEY = re.compile(r"^Mcu\.IP[0-9]+$")


def find_ioc_file(project_root: Path, configured: str | None = None) -> Path:
    root = project_root.resolve()
    if root.is_file():
        if root.suffix.lower() != ".ioc":
            raise ConfigurationError(f"不是 CubeMX .ioc 文件: {root}")
        return root
    if configured:
        candidate = (root / configured).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ConfigurationError("project.ioc 不能指向项目目录之外") from exc
        if not candidate.is_file():
            raise ConfigurationError(f"找不到 CubeMX 文件: {candidate}")
        return candidate
    candidates = sorted(root.glob("*.ioc"))
    if not candidates:
        raise ConfigurationError(f"项目根目录中没有 .ioc 文件: {root}")
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise ConfigurationError(f"存在多个 .ioc 文件，请在 mrobot.yaml 指定 project.ioc: {names}")
    return candidates[0]


class STM32CubeMXParser:
    """Parse a CubeMX project once into the front-end-neutral ProjectModel."""

    def __init__(self, ioc_path: str | Path):
        self.path = Path(ioc_path).resolve()
        self.entries = self._read_entries()

    def _read_entries(self) -> dict[str, str]:
        try:
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            raise ConfigurationError(f"无法读取 CubeMX 文件 {self.path}: {exc}") from exc
        entries: dict[str, str] = {}
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            entries[key.strip()] = value.strip()
        if not entries:
            raise ConfigurationError(f"CubeMX 文件没有有效配置: {self.path}")
        return entries

    @staticmethod
    def _kind(name: str) -> str:
        match = _IP_KIND.match(name.upper())
        return match.group(1) if match else name.upper().split("_", 1)[0]

    def _peripherals(self) -> tuple[Peripheral, ...]:
        names: set[str] = set()
        for key, value in self.entries.items():
            if _MCU_IP_KEY.match(key) and value and value not in {"FREERTOS", "NVIC", "RCC", "SYS"}:
                names.add(value.split(".", 1)[0])
        result: list[Peripheral] = []
        for name in sorted(names):
            attributes = {
                key[len(name) + 1 :]: value
                for key, value in self.entries.items()
                if key.startswith(name + ".")
            }
            result.append(Peripheral(name=name, kind=self._kind(name), attributes=attributes))
        return tuple(result)

    def _pins(self) -> tuple[Pin, ...]:
        grouped: dict[str, dict[str, str]] = {}
        for key, value in self.entries.items():
            if "." not in key:
                continue
            name, attribute = key.split(".", 1)
            if _PIN_NAME.match(name):
                grouped.setdefault(name, {})[attribute] = value
        return tuple(
            Pin(
                name=name,
                signal=attributes.get("Signal", ""),
                label=attributes.get("GPIO_Label", ""),
                attributes=attributes,
            )
            for name, attributes in sorted(grouped.items())
        )

    def parse(self, project_root: str | Path | None = None) -> ProjectModel:
        root = Path(project_root).resolve() if project_root else self.path.parent
        mcu = self.entries.get("Mcu.Name") or self.entries.get("Mcu.CPN") or self.entries.get("Mcu.UserName", "")
        family = self.entries.get("Mcu.Family", "")
        if not family and mcu.upper().startswith("STM32"):
            family_match = re.match(r"STM32([A-Z][0-9])", mcu.upper())
            family = f"STM32{family_match.group(1)}" if family_match else "STM32"
        series_match = re.match(r"(STM32[A-Z][0-9])", mcu.upper())
        series = series_match.group(1) if series_match else family.upper()
        freertos = any(
            (_MCU_IP_KEY.match(key) and value == "FREERTOS") or key.startswith("FREERTOS.")
            for key, value in self.entries.items()
        )
        metadata_keys = ("MxCube.Version", "ProjectManager.ProjectName", "ProjectManager.ToolChain", "Mcu.Package")
        metadata = {key: self.entries[key] for key in metadata_keys if key in self.entries}
        return ProjectModel(
            project_root=str(root),
            ioc_path=str(self.path),
            name=self.entries.get("ProjectManager.ProjectName") or self.path.stem,
            mcu=mcu,
            family=family,
            series=series,
            freertos=freertos,
            peripherals=self._peripherals(),
            pins=self._pins(),
            metadata=metadata,
        )
