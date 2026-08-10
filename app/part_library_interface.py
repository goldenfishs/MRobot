from __future__ import annotations

from pathlib import Path, PurePosixPath
import re

from PyQt5.QtCore import QSettings, QStandardPaths, Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QSplitter,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    ListWidget,
    PrimaryPushButton,
    ProgressBar,
    ProgressRing,
    PushButton,
    SearchLineEdit,
    StrongBodyLabel,
    TableWidget,
    TitleLabel,
)

from .part_library import ArchiveEntry, PartCatalog, format_size
from .part_library.catalog import DOCUMENT_EXTENSIONS, IMAGE_EXTENSIONS, MODEL_EXTENSIONS
from .part_library.workers import (
    ArchiveExportThread,
    CatalogScanThread,
    CloudCatalogThread,
    PreviewLoadThread,
)
from .home_interface import resource_path


ARCHIVE_SETTING_KEY = "parts/archivePath"
DEFAULT_CLOUD_CATALOG_URL = "https://download.qutmrobot.cn/parts/v1/catalog.json"


def default_local_library_dir() -> Path:
    documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    base = Path(documents) if documents else Path.home() / "Documents"
    return base / "MRobot" / "零件库"


def default_catalog_cache_path() -> Path:
    cache_location = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
    base = Path(cache_location) if cache_location else Path.home() / ".cache" / "MRobot"
    return base / "parts" / "catalog.json"


def discover_part_archive() -> Path | None:
    download_location = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
    if not download_location:
        return None
    download_dir = Path(download_location)
    for filename in ("零件库.zip", "MRobot零件库.zip", "MRobot-parts.zip"):
        candidate = download_dir / filename
        if candidate.is_file():
            return candidate
    return None


