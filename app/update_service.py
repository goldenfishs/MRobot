"""Platform-neutral update service shared by GUI and command-line frontends."""

from __future__ import annotations

import hashlib
import os
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import requests
from packaging.version import InvalidVersion, Version
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import __version__


DEFAULT_REPOSITORY = "goldenfishs/MRobot"
DEFAULT_UPDATE_ORIGIN = "https://updates.mrobot.cn"
GITHUB_API_VERSION = "2022-11-28"


class UpdateError(RuntimeError):
    """An update could not be checked, downloaded, verified or installed."""


class UnsupportedPlatformError(UpdateError):
    """There is no compatible update artifact for this runtime."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int
    sha256: str | None
    checksum_url: str | None = None


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    asset: ReleaseAsset
    release_notes: str
    release_date: str
    release_url: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data.update(
            download_url=self.asset.url,
            asset_name=self.asset.name,
            asset_size=self.asset.size,
            sha256=self.asset.sha256,
        )
        return data


@dataclass(frozen=True)
class DownloadedUpdate:
    info: UpdateInfo
    path: Path
    temporary_root: Path


@dataclass(frozen=True)
class InstallPlan:
    command: tuple[str, ...]
    description: str
    requires_exit: bool = True


ProgressCallback = Callable[[int, int], None]


def normalized_architecture(machine: str | None = None) -> str:
    value = (machine or platform.machine()).lower()
    if value in {"amd64", "x86_64"}:
        return "x64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value.replace(" ", "-")


def normalized_system(system: str | None = None) -> str:
    value = (system or platform.system()).lower()
    if value == "darwin":
        return "macos"
    if value in {"windows", "linux"}:
        return value
    raise UnsupportedPlatformError(f"不支持自动更新的平台：{value}")


def _asset_priority(name: str, system: str, arch: str) -> int | None:
    lower = name.lower()
    marker = f"-{system}-{arch}"
    if marker not in lower or lower.endswith(".sha256"):
        return None
    if system == "windows":
        if lower.endswith("-setup.exe"):
            return 0
        if lower.endswith(".zip"):
            return 1
    elif system == "macos" and lower.endswith(".dmg"):
        return 0
    elif system == "linux" and lower.endswith(".tar.gz"):
        return 0
    return None


def _parse_digest(value: object) -> str | None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return None
    digest = value.partition(":")[2].lower()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        return None
    return digest


class UpdateService:
    """Discover, verify and prepare native MRobot desktop updates."""

    def __init__(
        self,
        current_version: str = __version__,
        repository: str = DEFAULT_REPOSITORY,
        *,
        system: str | None = None,
        machine: str | None = None,
        executable: str | os.PathLike[str] | None = None,
        frozen: bool | None = None,
        session: requests.Session | None = None,
        manifest_urls: Iterable[str] | None = None,
    ) -> None:
        self.current_version = current_version
        self.repository = repository
        self.system = normalized_system(system)
        self.architecture = normalized_architecture(machine)
        self.executable = Path(executable or sys.executable).resolve()
        self.frozen = getattr(sys, "frozen", False) if frozen is None else frozen
        self.manifest_urls = tuple(
            manifest_urls
            or (
                f"{DEFAULT_UPDATE_ORIGIN}/stable/update.json",
                f"https://github.com/{repository}/releases/latest/download/update.json",
            )
        )
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": f"MRobot-Updater/{current_version}",
            }
        )
        if session is None:
            retry = Retry(
                total=3,
                connect=3,
                read=2,
                status=2,
                backoff_factor=0.6,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET"}),
            )
            adapter = HTTPAdapter(max_retries=retry)
            self.session.mount("https://", adapter)

    @property
    def latest_release_api(self) -> str:
        return f"https://api.github.com/repos/{self.repository}/releases/latest"

    @property
    def latest_manifest_url(self) -> str:
        return f"https://github.com/{self.repository}/releases/latest/download/update.json"

    def check(self) -> UpdateInfo | None:
        """Check the MRobot origin, GitHub manifest, then the legacy API."""
        manifest_errors: list[Exception] = []
        for manifest_url in self.manifest_urls:
            try:
                response = self.session.get(manifest_url, timeout=15)
                if response.status_code == 200:
                    update = self._update_from_manifest(response.json())
                    if update is not None:
                        return update
                    continue
                if response.status_code != 404:
                    response.raise_for_status()
            except (requests.RequestException, RuntimeError, ValueError, KeyError, InvalidVersion, UpdateError) as exc:
                manifest_errors.append(exc)
        try:
            return self._check_legacy_release_api()
        except UpdateError as exc:
            if manifest_errors:
                raise UpdateError("无法连接更新服务，请检查网络或代理设置，稍后再试") from exc
            raise

    def _update_from_manifest(self, manifest: dict[str, object]) -> UpdateInfo | None:
        try:
            if int(manifest.get("schema_version", 0)) != 1:
                raise UpdateError("不支持的更新清单版本")
            latest = str(manifest["version"]).removeprefix("v")
            if Version(latest) <= Version(self.current_version):
                return None
            raw_assets = manifest.get("assets")
            if not isinstance(raw_assets, list):
                raise UpdateError("更新清单缺少 assets")
            asset = self._select_asset(raw_assets)
            return UpdateInfo(
                version=latest,
                asset=asset,
                release_notes=str(manifest.get("release_notes") or ""),
                release_date=str(manifest.get("published_at") or ""),
                release_url=str(manifest.get("release_url") or ""),
            )
        except (KeyError, ValueError, InvalidVersion) as exc:
            raise UpdateError(f"更新清单无效：{exc}") from exc

    def _check_legacy_release_api(self) -> UpdateInfo | None:
        try:
            response = self.session.get(self.latest_release_api, timeout=15)
            if response.status_code in {403, 429}:
                raise UpdateError("GitHub 更新检查暂时受到频率限制，请稍后重试")
            response.raise_for_status()
            release = response.json()
            latest = str(release["tag_name"]).removeprefix("v")
            if Version(latest) <= Version(self.current_version):
                return None
        except UpdateError:
            raise
        except (requests.RequestException, KeyError, ValueError, InvalidVersion) as exc:
            raise UpdateError(f"检查更新失败：{exc}") from exc

        asset = self._select_asset(release.get("assets", ()))
        return UpdateInfo(
            version=latest,
            asset=asset,
            release_notes=str(release.get("body") or ""),
            release_date=str(release.get("published_at") or ""),
            release_url=str(release.get("html_url") or ""),
        )

    def _select_asset(self, assets: Iterable[dict[str, object]]) -> ReleaseAsset:
        items = [item for item in assets if isinstance(item, dict)]
        candidates: list[tuple[int, dict[str, object]]] = []
        for item in items:
            name = str(item.get("name") or "")
            priority = _asset_priority(name, self.system, self.architecture)
            if priority is not None:
                candidates.append((priority, item))
        if not candidates:
            raise UnsupportedPlatformError(
                f"该版本没有 {self.system}-{self.architecture} 安装包，请前往 Releases 手动下载"
            )
        item = min(candidates, key=lambda candidate: candidate[0])[1]
        name = str(item["name"])
        checksum_name = f"{name}.sha256"
        checksum_url = next(
            (
                str(candidate.get("browser_download_url"))
                for candidate in items
                if candidate.get("name") == checksum_name
            ),
            None,
        )
        return ReleaseAsset(
            name=name,
            url=str(item.get("browser_download_url") or item["url"]),
            size=int(item.get("size") or 0),
            sha256=_parse_digest(item.get("digest")) or _parse_digest(f"sha256:{item.get('sha256', '')}"),
            checksum_url=checksum_url,
        )

    def download(self, info: UpdateInfo, progress: ProgressCallback | None = None) -> DownloadedUpdate:
        if Path(info.asset.name).name != info.asset.name:
            raise UpdateError("发布资源名称不安全")
        temporary_root = Path(tempfile.mkdtemp(prefix="mrobot-update-"))
        target = temporary_root / info.asset.name
        digest = hashlib.sha256()
        downloaded = 0
        try:
            with self.session.get(info.asset.url, stream=True, timeout=(15, 120)) as response:
                response.raise_for_status()
                with target.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if not chunk:
                            continue
                        output.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)
                        if progress:
                            progress(downloaded, info.asset.size)
            if info.asset.size and downloaded != info.asset.size:
                raise UpdateError(f"下载大小不匹配：应为 {info.asset.size}，实际为 {downloaded}")
            expected = info.asset.sha256 or self._download_checksum(info.asset)
            if not expected:
                raise UpdateError("发布资源缺少 SHA-256，已拒绝安装")
            if digest.hexdigest() != expected:
                raise UpdateError("SHA-256 校验失败，已拒绝安装")
            return DownloadedUpdate(info=info, path=target, temporary_root=temporary_root)
        except Exception:
            shutil.rmtree(temporary_root, ignore_errors=True)
            raise

    def _download_checksum(self, asset: ReleaseAsset) -> str | None:
        if not asset.checksum_url:
            return None
        try:
            response = self.session.get(asset.checksum_url, timeout=15)
            response.raise_for_status()
            digest = response.text.strip().split()[0].lower()
        except (requests.RequestException, IndexError) as exc:
            raise UpdateError(f"下载校验文件失败：{exc}") from exc
        return digest if len(digest) == 64 and all(c in "0123456789abcdef" for c in digest) else None

    def prepare_install(self, downloaded: DownloadedUpdate, process_id: int | None = None) -> InstallPlan:
        if not self.frozen:
            raise UpdateError("源码运行模式不能覆盖自身，请使用 pip/git 更新或仅下载桌面安装包")
        pid = process_id or os.getpid()
        if self.system == "windows":
            return self._prepare_windows(downloaded, pid)
        if self.system == "macos":
            return self._prepare_macos(downloaded, pid)
        return self._prepare_linux(downloaded, pid)

    def _prepare_windows(self, downloaded: DownloadedUpdate, pid: int) -> InstallPlan:
        if not downloaded.path.name.lower().endswith("-setup.exe"):
            raise UpdateError("Windows 自动安装需要 setup.exe 安装包")
        script = downloaded.temporary_root / "install-mrobot.ps1"
        script.write_text(
            """param([string]$Installer, [string]$TempRoot)
