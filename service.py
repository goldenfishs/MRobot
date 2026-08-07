from __future__ import annotations

from pathlib import Path

from .config import CONFIG_NAME, MCodeConfig, write_json_yaml
from .errors import MCodeError
from .models import Diagnostic, GenerationPlan, ProjectModel, Severity
from .packages import load_manifest, resolve_packages
from .planner import apply_plan, build_plan
from .stm32 import STM32CubeMXParser, find_ioc_file


class MCodeService:
    """Stable application API shared by every MCode front end."""

    def inspect(self, project: str | Path) -> ProjectModel:
        input_path = Path(project).resolve()
        root = input_path.parent if input_path.is_file() else input_path
        config = MCodeConfig.load(root)
        ioc = find_ioc_file(input_path, config.ioc if input_path.is_dir() else None)
        return STM32CubeMXParser(ioc).parse(root)

    def initialize(self, project: str | Path, force: bool = False) -> Path:
        root = Path(project).resolve()
        if not root.is_dir():
            raise MCodeError(f"项目目录不存在: {root}")
        target = root / CONFIG_NAME
        if target.exists() and not force:
            raise MCodeError(f"配置已存在，使用 --force 才能覆盖: {target}")
        ioc = find_ioc_file(root)
        config = MCodeConfig.defaults(root)
        write_json_yaml(target, config.template(ioc.name))
        return target

    def plan(self, project: str | Path) -> GenerationPlan:
        root = Path(project).resolve()
        if root.is_file():
            root = root.parent
        config = MCodeConfig.load(root)
        model = self.inspect(root)
        packages = resolve_packages(config, model)
        return build_plan(config, model, packages)

    def generate(self, project: str | Path) -> GenerationPlan:
        plan = self.plan(project)
        apply_plan(plan)
        return plan

    def validate(self, project: str | Path) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        try:
            model = self.inspect(project)
            if not model.mcu:
                diagnostics.append(Diagnostic("MCODE_STM32_001", "CubeMX 文件未声明 MCU 型号", Severity.WARNING, model.ioc_path))
            plan = self.plan(project)
            for change in plan.changes:
                if change.action.value == "conflict":
                    diagnostics.append(Diagnostic("MCODE_GEN_001", change.reason, Severity.ERROR, change.path, "恢复文件或显式迁移后再生成"))
        except MCodeError as exc:
            diagnostics.append(Diagnostic("MCODE_CONFIG_001", str(exc), Severity.ERROR))
        return tuple(diagnostics)

    def validate_package(self, package: str | Path) -> tuple[Diagnostic, ...]:
        try:
            load_manifest(package)
        except MCodeError as exc:
            return (Diagnostic("MCODE_PACKAGE_001", str(exc), Severity.ERROR, str(package)),)
        return ()
