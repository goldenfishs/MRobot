from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mcode.errors import ConfigurationError
from mcode.stm32 import STM32CubeMXParser, find_ioc_file
from tests.helpers import write_ioc


REPOSITORY = Path(__file__).resolve().parents[1]
FIXTURES = REPOSITORY / "tests/fixtures/cubemx"


class CubeMXParserTests(unittest.TestCase):
    def test_parses_real_f4_project_once_into_model(self):
        path = FIXTURES / "DevC.ioc"
        model = STM32CubeMXParser(path).parse()
        self.assertEqual(model.family, "STM32F4")
        self.assertTrue(model.freertos)
        self.assertEqual([item.name for item in model.peripherals_of("CAN")], ["CAN1", "CAN2"])
        self.assertNotIn("28", [item.name for item in model.peripherals])
        self.assertIn("bsp.pwm", model.capabilities)
        self.assertIn("bsp.gpio", model.capabilities)
        self.assertIn("bsp.uart", model.capabilities)

    def test_parses_real_h7_fdcan_project(self):
        path = FIXTURES / "CtrBoard-H7_ALL.ioc"
        model = STM32CubeMXParser(path).parse()
        self.assertEqual(model.family, "STM32H7")
        self.assertEqual([item.name for item in model.peripherals_of("FDCAN")], ["FDCAN1", "FDCAN2", "FDCAN3"])
        self.assertIn("bsp.can", model.capabilities)
        self.assertNotIn("26", [item.name for item in model.peripherals])

    def test_real_fixture_exposes_labels_and_pwm_without_gui_facade(self):
        model = STM32CubeMXParser(FIXTURES / "DevC.ioc").parse()
        self.assertTrue(any(pin.label for pin in model.pins))
        self.assertTrue(any("TIM" in pin.signal for pin in model.pins))

    def test_ioc_discovery_requires_explicit_choice_for_multiple_files(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_ioc(root, "one.ioc")
            write_ioc(root, "two.ioc")
            with self.assertRaises(ConfigurationError):
                find_ioc_file(root)
            self.assertEqual(find_ioc_file(root, "two.ioc").name, "two.ioc")


if __name__ == "__main__":
    unittest.main()
