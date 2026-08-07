from pathlib import Path


def test_gui_generation_uses_only_mcode_service() -> None:
    source = (Path(__file__).resolve().parents[1] / "app/code_generate_interface.py").read_text(encoding="utf-8")
    assert "self.mcode.configure" in source
    assert "self.mcode.generate" in source
    assert "bsp.generate_bsp" not in source
    assert "component.generate_component" not in source
    assert "device.generate_device" not in source
