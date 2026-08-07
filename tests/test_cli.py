import contextlib
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mcode.cli import run
from tests.helpers import write_ioc, write_package


class CLITests(unittest.TestCase):
    def test_init_and_json_inspect(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root)
            output = StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(run(["init", str(root), "--json"]), 0)
            self.assertTrue((root / "mrobot.yaml").exists())
            output = StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(run(["inspect", str(root), "--json"]), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["family"], "STM32F4")
            self.assertIn("platform.stm32cubemx", data["capabilities"])

    def test_validate_returns_stable_error_exit_code(self):
        with TemporaryDirectory() as temporary:
            output = StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(run(["validate", temporary, "--json"]), 2)
            self.assertFalse(json.loads(output.getvalue())["valid"])

    def test_package_validate(self):
        with TemporaryDirectory() as temporary:
            root = write_package(Path(temporary) / "device", "mrobot.device.demo")
            output = StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(run(["package", "validate", str(root), "--json"]), 0)
            self.assertTrue(json.loads(output.getvalue())["valid"])


if __name__ == "__main__":
    unittest.main()
