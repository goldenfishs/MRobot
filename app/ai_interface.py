from __future__ import annotations

import html
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

import markdown as markdown_renderer
from PyQt5.QtCore import QEvent, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    ComboBox,
    DoubleSpinBox,
    FluentIcon,
    LineEdit,
    PasswordLineEdit,
    PrimaryPushButton,
    PrimaryToolButton,
    PushButton,
    SearchLineEdit,
    SimpleCardWidget,
    SpinBox,
    StrongBodyLabel,
    SubtitleLabel,
    SwitchButton,
    ToolButton,
    TransparentPushButton,
    TransparentToolButton,
    isDarkTheme,
    qconfig,
)

from .ai import (
    AICancelled,
    AIClientError,
    AIConversationStore,
    AIProfileStore,
    AIProviderConfig,
    Conversation,
    MRobotAssistant,
    MRobotToolRegistry,
    OpenAICompatibleClient,
    PROVIDER_PRESETS,
)
from .home_interface import resource_path


ACCENT = "#ff4f91"


def render_assistant_markdown(value: str, *, streaming: bool = False) -> str:
    """Render model output as safe, styled Markdown for Qt rich-text labels."""
    dark = isDarkTheme()
    text = "#f3f4f6" if dark else "#24262b"
    muted = "#b4b8c1" if dark else "#626873"
    code_background = "#27292e" if dark else "#f5f6f8"
    code_border = "#3c3f45" if dark else "#e1e4e8"
    quote_border = "#ff73a8" if dark else "#ff8fba"

    stylesheet = f"""
        body {{ color: {text}; font-size: 14px; }}
        p {{ margin: 0 0 9px 0; }}
        h1 {{ font-size: 22px; font-weight: 700; margin: 13px 0 8px 0; }}
        h2 {{ font-size: 18px; font-weight: 700; margin: 12px 0 7px 0; }}
        h3 {{ font-size: 16px; font-weight: 650; margin: 11px 0 6px 0; }}
        h4, h5, h6 {{ font-size: 15px; font-weight: 650; margin: 10px 0 6px 0; }}
        ul, ol {{ margin: 3px 0 10px 0; }}
        li {{ margin: 2px 0; }}
        a {{ color: {ACCENT}; text-decoration: none; }}
        blockquote {{ color: {muted}; border-left: 3px solid {quote_border}; margin: 8px 0; padding-left: 10px; }}
        code {{ background-color: {code_background}; font-family: Menlo, Monaco, monospace; }}
        pre {{ background-color: {code_background}; border: 1px solid {code_border};
               font-family: Menlo, Monaco, monospace; margin: 8px 0 10px 0;
               padding: 10px; white-space: pre-wrap; }}
        table {{ border-collapse: collapse; margin: 8px 0 10px 0; }}
        th, td {{ border: 1px solid {code_border}; padding: 6px 10px; }}
        th {{ background-color: {code_background}; font-weight: 650; }}
        hr {{ color: {code_border}; }}
        """
    # Escape raw HTML from model output before parsing. Markdown constructs
    # remain intact, while arbitrary tags cannot enter Qt's rich-text engine.
    body = markdown_renderer.markdown(
        html.escape(value),
        extensions=("extra", "sane_lists", "nl2br"),
        output_format="html5",
    )
    if streaming:
        body += f'<span style="color:{ACCENT};">&nbsp;▍</span>'
    return f"<html><head><style>{stylesheet}</style></head><body>{body}</body></html>"


