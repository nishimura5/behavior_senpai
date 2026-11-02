import os
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app_feat_mix import App as MixApp
from behavior_senpai import df_attrs, feature_proc, file_inout
from behavior_senpai.hdf_df import DataFrameStorage
from gui_parts import TempFile
from test_feature_filter_timeaxis import amplitudes, signal_frame


class MixFilterIntegrationTests(unittest.TestCase):
    """Real Tk panel and CSV/HDF5; no VideoCapture objects are created."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        settings = patch.object(TempFile, "_find_data_dir", return_value=self.temp.name)
        settings.start()
        self.addCleanup(settings.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = MixApp(self.root, {"calc_case": "case", "trk_pkl_name": "target.pkl"})
        self.app.unbind("<Map>")
        self.addCleanup(self.app.close)
        self.app.pkl_dir = os.path.join(self.temp.name, "trk")
        os.makedirs(self.app.pkl_dir)
        self.app.calc_dir = os.path.join(self.temp.name, "calc")
        self.app.track_name = "target.pkl"
        self.path = Path(self.app.calc_dir) / "case" / "target.feat"
        frame = pd.concat([signal_frame(15, member="a"), signal_frame(30, member="b", scale=3.)]).sort_index()
        frame.attrs["scene_table"] = {"description": ["test", "test"], "member": ["a", "a"],
                                       "start": ["00:00:00.000", "00:01:00.000"],
                                       "end": ["00:00:40.000", "00:01:59.999"]}
        self.frame = frame
        self.app.src_attrs = df_attrs.DfAttrs(frame)
        self.app.src_attrs.load_scene_table()
        self.app.scene_combo.set_values(["", "test"])
        storage = DataFrameStorage(str(self.path))
        storage.save_points_df(frame, "target.pkl", [["distance (|AB|)", "a", "0", "1", "None"]])
        loader = file_inout.PickleLoader(self.app.calc_dir)
        loader.set_tar_path(str(self.path))
        self.app.load_feat(loader)
        self.app.tree.set_members(["a", "b"])
        self.rows = [["filtered_a", "a", "wave", " ", " ", "Bandpassfilter", ""],
                     ["filtered_b", "b", "wave", " ", " ", "Bandpassfilter", ""]]
        for row in self.rows:
            self.app.tree.insert(row)
        self.app.tree.tree.selection_set(self.app.tree.tree.get_children())

    def test_real_draw_csv_and_hdf_output_agree_and_preserve_member_timestamps(self):
        self.app.draw()
        self.assertEqual(str(self.app.export_btn["state"]), "normal")
        result = self.app.feat_df
        pd.testing.assert_series_equal(result["timestamp"], self.frame["timestamp"])
        for member, scale in [("a", 1.), ("b", 3.)]:
            selected = result.loc[result.index.get_level_values("member") == member]
            gains = amplitudes(selected[f"filtered_{member}"], selected["timestamp"].to_numpy() / 1000., [.7, 4.])
            self.assertAlmostEqual(gains[0], scale, delta=.025 * scale)
            self.assertLess(gains[1], .025 * scale)
        self.app.export()
        pd.testing.assert_frame_equal(DataFrameStorage(str(self.path)).load_mixnorm_df(), result)
        with patch("export_csv.messagebox.showinfo"):
            self.app.export_csv()
        csv = pd.read_csv(next((Path(self.temp.name) / "csv").glob("*.csv")))
        expected = result.reset_index()
        for column in ["frame", "member", "timestamp", "filtered_a", "filtered_b"]:
            pd.testing.assert_series_equal(csv[column], expected[column], check_dtype=False)

    def test_csv_and_draw_use_independent_scenes(self):
        self.app.scene_combo.set("test")
        self.app.draw()
        self.assertEqual(str(self.app.export_btn["state"]), "normal")
        ranges = self.app.src_attrs.get_scenes("test")
        csv = self.app._make_csv_dataframe(self.rows, ranges)
        for member in ["a", "b"]:
            signal = self.frame.loc[self.frame.index.get_level_values("member") == member]
            expected = feature_proc.calc(signal["wave"], "bandpass", timestamps=signal["timestamp"], scene_ranges=ranges)
            actual = self.app.feat_df.loc[signal.index, f"filtered_{member}"]
            np.testing.assert_allclose(actual, expected, equal_nan=True)
            exported = csv.loc[csv.member == member].set_index("frame")
            expected = expected.dropna().droplevel("member")
            np.testing.assert_allclose(exported[f"filtered_{member}"], expected)

    def test_filter_error_disables_save_and_preserves_feat_and_csv(self):
        self.app.draw()
        self.app.export()
        with patch("export_csv.messagebox.showinfo"):
            self.app.export_csv()
        csv_path = next((Path(self.temp.name) / "csv").glob("*.csv"))
        feat_before, csv_before = self.path.read_bytes(), csv_path.read_bytes()
        for problem in ["missing", "irregular", "duplicate", "short"]:
            with self.subTest(problem=problem):
                self.app.tar_df = self.frame.copy()
                if problem == "missing":
                    self.app.tar_df.iloc[50, 0] = np.nan
                elif problem == "irregular":
                    self.app.tar_df.iloc[50, 1] += 10.
                elif problem == "duplicate":
                    self.app.tar_df.loc[(25, "a"), "timestamp"] = self.app.tar_df.loc[(24, "a"), "timestamp"]
                else:
                    self.app.tar_df = self.app.tar_df.iloc[:10]
                with patch("app_feat_mix.messagebox.showerror") as error:
                    self.app.draw()
                    error.assert_called_once()
                self.assertEqual(str(self.app.export_btn["state"]), "disabled")
                self.assertTrue(self.app.feat_df.empty)
                self.app.export()  # Also safe when called directly after a failed draw.
                with patch("app_feat_mix.messagebox.showerror") as error:
                    self.app.export_csv()
                    error.assert_called_once()
                self.assertEqual(self.path.read_bytes(), feat_before)
                self.assertEqual(csv_path.read_bytes(), csv_before)


if __name__ == "__main__":
    unittest.main()
