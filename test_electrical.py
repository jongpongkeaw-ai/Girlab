import math
import unittest
from unittest.mock import patch

from electrical import analyze_dc, main


class AnalyzeDcTests(unittest.TestCase):
    def test_calculates_current_and_power(self):
        self.assertEqual(
            analyze_dc(12, 6),
            {"current_a": 2.0, "power_w": 24.0},
        )

    def test_accepts_zero_voltage(self):
        self.assertEqual(
            analyze_dc(0, 6),
            {"current_a": 0.0, "power_w": 0.0},
        )

    def test_rejects_non_positive_resistance(self):
        for resistance in (0, -1):
            with self.subTest(resistance=resistance):
                with self.assertRaises(ValueError):
                    analyze_dc(12, resistance)

    def test_rejects_non_finite_voltage(self):
        for voltage in (math.inf, -math.inf, math.nan):
            with self.subTest(voltage=voltage):
                with self.assertRaises(ValueError):
                    analyze_dc(voltage, 6)

    def test_rejects_non_finite_resistance(self):
        for resistance in (math.inf, -math.inf, math.nan):
            with self.subTest(resistance=resistance):
                with self.assertRaises(ValueError):
                    analyze_dc(12, resistance)


class MainTests(unittest.TestCase):
    @patch("builtins.print")
    @patch("builtins.input", side_effect=("12", "6"))
    def test_prints_results_for_valid_input(self, mocked_input, mocked_print):
        self.assertEqual(main(), 0)
        self.assertEqual(mocked_input.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in mocked_print.call_args_list],
            ["Current: 2.000 A", "Power: 24.000 W"],
        )

    @patch("builtins.print")
    @patch("builtins.input", side_effect=("12", "0"))
    def test_reports_invalid_resistance(self, mocked_input, mocked_print):
        self.assertEqual(main(), 1)
        self.assertEqual(mocked_input.call_count, 2)
        self.assertIn("Invalid input:", mocked_print.call_args.args[0])

    @patch("builtins.print")
    @patch("builtins.input", side_effect=("not a number",))
    def test_reports_non_numeric_input(self, mocked_input, mocked_print):
        self.assertEqual(main(), 1)
        self.assertEqual(mocked_input.call_count, 1)
        self.assertIn("Invalid input:", mocked_print.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