$process = Start-Process -FilePath $Installer -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CLOSEAPPLICATIONS','/RESTARTAPPLICATIONS' -Wait -PassThru
if ($process.ExitCode -eq 0) { Remove-Item -LiteralPath $TempRoot -Recurse -Force -ErrorAction SilentlyContinue }
exit $process.ExitCode
""",
            encoding="utf-8-sig",
        )
        return InstallPlan(
            command=(
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
                "-Installer",
                str(downloaded.path),
                "-TempRoot",
                str(downloaded.temporary_root),
            ),
            description=f"安装 MRobot {downloaded.info.version} 并重新启动",
        )

    def _prepare_macos(self, downloaded: DownloadedUpdate, pid: int) -> InstallPlan:
        app_bundle = next((path for path in (self.executable, *self.executable.parents) if path.suffix == ".app"), None)
        if app_bundle is None:
            raise UpdateError("无法确定当前 MRobot.app 的位置")
        helper = downloaded.temporary_root / "install-mrobot.sh"
        helper.write_text(
            r"""#!/bin/sh
set -eu
pid="$1"
package="$2"
target="$3"
temp_root="$4"
while kill -0 "$pid" 2>/dev/null; do sleep 1; done
mount_output="$(hdiutil attach "$package" -nobrowse -readonly)"
mount_point="$(printf '%s\n' "$mount_output" | sed -n 's|^.*\t\(/Volumes/.*\)$|\1|p' | tail -n 1)"
if [ -z "$mount_point" ] || [ ! -d "$mount_point/MRobot.app" ]; then exit 2; fi
backup="${target}.mrobot-old"
rm -rf "$backup"
mv "$target" "$backup"
if ditto "$mount_point/MRobot.app" "$target"; then
    rm -rf "$backup"
    hdiutil detach "$mount_point" -quiet || true
    open "$target"
    rm -rf "$temp_root"
