import os
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app_feature_copy import App
from behavior_senpai.hdf_df import DataFrameStorage


class FeatureCopyTests(unittest.TestCase):
    def setUp(self):
        index = pd.MultiIndex.from_product([range(3), [7], [0, 1, 2]], names=["frame", "member", "keypoint"])
        self.track = pd.DataFrame(
            {"x": [0., 3., 0.] * 3, "y": [0., 0., 4.] * 3, "timestamp": np.repeat([0., 100., 200.], 3)},
            index=index,
        )
        self.track.attrs["scene_table"] = {
            "description": ["test"], "member": [7], "start": ["00:00:00.100"], "end": ["00:00:00.200"]
        }
        self.points_definitions = [
            ["distance (|AB|)", "original", "0", "1", "None"],
            ["cross_product (AB×AC)", "original", "0", "1", "2"],
            ["direction (∠BAx)", "original", "0", "2", ""],
        ]
        self.mix_definitions = [
            ["manual_cross", "original", "cross(0-1,0-2)", " ", " ", "No normalize"],
            ["manual_direction", "original", "sin(0-2)", "/", "norm(0-1)", "No normalize"],
        ]

    def test_copy_recalculates_manual_features_and_saves_definitions(self):
        with tempfile.TemporaryDirectory() as root:
            app = object.__new__(App)
            app.pkl_dir = os.path.join(root, "trk")
            app.feat_dir = os.path.join(root, "calc", "case")
            app.calc_case = "case"
            os.makedirs(app.pkl_dir)
            self.track.to_pickle(os.path.join(app.pkl_dir, "target.pkl"))

            # The source values deliberately differ from the target coordinates.
            source_points, _ = App._calculate_points(self.track, "7", self.points_definitions)
            source_points.loc[:, "cross(0-1,0-2)"] = 999.
            master = DataFrameStorage(os.path.join(root, "master.feat"))
            master.save_points_df(source_points, "master.pkl", self.points_definitions)
            master.save_mixnorm_source_cols(self.mix_definitions, "master.pkl")
            with patch("app_feature_copy.calc_features.execute_calc_features") as default_calc:
                app._create_feature_file(
                    "target.pkl", "test", master.load_mixnorm_source_cols(), master.load_points_source_cols()
                )
                default_calc.assert_not_called()

            target = DataFrameStorage(os.path.join(app.feat_dir, "target.feat"))
            points = target.load_points_df()
            mixed = target.load_mixnorm_df()
            self.assertEqual(points["cross(0-1,0-2)"].tolist(), [12., 12., 12.])
            self.assertTrue(pd.isna(mixed.loc[(0, "7"), "manual_cross"]))
            self.assertEqual(mixed.loc[(1, "7"), "manual_cross"], 12.)
            self.assertAlmostEqual(mixed.loc[(1, "7"), "manual_direction"], 1 / 3)
            self.assertEqual(mixed["timestamp"].tolist(), [0., 100., 200.])
            self.assertTrue(all(row[1] == "7" for row in target.load_points_source_cols()))
            self.assertTrue(all(row[1] == "7" for row in target.load_mixnorm_source_cols()))
            self.assertEqual(target.load_profile()["track_name"], "target.pkl")

    def test_all_manual_point_operations(self):
        cases = [
            ("distance (|AB|)", {"norm(0-1)": 3.}),
            ("sin,cos (∠BAC)", {"sin(0-1,0-2)": 1., "cos(0-1,0-2)": 0.}),
            ("angle3 (∠BAC)", {"angle(0-1,0-2)": 90.}),
            ("angle2 (∠BAx)", {"deg(0-1)": 0.}),
            ("angle2 (∠BAy)", {"deg_y(0-1)": 90.}),
            ("direction (∠BAx)", {"sin(0-1)": 0., "cos(0-1)": 1.}),
            ("xy_component (AB_x, AB_y)", {"component_x(0-1)": 3., "component_y(0-1)": 0.}),
            ("cross_product (AB×AC)", {"cross(0-1,0-2)": 12.}),
            ("dot_product (AB・AC)", {"dot(0-1,0-2)": 0.}),
            ("plus (AB+AC)", {"plus_x(0-1,0-2)": 3., "plus_y(0-1,0-2)": 4.}),
            ("norms (|AB||AC|)", {"norms(0-1,0-2)": 12.}),
        ]
        for code, expected in cases:
            with self.subTest(code=code):
                result, _ = App._calculate_points(self.track, "7", [[code, "original", "0", "1", "2"]])
                for column, value in expected.items():
                    np.testing.assert_allclose(result[column], value)

    def test_duplicate_definitions_do_not_duplicate_columns(self):
        result, _ = App._calculate_points(self.track, "7", self.points_definitions * 2)
        self.assertTrue(result.columns.is_unique)

    def test_missing_points_report_error(self):
        with self.assertRaisesRegex(ValueError, "Keypoints not found"):
            App._calculate_points(self.track, "7", [["angle3 (∠BAC)", "original", "0", "1", "99"]])

    def test_missing_mix_input_is_not_silently_skipped(self):
        points, _ = App._calculate_points(self.track, "7", self.points_definitions[:1])
        with self.assertRaisesRegex(ValueError, "manual_cross"):
            App._calculate_mixnorm(points, "7", [(0, 200)], self.mix_definitions)

    def test_failed_definition_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as root:
            app = object.__new__(App)
            app.pkl_dir = root
            app.feat_dir = root
            app.calc_case = "case"
            self.track.to_pickle(os.path.join(root, "target.pkl"))
            feat_path = os.path.join(root, "target.feat")
            with open(feat_path, "wb") as file:
                file.write(b"existing feature file")
            with self.assertRaisesRegex(ValueError, "manual_cross"):
                app._create_feature_file("target.pkl", "test", self.mix_definitions, self.points_definitions[:1])
            with open(feat_path, "rb") as file:
                self.assertEqual(file.read(), b"existing feature file")

    def test_template_without_points_definitions_uses_defaults(self):
        with tempfile.TemporaryDirectory() as root:
            app = object.__new__(App)
            app.pkl_dir = root
            app.feat_dir = root
            app.calc_case = "case"
            self.track.to_pickle(os.path.join(root, "target.pkl"))
            storage = DataFrameStorage(os.path.join(root, "target.feat"))

            def calculate_defaults(args):
                self.assertEqual(args["member"], "7")
                points, definitions = App._calculate_points(args["src_df"], args["member"], self.points_definitions)
                storage.save_points_df(points, args["trk_pkl_name"], definitions)

            with patch("app_feature_copy.calc_features.execute_calc_features", side_effect=calculate_defaults) as default_calc:
                app._create_feature_file("target.pkl", "test", self.mix_definitions, [])
                default_calc.assert_called_once()
            self.assertEqual(storage.load_mixnorm_df().loc[(1, "7"), "manual_cross"], 12.)


if __name__ == "__main__":
    unittest.main()