class BrandLogoLabel(QLabel):
    """Render the existing MRobot mark without a synthetic text badge."""

    def __init__(self, width: int, height: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("brandLogo")
        pixmap = QPixmap(resource_path("assets/logo/M.png"))
        self.setPixmap(pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignCenter)


class AIWorker(QThread):
    chunk_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    completed = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(
        self,
        config: AIProviderConfig,
        api_key: str,
        messages: list[dict[str, Any]],
        project_root: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.api_key = api_key
        self.messages = messages
        self.project_root = project_root
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        try:
            client = OpenAICompatibleClient(self.config, api_key=self.api_key)
            assistant = MRobotAssistant(client, MRobotToolRegistry(self.project_root or None))
            result = assistant.run(
                self.messages,
                on_text=self.chunk_received.emit,
                on_status=self.status_changed.emit,
                cancelled=lambda: self._cancel_requested,
            )
            self.completed.emit(result)
        except AICancelled:
            self.cancelled.emit()
        except (AIClientError, ValueError, OSError, RuntimeError) as exc:
            self.failed.emit(str(exc))


class ConnectionTestWorker(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, config: AIProviderConfig, api_key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.api_key = api_key

    def run(self) -> None:
        try:
            models = OpenAICompatibleClient(self.config, api_key=self.api_key).list_models()
            self.succeeded.emit(models)
        except (AIClientError, ValueError, OSError, RuntimeError) as exc:
            self.failed.emit(str(exc))


class AISettingsDialog(QDialog):
    """Compact, grouped provider editor with an asynchronous connection test."""

    def __init__(self, config: AIProviderConfig, session_key: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aiSettingsDialog")
        self.setWindowTitle("模型连接")
        self.setMinimumSize(700, 640)
        self.resize(720, 680)
        self.test_worker: ConnectionTestWorker | None = None
        self._build_ui(config, session_key)
        self._apply_style()
        qconfig.themeChangedFinished.connect(self._schedule_theme_refresh)

    def _build_ui(self, config: AIProviderConfig, session_key: str) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        heading_row = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        heading.addWidget(SubtitleLabel("模型连接", self))
        description = CaptionLabel("连接 OpenAI、DeepSeek、Ollama 或任意兼容服务", self)
        description.setObjectName("mutedText")
        heading.addWidget(description)
        heading_row.addLayout(heading)
        heading_row.addStretch()
        protocol_badge = QLabel("密钥仅保存在本次运行", self)
        protocol_badge.setObjectName("safeBadge")
        heading_row.addWidget(protocol_badge)
        root.addLayout(heading_row)

        connection_card = SimpleCardWidget(self)
        connection_card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(connection_card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(14)
        card_layout.addWidget(StrongBodyLabel("连接信息", connection_card))

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)
        self.preset_combo = ComboBox(connection_card)
        self.preset_combo.addItem("保留当前参数", userData="")
        for preset_id, value in PROVIDER_PRESETS.items():
            self.preset_combo.addItem(str(value["label"]), userData=preset_id)
        self.name_edit = LineEdit(connection_card)
        self.name_edit.setText(config.name)
        self.name_edit.setPlaceholderText("例如：Lumivia")
        self.base_url_edit = LineEdit(connection_card)
        self.base_url_edit.setText(config.base_url)
        self.base_url_edit.setPlaceholderText("https://api.example.com/v1")
        self.model_edit = LineEdit(connection_card)
        self.model_edit.setText(config.model)
        self.model_edit.setPlaceholderText("模型 ID")
        self.protocol_combo = ComboBox(connection_card)
        self.protocol_combo.addItem("自动检测（推荐）", userData="auto")
        self.protocol_combo.addItem("OpenAI Responses", userData="responses")
        self.protocol_combo.addItem("Chat Completions", userData="chat")
        protocol_index = max(0, ["auto", "responses", "chat"].index(config.protocol) if config.protocol in {"auto", "responses", "chat"} else 0)
        self.protocol_combo.setCurrentIndex(protocol_index)
        self.key_edit = PasswordLineEdit(connection_card)
        self.key_edit.setText(session_key)
        self.key_edit.setPlaceholderText("留空时读取环境变量")
        self.key_env_edit = LineEdit(connection_card)
        self.key_env_edit.setText(config.api_key_env)
        self.key_env_edit.setPlaceholderText("OPENAI_API_KEY")

        self._add_field(grid, 0, 0, "服务预设", self.preset_combo)
        self._add_field(grid, 0, 1, "配置名称", self.name_edit)
        self._add_field(grid, 1, 0, "Base URL", self.base_url_edit, column_span=2)
        self._add_field(grid, 2, 0, "接口协议", self.protocol_combo)
        self._add_field(grid, 2, 1, "模型 ID", self.model_edit)
        self._add_field(grid, 3, 0, "API Key（本次运行）", self.key_edit)
        self._add_field(grid, 3, 1, "密钥环境变量", self.key_env_edit)
        card_layout.addLayout(grid)
        root.addWidget(connection_card)

        permission_card = SimpleCardWidget(self)
        permission_card.setObjectName("settingsCard")
        permission_layout = QHBoxLayout(permission_card)
        permission_layout.setContentsMargins(20, 15, 20, 15)
        permission_text = QVBoxLayout()
        permission_text.setSpacing(2)
        permission_text.addWidget(StrongBodyLabel("工程只读工具", permission_card))
        permission_caption = CaptionLabel("允许模型检查 CubeMX 配置、生成计划和源码；不会自动改文件或烧录", permission_card)
        permission_caption.setObjectName("mutedText")
        permission_caption.setWordWrap(True)
        permission_text.addWidget(permission_caption)
        permission_layout.addLayout(permission_text, 1)
        self.tools_switch = SwitchButton(permission_card)
        self.tools_switch.setOnText("已开启")
        self.tools_switch.setOffText("已关闭")
        self.tools_switch.setChecked(config.enable_tools)
        permission_layout.addWidget(self.tools_switch)
        root.addWidget(permission_card)

        self.advanced_button = PushButton(FluentIcon.CHEVRON_RIGHT, "高级设置", self)
        self.advanced_button.setCheckable(True)
        root.addWidget(self.advanced_button, 0, Qt.AlignLeft)
        self.advanced_card = SimpleCardWidget(self)
        self.advanced_card.setObjectName("settingsCard")
        advanced_layout = QGridLayout(self.advanced_card)
        advanced_layout.setContentsMargins(20, 16, 20, 18)
        advanced_layout.setHorizontalSpacing(14)
        self.temperature_spin = DoubleSpinBox(self.advanced_card)
        self.temperature_spin.setRange(0, 2)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(config.temperature)
        self.timeout_spin = SpinBox(self.advanced_card)
        self.timeout_spin.setRange(15, 600)
        self.timeout_spin.setValue(config.timeout)
        self._add_field(advanced_layout, 0, 0, "Temperature（Chat 接口）", self.temperature_spin)
        self._add_field(advanced_layout, 0, 1, "请求超时（秒）", self.timeout_spin)
        self.advanced_card.hide()
        root.addWidget(self.advanced_card)

        self.test_status = CaptionLabel("自动模式会优先尝试 Responses，再兼容 Chat Completions 和普通 JSON 返回。", self)
        self.test_status.setObjectName("mutedText")
        self.test_status.setWordWrap(True)
        root.addWidget(self.test_status)
        root.addStretch()

        actions = QHBoxLayout()
        self.test_button = PushButton(FluentIcon.SYNC, "测试连接", self)
        actions.addWidget(self.test_button)
        actions.addStretch()
        self.cancel_button = PushButton("取消", self)
        self.save_button = PrimaryPushButton("保存连接", self)
        actions.addWidget(self.cancel_button)
        actions.addWidget(self.save_button)
        root.addLayout(actions)

        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        self.advanced_button.toggled.connect(self._toggle_advanced)
        self.test_button.clicked.connect(self._test_connection)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._accept_if_valid)

    def _add_field(self, layout: QGridLayout, row: int, column: int, text: str, widget: QWidget, column_span: int = 1) -> None:
        container = QWidget(self)
        field_layout = QVBoxLayout(container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(5)
        label = CaptionLabel(text, container)
        label.setObjectName("fieldLabel")
        field_layout.addWidget(label)
        field_layout.addWidget(widget)
        layout.addWidget(container, row, column, 1, column_span)

    def _apply_style(self) -> None:
        dark = isDarkTheme()
        background = "#202124" if dark else "#f7f8fa"
        card = "#2b2d31" if dark else "#ffffff"
        border = "#3b3d43" if dark else "#e6e8ed"
        muted = "#a9adb7" if dark else "#717681"
        self.setStyleSheet(
            f"""
            QDialog#aiSettingsDialog {{ background: {background}; }}
            #settingsCard {{ background: {card}; border: 1px solid {border}; border-radius: 12px; }}
            #mutedText, #fieldLabel {{ color: {muted}; }}
            #safeBadge {{ color: #b83268; background: rgba(255,79,145,0.12); border-radius: 10px; padding: 5px 10px; }}
            """
        )
    def _schedule_theme_refresh(self, *_args: object) -> None:
        QTimer.singleShot(0, self._apply_style)

    def _toggle_advanced(self, checked: bool) -> None:
        self.advanced_card.setVisible(checked)
        self.advanced_button.setText("收起高级设置" if checked else "高级设置")
        self.adjustSize()

    def _apply_preset(self, *_args: object) -> None:
        preset_id = str(self.preset_combo.currentData() or "")
        if not preset_id:
            return
        config = AIProviderConfig.from_preset(preset_id)
        self.name_edit.setText(config.name)
        self.base_url_edit.setText(config.base_url)
        self.model_edit.setText(config.model)
        self.key_env_edit.setText(config.api_key_env)
        self.protocol_combo.setCurrentIndex(0)

    def config(self) -> AIProviderConfig:
        return AIProviderConfig(
            name=self.name_edit.text().strip(),
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            api_key_env=self.key_env_edit.text().strip(),
            protocol=str(self.protocol_combo.currentData() or "auto"),
            temperature=self.temperature_spin.value(),
            timeout=self.timeout_spin.value(),
            enable_tools=self.tools_switch.isChecked(),
        )

    def session_key(self) -> str:
        return self.key_edit.text().strip()

    def _validate(self) -> AIProviderConfig:
        config = self.config()
        if not config.name:
            raise AIClientError("请输入配置名称")
        if not config.model:
            raise AIClientError("请输入模型 ID")
        OpenAICompatibleClient(config, api_key=self.session_key())
        return config

    def _set_test_state(self, text: str, *, error: bool = False, success: bool = False) -> None:
        color = "#d53f58" if error else "#23895d" if success else "#717681"
        self.test_status.setStyleSheet(f"color: {color};")
        self.test_status.setText(text)

    def _accept_if_valid(self) -> None:
        try:
            self._validate()
        except AIClientError as exc:
            self._set_test_state(str(exc), error=True)
            return
        self.accept()

    def _test_connection(self) -> None:
        if self.test_worker and self.test_worker.isRunning():
            return
        try:
            config = self._validate()
        except AIClientError as exc:
            self._set_test_state(str(exc), error=True)
            return
        self.test_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self._set_test_state("正在检查服务和模型列表……")
        self.test_worker = ConnectionTestWorker(config, self.session_key(), self)
        self.test_worker.succeeded.connect(self._test_succeeded)
        self.test_worker.failed.connect(self._test_failed)
        self.test_worker.finished.connect(lambda: self.test_button.setEnabled(True))
        self.test_worker.finished.connect(lambda: self.save_button.setEnabled(True))
        self.test_worker.start()

    def _test_succeeded(self, models: object) -> None:
        values = tuple(models) if isinstance(models, (tuple, list)) else ()
        suffix = f"，服务返回 {len(values)} 个模型" if values else "，服务未提供模型目录但连接正常"
        self._set_test_state(f"连接成功{suffix}。实际对话时会自动确认生成协议。", success=True)

    def _test_failed(self, message: str) -> None:
        self._set_test_state(message, error=True)

    def reject(self) -> None:
        if self.test_worker and self.test_worker.isRunning():
            self._set_test_state("正在测试连接，请稍候……")
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if self.test_worker and self.test_worker.isRunning():
            self._set_test_state("正在测试连接，请稍候……")
            event.ignore()
            return
        super().closeEvent(event)


class ChatMessageWidget(QWidget):
    def __init__(self, role: str, text: str, parent: QWidget | None = None, *, streaming: bool = False) -> None:
        super().__init__(parent)
        self.role = role
        self.setObjectName("chatMessage")
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 7, 0, 7)
        root.setSpacing(10)
        if role == "user":
            root.addStretch(1)
            self.card = QFrame(self)
            self.card.setObjectName("userBubble")
            self.card.setMaximumWidth(680)
            card_layout = QVBoxLayout(self.card)
            card_layout.setContentsMargins(14, 10, 14, 10)
            self.content = QLabel(self.card)
            self.content.setObjectName("messageText")
            self.content.setWordWrap(True)
            self.content.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
            card_layout.addWidget(self.content)
            root.addWidget(self.card, 0, Qt.AlignTop)
        else:
            body = QVBoxLayout()
            body.setSpacing(0)
            self.content = QLabel(self)
            self.content.setObjectName("messageText")
            self.content.setWordWrap(True)
            self.content.setMaximumWidth(820)
            self.content.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
            self.content.setOpenExternalLinks(True)
            body.addWidget(self.content)
            root.addLayout(body, 1)
        self.set_text(text, streaming=streaming)

    def set_text(self, value: str, *, streaming: bool = False) -> None:
        self.raw_text = value
        self.streaming = streaming
        if self.role == "user":
            longest_line = max((len(line) for line in value.splitlines()), default=0)
            self.card.setFixedWidth(min(600, max(150, longest_line * 14 + 32)))
            formatted = html.escape(value).replace("\n", "<br>")
            if streaming:
                formatted += f'<span style="color:{ACCENT};">&nbsp;▍</span>'
        else:
            formatted = render_assistant_markdown(value, streaming=streaming)
        self.content.setText(formatted)

    def refresh_theme(self) -> None:
        self.set_text(self.raw_text, streaming=self.streaming)


class AIInterface(QWidget):
    """Focused, project-aware AI workspace backed by the shared app.ai core."""

    suggestion_prompts = (
        ("检查 CubeMX 工程", "读取当前工程配置，告诉我 MCU、工具链和潜在问题。"),
        ("规划代码生成", "根据当前工程给出安全的代码生成计划，不修改任何文件。"),
        ("分析驱动源码", "列出当前工程的关键驱动文件，并解释它们之间的关系。"),
        ("定位编译问题", "请根据工程信息给出一套从配置到构建的排查步骤。"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aiPage")
        self.profile_store = AIProfileStore()
        self.conversation_store = AIConversationStore()
        self.active_profile, self.profiles = self.profile_store.load()
        self.session_keys: dict[str, str] = {}
        self.conversations = self.conversation_store.load()
        self.current: Conversation | None = None
        self.worker: AIWorker | None = None
        self.streaming_text = ""
        self.streaming_widget: ChatMessageWidget | None = None
        self.last_error = ""
        self._build_ui()
        self._apply_style()
        qconfig.themeChangedFinished.connect(self._schedule_theme_refresh)
        self._reload_profiles()
        self._reload_conversations(select_first=True)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame(self)
        self.sidebar.setObjectName("aiSidebar")
        self.sidebar.setFixedWidth(218)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(14, 18, 14, 14)
        side.setSpacing(10)
        brand_row = QHBoxLayout()
        brand_mark = BrandLogoLabel(30, 24, self.sidebar)
        brand_row.addWidget(brand_mark)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        brand_text.addWidget(StrongBodyLabel("MRobot AI", self.sidebar))
        brand_caption = CaptionLabel("嵌入式开发助手 · Beta", self.sidebar)
        brand_caption.setObjectName("mutedText")
        brand_text.addWidget(brand_caption)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        side.addLayout(brand_row)

        self.new_button = TransparentPushButton("＋  新建对话", self.sidebar)
        self.new_button.setObjectName("newChatButton")
        self.new_button.setFixedHeight(36)
        side.addWidget(self.new_button)
        self.search_edit = SearchLineEdit(self.sidebar)
        self.search_edit.setPlaceholderText("搜索对话")
        self.search_edit.setFixedHeight(34)
        side.addWidget(self.search_edit)

        recent_label = CaptionLabel("对话", self.sidebar)
        recent_label.setObjectName("sectionLabel")
        side.addWidget(recent_label)
        self.conversation_list = QListWidget(self.sidebar)
        self.conversation_list.setObjectName("conversationList")
        self.conversation_list.setFrameShape(QFrame.NoFrame)
        self.conversation_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.conversation_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.conversation_list.setContextMenuPolicy(Qt.CustomContextMenu)
        side.addWidget(self.conversation_list, 1)

        self.edit_profile_button = TransparentPushButton("⚙  模型设置", self.sidebar)
        self.edit_profile_button.setObjectName("sideSettingsButton")
        side.addWidget(self.edit_profile_button)
        root.addWidget(self.sidebar)

        self.workspace = QFrame(self)
        self.workspace.setObjectName("aiWorkspace")
        self.workspace_layout = QVBoxLayout(self.workspace)
        self.workspace_layout.setContentsMargins(0, 0, 0, 12)
        self.workspace_layout.setSpacing(0)

        self.header = QFrame(self.workspace)
        self.header.setObjectName("aiHeader")
        self.header.setFixedHeight(58)
        header = QHBoxLayout(self.header)
        header.setContentsMargins(22, 8, 16, 8)
        header.setSpacing(8)
        title_area = QVBoxLayout()
        title_area.setSpacing(0)
        self.conversation_title = StrongBodyLabel("新对话", self.header)
        title_area.addWidget(self.conversation_title)
        self.model_meta = CaptionLabel("选择模型后开始", self.header)
        self.model_meta.setObjectName("mutedText")
        title_area.addWidget(self.model_meta)
        header.addLayout(title_area)
        header.addStretch()
        self.project_button = PushButton(FluentIcon.FOLDER, "选择工程", self.header)
        self.project_button.setObjectName("contextButton")
        self.project_button.setMaximumWidth(180)
        header.addWidget(self.project_button)
        self.profile_combo = ComboBox(self.header)
        self.profile_combo.setMinimumWidth(150)
        header.addWidget(self.profile_combo)
        self.add_profile_button = TransparentToolButton(FluentIcon.ADD, self.header)
        self.add_profile_button.setToolTip("添加模型连接")
        self.add_profile_button.setFixedSize(34, 34)
        header.addWidget(self.add_profile_button)
        self.profile_settings_button = TransparentToolButton(FluentIcon.MORE, self.header)
        self.profile_settings_button.setToolTip("当前模型设置")
        self.profile_settings_button.setFixedSize(34, 34)
        header.addWidget(self.profile_settings_button)
        self.workspace_layout.addWidget(self.header)

        self.chat_scroll = QScrollArea(self.workspace)
        self.chat_scroll.setObjectName("chatScroll")
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.NoFrame)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_content = QWidget(self.chat_scroll)
        self.chat_content.setObjectName("chatContent")
        self.message_layout = QVBoxLayout(self.chat_content)
        self.message_layout.setContentsMargins(42, 22, 42, 22)
        self.message_layout.setSpacing(4)
        self.chat_scroll.setWidget(self.chat_content)
        self.workspace_layout.addWidget(self.chat_scroll, 1)

        self.activity_label = CaptionLabel("", self.workspace)
        self.activity_label.setObjectName("activityLabel")
        self.activity_label.setAlignment(Qt.AlignCenter)
        self.activity_label.hide()
        self.workspace_layout.addWidget(self.activity_label)

        self.composer_shell = QWidget(self.workspace)
        self.composer_shell.setMaximumWidth(820)
        self.composer_shell.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        composer_shell_layout = QVBoxLayout(self.composer_shell)
        composer_shell_layout.setContentsMargins(20, 8, 20, 0)
        composer_shell_layout.setSpacing(7)
        self.composer = QFrame(self.composer_shell)
        self.composer.setObjectName("composerCard")
        composer = QVBoxLayout(self.composer)
        composer.setContentsMargins(15, 11, 11, 10)
        composer.setSpacing(7)
        self.input_box = QPlainTextEdit(self.composer)
        self.input_box.setObjectName("promptInput")
        self.input_box.setPlaceholderText("询问工程、代码生成或调试问题……")
        self.input_box.setFixedHeight(62)
        self.input_box.installEventFilter(self)
        composer.addWidget(self.input_box)
        composer_actions = QHBoxLayout()
        composer_actions.setSpacing(7)
        self.tools_button = PushButton(FluentIcon.CODE, "只读工具", self.composer)
        self.tools_button.setCheckable(True)
        self.tools_button.setChecked(True)
        self.tools_button.setToolTip("允许 AI 读取当前工程；不会修改或执行文件")
        composer_actions.addWidget(self.tools_button)
        self.context_caption = CaptionLabel("未选择工程", self.composer)
        self.context_caption.setObjectName("mutedText")
        composer_actions.addWidget(self.context_caption)
        composer_actions.addStretch()
        self.stop_button = ToolButton(FluentIcon.CANCEL, self.composer)
        self.stop_button.setToolTip("停止生成")
        self.stop_button.setFixedSize(38, 38)
        self.stop_button.hide()
        self.send_button = PrimaryToolButton(FluentIcon.SEND, self.composer)
        self.send_button.setToolTip("发送（Enter）")
        self.send_button.setFixedSize(38, 38)
        composer_actions.addWidget(self.stop_button)
        composer_actions.addWidget(self.send_button)
        composer.addLayout(composer_actions)
        composer_shell_layout.addWidget(self.composer)
        safety = CaptionLabel("AI 生成内容仅供参考；写入与烧录始终需要你的确认。", self.composer_shell)
        safety.setObjectName("safetyText")
        safety.setAlignment(Qt.AlignCenter)
        composer_shell_layout.addWidget(safety)
        composer_center = QHBoxLayout()
        composer_center.setContentsMargins(0, 0, 0, 0)
        composer_center.addStretch()
        composer_center.addWidget(self.composer_shell, 1)
        composer_center.addStretch()
        self.workspace_layout.addLayout(composer_center)
        self.bottom_spacer = QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.workspace_layout.addItem(self.bottom_spacer)
        root.addWidget(self.workspace, 1)

        self.add_profile_button.clicked.connect(self._add_profile)
        self.edit_profile_button.clicked.connect(self._edit_profile)
        self.profile_settings_button.clicked.connect(self._edit_profile)
        self.new_button.clicked.connect(self._new_conversation)
        self.search_edit.textChanged.connect(self._filter_conversations)
        self.conversation_list.currentItemChanged.connect(self._conversation_changed)
        self.conversation_list.customContextMenuRequested.connect(self._conversation_context_menu)
        self.project_button.clicked.connect(self._choose_project)
        self.profile_combo.currentTextChanged.connect(self._profile_changed)
        self.send_button.clicked.connect(self.send_message)
        self.stop_button.clicked.connect(self.stop_generation)
        self.input_box.textChanged.connect(self._update_send_button)
        self._update_send_button()

    def _apply_style(self) -> None:
        dark = isDarkTheme()
        page = "transparent"
        sidebar = "rgba(35,36,39,0.94)" if dark else "rgba(245,245,246,0.96)"
        workspace = "#1f2022" if dark else "#ffffff"
        border = "#383a3f" if dark else "#e8e8eb"
        text = "#f3f4f6" if dark else "#24262b"
        muted = "#a4a7ae" if dark else "#777a82"
        card = "#28292d" if dark else "#ffffff"
        user = "#303136" if dark else "#f0f0f2"
        selected = "#34353a" if dark else "#e9e9ec"
        self.setStyleSheet(
            f"""
            QWidget#aiPage {{ background: {page}; color: {text}; }}
            QFrame#aiSidebar {{ background: {sidebar}; border-right: 1px solid {border}; }}
            QFrame#aiWorkspace, QWidget#chatContent {{ background: {workspace}; }}
            QFrame#aiHeader {{ background: {workspace}; border-bottom: 1px solid {border}; }}
            QLabel#mutedText, QLabel#sectionLabel, QLabel#safetyText {{ color: {muted}; }}
            QLabel#sectionLabel {{ font-weight: 600; padding-left: 4px; }}
            QPushButton#newChatButton, QPushButton#sideSettingsButton {{ color: {text}; }}
            QListWidget#conversationList {{ background: transparent; border: none; outline: none; padding: 0; }}
            QListWidget#conversationList::item {{ min-height: 38px; border-radius: 8px; padding: 0 9px; margin: 1px 0; color: {text}; }}
            QListWidget#conversationList::item:hover {{ background: rgba(128,128,128,0.10); }}
            QListWidget#conversationList::item:selected {{ background: {selected}; color: {text}; border-left: 3px solid {ACCENT}; }}
            QScrollArea#chatScroll {{ background: {workspace}; border: none; }}
            QFrame#userBubble {{ background: {user}; border: none; border-radius: 15px; }}
            QLabel#messageText {{ color: {text}; font-size: 14px; line-height: 1.45; }}
            QLabel#emptyGreeting {{ color: {text}; font-size: 28px; font-weight: 700; }}
            QFrame#composerCard {{ background: {card}; border: 1px solid {border}; border-radius: 18px; }}
            QFrame#composerCard:focus-within {{ border: 1px solid rgba(255,79,145,0.42); }}
            #promptInput {{ background: transparent; border: none; padding: 0; }}
            QLabel#activityLabel {{ color: {muted}; padding: 4px; }}
            QFrame#errorCard {{ background: rgba(213,63,88,0.07); border: 1px solid rgba(213,63,88,0.26); border-radius: 11px; }}
            QFrame#emptySuggestion {{ background: transparent; border: 1px solid {border}; border-radius: 16px; }}
            QFrame#emptySuggestion:hover {{ border: 1px solid rgba(255,79,145,0.38); background: {selected}; }}
            """
        )
        palette = self.input_box.palette()
        palette.setColor(QPalette.Base, QColor(0, 0, 0, 0))
        palette.setColor(QPalette.Text, QColor(text))
        palette.setColor(QPalette.PlaceholderText, QColor(muted))
        self.input_box.setPalette(palette)
        for message in self.findChildren(ChatMessageWidget):
            message.refresh_theme()

    def _schedule_theme_refresh(self, *_args: object) -> None:
        QTimer.singleShot(0, self._apply_style)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() in {Qt.Key_Return, Qt.Key_Enter} and not event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(watched, event)

    def _update_send_button(self) -> None:
        busy = bool(self.worker and self.worker.isRunning())
        self.send_button.setEnabled(bool(self.input_box.toPlainText().strip()) and not busy)

    def _reload_profiles(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(self.profiles.keys())
        self.profile_combo.setCurrentText(self.active_profile)
        self.profile_combo.blockSignals(False)
        self._update_header()

    def _reload_conversations(self, select_first: bool = False) -> None:
        selected_id = self.current.conversation_id if self.current else ""
        self.conversation_list.blockSignals(True)
        self.conversation_list.clear()
        for conversation in sorted(self.conversations, key=lambda item: item.updated_at, reverse=True):
            item = QListWidgetItem(conversation.title)
            item.setData(Qt.UserRole, conversation.conversation_id)
            item.setToolTip(conversation.title)
            item.setSizeHint(QSize(0, 42))
            self.conversation_list.addItem(item)
            if conversation.conversation_id == selected_id:
                self.conversation_list.setCurrentItem(item)
        self.conversation_list.blockSignals(False)
        self._filter_conversations(self.search_edit.text())
        if self.conversation_list.count() == 0:
            self._new_conversation()
        elif select_first or self.conversation_list.currentItem() is None:
            self.conversation_list.setCurrentRow(0)
            self._conversation_changed(self.conversation_list.currentItem(), None)

    def _filter_conversations(self, value: str) -> None:
        query = value.strip().lower()
        for index in range(self.conversation_list.count()):
            item = self.conversation_list.item(index)
            item.setHidden(bool(query and query not in item.text().lower()))

    def _new_conversation(self) -> None:
        self._save_current()
        project_root = self.current.project_root if self.current else ""
        conversation = Conversation.create(self.active_profile, project_root)
        self.conversations.append(conversation)
        self.current = conversation
        self.last_error = ""
        self.conversation_store.save_all(self.conversations)
        self._reload_conversations()
        for index in range(self.conversation_list.count()):
            item = self.conversation_list.item(index)
            if item.data(Qt.UserRole) == conversation.conversation_id:
                self.conversation_list.setCurrentItem(item)
                break
        self._load_current()
        self.input_box.setFocus()

    def _conversation_context_menu(self, position) -> None:
        item = self.conversation_list.itemAt(position)
        if not item:
            return
        self.conversation_list.setCurrentItem(item)
        from qfluentwidgets import Action, RoundMenu

        menu = RoundMenu(parent=self)
        menu.addAction(Action(FluentIcon.DELETE, "删除对话", triggered=self._delete_conversation))
        menu.exec_(self.conversation_list.mapToGlobal(position))

    def _delete_conversation(self) -> None:
        if not self.current:
            return
        if QMessageBox.question(self, "删除对话", f"确定删除“{self.current.title}”吗？") != QMessageBox.Yes:
            return
        current_id = self.current.conversation_id
        self.conversations = [item for item in self.conversations if item.conversation_id != current_id]
        self.current = None
        self.conversation_store.save_all(self.conversations)
        self._reload_conversations(select_first=True)

    def _conversation_changed(self, current_item: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if not current_item:
            return
        self._save_current()
        conversation_id = str(current_item.data(Qt.UserRole))
        self.current = next((item for item in self.conversations if item.conversation_id == conversation_id), None)
        self.last_error = ""
        self._load_current()

    def _load_current(self) -> None:
        if not self.current:
            return
        if self.current.provider in self.profiles:
            self.active_profile = self.current.provider
            self.profile_combo.setCurrentText(self.active_profile)
        config = self.profiles.get(self.active_profile)
        self.tools_button.setChecked(config.enable_tools if config else True)
        self._update_header()
        self._render_chat()

    def _save_current(self) -> None:
        if not self.current:
            return
        self.current.provider = self.active_profile
        self.current.touch()
        self.conversation_store.save_all(self.conversations)

    def _profile_changed(self, name: str) -> None:
        if not name or name not in self.profiles:
            return
        self.active_profile = name
        if self.current:
            self.current.provider = name
        self.profile_store.save(self.active_profile, self.profiles)
        self._save_current()
        self.tools_button.setChecked(self.profiles[name].enable_tools)
        self._update_header()

    def _add_profile(self) -> None:
        dialog = AISettingsDialog(AIProviderConfig.from_preset("custom", "新模型"), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._store_dialog_profile(dialog, old_name=None)

    def _edit_profile(self) -> None:
        config = self.profiles.get(self.active_profile)
        if not config:
            return
        dialog = AISettingsDialog(config, self.session_keys.get(self.active_profile, ""), self)
        if dialog.exec_() == QDialog.Accepted:
            self._store_dialog_profile(dialog, old_name=self.active_profile)

    def _store_dialog_profile(self, dialog: AISettingsDialog, old_name: str | None) -> None:
        config = dialog.config()
        previous_key = ""
        if old_name and old_name != config.name:
            self.profiles.pop(old_name, None)
            previous_key = self.session_keys.pop(old_name, "")
        self.profiles[config.name] = config
        self.session_keys[config.name] = dialog.session_key() or previous_key
        self.active_profile = config.name
        self.profile_store.save(self.active_profile, self.profiles)
        self._reload_profiles()
        self.profile_combo.setCurrentText(config.name)

    def _choose_project(self) -> None:
        current_path = self.current.project_root if self.current else ""
        directory = QFileDialog.getExistingDirectory(self, "选择 MRobot 工程目录", current_path or str(Path.home()))
        if directory and self.current:
            self.current.project_root = directory
            self._save_current()
            self._update_header()

    def _update_header(self) -> None:
        config = self.profiles.get(self.active_profile)
        title = self.current.title if self.current else "新对话"
        self.conversation_title.setText(title)
        if config:
            protocol = {"auto": "自动协议", "responses": "Responses", "chat": "Chat"}.get(config.protocol, "自动协议")
            self.model_meta.setText(f"{config.model or '未设置模型'} · {protocol}")
        else:
            self.model_meta.setText("尚未配置模型")
        project = self.current.project_root if self.current else ""
        if project:
            name = Path(project).name or project
            self.project_button.setText(name)
            self.project_button.setToolTip(project)
            self.context_caption.setText(f"已连接 {name}")
            self.context_caption.show()
        else:
            self.project_button.setText("选择工程")
            self.project_button.setToolTip("选择 STM32CubeMX 或 MRobot 工程目录")
            self.context_caption.clear()
            self.context_caption.hide()

    def _set_activity(self, message: str = "") -> None:
        self.activity_label.setText(message)
        self.activity_label.setVisible(bool(message))

    def send_message(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        prompt = self.input_box.toPlainText().strip()
        if not prompt or not self.current:
            return
        self.current.messages.append({"role": "user", "content": prompt})
        if self.current.title == "新对话":
            self.current.title = prompt.replace("\n", " ")[:28]
        self.current.touch()
        self.input_box.clear()
        self.last_error = ""
        self._render_chat()
        self._start_request()

    def _start_request(self) -> None:
        if not self.current:
            return
        config = self.profiles[self.active_profile]
        tools_enabled = self.tools_button.isChecked()
        project_root = self.current.project_root if tools_enabled else ""
        if project_root and not Path(project_root).expanduser().is_dir():
            self._worker_failed("工程目录不存在，请重新选择工程或关闭只读工具")
            return
        self.streaming_text = ""
        self.streaming_widget = None
        self._set_busy(True)
        run_config = replace(config, enable_tools=tools_enabled)
        self.worker = AIWorker(
            run_config,
            self.session_keys.get(self.active_profile, ""),
            list(self.current.messages),
            project_root,
            self,
        )
        self.worker.chunk_received.connect(self._stream_chunk)
        self.worker.status_changed.connect(self._set_activity)
        self.worker.completed.connect(self._finish_response)
        self.worker.failed.connect(self._worker_failed)
        self.worker.cancelled.connect(self._worker_cancelled)
        self.worker.start()
        self._save_current()
        self._reload_conversations()

    def stop_generation(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_cancel()
            self._set_activity("正在停止……")

    def _stream_chunk(self, text: str) -> None:
        self.streaming_text += text
        if self.streaming_widget is None:
            self.streaming_widget = ChatMessageWidget("assistant", self.streaming_text, self.chat_content, streaming=True)
            self.message_layout.insertWidget(max(0, self.message_layout.count() - 1), self.streaming_widget)
        else:
            self.streaming_widget.set_text(self.streaming_text, streaming=True)
        self._scroll_to_bottom()

    def _finish_response(self, result: object) -> None:
        if self.current and hasattr(result, "messages"):
            self.current.messages = list(result.messages)
            self.current.touch()
        self.streaming_text = ""
        self.streaming_widget = None
        self.last_error = ""
        self._set_busy(False)
        self._save_current()
        self._render_chat()
        tool_count = len(result.tool_events) if hasattr(result, "tool_events") else 0
        self._set_activity(f"已使用 {tool_count} 次只读工具" if tool_count else "")
        if tool_count:
            QTimer.singleShot(3500, lambda: self._set_activity(""))

    def _worker_failed(self, message: str) -> None:
        self.streaming_text = ""
        self.streaming_widget = None
        self.last_error = message
        self._set_busy(False)
        self._set_activity("")
        self._render_chat()

    def _worker_cancelled(self) -> None:
        self.streaming_text = ""
        self.streaming_widget = None
        self._set_busy(False)
        self._set_activity("已停止生成")
        self._render_chat()
        QTimer.singleShot(2500, lambda: self._set_activity(""))

    def _retry_last(self) -> None:
        if not self.current or not self.current.messages:
            return
        self.last_error = ""
        self._render_chat()
        self._start_request()

    def _set_busy(self, busy: bool) -> None:
        self.send_button.setVisible(not busy)
        self.stop_button.setVisible(busy)
        self.profile_combo.setEnabled(not busy)
        self.profile_settings_button.setEnabled(not busy)
        self.add_profile_button.setEnabled(not busy)
        self.edit_profile_button.setEnabled(not busy)
        self.tools_button.setEnabled(not busy)
        self._update_send_button()
        self._set_activity("MRobot 正在思考……" if busy else "")

    def _clear_message_layout(self) -> None:
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def _render_chat(self) -> None:
        self._clear_message_layout()
        self.streaming_widget = None
        if not self.current:
            return
        visible = [message for message in self.current.messages if message.get("role") in {"user", "assistant"} and message.get("content")]
        is_empty = not visible and not self.last_error
        self._set_empty_layout(is_empty)
        if is_empty:
            self.message_layout.addWidget(self._empty_state(), 1)
        else:
            for message in visible:
                self.message_layout.addWidget(ChatMessageWidget(str(message.get("role")), str(message.get("content") or ""), self.chat_content))
            if self.last_error:
                self.message_layout.addWidget(self._error_card(self.last_error))
            self.message_layout.addItem(QSpacerItem(0, 12, QSizePolicy.Minimum, QSizePolicy.Expanding))
        QTimer.singleShot(0, self._scroll_to_bottom)

    def _set_empty_layout(self, empty: bool) -> None:
        """Place the first-run composer near the greeting, then dock it for chat."""
        self.input_box.setFixedHeight(92 if empty else 54)
        self.chat_scroll.setMaximumHeight(330 if empty else 16777215)
        self.workspace_layout.setStretch(1, 0 if empty else 1)
        self.workspace_layout.setStretch(4, 1 if empty else 0)

    @staticmethod
    def _greeting() -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "早上好。"
        if 12 <= hour < 18:
            return "下午好。"
        return "晚上好。"

    def _empty_state(self) -> QWidget:
        empty = QWidget(self.chat_content)
        empty.setObjectName("emptyState")
        layout = QVBoxLayout(empty)
        layout.setContentsMargins(40, 26, 40, 10)
        layout.setSpacing(11)
        layout.addStretch(2)
        title = QLabel(self._greeting(), empty)
        title.setObjectName("emptyGreeting")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        description = BodyLabel("选择一个工程，或直接描述你想解决的嵌入式开发问题。", empty)
        description.setObjectName("mutedText")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        suggestions = QHBoxLayout()
        suggestions.setSpacing(8)
        suggestions.addStretch()
        for label, prompt in self.suggestion_prompts[:3]:
            card = QFrame(empty)
            card.setObjectName("emptySuggestion")
            card.setCursor(Qt.PointingHandCursor)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 8, 14, 8)
            text = BodyLabel(label, card)
            card_layout.addWidget(text)
            card.mousePressEvent = lambda _event, value=prompt: self._use_suggestion(value)  # type: ignore[method-assign]
            suggestions.addWidget(card)
        suggestions.addStretch()
        layout.addLayout(suggestions)
        layout.addStretch(1)
        return empty

    def _use_suggestion(self, prompt: str) -> None:
        self.input_box.setPlainText(prompt)
        self.input_box.setFocus()

    def _error_card(self, message: str) -> QWidget:
        card = QFrame(self.chat_content)
        card.setObjectName("errorCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        title = StrongBodyLabel("这次请求没有完成", card)
        title.setStyleSheet("color:#c33855;")
        layout.addWidget(title)
        detail = BodyLabel(message, card)
        detail.setWordWrap(True)
        layout.addWidget(detail)
        actions = QHBoxLayout()
        retry = PushButton(FluentIcon.SYNC, "重试", card)
        settings = PushButton(FluentIcon.SETTING, "检查模型设置", card)
        retry.clicked.connect(self._retry_last)
        settings.clicked.connect(self._edit_profile)
        actions.addWidget(retry)
        actions.addWidget(settings)
        actions.addStretch()
        layout.addLayout(actions)
        return card

    def _scroll_to_bottom(self) -> None:
        bar = self.chat_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_cancel()
            self.worker.wait(1500)
        self._save_current()
        super().closeEvent(event)
