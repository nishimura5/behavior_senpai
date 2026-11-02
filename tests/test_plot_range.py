import os
import sys
import tkinter as tk
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app_feat_mix import App
from gui_feat_mix import FeatMixTreeDialog


class PlotRangeTests(unittest.TestCase):
    def test_signed_ranges_whitespace_and_legacy_examples(self):
        cases = {"0-1": (0., 1.), "10.0-30.0": (10., 30.), "-1-1": (-1., 1.),
                 "-180-180": (-180., 180.), "-10--2": (-10., -2.), "  -10 - -2  ": (-10., -2.),
                 "+1-+3": (1., 3.), "-.5-.5": (-.5, .5), "-1e-3-2e+1": (-.001, 20.)}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(App._parse_plot_range(text), expected)
        self.assertIsNone(App._parse_plot_range("  "))

    def test_invalid_nonfinite_and_reversed_ranges_report_reasons(self):
        for text in ["x-y", "1", "1-2-3", "nan-1", "0-inf", "-inf-1", "0-1e999", "2-1", "-1--2", "1-1"]:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "finite.*lower < upper"):
                App._parse_plot_range(text)

    def test_real_dialog_keeps_invalid_input_and_accepts_signed_range(self):
        root = tk.Tk()
        root.withdraw()
        try:
            dialog = FeatMixTreeDialog(root, ["7"], contain_blank=False)
            dialog.plot_range_entry.update("2-1")
            with patch("gui_feat_mix.messagebox.showerror") as error:
                dialog.on_ok()
                error.assert_called_once()
            self.assertTrue(dialog.winfo_exists())
            self.assertIsNone(dialog.selected_member)
            dialog.plot_range_entry.update(" -10 - -2 ")
            dialog.on_ok()
            self.assertFalse(dialog.winfo_exists())
            self.assertEqual(App._parse_plot_range(dialog.selected_plot_range), (-10., -2.))
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
