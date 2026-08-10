from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
import json
from pathlib import Path, PurePosixPath
from typing import Callable, Sequence
from urllib.parse import quote, urljoin, urlparse
from zipfile import BadZipFile, ZipFile, ZipInfo

import requests


MODEL_EXTENSIONS = {
    ".sldprt",
    ".sldasm",
    ".step",
    ".stp",
    ".x_t",
    ".x_b",
    ".iges",
    ".igs",
    ".stl",
    ".obj",
}
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp", ".bmp"}
DOCUMENT_EXTENSIONS = {".pdf", ".md", ".txt", ".doc", ".docx", ".xls", ".xlsx"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".tar", ".gz"}
CODE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".s",
    ".py",
    ".cmake",
    ".uvprojx",
}


class PartLibraryError(RuntimeError):
    """Raised when a part archive cannot be indexed or safely extracted."""


def _decode_legacy_name(info: ZipInfo) -> str:
    """Repair GBK/GB18030 filenames stored as CP437 by older ZIP tools."""

    name = info.filename
    if info.flag_bits & 0x800:
        return name
    try:
        raw_name = name.encode("cp437")
    except UnicodeEncodeError:
        return name
    for encoding in ("gb18030", "utf-8"):
        try:
            return raw_name.decode(encoding)
        except UnicodeDecodeError:
            continue
    return name


def _normalise_member_path(info: ZipInfo) -> str:
    decoded = _decode_legacy_name(info).replace("\\", "/")
    path = PurePosixPath(decoded)
    if path.is_absolute() or ".." in path.parts:
        raise PartLibraryError(f"资料包包含不安全路径：{decoded}")
    parts = tuple(part for part in path.parts if part not in ("", "."))
    if not parts:
        return ""
    return PurePosixPath(*parts).as_posix()


def _entry_kind(extension: str) -> str:
    if extension == ".sldprt":
        return "SolidWorks 零件"
    if extension == ".sldasm":
        return "SolidWorks 装配体"
    if extension in MODEL_EXTENSIONS:
        return "通用 3D 模型"
    if extension in IMAGE_EXTENSIONS:
        return "预览图片"
    if extension in DOCUMENT_EXTENSIONS:
        return "文档"
    if extension in ARCHIVE_EXTENSIONS:
        return "压缩包"
    if extension in CODE_EXTENSIONS:
        return "代码/工程"
    return "其他文件"


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    """A decoded, safe view of one file inside the mounted archive."""

    archive_name: str
    path: str
    size: int
    compressed_size: int
    collection: str
    category: str
    subcategory: str
    extension: str
    kind: str
    preview_archive_name: str | None = None
    download_url: str | None = None
    preview_url: str | None = None

    @property
    def name(self) -> str:
        return PurePosixPath(self.path).name

    @property
    def directory(self) -> str:
        parent = PurePosixPath(self.path).parent
        return "" if str(parent) == "." else parent.as_posix()

    @property
    def is_model(self) -> bool:
        return self.extension in MODEL_EXTENSIONS


