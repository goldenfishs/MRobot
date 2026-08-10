from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPlainTextEdit,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    CheckBox,
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    ProgressRing,
    PushButton,
    SearchLineEdit,
    StrongBodyLabel,
    TableWidget,
    TitleLabel,
)

from mcode.config import CONFIG_NAME, MCodeConfig
from mcode.errors import MCodeError
from mcode.models import ChangeAction, GenerationPlan
from mcode.packages import version_key
from mcode.registry import RegistryEntry
from mcode.service import MCodeService


PACKAGE_TYPE_LABELS = {
    "platform": "平台",
    "board": "板卡",
    "bsp": "BSP",
    "device": "设备",
    "component": "组件",
    "algorithm": "算法",
    "module": "模块",
    "task": "任务",
}

PLATFORM_PACKAGES = {
    "stm32cubemx": "mrobot.platform.stm32",
    "esp-idf": "mrobot.platform.esp-idf",
    "wch-ch32": "mrobot.platform.wch-ch32",
    "hpm-sdk": "mrobot.platform.hpm-sdk",
    "ti-mspm0": "mrobot.platform.ti-mspm0",
}


def package_type(package_id: str) -> str:
    parts = package_id.split(".")
    return parts[1] if len(parts) > 2 else "component"


def latest_registry_entries(entries: tuple[RegistryEntry, ...]) -> tuple[RegistryEntry, ...]:
    latest: dict[str, RegistryEntry] = {}
    for entry in entries:
        previous = latest.get(entry.package_id)
        if previous is None or version_key(entry.version) > version_key(previous.version):
            latest[entry.package_id] = entry
    return tuple(sorted(latest.values(), key=lambda item: (package_type(item.package_id), item.package_id)))


def describe_plan(plan: GenerationPlan) -> tuple[str, str]:
    counts = {action: 0 for action in ChangeAction}
    lines: list[str] = []
    labels = {
        ChangeAction.CREATE: "新增",
        ChangeAction.UPDATE: "更新",
        ChangeAction.DELETE: "删除",
        ChangeAction.NOOP: "不变",
        ChangeAction.SKIP: "保留",
        ChangeAction.CONFLICT: "冲突",
    }
    for change in plan.changes:
        counts[change.action] += 1
        lines.append(f"[{labels[change.action]}] {change.path}\n    {change.reason}")
    summary = (
        f"{len(plan.packages)} 个包 · "
        f"新增 {counts[ChangeAction.CREATE]} · "
        f"更新 {counts[ChangeAction.UPDATE]} · "
        f"删除 {counts[ChangeAction.DELETE]} · "
        f"冲突 {counts[ChangeAction.CONFLICT]}"
    )
    return summary, "\n".join(lines) or "没有文件变更。"


class RegistryLoadThread(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, project_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_path = project_path

    def run(self) -> None:
        try:
            service = MCodeService()
            root = Path(self.project_path)
            self.completed.emit(latest_registry_entries(service.search_packages(root)))
        except (MCodeError, OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))


class PreparePlanThread(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        project_path: str,
        selected_ids: set[str],
        managed_ids: set[str],
        adopt_legacy: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.project_path = project_path
        self.selected_ids = selected_ids
        self.managed_ids = managed_ids
        self.adopt_legacy = adopt_legacy

    def run(self) -> None:
        try:
            root = Path(self.project_path)
            service = MCodeService()
            if not (root / CONFIG_NAME).exists():
                service.initialize(root)
            config = MCodeConfig.load(root)
            current_ids = {
                item.package_id
                for item in config.packages
                if item.enabled and item.package_id
            }
            for package_id in sorted(self.selected_ids - current_ids):
                service.install_package(root, package_id)
            for package_id in sorted((current_ids & self.managed_ids) - self.selected_ids):
                service.remove_package(root, package_id)
            self.completed.emit(service.plan(root, adopt_legacy=self.adopt_legacy))
        except (MCodeError, OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))


