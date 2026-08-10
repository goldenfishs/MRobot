from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
import requests

from app.part_library.catalog import (
    ArchiveEntry,
    PartCatalog,
    PartLibraryError,
    _decode_legacy_name,
    download_entries,
    extract_entries,
    format_size,
)
from tools.build_part_catalog import build_catalog


class FakeCatalogResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


class FakeCatalogSession:
    def __init__(self, payload: dict):
        self.payload = payload

    def get(self, _url: str, timeout: float):
        assert timeout > 0
        return FakeCatalogResponse(self.payload)


class FakeDownloadResponse:
    def __init__(self, content: bytes):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        pass

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]


class FakeDownloadSession:
    def __init__(self, content: bytes):
        self.content = content

    def get(self, _url: str, stream: bool, timeout: float):
        assert stream and timeout > 0
        return FakeDownloadResponse(self.content)


class FakeOfflineSession:
    def get(self, _url: str, timeout: float):
        assert timeout > 0
        raise requests.ConnectionError("offline")


def _build_archive(path: Path) -> Path:
    with ZipFile(path, "w") as archive:
        archive.writestr("机械/1.标准件/导轨/HGH20.SLDPRT", b"part")
        archive.writestr("机械/1.标准件/导轨/HG系列.SLDASM", b"assembly")
        archive.writestr("机械/1.标准件/导轨/系列图解.png", b"not-a-real-png")
        archive.writestr("机械/2.电机/电机.step", b"step")
        archive.writestr("附带资料/说明/README.txt", "说明".encode())
    return path


def test_catalog_classifies_models_and_matches_folder_preview(tmp_path: Path) -> None:
    catalog = PartCatalog.load(_build_archive(tmp_path / "parts.zip"))

    assert catalog.collections == ("机械", "附带资料")
    assert catalog.categories("机械", models_only=True) == ("1.标准件", "2.电机")
    part = next(entry for entry in catalog.entries if entry.name == "HGH20.SLDPRT")
    assert part.kind == "SolidWorks 零件"
    assert part.is_model
    assert part.preview_archive_name == "机械/1.标准件/导轨/系列图解.png"
    assert len(catalog.folder_entries(part)) == 3


def test_catalog_repairs_legacy_gb18030_filename() -> None:
    original = "机械/零件.SLDPRT"
    mojibake = original.encode("gb18030").decode("cp437")
    fake_info = SimpleNamespace(filename=mojibake, flag_bits=0)
    assert _decode_legacy_name(fake_info) == original


def test_catalog_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.SLDPRT", b"unsafe")

    with pytest.raises(PartLibraryError, match="不安全路径"):
        PartCatalog.load(archive_path)


def test_selected_entries_extract_with_decoded_hierarchy(tmp_path: Path) -> None:
    archive_path = _build_archive(tmp_path / "parts.zip")
    catalog = PartCatalog.load(archive_path)
    part = next(entry for entry in catalog.entries if entry.name == "HGH20.SLDPRT")

    exported = extract_entries(archive_path, (part,), tmp_path / "library")

    assert exported == [tmp_path / "library/机械/1.标准件/导轨/HGH20.SLDPRT"]
    assert exported[0].read_bytes() == b"part"


def test_folder_export_keeps_dependencies_together(tmp_path: Path) -> None:
    archive_path = _build_archive(tmp_path / "parts.zip")
    catalog = PartCatalog.load(archive_path)
    assembly = next(entry for entry in catalog.entries if entry.extension == ".sldasm")
    folder = catalog.folder_entries(assembly)

    exported = extract_entries(
        archive_path,
        folder,
        tmp_path / "export",
        flatten_to_folder="导轨",
    )

    assert len(exported) == 3
    assert (tmp_path / "export/导轨/HGH20.SLDPRT").is_file()
    assert (tmp_path / "export/导轨/HG系列.SLDASM").is_file()


def test_remote_catalog_builds_safe_encoded_download_urls(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "version": "test-v1",
        "generated_at": "2026-08-10T00:00:00Z",
        "base_url": "https://download.qutmrobot.cn/parts/v1/files/",
        "entries": [
            {
                "path": "机械/电机/达妙电机.SLDPRT",
                "size": 4,
                "preview": "机械/电机/预览图.jpg",
            }
        ],
    }
    catalog = PartCatalog.load_remote(
        "https://download.qutmrobot.cn/parts/v1/catalog.json",
        cache_path=tmp_path / "catalog.json",
        session=FakeCatalogSession(payload),
    )

    assert catalog.is_remote
    assert not catalog.cached
    assert catalog.version == "test-v1"
    entry = catalog.entries[0]
    assert "%E6%9C%BA%E6%A2%B0" in entry.download_url
    assert entry.download_url.endswith(".SLDPRT?v=test-v1")
    assert entry.preview_url.endswith(".jpg?v=test-v1")
    assert (tmp_path / "catalog.json").is_file()


def test_remote_catalog_rejects_insecure_origin() -> None:
    with pytest.raises(PartLibraryError, match="HTTPS"):
        PartCatalog.load_remote("http://example.com/catalog.json")


def test_remote_catalog_uses_cached_manifest_when_offline(tmp_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "version": "cached-v1",
        "base_url": "https://download.qutmrobot.cn/parts/v1/files/",
        "entries": [{"path": "机械/零件.SLDPRT", "size": 4}],
    }
    cache_path = tmp_path / "catalog.json"
    PartCatalog.load_remote(
        "https://download.qutmrobot.cn/parts/v1/catalog.json",
        cache_path=cache_path,
        session=FakeCatalogSession(payload),
    )

    catalog = PartCatalog.load_remote(
        "https://download.qutmrobot.cn/parts/v1/catalog.json",
        cache_path=cache_path,
        session=FakeOfflineSession(),
    )

    assert catalog.cached
    assert catalog.version == "cached-v1"
    assert catalog.entries[0].name == "零件.SLDPRT"


def test_cloud_entry_downloads_to_safe_local_path(tmp_path: Path) -> None:
    entry = ArchiveEntry(
        archive_name="机械/零件.SLDPRT",
        path="机械/零件.SLDPRT",
        size=4,
        compressed_size=4,
        collection="机械",
        category="未分类",
        subcategory="",
        extension=".sldprt",
        kind="SolidWorks 零件",
        download_url="https://download.qutmrobot.cn/parts/v1/files/part",
    )
    output = download_entries(
        (entry,),
        tmp_path / "downloads",
        session=FakeDownloadSession(b"part"),
    )
    assert output == [tmp_path / "downloads/机械/零件.SLDPRT"]
    assert output[0].read_bytes() == b"part"


def test_static_cloud_catalog_builder_extracts_only_requested_collection(tmp_path: Path) -> None:
    source = _build_archive(tmp_path / "parts.zip")
    manifest_path = build_catalog(source, tmp_path / "cloud")
    payload = __import__("json").loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["file_count"] == 4
    assert payload["model_count"] == 3
    assert all(item["path"].startswith("机械/") for item in payload["entries"])
    assert (tmp_path / "cloud/files/机械/1.标准件/导轨/HGH20.SLDPRT").is_file()


@pytest.mark.parametrize(
    ("size", "display"),
    [(0, "0 B"), (1024, "1.0 KB"), (3 * 1024**3, "3.0 GB")],
)
def test_format_size(size: int, display: str) -> None:
    assert format_size(size) == display