class PartLibraryInterface(QWidget):
    """Browse the cloud catalogue with cached and local-ZIP fallbacks."""

    def __init__(
        self,
        parent=None,
        *,
        settings: QSettings | None = None,
        auto_discover: bool = True,
    ) -> None:
        super().__init__(parent=parent)
        self.setObjectName("partLibraryInterface")
        self.settings = settings or QSettings("MRobot", "MRobot")
        self.local_library_dir = default_local_library_dir()
        self.catalog: PartCatalog | None = None
        self.selected_entry: ArchiveEntry | None = None
        self._entries_by_path: dict[str, ArchiveEntry] = {}
        self._preview_cache: dict[str, QPixmap] = {}
        self._scan_thread: CatalogScanThread | None = None
        self._cloud_thread: CloudCatalogThread | None = None
        self._preview_thread: PreviewLoadThread | None = None
        self._preview_loading_path = ""
        self._export_thread: ArchiveExportThread | None = None
        self._export_bar: InfoBar | None = None

        self._build_ui()

        self.auto_discover = auto_discover
        self.load_cloud_catalog()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        self.source_card = CardWidget(self)
        source_layout = QHBoxLayout(self.source_card)
        source_layout.setContentsMargins(20, 16, 16, 16)
        source_layout.setSpacing(12)
        self.source_icon = QLabel(self.source_card)
        self.source_icon.setAlignment(Qt.AlignCenter)
        self.source_icon.setFixedSize(48, 48)
        logo = QPixmap(resource_path("assets/logo/M.png"))
        self.source_icon.setPixmap(
            logo.scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        source_layout.addWidget(self.source_icon)
        source_text = QVBoxLayout()
        source_text.setSpacing(2)
        self.source_title = TitleLabel("零件库", self.source_card)
        self.source_description = BodyLabel(
            "精选机器人常用 3D 模型，快速搜索、在线预览、按需下载。",
            self.source_card,
        )
        source_text.addWidget(self.source_title)
        source_text.addWidget(self.source_description)
        source_layout.addLayout(source_text, 1)

        source_state = QVBoxLayout()
        source_state.setSpacing(1)
        self.source_status = StrongBodyLabel("正在连接云端", self.source_card)
        self.source_status.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.source_status.setStyleSheet("color: palette(highlight); font-weight: 600;")
        self.source_meta = CaptionLabel("正在同步目录…", self.source_card)
        self.source_meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        source_state.addWidget(self.source_status)
        source_state.addWidget(self.source_meta)
        source_layout.addLayout(source_state)

        self.source_progress = ProgressRing(self.source_card)
        self.source_progress.setFixedSize(22, 22)
        self.source_progress.hide()
        source_layout.addWidget(self.source_progress)

        self.open_local_button = PushButton(FluentIcon.FOLDER, "下载目录", self.source_card)
        self.open_local_button.clicked.connect(self.open_local_library)
        source_layout.addWidget(self.open_local_button)
        self.open_source_button = PushButton(FluentIcon.SYNC, "刷新", self.source_card)
        self.open_source_button.clicked.connect(self.reload_archive)
        source_layout.addWidget(self.open_source_button)
        self.choose_source_button = PushButton(FluentIcon.ZIP_FOLDER, "离线包", self.source_card)
        self.choose_source_button.clicked.connect(self.choose_archive)
        source_layout.addWidget(self.choose_source_button)
        root.addWidget(self.source_card)

        self.content_stack = QStackedWidget(self)
        self.empty_page = self._create_empty_page()
        self.browser_page = self._create_browser_page()
        self.content_stack.addWidget(self.empty_page)
        self.content_stack.addWidget(self.browser_page)
        root.addWidget(self.content_stack, 1)

    def _create_empty_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        empty_card = CardWidget(page)
        empty_card.setMaximumWidth(580)
        card_layout = QVBoxLayout(empty_card)
        card_layout.setContentsMargins(42, 36, 42, 36)
        card_layout.setSpacing(12)
        icon = QLabel("3D", empty_card)
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 34px; font-weight: 700; color: palette(highlight);")
        card_layout.addWidget(icon)
        title = TitleLabel("正在连接云端零件库", empty_card)
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)
        description = BodyLabel(
            "目录会保存在本机以便断网浏览；零件和预览仅在需要时下载。",
            empty_card,
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        card_layout.addWidget(description)
        button_row = QHBoxLayout()
        button_row.addStretch()
        choose = PushButton(FluentIcon.ZIP_FOLDER, "使用离线 ZIP", empty_card)
        choose.clicked.connect(self.choose_archive)
        button_row.addWidget(choose)
        button_row.addStretch()
        card_layout.addLayout(button_row)
        hint = CaptionLabel("连接失败时仍可选择本地 ZIP 继续使用。", empty_card)
        hint.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(hint)
        layout.addWidget(empty_card)
        return page

    def _create_browser_page(self) -> QWidget:
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        filters = CardWidget(page)
        filter_layout = QHBoxLayout(filters)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(10)
        self.search_edit = SearchLineEdit(filters)
        self.search_edit.setPlaceholderText("搜索名称、型号或路径")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumWidth(260)
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_edit, 1)
        self.collection_combo = ComboBox(filters)
        self.collection_combo.setMinimumWidth(130)
        self.collection_combo.currentTextChanged.connect(self._collection_changed)
        filter_layout.addWidget(self.collection_combo)
        self.kind_combo = ComboBox(filters)
        self.kind_combo.setMinimumWidth(170)
        self.kind_combo.addItem("全部 3D 模型", userData="models")
        self.kind_combo.addItem("SolidWorks 零件", userData=".sldprt")
        self.kind_combo.addItem("SolidWorks 装配体", userData=".sldasm")
        self.kind_combo.addItem("通用 3D 格式", userData="neutral")
        self.kind_combo.addItem("图片与文档", userData="reference")
        self.kind_combo.addItem("全部文件", userData="all")
        self.kind_combo.currentTextChanged.connect(self._kind_changed)
        filter_layout.addWidget(self.kind_combo)
        self.result_count = CaptionLabel("0 个结果", filters)
        self.result_count.setMinimumWidth(82)
        self.result_count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        filter_layout.addWidget(self.result_count)
        layout.addWidget(filters)

        splitter = QSplitter(Qt.Horizontal, page)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._create_category_panel(splitter))
        splitter.addWidget(self._create_result_panel(splitter))
        splitter.addWidget(self._create_detail_panel(splitter))
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([180, 470, 280])
        layout.addWidget(splitter, 1)
        return page

    def _create_category_panel(self, parent: QWidget) -> QWidget:
        card = CardWidget(parent)
        card.setMinimumWidth(160)
        card.setMaximumWidth(220)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(StrongBodyLabel("分类", card))
        self.category_list = ListWidget(card)
        self.category_list.setFrameShape(QFrame.NoFrame)
        self.category_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.category_list.currentItemChanged.connect(self._apply_filters)
        layout.addWidget(self.category_list, 1)
        return card

    def _create_result_panel(self, parent: QWidget) -> QWidget:
        card = CardWidget(parent)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(8)
        title_row = QHBoxLayout()
        title_row.addWidget(StrongBodyLabel("零件与装配体", card))
        title_row.addStretch()
        self.refresh_button = PushButton(FluentIcon.SYNC, "重新索引", card)
        self.refresh_button.clicked.connect(self.reload_archive)
        title_row.addWidget(self.refresh_button)
        layout.addLayout(title_row)

        self.result_table = TableWidget(card)
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["名称", "类型", "大小"])
        self.result_table.verticalHeader().hide()
        self.result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.result_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSortingEnabled(True)
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.result_table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.result_table, 1)
        return card

    def _create_detail_panel(self, parent: QWidget) -> QWidget:
        card = CardWidget(parent)
        card.setMinimumWidth(250)
        card.setMaximumWidth(340)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(StrongBodyLabel("详细信息", card))

        self.preview_label = QLabel("选择一个零件\n查看详细信息", card)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setWordWrap(True)
        self.preview_label.setFixedHeight(150)
        self.preview_label.setStyleSheet(
            "border: 1px solid palette(mid); border-radius: 12px; "
            "background: palette(alternate-base); color: palette(mid);"
        )
        layout.addWidget(self.preview_label)
        layout.addSpacing(4)
        self.detail_name = StrongBodyLabel("未选择", card)
        self.detail_name.setWordWrap(True)
        layout.addWidget(self.detail_name)
        self.detail_kind = CaptionLabel("", card)
        layout.addWidget(self.detail_kind)
        self.detail_path = BodyLabel("", card)
        self.detail_path.setWordWrap(True)
        self.detail_path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.detail_path)
        self.detail_meta = CaptionLabel("", card)
        layout.addWidget(self.detail_meta)
        layout.addStretch()
        self.install_button = PrimaryPushButton(FluentIcon.DOWNLOAD, "下载此文件", card)
        self.install_button.clicked.connect(self.install_selected_file)
        self.install_button.setEnabled(False)
        layout.addWidget(self.install_button)
        self.export_folder_button = PushButton(FluentIcon.FOLDER_ADD, "导出所在目录…", card)
        self.export_folder_button.clicked.connect(self.export_selected_folder)
        self.export_folder_button.setEnabled(False)
        layout.addWidget(self.export_folder_button)
        return card

    def choose_archive(self) -> None:
        configured = self.settings.value(ARCHIVE_SETTING_KEY, "", type=str)
        start = str(Path(configured).parent) if configured else QStandardPaths.writableLocation(
            QStandardPaths.DownloadLocation
        )
        filename, _ = QFileDialog.getOpenFileName(self, "选择零件资料包", start, "ZIP 资料包 (*.zip)")
        if filename:
            self.mount_archive(Path(filename))

    def mount_archive(self, source: str | Path) -> None:
        if self._scan_thread and self._scan_thread.isRunning():
            return
        source_path = Path(source).expanduser()
        self.source_status.setText("正在读取离线包")
        self.source_status.setStyleSheet("color: palette(highlight); font-weight: 600;")
        self.source_meta.setText(source_path.name)
        self.source_progress.show()
        self.choose_source_button.setEnabled(False)
        self.open_source_button.setEnabled(False)
        self.content_stack.setCurrentWidget(self.empty_page)

        self._scan_thread = CatalogScanThread(source_path, self)
        self._scan_thread.catalog_ready.connect(self._catalog_loaded)
        self._scan_thread.scan_failed.connect(self._catalog_failed)
        self._scan_thread.finished.connect(self._scan_finished)
        self._scan_thread.start()

    def load_cloud_catalog(self) -> None:
        if self._cloud_thread and self._cloud_thread.isRunning():
            return
        self.source_status.setText("正在连接云端")
        self.source_status.setStyleSheet("color: palette(highlight); font-weight: 600;")
        self.source_meta.setText("正在同步目录…")
        self.source_progress.show()
        self.open_source_button.setEnabled(False)
        self.choose_source_button.setEnabled(False)

        self._cloud_thread = CloudCatalogThread(
            DEFAULT_CLOUD_CATALOG_URL,
            default_catalog_cache_path(),
            self,
        )
        self._cloud_thread.catalog_ready.connect(self._catalog_loaded)
        self._cloud_thread.load_failed.connect(self._cloud_catalog_failed)
        self._cloud_thread.finished.connect(self._cloud_load_finished)
        self._cloud_thread.start()

    def reload_archive(self) -> None:
        if self.catalog and not self.catalog.is_remote:
            self.mount_archive(self.catalog.source)
        else:
            self.load_cloud_catalog()

    def _cloud_catalog_failed(self, message: str) -> None:
        configured = self.settings.value(ARCHIVE_SETTING_KEY, "", type=str)
        fallback = Path(configured).expanduser() if configured else None
        if not fallback or not fallback.is_file():
            fallback = discover_part_archive() if self.auto_discover else None
        if fallback and fallback.is_file():
            InfoBar.warning(
                title="云端暂时不可用",
                content="正在切换到本地离线资料包。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=4500,
            )
            self.mount_archive(fallback)
            return
        self.catalog = None
        self._show_empty_state(message)

    def _scan_finished(self) -> None:
        self.source_progress.hide()
        self.choose_source_button.setEnabled(True)
        if self._scan_thread:
            self._scan_thread.deleteLater()
        self._scan_thread = None

    def _cloud_load_finished(self) -> None:
        if not (self._scan_thread and self._scan_thread.isRunning()):
            self.source_progress.hide()
            self.choose_source_button.setEnabled(True)
            self.open_source_button.setEnabled(True)
        if self._cloud_thread:
            self._cloud_thread.deleteLater()
        self._cloud_thread = None

    def _catalog_loaded(self, catalog: PartCatalog) -> None:
        self.catalog = catalog
        self.selected_entry = None
        self._entries_by_path = {entry.path: entry for entry in catalog.entries}
        self._preview_cache.clear()
        if not catalog.is_remote:
            self.settings.setValue(ARCHIVE_SETTING_KEY, str(catalog.source))
            self.settings.sync()

        mechanical = sum(1 for entry in catalog.entries if entry.collection == "机械" and entry.is_model)
        if catalog.is_remote:
            if catalog.cached:
                self.source_status.setText("● 使用离线缓存")
                self.source_status.setStyleSheet("color: #d09228; font-weight: 600;")
                self.source_meta.setText(f"{mechanical} 个模型 · 可刷新重连")
            else:
                self.source_status.setText("● 云端已同步")
                self.source_status.setStyleSheet("color: #2e9b63; font-weight: 600;")
                self.source_meta.setText(f"{mechanical} 个模型可用")
            self.install_button.setText("下载此文件")
            self.export_folder_button.setText("下载所在目录…")
        else:
            source_path = Path(catalog.source)
            self.source_status.setText("● 离线资料包")
            self.source_status.setStyleSheet("color: #d09228; font-weight: 600;")
            self.source_meta.setText(f"{mechanical} 个模型 · {source_path.name}")
            self.install_button.setText("安装此文件")
            self.export_folder_button.setText("导出所在目录…")
        self.open_source_button.setEnabled(True)

        self.collection_combo.blockSignals(True)
        self.collection_combo.clear()
        for collection in catalog.collections:
            count = sum(1 for entry in catalog.entries if entry.collection == collection)
            self.collection_combo.addItem(f"{collection}  {count}", userData=collection)
        preferred_index = 0
        for index in range(self.collection_combo.count()):
            if self.collection_combo.itemData(index) == "机械":
                preferred_index = index
                break
        self.collection_combo.setCurrentIndex(preferred_index)
        self.collection_combo.blockSignals(False)
        self._populate_categories()
        self._apply_filters()
        self.content_stack.setCurrentWidget(self.browser_page)

    def _catalog_failed(self, message: str) -> None:
        self.catalog = None
        self._show_empty_state()
        InfoBar.error(
            title="无法打开资料包",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=6000,
        )

    def _show_empty_state(self, message: str = "") -> None:
        self.content_stack.setCurrentWidget(self.empty_page)
        self.source_status.setText("云端暂时不可用")
        self.source_status.setStyleSheet("color: #c94f4f; font-weight: 600;")
        self.source_meta.setText(message or "刷新重试，或选择离线包")
        self.open_source_button.setEnabled(True)
        self.choose_source_button.setEnabled(True)

    def _current_collection(self) -> str:
        return self.collection_combo.currentData() or ""

    def _current_kind_filter(self) -> str:
        return self.kind_combo.currentData() or "models"

    def _collection_changed(self) -> None:
        self._populate_categories()
        self._apply_filters()

    def _kind_changed(self) -> None:
        self._populate_categories()
        self._apply_filters()

    def _matches_kind(self, entry: ArchiveEntry) -> bool:
        selection = self._current_kind_filter()
        if selection == "all":
            return True
        if selection == "models":
            return entry.is_model
        if selection in (".sldprt", ".sldasm"):
            return entry.extension == selection
        if selection == "neutral":
            return entry.is_model and entry.extension not in {".sldprt", ".sldasm"}
        if selection == "reference":
            return entry.extension in IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS
        return True

    def _populate_categories(self) -> None:
        if not self.catalog:
            return
        collection = self._current_collection()
        counts: dict[str, int] = {}
        for entry in self.catalog.entries:
            if entry.collection == collection and self._matches_kind(entry):
                counts[entry.category] = counts.get(entry.category, 0) + 1
        self.category_list.blockSignals(True)
        self.category_list.clear()
        all_item = QListWidgetItem(f"全部分类  {sum(counts.values())}")
        all_item.setData(Qt.UserRole, "")
        self.category_list.addItem(all_item)
        def category_sort_key(item: tuple[str, int]) -> tuple[int, str]:
            name = item[0]
            match = re.match(r"^(\d+)", name)
            return (int(match.group(1)) if match else 10_000, name)

        for category, count in sorted(counts.items(), key=category_sort_key):
            item = QListWidgetItem(f"{category}  {count}")
            item.setData(Qt.UserRole, category)
            item.setToolTip(category)
            self.category_list.addItem(item)
        self.category_list.setCurrentRow(0)
        self.category_list.blockSignals(False)

    def _apply_filters(self, *_args) -> None:
        if not self.catalog:
            return
        query = self.search_edit.text().strip().casefold()
        collection = self._current_collection()
        category_item = self.category_list.currentItem()
        category = category_item.data(Qt.UserRole) if category_item else ""
        entries = [
            entry
            for entry in self.catalog.entries
            if entry.collection == collection
            and (not category or entry.category == category)
            and self._matches_kind(entry)
            and (not query or query in entry.path.casefold() or query in entry.kind.casefold())
        ]

        self.result_table.setSortingEnabled(False)
        self.result_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            name_item = QTableWidgetItem(entry.name)
            name_item.setData(Qt.UserRole, entry.path)
            name_item.setToolTip(entry.path)
            self.result_table.setItem(row, 0, name_item)
            self.result_table.setItem(row, 1, QTableWidgetItem(entry.kind))
            size_item = QTableWidgetItem(format_size(entry.size))
            size_item.setData(Qt.UserRole, entry.size)
            self.result_table.setItem(row, 2, size_item)
            self.result_table.setRowHeight(row, 40)
        self.result_table.setSortingEnabled(True)
        self.result_count.setText(f"{len(entries)} 个结果")
        self.result_table.clearSelection()
        self._show_entry(None)

    def _selection_changed(self) -> None:
        selected = self.result_table.selectedItems()
        if not selected:
            self._show_entry(None)
            return
        row = selected[0].row()
        path_item = self.result_table.item(row, 0)
        path = path_item.data(Qt.UserRole) if path_item else None
        self._show_entry(self._entries_by_path.get(path))

    def _show_entry(self, entry: ArchiveEntry | None) -> None:
        self.selected_entry = entry
        enabled = entry is not None
        self.install_button.setEnabled(enabled)
        self.export_folder_button.setEnabled(enabled)
        if entry is None:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("选择一个零件\n查看详细信息")
            self.detail_name.setText("未选择")
            self.detail_kind.clear()
            self.detail_path.clear()
            self.detail_meta.clear()
            return

        self.detail_name.setText(entry.name)
        self.detail_kind.setText(f"{entry.kind} · {entry.category}")
        self.detail_path.setText(entry.path)
        folder_count = len(self.catalog.folder_entries(entry)) if self.catalog else 1
        self.detail_meta.setText(f"{format_size(entry.size)} · 所在目录 {folder_count} 个文件")

        pixmap = self._preview_cache.get(entry.preview_archive_name or "")
        if (
            pixmap is None
            and self.catalog
            and self.catalog.is_remote
            and entry.preview_url
        ):
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("正在加载预览…")
            self._start_preview_load(entry)
            return
        if pixmap is None:
            pixmap = self._preview_for_entry(entry)
        if pixmap and not pixmap.isNull():
            self.preview_label.setText("")
            self.preview_label.setPixmap(
                pixmap.scaled(210, 132, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.preview_label.setPixmap(QPixmap())
            suffix = entry.extension.lstrip(".").upper() or "FILE"
            self.preview_label.setText(f"{suffix}\n暂无预览图")

    def _preview_for_entry(self, entry: ArchiveEntry) -> QPixmap | None:
        if not self.catalog or not entry.preview_archive_name:
            return None
        cached = self._preview_cache.get(entry.preview_archive_name)
        if cached is not None:
            return cached
        data = self.catalog.read_preview(entry)
        if not data:
            return None
        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return None
        self._preview_cache[entry.preview_archive_name] = pixmap
        return pixmap

    def _start_preview_load(self, entry: ArchiveEntry) -> None:
        if not self.catalog or not entry.preview_url:
            return
        if self._preview_thread and self._preview_thread.isRunning():
            return
        self._preview_loading_path = entry.path
        self._preview_thread = PreviewLoadThread(self.catalog, entry, self)
        self._preview_thread.preview_ready.connect(self._remote_preview_ready)
        self._preview_thread.finished.connect(self._preview_load_finished)
        self._preview_thread.start()

    def _remote_preview_ready(self, entry_path: str, data: bytes | None) -> None:
        entry = self._entries_by_path.get(entry_path)
        if entry and entry.preview_archive_name:
            pixmap = QPixmap()
            if data:
                pixmap.loadFromData(data)
            # Cache a null pixmap as a negative result to avoid retry loops.
            self._preview_cache[entry.preview_archive_name] = pixmap
        if self.selected_entry and self.selected_entry.path == entry_path:
            # The cache now makes _show_entry render without starting a second request.
            self._show_entry(self.selected_entry)

    def _preview_load_finished(self) -> None:
        loaded_path = self._preview_loading_path
        if self._preview_thread:
            self._preview_thread.deleteLater()
        self._preview_thread = None
        self._preview_loading_path = ""
        if self.selected_entry and self.selected_entry.path != loaded_path:
            self._show_entry(self.selected_entry)

    def install_selected_file(self) -> None:
        if not self.catalog or not self.selected_entry:
            return
        self._start_export((self.selected_entry,), self.local_library_dir)

    def export_selected_folder(self) -> None:
        if not self.catalog or not self.selected_entry:
            return
        destination = QFileDialog.getExistingDirectory(
            self,
            "选择导出位置",
            QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation),
        )
        if not destination:
            return
        entries = self.catalog.folder_entries(self.selected_entry)
        folder_name = PurePosixPath(self.selected_entry.directory).name or "零件"
        self._start_export(entries, Path(destination), flatten_to_folder=folder_name)

    def _start_export(
        self,
        entries: tuple[ArchiveEntry, ...],
        destination: Path,
        *,
        flatten_to_folder: str | None = None,
    ) -> None:
        if not self.catalog or (self._export_thread and self._export_thread.isRunning()):
            return
        self.install_button.setEnabled(False)
        self.export_folder_button.setEnabled(False)
        self._export_thread = ArchiveExportThread(
            self.catalog,
            entries,
            destination,
            flatten_to_folder=flatten_to_folder,
            parent=self,
        )
        self._export_thread.progress_changed.connect(self._export_progress)
        self._export_thread.export_ready.connect(self._export_finished)
        self._export_thread.export_failed.connect(self._export_failed)
        self._export_thread.finished.connect(self._export_thread_finished)

        self._export_bar = InfoBar(
            icon=FluentIcon.DOWNLOAD,
            title="正在下载" if self.catalog.is_remote else "正在导出",
            content="正在准备文件…",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=-1,
        )
        progress = ProgressBar(self._export_bar)
        progress.setFixedWidth(150)
        progress.setValue(0)
        progress.setObjectName("partExportProgress")
        self._export_bar.addWidget(progress)
        self._export_bar.closeButton.clicked.connect(self._cancel_export)
        self._export_bar.show()
        self._export_thread.start()

    def _cancel_export(self) -> None:
        if self._export_thread and self._export_thread.isRunning():
            self._export_thread.cancel()
        # The InfoBar owns its closing animation and can be deleted before the
        # worker observes cancellation.  Stop touching its widgets immediately.
        self._export_bar = None

    def _export_progress(self, percentage: int, filename: str) -> None:
        if not self._export_bar:
            return
        self._export_bar.contentLabel.setText(filename)
        progress = self._export_bar.findChild(ProgressBar, "partExportProgress")
        if progress:
            progress.setValue(percentage)

    def _export_finished(self, exported: list[Path], cancelled: bool) -> None:
        if self._export_bar:
            self._export_bar.close()
            self._export_bar = None
        if cancelled:
            InfoBar.warning(
                title="已停止导出",
                content=f"已保留 {len(exported)} 个完成的文件。",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3500,
            )
            return
        InfoBar.success(
            title="下载完成" if self.catalog and self.catalog.is_remote else "导出完成",
            content=f"已保存 {len(exported)} 个文件。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=4000,
        )

    def _export_failed(self, message: str) -> None:
        if self._export_bar:
            self._export_bar.close()
            self._export_bar = None
        InfoBar.error(
            title="导出失败",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=6000,
        )

    def _export_thread_finished(self) -> None:
        self.install_button.setEnabled(self.selected_entry is not None)
        self.export_folder_button.setEnabled(self.selected_entry is not None)
        if self._export_thread:
            self._export_thread.deleteLater()
        self._export_thread = None

    def open_archive_location(self) -> None:
        if self.catalog and not self.catalog.is_remote:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.catalog.source).parent)))

    def open_local_library(self) -> None:
        self.local_library_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.local_library_dir)))

    def closeEvent(self, event) -> None:
        if self._export_thread and self._export_thread.isRunning():
            self._export_thread.cancel()
            self._export_thread.wait(3000)
        if self._scan_thread and self._scan_thread.isRunning():
            self._scan_thread.wait(3000)
        if self._cloud_thread and self._cloud_thread.isRunning():
            self._cloud_thread.wait(3000)
        if self._preview_thread and self._preview_thread.isRunning():
            self._preview_thread.wait(3000)
        super().closeEvent(event)