@dataclass(frozen=True, slots=True)
class PartCatalog:
    source: Path | str
    entries: tuple[ArchiveEntry, ...]
    archive_size: int
    unpacked_size: int
    source_kind: str = "archive"
    version: str = ""
    generated_at: str = ""
    cached: bool = False

    @classmethod
    def load(cls, source: str | Path) -> "PartCatalog":
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise PartLibraryError("找不到零件资料包，请重新选择 ZIP 文件。")
        if source_path.suffix.lower() != ".zip":
            raise PartLibraryError("目前仅支持 ZIP 格式的零件资料包。")

        provisional: list[ArchiveEntry] = []
        previews_by_directory: dict[str, str] = {}
        unpacked_size = 0
        try:
            with ZipFile(source_path) as archive:
                for info in archive.infolist():
                    decoded_path = _normalise_member_path(info)
                    if not decoded_path or info.is_dir() or decoded_path.endswith("/"):
                        continue
                    path = PurePosixPath(decoded_path)
                    # SolidWorks lock files are never useful catalogue entries.
                    if path.name.startswith("~$"):
                        continue
                    parts = path.parts
                    collection = parts[0] if parts else "未分类"
                    category = parts[1] if len(parts) > 2 else "未分类"
                    subcategory = parts[2] if len(parts) > 3 else ""
                    extension = path.suffix.lower()
                    entry = ArchiveEntry(
                        archive_name=info.filename,
                        path=decoded_path,
                        size=info.file_size,
                        compressed_size=info.compress_size,
                        collection=collection,
                        category=category,
                        subcategory=subcategory,
                        extension=extension,
                        kind=_entry_kind(extension),
                    )
                    provisional.append(entry)
                    unpacked_size += info.file_size
                    if extension in IMAGE_EXTENSIONS:
                        previews_by_directory.setdefault(entry.directory, info.filename)
        except (BadZipFile, OSError) as exc:
            raise PartLibraryError(f"无法读取零件资料包：{exc}") from exc

        if not provisional:
            raise PartLibraryError("资料包中没有可用文件。")

        entries = tuple(
            replace(entry, preview_archive_name=previews_by_directory.get(entry.directory))
            for entry in provisional
        )
        return cls(
            source=source_path,
            entries=entries,
            archive_size=source_path.stat().st_size,
            unpacked_size=unpacked_size,
        )

    @classmethod
    def load_remote(
        cls,
        catalog_url: str,
        *,
        cache_path: str | Path | None = None,
        timeout: float = 15.0,
        session=requests,
    ) -> "PartCatalog":
        parsed = urlparse(catalog_url)
        if parsed.scheme != "https":
            raise PartLibraryError("云端零件目录必须使用 HTTPS。")

        cached = False
        payload: dict
        try:
            response = session.get(catalog_url, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            if cache_path is not None:
                target = Path(cache_path).expanduser()
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = target.with_suffix(target.suffix + ".tmp")
                temporary.write_text(
                    json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                temporary.replace(target)
        except (requests.RequestException, ValueError, OSError) as exc:
            if cache_path is None or not Path(cache_path).is_file():
                raise PartLibraryError(f"无法连接云端零件库：{exc}") from exc
            try:
                payload = json.loads(Path(cache_path).read_text(encoding="utf-8"))
                cached = True
            except (OSError, ValueError) as cache_exc:
                raise PartLibraryError(f"云端目录与本地缓存均不可用：{cache_exc}") from cache_exc

        if payload.get("schema_version") != 1:
            raise PartLibraryError("云端零件目录版本不受支持。")
        version = str(payload.get("version") or "")
        base_url = str(payload.get("base_url") or urljoin(catalog_url, "files/"))
        if urlparse(base_url).scheme != "https":
            raise PartLibraryError("云端零件下载地址必须使用 HTTPS。")

        provisional: list[ArchiveEntry] = []
        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise PartLibraryError("云端零件目录格式无效。")
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            decoded_path = str(item.get("path") or "").replace("\\", "/")
            safe_path = PurePosixPath(decoded_path)
            if not decoded_path or safe_path.is_absolute() or ".." in safe_path.parts:
                raise PartLibraryError(f"云端目录包含不安全路径：{decoded_path}")
            parts = safe_path.parts
            extension = safe_path.suffix.lower()
            preview_path = str(item.get("preview") or "") or None
            if preview_path:
                preview_candidate = PurePosixPath(preview_path)
                if preview_candidate.is_absolute() or ".." in preview_candidate.parts:
                    raise PartLibraryError(f"云端目录包含不安全预览路径：{preview_path}")
            encoded_path = quote(decoded_path, safe="/")
            cache_key = f"?v={quote(version, safe='')}" if version else ""
            preview_url = (
                urljoin(base_url, quote(preview_path, safe="/")) + cache_key
                if preview_path
                else None
            )
            provisional.append(
                ArchiveEntry(
                    archive_name=decoded_path,
                    path=decoded_path,
                    size=max(0, int(item.get("size") or 0)),
                    compressed_size=max(0, int(item.get("size") or 0)),
                    collection=parts[0] if parts else "未分类",
                    category=parts[1] if len(parts) > 2 else "未分类",
                    subcategory=parts[2] if len(parts) > 3 else "",
                    extension=extension,
                    kind=_entry_kind(extension),
                    preview_archive_name=preview_path,
                    download_url=urljoin(base_url, encoded_path) + cache_key,
                    preview_url=preview_url,
                )
            )
        if not provisional:
            raise PartLibraryError("云端零件目录中没有可用文件。")
        total_size = sum(entry.size for entry in provisional)
        return cls(
            source=catalog_url,
            entries=tuple(provisional),
            archive_size=int(payload.get("total_size") or total_size),
            unpacked_size=total_size,
            source_kind="remote",
            version=version,
            generated_at=str(payload.get("generated_at") or ""),
            cached=cached,
        )

    @property
    def is_remote(self) -> bool:
        return self.source_kind == "remote"

    @property
    def collections(self) -> tuple[str, ...]:
        counts = Counter(entry.collection for entry in self.entries)
        return tuple(name for name, _ in counts.most_common())

    def entries_for_collection(self, collection: str) -> tuple[ArchiveEntry, ...]:
        return tuple(entry for entry in self.entries if entry.collection == collection)

    def categories(self, collection: str, models_only: bool = False) -> tuple[str, ...]:
        counts = Counter(
            entry.category
            for entry in self.entries
            if entry.collection == collection and (entry.is_model or not models_only)
        )
        return tuple(name for name, _ in counts.most_common())

    def folder_entries(self, entry: ArchiveEntry) -> tuple[ArchiveEntry, ...]:
        return tuple(item for item in self.entries if item.directory == entry.directory)

    def read_preview(self, entry: ArchiveEntry, limit: int = 16 * 1024 * 1024) -> bytes | None:
        if entry.preview_url:
            for _attempt in range(2):
                try:
                    response = requests.get(entry.preview_url, timeout=15)
                    response.raise_for_status()
                    if len(response.content) > limit:
                        return None
                    return response.content
                except requests.RequestException:
                    continue
            return None
        if not entry.preview_archive_name or not isinstance(self.source, Path):
            return None
        try:
            with ZipFile(self.source) as archive:
                info = archive.getinfo(entry.preview_archive_name)
                if info.file_size > limit:
                    return None
                return archive.read(info)
        except (BadZipFile, KeyError, OSError):
            return None


def _safe_destination(root: Path, relative_path: str) -> Path:
    destination = (root / Path(*PurePosixPath(relative_path).parts)).resolve()
    try:
        destination.relative_to(root.resolve())
    except ValueError as exc:
        raise PartLibraryError(f"拒绝导出不安全路径：{relative_path}") from exc
    return destination


def extract_entries(
    source: str | Path,
    entries: Sequence[ArchiveEntry],
    destination: str | Path,
    *,
    flatten_to_folder: str | None = None,
    progress: Callable[[int, int, str], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
) -> list[Path]:
    """Extract selected entries with decoded names and traversal protection.

    ``flatten_to_folder`` is used for the "export containing folder" action:
    dependencies remain together without recreating the full archive hierarchy.
    """

    target_root = Path(destination).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    selected = tuple(entries)
    total = sum(entry.size for entry in selected)
    completed = 0
    exported: list[Path] = []

    try:
        with ZipFile(Path(source)) as archive:
            for entry in selected:
                if cancelled and cancelled():
                    break
                if flatten_to_folder is None:
                    relative_path = entry.path
                else:
                    relative_path = PurePosixPath(flatten_to_folder, entry.name).as_posix()
                output_path = _safe_destination(target_root, relative_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry.archive_name) as source_file, output_path.open("wb") as output_file:
                    while True:
                        if cancelled and cancelled():
                            output_file.close()
                            output_path.unlink(missing_ok=True)
                            return exported
                        chunk = source_file.read(1024 * 1024)
                        if not chunk:
                            break
                        output_file.write(chunk)
                        completed += len(chunk)
                        if progress:
                            progress(completed, total, entry.name)
                exported.append(output_path)
    except (BadZipFile, KeyError, OSError) as exc:
        raise PartLibraryError(f"导出零件失败：{exc}") from exc
    return exported


def download_entries(
    entries: Sequence[ArchiveEntry],
    destination: str | Path,
    *,
    flatten_to_folder: str | None = None,
    progress: Callable[[int, int, str], None] | None = None,
    cancelled: Callable[[], bool] | None = None,
    timeout: float = 30.0,
    session=requests,
) -> list[Path]:
    """Download selected cloud entries while preserving the safe hierarchy."""

    target_root = Path(destination).expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)
    selected = tuple(entries)
    total = sum(entry.size for entry in selected)
    completed = 0
    downloaded: list[Path] = []

    for entry in selected:
        if cancelled and cancelled():
            break
        if not entry.download_url or urlparse(entry.download_url).scheme != "https":
            raise PartLibraryError(f"零件缺少安全下载地址：{entry.path}")
        relative_path = (
            entry.path
            if flatten_to_folder is None
            else PurePosixPath(flatten_to_folder, entry.name).as_posix()
        )
        output_path = _safe_destination(target_root, relative_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path = output_path.with_suffix(output_path.suffix + ".part")
        try:
            with session.get(entry.download_url, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                with partial_path.open("wb") as output_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if cancelled and cancelled():
                            partial_path.unlink(missing_ok=True)
                            return downloaded
                        if not chunk:
                            continue
                        output_file.write(chunk)
                        completed += len(chunk)
                        if progress:
                            progress(completed, total, entry.name)
            if entry.size and partial_path.stat().st_size != entry.size:
                partial_path.unlink(missing_ok=True)
                raise PartLibraryError(f"零件下载不完整：{entry.name}")
            partial_path.replace(output_path)
            downloaded.append(output_path)
        except requests.RequestException as exc:
            partial_path.unlink(missing_ok=True)
            raise PartLibraryError(f"下载零件失败：{entry.name}：{exc}") from exc
        except OSError as exc:
            partial_path.unlink(missing_ok=True)
            raise PartLibraryError(f"保存零件失败：{entry.name}：{exc}") from exc
    return downloaded


def format_size(size: int) -> str:
    value = float(size)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"
