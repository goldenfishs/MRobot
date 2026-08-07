import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mcode.errors import GenerationConflict
from mcode.models import ChangeAction
from mcode.service import MCodeService
from tests.helpers import write_config, write_ioc, write_package


class GenerationTests(unittest.TestCase):
    def _project(self, root: Path):
        write_ioc(root)
        package = write_package(
            root / "packages/imu",
            "mrobot.device.imu",
            requires=["bsp.spi"],
            files=[
                {"source": "src/imu.c", "destination": "User/MRobot/packages/imu/imu.c", "policy": "generated"},
                {"source": "templates/imu_config.h", "destination": "User/MRobot/config/imu_config.h", "policy": "scaffold"},
            ],
        )
        (package / "src").mkdir()
        (package / "src/imu.c").write_text("int imu(void) { return 1; }\n", encoding="utf-8")
        (package / "templates").mkdir()
        (package / "templates/imu_config.h").write_text("#define IMU_BUS 1\n", encoding="utf-8")
        write_config(root, ["packages/imu"])

    def test_plan_generate_and_idempotent_rerun(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project(root)
            service = MCodeService()
            first = service.plan(root)
            self.assertFalse(first.has_errors)
            self.assertTrue(all(item.action == ChangeAction.CREATE for item in first.changes))
            service.generate(root)
            second = service.plan(root)
            actions = {item.path: item.action for item in second.changes}
            self.assertEqual(actions["User/MRobot/packages/imu/imu.c"], ChangeAction.NOOP)
            self.assertEqual(actions["User/MRobot/config/imu_config.h"], ChangeAction.SKIP)
            self.assertTrue((root / ".mrobot/generated-state.json").is_file())
            cmake = (root / "User/MRobot/generated/MCode.generated.cmake").read_text()
            self.assertIn("../packages/imu/imu.c", cmake)

    def test_generated_file_user_edit_becomes_conflict(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project(root)
            service = MCodeService()
            service.generate(root)
            target = root / "User/MRobot/packages/imu/imu.c"
            target.write_text("user edit\n", encoding="utf-8")
            plan = service.plan(root)
            self.assertTrue(plan.has_conflicts)
            with self.assertRaises(GenerationConflict):
                service.generate(root)
            self.assertEqual(target.read_text(), "user edit\n")

    def test_scaffold_is_never_overwritten(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project(root)
            service = MCodeService()
            service.generate(root)
            target = root / "User/MRobot/config/imu_config.h"
            target.write_text("#define USER_VALUE 42\n", encoding="utf-8")
            source = root / "packages/imu/templates/imu_config.h"
            source.write_text("#define PACKAGE_VALUE 9\n", encoding="utf-8")
            service.generate(root)
            self.assertEqual(target.read_text(), "#define USER_VALUE 42\n")

    def test_removed_package_deletes_only_tracked_generated_files(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self._project(root)
            service = MCodeService()
            service.generate(root)
            write_config(root, [])
            plan = service.plan(root)
            deletion = next(item for item in plan.changes if item.path.endswith("imu.c"))
            self.assertEqual(deletion.action, ChangeAction.DELETE)
            service.generate(root)
            self.assertFalse((root / "User/MRobot/packages/imu/imu.c").exists())
            self.assertTrue((root / "User/MRobot/config/imu_config.h").exists())
            state = json.loads((root / ".mrobot/generated-state.json").read_text())
            self.assertNotIn("User/MRobot/packages/imu/imu.c", state["files"])


if __name__ == "__main__":
    unittest.main()
