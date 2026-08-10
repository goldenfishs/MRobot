from pathlib import Path


def test_gui_generation_uses_only_mcode_service() -> None:
    source = (Path(__file__).resolve().parents[1] / "app/code_generate_interface.py").read_text(encoding="utf-8")
    assert "MCodeService().generate" in source
    assert "service.search_packages" in source
    assert "service.install_package" in source
    assert "service.remove_package" in source
    assert "bsp.generate_bsp" not in source
    assert "component.generate_component" not in source
    assert "device.generate_device" not in source
    assert "CodeGenerator" not in source
    assert "assets/User_code" not in source


def test_desktop_has_no_runtime_legacy_user_code_dependency() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "assets/User_code").exists()
    runtime = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (root / "app").rglob("*.py")
    )
    assert "User_code" not in runtime
    assert "qutrobot.top:5000" not in runtime


def test_gui_update_frontend_uses_shared_update_service() -> None:
    root = Path(__file__).resolve().parents[1]
    main = (root / "app" / "main_window.py").read_text(encoding="utf-8")
    adapter = (root / "app" / "tools" / "auto_updater.py").read_text(encoding="utf-8")
    assert "UpdateCheckThread" in main
    assert 'updates/autoInstall' in main
    assert "UpdateService" in adapter
    assert "requests.get" not in adapter
