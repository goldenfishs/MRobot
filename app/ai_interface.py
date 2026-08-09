from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QEvent, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, FluentIcon, InfoBar, InfoBarPosition, PrimaryPushButton, PushButton, SubtitleLabel, TitleLabel

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
            tools = MRobotToolRegistry(self.project_root or None)
            assistant = MRobotAssistant(client, tools)
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


class AISettingsDialog(QDialog):
    def __init__(self, config: AIProviderConfig, session_key: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AI 模型配置")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        title = SubtitleLabel("连接自定义 AI", self)
        layout.addWidget(title)
        description = BodyLabel("支持 OpenAI-compatible /v1/chat/completions 接口。API Key 默认只保存在本次运行内。", self)
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(12)
        self.preset_combo = QComboBox(self)
        self.preset_combo.addItem("保持当前参数", "")
        for preset_id, value in PROVIDER_PRESETS.items():
            self.preset_combo.addItem(str(value["label"]), preset_id)
        self.name_edit = QLineEdit(config.name, self)
        self.base_url_edit = QLineEdit(config.base_url, self)
        self.model_edit = QLineEdit(config.model, self)
        self.key_env_edit = QLineEdit(config.api_key_env, self)
        self.key_edit = QLineEdit(session_key, self)
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("留空时读取下面的环境变量")
        self.temperature_spin = QDoubleSpinBox(self)
        self.temperature_spin.setRange(0, 2)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(config.temperature)
        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setRange(15, 600)
        self.timeout_spin.setValue(config.timeout)
        self.tools_check = QCheckBox("允许模型调用 MRobot 只读工程工具", self)
        self.tools_check.setChecked(config.enable_tools)
        form.addRow("服务预设", self.preset_combo)
        form.addRow("配置名称", self.name_edit)
        form.addRow("Base URL", self.base_url_edit)
        form.addRow("模型 ID", self.model_edit)
        form.addRow("API Key（本次运行）", self.key_edit)
        form.addRow("API Key 环境变量", self.key_env_edit)
        form.addRow("Temperature", self.temperature_spin)
        form.addRow("超时（秒）", self.timeout_spin)
        form.addRow("工具权限", self.tools_check)
        layout.addLayout(form)

        warning = QLabel("安全提示：远程地址必须使用 HTTPS；只有 localhost/127.0.0.1 可以使用 HTTP。API Key 不会写入配置文件或对话历史。", self)
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #8a6500; padding: 8px;")
        layout.addWidget(warning)

        actions = QHBoxLayout()
        self.test_button = QPushButton("测试连接", self)
        actions.addWidget(self.test_button)
        actions.addStretch()
        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        self.buttons.button(QDialogButtonBox.Save).setText("保存")
        self.buttons.button(QDialogButtonBox.Cancel).setText("取消")
        actions.addWidget(self.buttons)
        layout.addLayout(actions)

        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        self.test_button.clicked.connect(self._test_connection)
        self.buttons.accepted.connect(self._accept_if_valid)
        self.buttons.rejected.connect(self.reject)

    def _apply_preset(self) -> None:
        preset_id = str(self.preset_combo.currentData() or "")
        if not preset_id:
            return
        config = AIProviderConfig.from_preset(preset_id)
        self.name_edit.setText(config.name)
        self.base_url_edit.setText(config.base_url)
        self.model_edit.setText(config.model)
        self.key_env_edit.setText(config.api_key_env)

    def config(self) -> AIProviderConfig:
        return AIProviderConfig(
            name=self.name_edit.text().strip(),
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            api_key_env=self.key_env_edit.text().strip(),
            temperature=self.temperature_spin.value(),
            timeout=self.timeout_spin.value(),
            enable_tools=self.tools_check.isChecked(),
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

    def _accept_if_valid(self) -> None:
        try:
            self._validate()
        except AIClientError as exc:
            QMessageBox.warning(self, "配置无效", str(exc))
            return
        self.accept()

    def _test_connection(self) -> None:
        try:
            config = self._validate()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            models = OpenAICompatibleClient(config, api_key=self.session_key()).list_models()
            detail = f"连接成功，服务返回 {len(models)} 个模型。"
            if config.model not in models and models:
                detail += "\n当前模型 ID 不在返回列表中，请确认服务是否允许直接填写未列出的模型。"
            QMessageBox.information(self, "连接成功", detail)
        except AIClientError as exc:
            QMessageBox.warning(self, "连接失败", str(exc))
        finally:
            QApplication.restoreOverrideCursor()


class AIInterface(QWidget):
    """Project-aware AI workbench backed by the shared app.ai core."""

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
        self._build_ui()
        self._reload_profiles()
        self._reload_conversations(select_first=True)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        header.addWidget(TitleLabel("MRobot AI 工作台", self))
        header.addStretch()
        self.profile_combo = QComboBox(self)
        self.profile_combo.setMinimumWidth(180)
        self.profile_combo.currentTextChanged.connect(self._profile_changed)
        header.addWidget(self.profile_combo)
        self.add_profile_button = PushButton(FluentIcon.ADD, "添加模型", self)
        self.edit_profile_button = PushButton(FluentIcon.SETTING, "模型设置", self)
        header.addWidget(self.add_profile_button)
        header.addWidget(self.edit_profile_button)
        root.addLayout(header)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        sidebar = QFrame(splitter)
        sidebar.setMinimumWidth(190)
        sidebar.setMaximumWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_header = QHBoxLayout()
        sidebar_header.addWidget(SubtitleLabel("对话", sidebar))
        sidebar_header.addStretch()
        self.new_button = QPushButton("＋", sidebar)
        self.new_button.setFixedWidth(34)
        sidebar_header.addWidget(self.new_button)
        sidebar_layout.addLayout(sidebar_header)
        self.conversation_list = QListWidget(sidebar)
        sidebar_layout.addWidget(self.conversation_list, 1)
        self.delete_button = QPushButton("删除当前对话", sidebar)
        sidebar_layout.addWidget(self.delete_button)
        splitter.addWidget(sidebar)

        workspace = QFrame(splitter)
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(14, 0, 0, 0)
        context_row = QHBoxLayout()
        context_row.addWidget(BodyLabel("工程上下文", workspace))
        self.project_edit = QLineEdit(workspace)
        self.project_edit.setPlaceholderText("可选：选择 STM32CubeMX 或其他 MRobot 工程目录")
        context_row.addWidget(self.project_edit, 1)
        self.project_button = PushButton(FluentIcon.FOLDER, "选择工程", workspace)
        context_row.addWidget(self.project_button)
        self.tools_check = QCheckBox("允许只读工程工具", workspace)
        self.tools_check.setChecked(True)
        context_row.addWidget(self.tools_check)
        workspace_layout.addLayout(context_row)

        self.status_label = QLabel("未连接 · 工具仅限读取和诊断", workspace)
        self.status_label.setStyleSheet("color: #6b7280; padding: 2px 4px;")
        workspace_layout.addWidget(self.status_label)

        self.chat_display = QTextBrowser(workspace)
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("QTextBrowser { border: 1px solid rgba(128,128,128,0.25); border-radius: 10px; padding: 12px; }")
        workspace_layout.addWidget(self.chat_display, 1)

        composer = QFrame(workspace)
        composer.setStyleSheet("QFrame { border: 1px solid rgba(128,128,128,0.30); border-radius: 10px; }")
        composer_layout = QVBoxLayout(composer)
        self.input_box = QPlainTextEdit(composer)
        self.input_box.setPlaceholderText("询问工程、驱动、代码生成计划或调试问题……（Ctrl+Enter 发送）")
        self.input_box.setMaximumHeight(120)
        self.input_box.setStyleSheet("border: none;")
        self.input_box.installEventFilter(self)
        composer_layout.addWidget(self.input_box)
        composer_actions = QHBoxLayout()
        composer_actions.addWidget(QLabel("AI 可能出错；生成、烧录等写操作必须由你确认。", composer))
        composer_actions.addStretch()
        self.stop_button = PushButton("停止", composer)
        self.stop_button.setEnabled(False)
        self.send_button = PrimaryPushButton(FluentIcon.SEND, "发送", composer)
        composer_actions.addWidget(self.stop_button)
        composer_actions.addWidget(self.send_button)
        composer_layout.addLayout(composer_actions)
        workspace_layout.addWidget(composer)
        splitter.addWidget(workspace)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.add_profile_button.clicked.connect(self._add_profile)
        self.edit_profile_button.clicked.connect(self._edit_profile)
        self.new_button.clicked.connect(self._new_conversation)
        self.delete_button.clicked.connect(self._delete_conversation)
        self.conversation_list.currentItemChanged.connect(self._conversation_changed)
        self.project_button.clicked.connect(self._choose_project)
        self.project_edit.editingFinished.connect(self._project_changed)
        self.send_button.clicked.connect(self.send_message)
        self.stop_button.clicked.connect(self.stop_generation)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self.input_box and event.type() == QEvent.KeyPress:
            if event.key() in {Qt.Key_Return, Qt.Key_Enter} and event.modifiers() & Qt.ControlModifier:
                self.send_message()
                return True
        return super().eventFilter(watched, event)

    def _reload_profiles(self) -> None:
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItems(self.profiles.keys())
        self.profile_combo.setCurrentText(self.active_profile)
        self.profile_combo.blockSignals(False)
        self._update_status()

    def _reload_conversations(self, select_first: bool = False) -> None:
        selected_id = self.current.conversation_id if self.current else ""
        self.conversation_list.blockSignals(True)
        self.conversation_list.clear()
        for conversation in sorted(self.conversations, key=lambda item: item.updated_at, reverse=True):
            item = QListWidgetItem(conversation.title)
            item.setData(Qt.UserRole, conversation.conversation_id)
            self.conversation_list.addItem(item)
            if conversation.conversation_id == selected_id:
                self.conversation_list.setCurrentItem(item)
        self.conversation_list.blockSignals(False)
        if self.conversation_list.count() == 0:
            self._new_conversation()
        elif select_first or self.conversation_list.currentItem() is None:
            self.conversation_list.setCurrentRow(0)
            self._conversation_changed(self.conversation_list.currentItem(), None)

    def _new_conversation(self) -> None:
        self._save_current()
        conversation = Conversation.create(self.active_profile, self.project_edit.text().strip() if hasattr(self, "project_edit") else "")
        self.conversations.append(conversation)
        self.current = conversation
        self.conversation_store.save_all(self.conversations)
        self._reload_conversations(select_first=False)
        for index in range(self.conversation_list.count()):
            item = self.conversation_list.item(index)
            if item.data(Qt.UserRole) == conversation.conversation_id:
                self.conversation_list.setCurrentItem(item)
                break
        self._load_current()

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
        self._load_current()

    def _load_current(self) -> None:
        if not self.current:
            return
        if self.current.provider in self.profiles:
            self.active_profile = self.current.provider
            self.profile_combo.setCurrentText(self.active_profile)
        self.project_edit.setText(self.current.project_root)
        self._render_chat()

    def _save_current(self) -> None:
        if not self.current:
            return
        self.current.project_root = self.project_edit.text().strip()
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
        self._update_status()

    def _add_profile(self) -> None:
        candidate = AIProviderConfig.from_preset("custom", "新模型")
        dialog = AISettingsDialog(candidate, parent=self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._store_dialog_profile(dialog, old_name=None)

    def _edit_profile(self) -> None:
        config = self.profiles[self.active_profile]
        dialog = AISettingsDialog(config, self.session_keys.get(self.active_profile, ""), self)
        if dialog.exec_() != QDialog.Accepted:
            return
        self._store_dialog_profile(dialog, old_name=self.active_profile)

    def _store_dialog_profile(self, dialog: AISettingsDialog, old_name: str | None) -> None:
        config = dialog.config()
        if old_name and old_name != config.name:
            self.profiles.pop(old_name, None)
            previous_key = self.session_keys.pop(old_name, "")
        else:
            previous_key = ""
        self.profiles[config.name] = config
        self.session_keys[config.name] = dialog.session_key() or previous_key
        self.active_profile = config.name
        self.profile_store.save(self.active_profile, self.profiles)
        self._reload_profiles()
        self.profile_combo.setCurrentText(config.name)

    def _choose_project(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择 MRobot 工程目录", self.project_edit.text() or str(Path.home()))
        if directory:
            self.project_edit.setText(directory)
            self._project_changed()

    def _project_changed(self) -> None:
        if self.current:
            self.current.project_root = self.project_edit.text().strip()
            self._save_current()
        self._update_status()

    def _update_status(self, message: str = "") -> None:
        config = self.profiles.get(self.active_profile)
        if message:
            self.status_label.setText(message)
            return
        if not config:
            self.status_label.setText("未配置模型")
            return
        project = self.project_edit.text().strip() if hasattr(self, "project_edit") else ""
        context = "已选择工程，只读工具可用" if project else "未选择工程"
        self.status_label.setText(f"{config.name} · {config.model or '未设置模型'} · {context}")

    def send_message(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        prompt = self.input_box.toPlainText().strip()
        if not prompt or not self.current:
            return
        config = self.profiles[self.active_profile]
        project_root = self.project_edit.text().strip() if self.tools_check.isChecked() else ""
        if project_root and not Path(project_root).expanduser().is_dir():
            self._show_error("工程目录不存在，请重新选择或关闭只读工程工具")
            return
        self.current.messages.append({"role": "user", "content": prompt})
        if self.current.title == "新对话":
            self.current.title = prompt.replace("\n", " ")[:28]
        self.current.touch()
        self.input_box.clear()
        self.streaming_text = ""
        self._render_chat()
        self._set_busy(True)
        self.worker = AIWorker(
            config,
            self.session_keys.get(self.active_profile, ""),
            list(self.current.messages),
            project_root,
            self,
        )
        self.worker.chunk_received.connect(self._stream_chunk)
        self.worker.status_changed.connect(self._update_status)
        self.worker.completed.connect(self._finish_response)
        self.worker.failed.connect(self._worker_failed)
        self.worker.cancelled.connect(self._worker_cancelled)
        self.worker.start()
        self._save_current()
        self._reload_conversations()

    def stop_generation(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_cancel()
            self._update_status("正在停止……")

    def _stream_chunk(self, text: str) -> None:
        self.streaming_text += text
        self._render_chat(streaming=self.streaming_text)

    def _finish_response(self, result: object) -> None:
        if self.current and hasattr(result, "messages"):
            self.current.messages = list(result.messages)
            self.current.touch()
        self.streaming_text = ""
        self._set_busy(False)
        self._save_current()
        self._render_chat()
        tool_count = len(result.tool_events) if hasattr(result, "tool_events") else 0
        suffix = f" · 使用 {tool_count} 次只读工具" if tool_count else ""
        self._update_status(f"回答完成{suffix}")

    def _worker_failed(self, message: str) -> None:
        self.streaming_text = ""
        self._set_busy(False)
        self._update_status("请求失败")
        self._show_error(message)

    def _worker_cancelled(self) -> None:
        self.streaming_text = ""
        self._set_busy(False)
        self._update_status("已停止生成")
        self._render_chat()

    def _set_busy(self, busy: bool) -> None:
        self.send_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.profile_combo.setEnabled(not busy)
        self.add_profile_button.setEnabled(not busy)
        self.edit_profile_button.setEnabled(not busy)

    def _show_error(self, message: str) -> None:
        InfoBar.error(
            title="AI 请求失败",
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,
            parent=self,
        )

    def _render_chat(self, streaming: str = "") -> None:
        if not self.current:
            self.chat_display.clear()
            return
        blocks: list[str] = []
        visible = [message for message in self.current.messages if message.get("role") in {"user", "assistant"}]
        if not visible and not streaming:
            blocks.append(
                '<div style="text-align:center; margin:80px 20px;">'
                '<h2>MRobot AI 工作台</h2>'
                '<p>连接你自己的模型，选择工程后即可检查 CubeMX 配置、生成计划和诊断。</p>'
                '<p style="color:#777;">当前工具全部只读，不会自动改代码或烧录。</p></div>'
            )
        for message in visible:
            role = str(message.get("role"))
            content = html.escape(str(message.get("content") or "")).replace("\n", "<br>")
            if role == "user":
                blocks.append(f'<div style="margin:12px 0 12px 18%; padding:12px; background:#f18cb933; border-radius:10px;"><b>你</b><br>{content}</div>')
            elif content:
                blocks.append(f'<div style="margin:12px 18% 12px 0; padding:12px; background:#80808018; border-radius:10px;"><b>MRobot AI</b><br>{content}</div>')
        if streaming:
            content = html.escape(streaming).replace("\n", "<br>")
            blocks.append(f'<div style="margin:12px 18% 12px 0; padding:12px; background:#80808018; border-radius:10px;"><b>MRobot AI</b><br>{content}<span style="color:#f18cb9;"> ▍</span></div>')
        self.chat_display.setHtml("".join(blocks))
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_cancel()
            self.worker.wait(1500)
        self._save_current()
        super().closeEvent(event)
