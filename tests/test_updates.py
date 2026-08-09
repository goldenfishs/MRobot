from __future__ import annotations

import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path

import pytest
import requests

from app.update_service import (
    DownloadedUpdate,
    ReleaseAsset,
    UnsupportedPlatformError,
    UpdateError,
    UpdateInfo,
    UpdateService,
)
from tools.create_update_manifest import create_manifest


class FakeResponse:
    def __init__(self, *, payload=None, content: bytes = b"", status: int = 200):
        self.payload = payload
        self.content = content
        self.status_code = status
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size: int):
        for offset in range(0, len(self.content), chunk_size):
            yield self.content[offset : offset + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}
        self.calls = []

    def get(self, url, **_kwargs):
        self.calls.append(url)
        response = self.responses.get(url, FakeResponse(status=404))
        if isinstance(response, Exception):
            raise response
        return response


def release_payload(version: str = "0.4.0") -> dict:
    names = (
        f"MRobot-v{version}-macos-arm64.dmg",
        f"MRobot-v{version}-windows-x64.zip",
        f"MRobot-v{version}-windows-x64-setup.exe",
        f"MRobot-v{version}-linux-x64.tar.gz",
    )
    return {
        "tag_name": f"v{version}",
        "body": "notes",
        "published_at": "2026-08-09T00:00:00Z",
        "html_url": "https://github.com/goldenfishs/MRobot/releases/latest",
        "assets": [
            {
                "name": name,
                "browser_download_url": f"https://download/{name}",
                "size": 4,
                "digest": "sha256:" + "a" * 64,
            }
            for name in names
        ],
    }


def test_check_prefers_rate_limit_free_update_manifest() -> None:
    manifest_url = "https://updates.mrobot.cn/stable/update.json"
    manifest = {
        "schema_version": 1,
        "version": "0.4.0",
        "published_at": "2026-08-09T00:00:00Z",
        "release_url": "https://github.com/goldenfishs/MRobot/releases/tag/v0.4.0",
        "assets": [
            {
                "name": "MRobot-v0.4.0-macos-arm64.dmg",
                "url": "https://download/macos.dmg",
                "size": 100,
                "sha256": "b" * 64,
            }
        ],
    }
    service = UpdateService(
        "0.3.3",
        system="Darwin",
        machine="arm64",
        session=FakeSession({manifest_url: FakeResponse(payload=manifest)}),
    )
    update = service.check()
    assert update is not None
    assert update.asset.sha256 == "b" * 64
    assert update.asset.url == "https://download/macos.dmg"


def test_origin_tls_failure_falls_back_to_github_manifest() -> None:
    origin = "https://updates.mrobot.cn/stable/update.json"
    manifest_url = "https://github.com/goldenfishs/MRobot/releases/latest/download/update.json"
    api = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
    payload = release_payload()
    manifest = {
        "schema_version": 1,
        "version": "0.4.0",
        "assets": [
            {
                "name": asset["name"],
                "url": asset["browser_download_url"],
                "size": asset["size"],
                "sha256": "a" * 64,
            }
            for asset in payload["assets"]
        ],
    }
    session = FakeSession(
        {
            origin: requests.exceptions.SSLError("TLS EOF"),
            manifest_url: FakeResponse(payload=manifest),
            api: FakeResponse(payload=payload),
        }
    )
    service = UpdateService(
        "0.3.3",
        system="Darwin",
        machine="arm64",
        session=session,
    )
    update = service.check()
    assert update is not None
    assert update.version == "0.4.0"
    assert api not in session.calls


def test_all_update_endpoints_failing_returns_short_network_message() -> None:
    origin = "https://updates.mrobot.cn/stable/update.json"
    manifest_url = "https://github.com/goldenfishs/MRobot/releases/latest/download/update.json"
    api = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
    ssl_error = requests.exceptions.SSLError("very long TLS implementation detail")
    service = UpdateService(
        "0.3.3",
        system="Darwin",
        machine="arm64",
        session=FakeSession({origin: ssl_error, manifest_url: ssl_error, api: ssl_error}),
    )
    with pytest.raises(UpdateError, match="网络或代理") as captured:
        service.check()
    assert "implementation detail" not in str(captured.value)


def test_legacy_api_rate_limit_has_friendly_message() -> None:
    api = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
    service = UpdateService(
        "0.3.3",
        system="Darwin",
        machine="arm64",
        session=FakeSession({api: FakeResponse(status=403)}),
    )
    with pytest.raises(UpdateError, match="频率限制") as captured:
        service.check()
    assert "api.github.com" not in str(captured.value)


def test_release_manifest_contains_all_native_artifacts_and_digests(tmp_path: Path) -> None:
    for name in (
        "MRobot-v0.4.0-macos-arm64.dmg",
        "MRobot-v0.4.0-windows-x64.zip",
        "MRobot-v0.4.0-windows-x64-setup.exe",
        "MRobot-v0.4.0-linux-x64.tar.gz",
    ):
        (tmp_path / name).write_bytes(name.encode())
    target = create_manifest(tmp_path, "goldenfishs/MRobot", "v0.4.0")
    manifest = json.loads(target.read_text(encoding="utf-8"))
    assert manifest["version"] == "0.4.0"
    assert len(manifest["assets"]) == 4
    assert all(len(asset["sha256"]) == 64 for asset in manifest["assets"])
    assert (tmp_path / "update.json.sha256").is_file()

    mirror = create_manifest(
        tmp_path,
        "goldenfishs/MRobot",
        "v0.4.0",
        "https://updates.mrobot.cn/releases/v0.4.0",
    )
    mirror_manifest = json.loads(mirror.read_text(encoding="utf-8"))
    assert all(
        asset["url"].startswith("https://updates.mrobot.cn/releases/v0.4.0/")
        for asset in mirror_manifest["assets"]
    )