else
    rm -rf "$target"
    mv "$backup" "$target"
    hdiutil detach "$mount_point" -quiet || true
    open "$target"
    exit 3
fi
""",
            encoding="utf-8",
        )
        helper.chmod(0o700)
        arguments = (str(helper), str(pid), str(downloaded.path), str(app_bundle), str(downloaded.temporary_root))
        if os.access(app_bundle.parent, os.W_OK) and os.access(app_bundle, os.W_OK):
            command = ("/bin/sh", *arguments)
        else:
            shell_command = " ".join(shlex.quote(value) for value in arguments)
            apple_script = f'do shell script "{shell_command.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}" with administrator privileges'
            command = ("/usr/bin/osascript", "-e", apple_script)
        return InstallPlan(command=command, description=f"安装 MRobot {downloaded.info.version} 并重新启动")

    def _prepare_linux(self, downloaded: DownloadedUpdate, pid: int) -> InstallPlan:
        if not os.access(self.executable.parent, os.W_OK) or not os.access(self.executable, os.W_OK):
            raise UpdateError("当前程序目录不可写，请手动解压更新包或将 MRobot 安装到用户目录")
        stage = downloaded.temporary_root / "stage"
        stage.mkdir()
        self._safe_extract_tar(downloaded.path, stage)
        replacement = stage / "MRobot" / "MRobot"
        if not replacement.is_file():
            raise UpdateError("Linux 更新包中缺少 MRobot 可执行文件")
        replacement.chmod(replacement.stat().st_mode | 0o111)
        helper = downloaded.temporary_root / "install-mrobot.sh"
        helper.write_text(
            """#!/bin/sh
