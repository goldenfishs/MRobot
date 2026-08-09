from __future__ import annotations

import argparse
import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE_DIST = ROOT / "release-dist"


def project_version() -> str:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def release_version() -> str:
    configured = os.environ.get("MROBOT_RELEASE_VERSION", "").removeprefix("v")
    version = project_version()
    if configured and configured != version:
        raise SystemExit(f"release version {configured} does not match pyproject version {version}")
    return version


def architecture() -> str:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return "x64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    return machine.replace(" ", "-")


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build() -> None:
    run(sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "MRobot.spec")


def write_checksum(artifact: Path) -> Path:
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    target = artifact.with_suffix(artifact.suffix + ".sha256")
    target.write_text(f"{digest}  {artifact.name}\n", encoding="utf-8")
    return target


def package_macos(version: str, arch: str) -> Path:
    app = DIST / "MRobot.app"
    if not app.is_dir():
        raise SystemExit(f"missing macOS app: {app}")
    run("codesign", "--force", "--deep", "--sign", "-", str(app))
    run("codesign", "--verify", "--deep", "--strict", str(app))
    target = RELEASE_DIST / f"MRobot-v{version}-macos-{arch}.dmg"
    with tempfile.TemporaryDirectory(prefix="mrobot-dmg-") as temporary:
        stage = Path(temporary)
        run("ditto", str(app), str(stage / "MRobot.app"))
        (stage / "Applications").symlink_to("/Applications")
        run(
            "hdiutil",
            "create",
            "-volname",
            f"MRobot {version}",
            "-srcfolder",
            str(stage),
            "-ov",
            "-format",
            "UDZO",
            str(target),
        )
    return target


def package_windows(version: str, arch: str) -> Path:
    executable = DIST / "MRobot.exe"
    if not executable.is_file():
        raise SystemExit(f"missing Windows executable: {executable}")
    target = RELEASE_DIST / f"MRobot-v{version}-windows-{arch}.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(executable, "MRobot/MRobot.exe")
    return target


def package_linux(version: str, arch: str) -> Path:
    executable = DIST / "MRobot"
    if not executable.is_file():
        raise SystemExit(f"missing Linux executable: {executable}")
    executable.chmod(executable.stat().st_mode | 0o111)
    target = RELEASE_DIST / f"MRobot-v{version}-linux-{arch}.tar.gz"
    with tarfile.open(target, "w:gz") as archive:
        archive.add(executable, arcname="MRobot/MRobot")
    return target


def package() -> tuple[Path, Path]:
    version = release_version()
    arch = architecture()
    if RELEASE_DIST.exists():
        shutil.rmtree(RELEASE_DIST)
    RELEASE_DIST.mkdir(parents=True)

    if sys.platform == "darwin":
        artifact = package_macos(version, arch)
    elif sys.platform == "win32":
        artifact = package_windows(version, arch)
    elif sys.platform.startswith("linux"):
        artifact = package_linux(version, arch)
    else:
        raise SystemExit(f"unsupported desktop platform: {sys.platform}")
    checksum = write_checksum(artifact)
    print(artifact)
    print(checksum)
    return artifact, checksum


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and package the native MRobot desktop application")
    parser.add_argument("--package-only", action="store_true", help="package an existing dist build")
    args = parser.parse_args()
    if not args.package_only:
        build()
    package()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
