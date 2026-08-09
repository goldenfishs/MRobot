from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_desktop_dependencies_cover_runtime_imports() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"Jinja2>=3.1"' in project
    assert '"openpyxl>=3.1"' in project
    assert '"packaging>=23.0"' in project


def test_bundle_contains_complete_assets_and_uses_meipass() -> None:
    spec = (ROOT / "MRobot.spec").read_text(encoding="utf-8")
    generator = (ROOT / "app" / "tools" / "code_generator.py").read_text(encoding="utf-8")
    assert "('assets', 'assets')" in spec
    assert "getattr(sys, '_MEIPASS'" in generator


def test_frozen_runtime_does_not_write_inside_app_bundle() -> None:
    entrypoint = (ROOT / "MRobot.py").read_text(encoding="utf-8")
    assert "Application Support' / 'MRobot" in entrypoint
    assert "os.path.dirname(sys.executable) if getattr(sys, 'frozen'" not in entrypoint


def test_native_release_matrix_covers_primary_desktop_platforms() -> None:
    workflow = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
    builder = (ROOT / "tools" / "build_desktop.py").read_text(encoding="utf-8")
    for runner in ("macos-15", "windows-2025", "ubuntu-24.04"):
        assert runner in workflow
    for suffix in (".dmg", ".zip", ".tar.gz"):
        assert suffix in builder


def test_desktop_version_has_one_runtime_source() -> None:
    project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = (ROOT / "app" / "_version.py").read_text(encoding="utf-8")
    about = (ROOT / "app" / "about_interface.py").read_text(encoding="utf-8")
    assert 'dynamic = ["version"]' in project
    assert '__version__ = "0.4.1"' in version
    assert '__version__ = "1.1.1"' not in about


def test_release_builds_windows_auto_update_installer() -> None:
    workflow = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
    installer = (ROOT / "MRobot.iss").read_text(encoding="utf-8")
    assert "choco install innosetup" in workflow
    assert "PrivilegesRequired=lowest" in installer
    assert "-setup" in installer


def test_release_publishes_rate_limit_free_update_manifest() -> None:
    workflow = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
    assert "create_update_manifest.py" in workflow
    assert "update.json" in (ROOT / "tools" / "create_update_manifest.py").read_text(encoding="utf-8")


def test_release_publishes_to_mrobot_update_origin() -> None:
    workflow = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text(encoding="utf-8")
    update_service = (ROOT / "app" / "update_service.py").read_text(encoding="utf-8")
    assert "https://updates.qutmrobot.cn" in update_service
    assert "https://download.qutmrobot.cn" in workflow
    assert "MROBOT_UPDATE_SSH_KEY" in workflow
    assert "rsync -az --delay-updates" in workflow
