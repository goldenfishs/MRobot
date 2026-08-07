from __future__ import annotations

import json
from pathlib import Path


def write_ioc(root: Path, name: str = "demo.ioc", ips: tuple[str, ...] = ("SPI1", "FREERTOS")) -> Path:
    lines = [
        "#MicroXplorer Configuration settings - do not modify",
        "Mcu.Name=STM32F407IGHx",
        "Mcu.Family=STM32F4",
        "ProjectManager.ProjectName=demo",
        f"Mcu.IPNb={len(ips)}",
    ]
    lines.extend(f"Mcu.IP{index}={value}" for index, value in enumerate(ips))
    lines.extend([
        "PA4.GPIO_Label=IMU_CS",
        "PA4.Signal=GPIO_Output",
        "PC4.GPIO_Label=IMU_INT",
        "PC4.GPIO_ModeDefaultEXTI=GPIO_MODE_IT_FALLING",
        "PC4.Signal=GPXTI4",
        "PE9.GPIO_Label=MOTOR_PWM",
        "PE9.Signal=S_TIM1_CH1",
        "TIM1.Channel-PWM\\ Generation1\\ CH1=TIM_CHANNEL_1",
    ])
    path = root / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_config(root: Path, packages: list[str] | None = None) -> Path:
    value = {
        "schema_version": 1,
        "project": {"ioc": "demo.ioc", "platform": "stm32cubemx"},
        "output": {"generated_root": "User/MRobot/generated"},
        "package_roots": ["packages"],
        "packages": packages or [],
    }
    path = root / "mrobot.yaml"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def write_package(
    root: Path,
    package_id: str,
    package_type: str = "device",
    dependencies: list[str | dict] | None = None,
    requires: list[str] | None = None,
    provides: list[str] | None = None,
    files: list[dict] | None = None,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    value = {
        "schema_version": 1,
        "package": {"id": package_id, "name": package_id, "type": package_type, "version": "0.1.0"},
        "dependencies": dependencies or [],
        "requires": requires or [],
        "provides": provides or [],
        "files": files or [],
    }
    (root / "mrobot-package.yaml").write_text(json.dumps(value), encoding="utf-8")
    return root