@pytest.mark.parametrize(
    ("system", "machine", "suffix"),
    (
        ("Darwin", "arm64", "macos-arm64.dmg"),
        ("Windows", "AMD64", "windows-x64-setup.exe"),
        ("Linux", "x86_64", "linux-x64.tar.gz"),
    ),
)
def test_check_selects_exact_native_asset(system: str, machine: str, suffix: str) -> None:
    api = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
    service = UpdateService(
        "0.3.3",
        system=system,
        machine=machine,
        session=FakeSession({api: FakeResponse(payload=release_payload())}),
    )
    update = service.check()
    assert update is not None
    assert update.asset.name.endswith(suffix)


def test_check_rejects_wrong_architecture_instead_of_falling_back() -> None:
    api = "https://api.github.com/repos/goldenfishs/MRobot/releases/latest"
    service = UpdateService(
        "0.3.3",
        system="Darwin",
        machine="x86_64",
        session=FakeSession({api: FakeResponse(payload=release_payload())}),
    )
    with pytest.raises(UnsupportedPlatformError):
        service.check()


def test_download_requires_matching_sha256() -> None:
    content = b"safe update"
    url = "https://download/update.tar.gz"
    asset = ReleaseAsset("MRobot-v0.4.0-linux-x64.tar.gz", url, len(content), hashlib.sha256(content).hexdigest())
    info = UpdateInfo("0.4.0", asset, "", "", "")
    service = UpdateService("0.3.3", system="Linux", machine="x86_64", session=FakeSession({url: FakeResponse(content=content)}))
    downloaded = service.download(info)
    try:
        assert downloaded.path.read_bytes() == content
    finally:
        shutil.rmtree(downloaded.temporary_root)


def test_download_removes_temporary_files_on_bad_digest() -> None:
    content = b"tampered"
    url = "https://download/update.tar.gz"
    asset = ReleaseAsset("MRobot-v0.4.0-linux-x64.tar.gz", url, len(content), "0" * 64)
    info = UpdateInfo("0.4.0", asset, "", "", "")
    service = UpdateService("0.3.3", system="Linux", machine="x86_64", session=FakeSession({url: FakeResponse(content=content)}))
    with pytest.raises(UpdateError, match="SHA-256"):
        service.download(info)


def _linux_download(tmp_path: Path, member_name: str = "MRobot/MRobot") -> DownloadedUpdate:
    archive_path = tmp_path / "MRobot-v0.4.0-linux-x64.tar.gz"
    payload = b"executable"
    with tarfile.open(archive_path, "w:gz") as archive:
        member = tarfile.TarInfo(member_name)
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    asset = ReleaseAsset(archive_path.name, "https://download/linux", archive_path.stat().st_size, "a" * 64)
    return DownloadedUpdate(UpdateInfo("0.4.0", asset, "", "", ""), archive_path, tmp_path)


def test_linux_install_is_deferred_until_current_process_exits(tmp_path: Path) -> None:
    executable = tmp_path / "installed" / "MRobot"
    executable.parent.mkdir()
    executable.write_bytes(b"old")
    executable.chmod(0o700)
    service = UpdateService("0.3.3", system="Linux", machine="x86_64", executable=executable, frozen=True)
    plan = service.prepare_install(_linux_download(tmp_path), process_id=1234)
    assert plan.requires_exit
    assert plan.command[0] == "/bin/sh"
    assert "1234" in plan.command
    assert "while kill -0" in Path(plan.command[1]).read_text(encoding="utf-8")


def test_linux_install_rejects_archive_traversal(tmp_path: Path) -> None:
    executable = tmp_path / "MRobot"
    executable.write_bytes(b"old")
    executable.chmod(0o700)
    service = UpdateService("0.3.3", system="Linux", machine="x86_64", executable=executable, frozen=True)
    with pytest.raises(UpdateError, match="不安全路径"):
        service.prepare_install(_linux_download(tmp_path, "../outside"))


def test_windows_installer_uses_detached_inno_setup(tmp_path: Path) -> None:
    installer = tmp_path / "MRobot-v0.4.0-windows-x64-setup.exe"
    installer.write_bytes(b"setup")
    asset = ReleaseAsset(installer.name, "https://download/setup", 5, "a" * 64)
    downloaded = DownloadedUpdate(UpdateInfo("0.4.0", asset, "", "", ""), installer, tmp_path)
    service = UpdateService("0.3.3", system="Windows", machine="AMD64", frozen=True)
    plan = service.prepare_install(downloaded)
    assert plan.command[0] == "powershell.exe"
    script = Path(plan.command[plan.command.index("-File") + 1]).read_text(encoding="utf-8-sig")
    assert "/VERYSILENT" in script
    assert "Start-Process" in script


def test_macos_install_replaces_app_only_after_exit(tmp_path: Path) -> None:
    executable = tmp_path / "MRobot.app" / "Contents" / "MacOS" / "MRobot"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"old")
    package = tmp_path / "MRobot-v0.4.0-macos-arm64.dmg"
    package.write_bytes(b"dmg")
    asset = ReleaseAsset(package.name, "https://download/macos", 3, "a" * 64)
    downloaded = DownloadedUpdate(UpdateInfo("0.4.0", asset, "", "", ""), package, tmp_path)
    service = UpdateService("0.3.3", system="Darwin", machine="arm64", executable=executable, frozen=True)
    plan = service.prepare_install(downloaded, process_id=4321)
    assert plan.command[0] == "/bin/sh"
    helper = Path(plan.command[1]).read_text(encoding="utf-8")
    assert "while kill -0" in helper
    assert "ditto" in helper
    assert ".mrobot-old" in helper
