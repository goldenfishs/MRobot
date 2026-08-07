from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mcode.config import MCodeConfig
from mcode.errors import ResolutionError
from mcode.packages import resolve_packages
from mcode.stm32 import STM32CubeMXParser
from tests.helpers import write_config, write_ioc, write_package


class PackageResolverTests(unittest.TestCase):
    def _project(self, root: Path):
        return STM32CubeMXParser(root / "demo.ioc").parse(root)

    def test_resolves_transitive_dependencies_in_topological_order(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root)
            write_package(root / "packages/math", "mrobot.component.math", "component", provides=["component.math"])
            write_package(
                root / "packages/imu",
                "mrobot.device.imu",
                dependencies=["mrobot.component.math"],
                requires=["bsp.spi", "bsp.gpio"],
            )
            write_config(root, ["packages/imu"])
            packages = resolve_packages(MCodeConfig.load(root), self._project(root))
            self.assertEqual([item.package_id for item in packages], ["mrobot.component.math", "mrobot.device.imu"])

    def test_reports_missing_dependency(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root)
            write_package(root / "packages/imu", "mrobot.device.imu", dependencies=["mrobot.component.missing"])
            write_config(root, ["packages/imu"])
            with self.assertRaisesRegex(ResolutionError, "缺少依赖包"):
                resolve_packages(MCodeConfig.load(root), self._project(root))

    def test_reports_dependency_cycle(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root)
            write_package(root / "packages/a", "mrobot.component.a", "component", dependencies=["mrobot.component.b"])
            write_package(root / "packages/b", "mrobot.component.b", "component", dependencies=["mrobot.component.a"])
            write_config(root, ["packages/a"])
            with self.assertRaisesRegex(ResolutionError, "循环"):
                resolve_packages(MCodeConfig.load(root), self._project(root))

    def test_reports_unsatisfied_capability(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root, ips=("SPI1",))
            write_package(root / "packages/can", "mrobot.device.can", requires=["bsp.can"])
            write_config(root, ["packages/can"])
            with self.assertRaisesRegex(ResolutionError, "bsp.can"):
                resolve_packages(MCodeConfig.load(root), self._project(root))


if __name__ == "__main__":
    unittest.main()
