from mcode.registry import RegistryEntry

from app.code_generate_interface import describe_plan, latest_registry_entries, package_type


def test_registry_catalog_keeps_latest_version_per_package() -> None:
    entries = (
        RegistryEntry("mrobot.device.demo", "0.1.0", "old.zip"),
        RegistryEntry("mrobot.device.demo", "0.2.0", "new.zip"),
        RegistryEntry("mrobot.component.timer", "1.0.0", "timer.zip"),
    )
    result = latest_registry_entries(entries)
    assert [(entry.package_id, entry.version) for entry in result] == [
        ("mrobot.component.timer", "1.0.0"),
        ("mrobot.device.demo", "0.2.0"),
    ]


def test_package_type_is_derived_from_stable_package_id() -> None:
    assert package_type("mrobot.platform.stm32") == "platform"
    assert package_type("mrobot.algorithm.trajectory") == "algorithm"


def test_empty_generation_plan_has_readable_summary(tmp_path) -> None:
    from mcode.models import GenerationPlan

    summary, detail = describe_plan(GenerationPlan(str(tmp_path), ()))
    assert "新增 0" in summary
    assert detail == "没有文件变更。"
