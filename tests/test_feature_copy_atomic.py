"""Transactions exercise the real default calculator and real PyTables files."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app_feature_copy import App
from behavior_senpai.hdf_df import DataFrameStorage
from behavior_senpai import feature_proc


class FeatureCopyAtomicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = object.__new__(App)
        self.app.pkl_dir = os.path.join(self.temp.name, "trk")
        self.app.feat_dir = os.path.join(self.temp.name, "calc", "case")
        self.app.calc_case = "case"
        os.makedirs(self.app.pkl_dir)
        os.makedirs(self.app.feat_dir)
        index = pd.MultiIndex.from_product([range(3), [7], range(17)], names=["frame", "member", "keypoint"])
        self.track = pd.DataFrame({
            "x": np.tile(np.arange(17, dtype=float) + 1, 3),
            "y": np.tile(np.arange(17, dtype=float) ** 2 + 1, 3),
            "timestamp": np.repeat([0., 100., 200.], 17),
        }, index=index)
        self.track.attrs = {"model": "YOLO11 x-pose", "scene_table": {
            "description": ["test"], "member": [7], "start": ["00:00:00.100"], "end": ["00:00:00.200"],
        }}
        self.track.to_pickle(os.path.join(self.app.pkl_dir, "target.pkl"))
        self.path = Path(self.app.feat_dir) / "target.feat"
        self.points = [["distance (|AB|)", "old", "5", "6", "None"]]
        self.mix = [["shoulder", "old", "norm(5-6)", " ", " ", "No normalize"]]

    def seed(self):
        with pd.HDFStore(self.path, "w") as store:
            for key in ["traj/df", "dimredu/df", "custom/data"]:
                store.put(key, pd.DataFrame({"keep": [42.]}))

    def assert_clean(self):
        self.assertEqual(list(Path(self.app.feat_dir).glob(".feature-copy-*")), [])

    def test_filter_failure_preserves_existing_bytes_or_no_new_file_in_both_paths(self):
        mix = [["filtered", "old", "norm(5-6)", " ", " ", "Bandpassfilter"]]
        points, _ = App._calculate_points(self.track, "7", self.points)
        for definitions in [[], self.points]:
            for existing in [False, True]:
                with self.subTest(points=bool(definitions), existing=existing):
                    if self.path.exists():
                        self.path.unlink()
                    if existing:
                        DataFrameStorage(str(self.path)).save_points_df(points, "target.pkl", self.points)
                    before = self.path.read_bytes() if existing else None
                    with self.assertRaisesRegex(feature_proc.FilterInputError, "Too few samples"):
                        self.app._create_feature_file("target.pkl", "test", mix, definitions)
                    if existing:
                        self.assertEqual(self.path.read_bytes(), before)
                    else:
                        self.assertFalse(self.path.exists())
                    self.assert_clean()

    def test_filtered_feature_copy_reopens_correct_signal_in_both_paths(self):
        from test_feature_filter_timeaxis import amplitudes, signal_frame
        signal = signal_frame(15)
        timestamps = signal["timestamp"].to_numpy()
        index = pd.MultiIndex.from_product([range(len(signal)), [7], range(17)], names=["frame", "member", "keypoint"])
        track = pd.DataFrame({"x": np.tile(np.arange(17, dtype=float) + 1, len(signal)),
                              "y": 1., "timestamp": np.repeat(timestamps, 17)}, index=index)
        track.loc[pd.IndexSlice[:, 7, 5], "x"] = 0.
        track.loc[pd.IndexSlice[:, 7, 6], "x"] = 10. + signal["wave"].to_numpy()
        track.attrs = {"model": "YOLO11 x-pose", "scene_table": {
            "description": ["test"], "member": [7], "start": ["00:00:00.000"], "end": ["00:01:59.999"],
        }}
        track.to_pickle(os.path.join(self.app.pkl_dir, "target.pkl"))
        mix = [["filtered", "old", "norm(5-6)", " ", " ", "Bandpassfilter"]]
        for definitions in [[], self.points]:
            with self.subTest(points=bool(definitions)):
                self.app._create_feature_file("target.pkl", "test", mix, definitions)
                storage = DataFrameStorage(str(self.path))
                result = storage.load_mixnorm_df()
                gains = amplitudes(result["filtered"], result["timestamp"].to_numpy() / 1000., [.7, 4.])
                self.assertAlmostEqual(gains[0], 1., delta=.025)
                self.assertLess(gains[1], .025)
                self.assertEqual(result["timestamp"].tolist(), timestamps.tolist())
                self.assertEqual(storage.load_profile()["track_name"], "target.pkl")
                self.assertEqual(storage.load_mixnorm_source_cols(), [["filtered", "7", "norm(5-6)", " ", " ", "Bandpassfilter"]])
                self.assert_clean()

    def test_success_both_paths_reopen_data_definitions_profile_and_preserved_groups(self):
        for definitions in [[], self.points]:
            with self.subTest(points=bool(definitions)):
                # traj is deliberately a valid feature table because legacy defaults load it too.
                self.seed()
                index = pd.MultiIndex.from_product([range(3), ["7"]], names=["frame", "member"])
                traj = pd.DataFrame({"trajectory": [1., 2., 3.], "timestamp": [0., 100., 200.]}, index=index)
                with pd.HDFStore(self.path, "a") as store:
                    store.put("traj/df", traj)
                self.app._create_feature_file("target.pkl", "test", self.mix, definitions)
                target = DataFrameStorage(str(self.path))
                points = target.load_points_df()
                mixed = target.load_mixnorm_df()
                expected = np.sqrt(1 + 11 ** 2)
                np.testing.assert_allclose(points["norm(5-6)"], expected)
                self.assertTrue(pd.isna(mixed.loc[(0, "7"), "shoulder"]))
                np.testing.assert_allclose(mixed.loc[(slice(1, 2), "7"), "shoulder"], expected)
                self.assertEqual(mixed["timestamp"].tolist(), [0., 100., 200.])
                self.assertEqual(target.load_profile(), {"track_name": "target.pkl"})
                self.assertTrue(all(row[1] == "7" for row in target.load_points_source_cols()))
                self.assertEqual(target.load_mixnorm_source_cols(), [["shoulder", "7", "norm(5-6)", " ", " ", "No normalize"]])
                with pd.HDFStore(self.path, "r") as store:
                    pd.testing.assert_frame_equal(store["traj/df"], traj)
                    self.assertEqual(store["dimredu/df"]["keep"].tolist(), [42.])
                    self.assertEqual(store["custom/data"]["keep"].tolist(), [42.])
                self.assert_clean()

    def test_failures_leave_existing_bytes_or_no_new_file_and_clean_temps(self):
        real_points = DataFrameStorage.save_points_df
        real_mix = DataFrameStorage.save_mixnorm_df
        real_put = pd.HDFStore.put

        def fail_points(storage, *args):
            real_points(storage, *args)
            raise OSError("after points write")

        def fail_mix(storage, *args):
            real_mix(storage, *args)
            raise OSError("after mix write")

        def fail_mix_definitions(store, key, *args, **kwargs):
            if key == "mixnorm/source_cols":
                # mixnorm/df was already written, but its definitions have not been.
                raise OSError("during mix definitions write")
            return real_put(store, key, *args, **kwargs)

        for definitions in [[], self.points]:
            for existing in [False, True]:
                for failure in ["validation", "points", "mix", "mix-definitions", "replace"]:
                    with self.subTest(points=bool(definitions), existing=existing, failure=failure):
                        if self.path.exists():
                            self.path.unlink()
                        if existing:
                            # Seed real HDF5, including Points for the default path to replace.
                            points, _ = App._calculate_points(self.track, "7", self.points)
                            DataFrameStorage(str(self.path)).save_points_df(points, "target.pkl", self.points)
                        before = self.path.read_bytes() if existing else None
                        mix = self.mix if failure != "validation" else [["bad", "7", "missing", " ", " ", "No normalize"]]
                        if failure == "points":
                            context = patch.object(DataFrameStorage, "save_points_df", fail_points)
                        elif failure == "mix":
                            context = patch.object(DataFrameStorage, "save_mixnorm_df", fail_mix)
                        elif failure == "mix-definitions":
                            context = patch.object(pd.HDFStore, "put", fail_mix_definitions)
                        elif failure == "replace":
                            context = patch("behavior_senpai.hdf_df.os.replace", side_effect=OSError("replace failed"))
                        else:
                            from contextlib import nullcontext
                            context = nullcontext()
                        with context, self.assertRaises((ValueError, OSError)):
                            self.app._create_feature_file("target.pkl", "test", mix, definitions)
                        if existing:
                            self.assertEqual(self.path.read_bytes(), before)
                        else:
                            self.assertFalse(self.path.exists())
                        self.assert_clean()


if __name__ == "__main__":
    unittest.main()
