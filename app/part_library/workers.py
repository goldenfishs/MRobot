from __future__ import annotations

from pathlib import Path
from threading import Event

from PyQt5.QtCore import QThread, pyqtSignal

from .catalog import ArchiveEntry, PartCatalog, download_entries, extract_entries


class CatalogScanThread(QThread):
    catalog_ready = pyqtSignal(object)
    scan_failed = pyqtSignal(str)

    def __init__(self, source: str | Path, parent=None):
        super().__init__(parent)
        self.source = Path(source)

    def run(self) -> None:
        try:
            self.catalog_ready.emit(PartCatalog.load(self.source))
        except Exception as exc:
            self.scan_failed.emit(str(exc))


class CloudCatalogThread(QThread):
    catalog_ready = pyqtSignal(object)
    load_failed = pyqtSignal(str)

    def __init__(self, catalog_url: str, cache_path: str | Path, parent=None):
        super().__init__(parent)
        self.catalog_url = catalog_url
        self.cache_path = Path(cache_path)

    def run(self) -> None:
        try:
            self.catalog_ready.emit(
                PartCatalog.load_remote(self.catalog_url, cache_path=self.cache_path)
            )
        except Exception as exc:
            self.load_failed.emit(str(exc))


class ArchiveExportThread(QThread):
    progress_changed = pyqtSignal(int, str)
    export_ready = pyqtSignal(object, bool)
    export_failed = pyqtSignal(str)

    def __init__(
        self,
        catalog: PartCatalog,
        entries: tuple[ArchiveEntry, ...],
        destination: str | Path,
        *,
        flatten_to_folder: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.catalog = catalog
        self.entries = entries
        self.destination = Path(destination)
        self.flatten_to_folder = flatten_to_folder
        self._cancelled = Event()

    def cancel(self) -> None:
        self._cancelled.set()

    def run(self) -> None:
        def report(completed: int, total: int, name: str) -> None:
            percentage = 100 if total <= 0 else min(100, int(completed * 100 / total))
            self.progress_changed.emit(percentage, name)

        try:
            if self.catalog.is_remote:
                exported = download_entries(
                    self.entries,
                    self.destination,
                    flatten_to_folder=self.flatten_to_folder,
                    progress=report,
                    cancelled=self._cancelled.is_set,
                )
            else:
                exported = extract_entries(
                    self.catalog.source,
                    self.entries,
                    self.destination,
                    flatten_to_folder=self.flatten_to_folder,
                    progress=report,
                    cancelled=self._cancelled.is_set,
                )
            self.export_ready.emit(exported, self._cancelled.is_set())
        except Exception as exc:
            self.export_failed.emit(str(exc))


class PreviewLoadThread(QThread):
    preview_ready = pyqtSignal(str, object)

    def __init__(self, catalog: PartCatalog, entry: ArchiveEntry, parent=None):
        super().__init__(parent)
        self.catalog = catalog
        self.entry = entry

    def run(self) -> None:
        self.preview_ready.emit(self.entry.path, self.catalog.read_preview(self.entry))