class GenerateThread(QThread):
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, project_path: str, adopt_legacy: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.project_path = project_path
        self.adopt_legacy = adopt_legacy

    def run(self) -> None:
        try:
            plan = MCodeService().generate(self.project_path, adopt_legacy=self.adopt_legacy)
            self.completed.emit(plan)
        except (MCodeError, OSError, ValueError, RuntimeError) as exc:
            self.failed.emit(str(exc))


class GenerationPlanDialog(QDialog):
    def __init__(self, plan: GenerationPlan, allow_generate: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MCode 生成计划")
        self.setMinimumSize(720, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(12)
        title = TitleLabel("生成计划", self)
        root.addWidget(title)
        summary, detail = describe_plan(plan)
        summary_label = StrongBodyLabel(summary, self)
        root.addWidget(summary_label)
        hint = BodyLabel(
            "请先确认文件范围。冲突不会被覆盖，scaffold 文件仍归用户所有。",
            self,
        )
        hint.setWordWrap(True)
        root.addWidget(hint)
        details = QPlainTextEdit(self)
        details.setReadOnly(True)
        details.setPlainText(detail)
        root.addWidget(details, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        close_button = PushButton("关闭", self)
        close_button.clicked.connect(self.reject)
        buttons.addWidget(close_button)
        if allow_generate:
            generate_button = PrimaryPushButton(FluentIcon.PLAY, "确认生成", self)
            generate_button.clicked.connect(self.accept)
            buttons.addWidget(generate_button)
        root.addLayout(buttons)


class CodeGenerateInterface(QWidget):
    """Thin desktop frontend for MCode registry, plan and generation APIs."""

    def __init__(self, project_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CodeGenerateInterface")
        self.project_path = str(Path(project_path).resolve())
        self.mcode = MCodeService()
        self.project_model = None
        self.catalog_entries: tuple[RegistryEntry, ...] = ()
        self._registry_thread: RegistryLoadThread | None = None
        self._plan_thread: PreparePlanThread | None = None
        self._generate_thread: GenerateThread | None = None
        self._pending_generate = False
        self._populating = False
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        project_card = CardWidget(self)
        project_layout = QHBoxLayout(project_card)
        project_layout.setContentsMargins(20, 16, 16, 16)
        project_layout.setSpacing(12)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title_label = TitleLabel("MCode 代码生成", project_card)
        self.project_label = BodyLabel("正在解析工程…", project_card)
        self.project_meta = CaptionLabel("", project_card)
        text.addWidget(self.title_label)
        text.addWidget(self.project_label)
        text.addWidget(self.project_meta)
        project_layout.addLayout(text, 1)
        self.project_progress = ProgressRing(project_card)
        self.project_progress.setFixedSize(22, 22)
        self.project_progress.hide()
        project_layout.addWidget(self.project_progress)
        refresh_button = PushButton(FluentIcon.SYNC, "刷新", project_card)
        refresh_button.clicked.connect(self.refresh)
        project_layout.addWidget(refresh_button)
        self.validate_button = PushButton(FluentIcon.ACCEPT, "校验工程", project_card)
        self.validate_button.clicked.connect(self.validate_project)
        project_layout.addWidget(self.validate_button)
        root.addWidget(project_card)

        filters = CardWidget(self)
        filter_layout = QHBoxLayout(filters)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(10)
        self.search_edit = SearchLineEdit(filters)
        self.search_edit.setPlaceholderText("搜索包名、说明或能力")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_edit, 1)
        self.type_combo = ComboBox(filters)
        self.type_combo.addItem("全部类型", userData="all")
        for key, label in PACKAGE_TYPE_LABELS.items():
            self.type_combo.addItem(label, userData=key)
        self.type_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.type_combo)
        self.selection_label = CaptionLabel("0 个已选择", filters)
        self.selection_label.setMinimumWidth(90)
        self.selection_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        filter_layout.addWidget(self.selection_label)
        root.addWidget(filters)

        self.package_table = TableWidget(self)
        self.package_table.setColumnCount(4)
        self.package_table.setHorizontalHeaderLabels(["包", "版本", "类型", "说明"])
        self.package_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.package_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.package_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.package_table.verticalHeader().hide()
        header = self.package_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.package_table.itemChanged.connect(self._selection_changed)
        root.addWidget(self.package_table, 1)

        action_card = CardWidget(self)
        action_layout = QHBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(12)
        self.status_label = BodyLabel("正在加载官方包索引…", action_card)
        action_layout.addWidget(self.status_label, 1)
        self.adopt_checkbox = CheckBox("迁移旧 USER 区域", action_card)
        self.adopt_checkbox.setToolTip("仅接管同时含有可识别 USER BEGIN/END 标记的旧文件")
        action_layout.addWidget(self.adopt_checkbox)
        self.preview_button = PushButton(FluentIcon.VIEW, "应用并预览", action_card)
        self.preview_button.clicked.connect(lambda: self.prepare_plan(False))
        self.preview_button.setEnabled(False)
        action_layout.addWidget(self.preview_button)
        self.generate_button = PrimaryPushButton(FluentIcon.PLAY, "预览后生成", action_card)
        self.generate_button.clicked.connect(lambda: self.prepare_plan(True))
        self.generate_button.setEnabled(False)
        action_layout.addWidget(self.generate_button)
        root.addWidget(action_card)

    def refresh(self) -> None:
        try:
            self.project_model = self.mcode.inspect(self.project_path)
            model = self.project_model
            self.project_label.setText(Path(self.project_path).name)
            self.project_meta.setText(
                f"{model.platform} · {model.mcu or 'MCU 未识别'} · "
                f"FreeRTOS {'已启用' if model.freertos else '未启用'} · "
                f"{len(model.peripherals)} 个外设"
            )
        except MCodeError as exc:
            self.project_label.setText(Path(self.project_path).name)
            self.project_meta.setText(f"工程解析失败：{exc}")
        self.load_registry()

    def load_registry(self) -> None:
        if self._registry_thread and self._registry_thread.isRunning():
            return
        self._set_busy(True, "正在同步官方包索引…")
        self._registry_thread = RegistryLoadThread(self.project_path, self)
        self._registry_thread.completed.connect(self._registry_loaded)
        self._registry_thread.failed.connect(self._operation_failed)
        self._registry_thread.finished.connect(lambda: self._set_busy(False))
        self._registry_thread.start()

    def _registry_loaded(self, value: object) -> None:
        self.catalog_entries = tuple(value)  # type: ignore[arg-type]
        self._populate_table()
        self.status_label.setText(f"官方索引已连接，共 {len(self.catalog_entries)} 个包")

    def _populate_table(self) -> None:
        config = MCodeConfig.load(Path(self.project_path))
        selected = {
            item.package_id
            for item in config.packages
            if item.enabled and item.package_id
        }
        required = PLATFORM_PACKAGES.get(config.platform)
        if required:
            selected.add(required)
        self._populating = True
        self.package_table.setRowCount(len(self.catalog_entries))
        for row, entry in enumerate(self.catalog_entries):
            item = QTableWidgetItem(entry.package_id)
            item.setData(Qt.UserRole, entry.package_id)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if entry.package_id in selected else Qt.Unchecked)
            if entry.package_id == required:
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                item.setToolTip("当前工程平台的必选包")
            self.package_table.setItem(row, 0, item)
            self.package_table.setItem(row, 1, QTableWidgetItem(entry.version))
            type_name = PACKAGE_TYPE_LABELS.get(package_type(entry.package_id), package_type(entry.package_id))
            self.package_table.setItem(row, 2, QTableWidgetItem(type_name))
            description = entry.description or "暂无说明"
            if entry.provides:
                description += " · " + ", ".join(entry.provides)
            self.package_table.setItem(row, 3, QTableWidgetItem(description))
        self._populating = False
        self._selection_changed()
        self._apply_filters()
        self.preview_button.setEnabled(bool(self.catalog_entries))
        self.generate_button.setEnabled(bool(self.catalog_entries))

    def _apply_filters(self) -> None:
        query = self.search_edit.text().strip().lower()
        selected_type = self.type_combo.currentData() or "all"
        for row, entry in enumerate(self.catalog_entries):
            haystack = " ".join((entry.package_id, entry.description, *entry.provides)).lower()
            visible = (not query or query in haystack) and (
                selected_type == "all" or package_type(entry.package_id) == selected_type
            )
            self.package_table.setRowHidden(row, not visible)

    def _selection_changed(self, *_args) -> None:
        if self._populating:
            return
        self.selection_label.setText(f"{len(self._selected_ids())} 个已选择")

    def _selected_ids(self) -> set[str]:
        selected: set[str] = set()
        for row in range(self.package_table.rowCount()):
            item = self.package_table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                selected.add(str(item.data(Qt.UserRole)))
        return selected

    def prepare_plan(self, generate_after: bool) -> None:
        if self._plan_thread and self._plan_thread.isRunning():
            return
        self._pending_generate = generate_after
        self._set_busy(True, "正在安装所选包并计算生成计划…")
        self._plan_thread = PreparePlanThread(
            self.project_path,
            self._selected_ids(),
            {entry.package_id for entry in self.catalog_entries},
            self.adopt_checkbox.isChecked(),
            self,
        )
        self._plan_thread.completed.connect(self._plan_prepared)
        self._plan_thread.failed.connect(self._operation_failed)
        self._plan_thread.finished.connect(lambda: self._set_busy(False))
        self._plan_thread.start()

    def _plan_prepared(self, value: object) -> None:
        plan: GenerationPlan = value  # type: ignore[assignment]
        allow_generate = self._pending_generate and not plan.has_errors
        dialog = GenerationPlanDialog(plan, allow_generate, self)
        if plan.has_errors:
            self.status_label.setText("计划包含冲突，请查看详情后修复")
            dialog.exec()
            return
        self.status_label.setText("包配置已保存，生成计划可执行")
        if dialog.exec() and allow_generate:
            self._run_generate()

    def _run_generate(self) -> None:
        if self._generate_thread and self._generate_thread.isRunning():
            return
        self._set_busy(True, "正在原子写入生成文件…")
        self._generate_thread = GenerateThread(
            self.project_path,
            self.adopt_checkbox.isChecked(),
            self,
        )
        self._generate_thread.completed.connect(self._generation_completed)
        self._generate_thread.failed.connect(self._operation_failed)
        self._generate_thread.finished.connect(lambda: self._set_busy(False))
        self._generate_thread.start()

    def _generation_completed(self, value: object) -> None:
        plan: GenerationPlan = value  # type: ignore[assignment]
        self.status_label.setText(f"生成完成：{plan.changed_count} 个文件发生变化")
        InfoBar.success(
            title="MCode 生成完成",
            content=f"已解析 {len(plan.packages)} 个包，写入 {plan.changed_count} 个文件。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=5000,
        )

    def validate_project(self) -> None:
        diagnostics = self.mcode.validate(self.project_path)
        errors = [item for item in diagnostics if item.severity.value == "error"]
        warnings = [item for item in diagnostics if item.severity.value == "warning"]
        if errors:
            InfoBar.error(
                title="工程校验失败",
                content="；".join(item.message for item in errors),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=6000,
            )
            return
        InfoBar.success(
            title="工程校验通过",
            content=f"没有错误，{len(warnings)} 条警告。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=3000,
        )

    def _operation_failed(self, message: str) -> None:
        self.status_label.setText("操作失败")
        InfoBar.error(
            title="MCode 操作失败",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=7000,
        )

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        self.project_progress.setVisible(busy)
        self.preview_button.setEnabled(not busy and bool(self.catalog_entries))
        self.generate_button.setEnabled(not busy and bool(self.catalog_entries))
        self.validate_button.setEnabled(not busy)
        if message:
            self.status_label.setText(message)