set -eu
pid="$1"
source="$2"
target="$3"
temp_root="$4"
while kill -0 "$pid" 2>/dev/null; do sleep 1; done
backup="${target}.mrobot-old"
rm -f "$backup"
mv "$target" "$backup"
if cp "$source" "$target" && chmod +x "$target"; then
    "$target" >/dev/null 2>&1 &
    rm -f "$backup"
    rm -rf "$temp_root"
else
    rm -f "$target"
    mv "$backup" "$target"
    "$target" >/dev/null 2>&1 &
    exit 3
fi
""",
            encoding="utf-8",
        )
        helper.chmod(0o700)
        return InstallPlan(
            command=(
                "/bin/sh",
                str(helper),
                str(pid),
                str(replacement),
                str(self.executable),
                str(downloaded.temporary_root),
            ),
            description=f"安装 MRobot {downloaded.info.version} 并重新启动",
        )

    @staticmethod
    def _safe_extract_tar(archive_path: Path, destination: Path) -> None:
        with tarfile.open(archive_path, "r:gz") as archive:
            destination_root = destination.resolve()
            for member in archive.getmembers():
                target = (destination / member.name).resolve()
                if not target.is_relative_to(destination_root):
                    raise UpdateError("更新包包含不安全路径")
                if member.issym() or member.islnk():
                    raise UpdateError("更新包包含不允许的链接")
            if sys.version_info >= (3, 12):
                archive.extractall(destination, filter="data")
            else:
                archive.extractall(destination)

    def launch_install(self, plan: InstallPlan) -> subprocess.Popen[bytes]:
        kwargs: dict[str, object] = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if self.system == "windows":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        try:
            return subprocess.Popen(plan.command, **kwargs)  # type: ignore[arg-type]
        except OSError as exc:
            raise UpdateError(f"无法启动更新安装程序：{exc}") from exc
