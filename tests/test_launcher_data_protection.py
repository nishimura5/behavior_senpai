"""Real launcher, Tk dialogs, video, and PKL; only user choices/failures are injected."""
import copy
import os
import subprocess
import sys
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import app_feature_copy
import app_track_list
import launcher
from behavior_senpai.hdf_df import DataFrameStorage
from gui_parts import TempFile


class LauncherDataProtectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = patch.object(TempFile, "_find_data_dir", return_value=self.temp.name)
        self.settings.start()
        self.addCleanup(self.settings.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.dialog_errors = []
        self.addCleanup(lambda: self.assertEqual(self.dialog_errors, []))
        video = os.path.join(self.temp.name, "test.avi")
        writer = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 64))
        self.assertTrue(writer.isOpened())
        for _ in range(3):
            writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
        writer.release()
        self.pkl_dir = Path(self.temp.name) / "trk"
        self.pkl_dir.mkdir()
        self.path = self.pkl_dir / "target.pkl"
        self.other = self.pkl_dir / "other.pkl"
        index = pd.MultiIndex.from_product([range(3), ["7"], range(17)], names=["frame", "member", "keypoint"])
        self.track = pd.DataFrame({"x": np.tile(np.arange(17) + 1., 3), "y": 2., "conf": 1.,
                                   "timestamp": np.repeat([0., 100., 200.], 17)}, index=index)
        self.track.attrs = {"model": "YOLO11 x-pose", "video_name": "test.avi", "frame_size": (64, 64),
                            "scene_table": {"description": [], "member": [], "start": [], "end": []}}
        self.track.to_pickle(self.path)
        self.track.to_pickle(self.other)
        # Count the real constructor and reject a second call before it can corrupt memory.
        real_capture = launcher.vcap.VideoCap
        self.capture_count = 0

        def create_capture():
            self.assertEqual(self.capture_count, 0, "Only one VideoCapture may be created per process")
            self.capture_count += 1
            return real_capture()

        constructor = patch.object(launcher.vcap, "VideoCap", side_effect=create_capture)
        constructor.start()
        self.addCleanup(constructor.stop)
        self.app = launcher.App(self.root)
        self.addCleanup(self.app.vcap.release)
        self.app.pkl_selector.set_trk_path(str(self.path))
        self.assertTrue(self.app.load())
        self.root.deiconify()
        self.root.update()

    def edit(self, kind):
        if kind == "coordinates":
            self.app.src_df.iloc[0, 0] = 123.
        else:
            self.app.src_df.attrs["scene_table"]["description"].append("unsaved")

    def close_dialog(self, action=None):
        def close():
            dialog = getattr(self.app, "a", None)
            if dialog is None or not dialog.master.winfo_exists() or not dialog.winfo_ismapped():
                self.root.after(50, close)
                return
            try:
                if action:
                    action(dialog)
            except Exception as error:
                self.dialog_errors.append(error)
            finally:
                dialog.close()
                dialog.master.destroy()
        self.root.after(50, close)

    def test_coordinate_and_nested_attrs_save_discard_cancel_and_failed_save(self):
        for kind in ["coordinates", "attrs"]:
            for choice in ["save", "discard", "cancel", "failure", "missing"]:
                with self.subTest(kind=kind, choice=choice):
                    self.track.to_pickle(self.path)
                    self.app.pkl_selector.set_trk_path(str(self.path))
                    self.app.load(check_unsaved=False)
                    self.edit(kind)
                    edited = copy.deepcopy(self.app.src_df)
                    edited.attrs = copy.deepcopy(self.app.src_df.attrs)
                    self.assertTrue(self.app.has_unsaved_changes())
                    answer = {"save": True, "discard": False, "cancel": None, "failure": True, "missing": True}[choice]
                    before = self.path.read_bytes()
                    with patch("launcher.messagebox.askyesnocancel", return_value=answer), \
                         patch("launcher.messagebox.showinfo"), patch("launcher.messagebox.showerror"):
                        if choice == "failure":
                            # Fail after opening the real staging file: original must survive.
                            def fail_write(df, path, *args, **kwargs):
                                Path(path).write_bytes(b"partial pickle")
                                raise OSError("disk full")
                            with patch.object(pd.DataFrame, "to_pickle", fail_write):
                                result = self.app._resolve_unsaved_changes(reload_on_discard=True)
                        elif choice == "missing":
                            self.path.unlink()
                            result = self.app._resolve_unsaved_changes(reload_on_discard=True)
                        else:
                            result = self.app._resolve_unsaved_changes(reload_on_discard=True)
                    self.assertEqual(result, choice in ["save", "discard"])
                    if choice in ["cancel", "failure", "missing"]:
                        self.assertTrue(self.app._tracks_equal(self.app.src_df, edited))
                        self.assertTrue(self.app.has_unsaved_changes())
                        if choice != "missing":
                            self.assertEqual(self.path.read_bytes(), before)
                    elif choice == "save":
                        self.assertTrue(self.app._tracks_equal(pd.read_pickle(self.path), edited))
                        self.assertFalse(self.app.has_unsaved_changes())
                    else:
                        self.assertTrue(self.app._tracks_equal(self.app.src_df, self.track))
                        self.assertFalse(self.app.has_unsaved_changes())
                    self.assertEqual(list(self.pkl_dir.glob(".track-save-*")), [])

    def test_real_dialogs_no_change_preserve_dataframe_identity(self):
        for dialog in [app_feature_copy.App, app_track_list.App]:
            with self.subTest(dialog=dialog.__module__):
                current = self.app.src_df
                grabs = []
                self.close_dialog(lambda app: grabs.append(app.master.grab_current() == app.master))
                with patch.object(self.app, "load", wraps=self.app.load) as load:
                    self.app.launch_window(dialog, reload_pkl=True)
                load.assert_not_called()
                self.assertIs(self.app.src_df, current)
                self.assertEqual(grabs, [True])
                self.assertEqual(self.capture_count, 1)

    def test_saved_edits_survive_unchanged_real_dialogs_without_reload(self):
        for dialog in [app_feature_copy.App, app_track_list.App]:
            for kind in ["coordinates", "attrs"]:
                with self.subTest(dialog=dialog.__module__, kind=kind):
                    self.edit(kind)
                    current = self.app.src_df
                    self.close_dialog()
                    with patch("launcher.messagebox.askyesnocancel", return_value=True), \
                         patch("launcher.messagebox.showinfo"), patch.object(self.app, "load", wraps=self.app.load) as load:
                        self.app.launch_window(dialog, reload_pkl=True)
                    load.assert_not_called()
                    self.assertIs(self.app.src_df, current)
                    self.assertTrue(self.app._tracks_equal(pd.read_pickle(self.path), current))

    def test_feature_copy_batch_uses_saved_edits_and_reports_each_failure(self):
        self.app.src_df.attrs["scene_table"] = {"description": ["test"], "member": ["7"],
                                                "start": ["00:00:00.000"], "end": ["00:00:00.200"]}
        self.edit("coordinates")
        definitions = [["distance (|AB|)", "7", "0", "1", "None"]]
        mixed = [["distance", "7", "norm(0-1)", " ", " ", "No normalize"]]
        master_path = str(Path(self.temp.name) / "master.feat")
        points, _ = app_feature_copy.App._calculate_points(self.track, "7", definitions)
        master = DataFrameStorage(master_path)
        master.save_points_df(points, "master.pkl", definitions)
        master.save_mixnorm_source_cols(mixed, "master.pkl")
        results = []

        def execute(dialog):
            dialog.master_feature_path = master_path
            for row in dialog.tree.get_children(""):
                dialog.tree.set(row, "scene", "test")
            with patch("app_feature_copy.messagebox.showwarning") as warning:
                dialog._execute()
            results.append(warning.call_args.args[1])
        self.close_dialog(execute)
        with patch("launcher.messagebox.askyesnocancel", return_value=True), patch("launcher.messagebox.showinfo"):
            self.app.launch_window(app_feature_copy.App, reload_pkl=True)
        self.assertIn("Created: 1", results[0])
        self.assertIn("Failed: 1", results[0])
        self.assertIn("other.pkl", results[0])
        feat_dir = Path(self.temp.name) / "calc" / self.app.calc_case_entry.get()
        self.assertFalse((feat_dir / "other.feat").exists())
        result = DataFrameStorage(str(feat_dir / "target.feat")).load_points_df()
        self.assertEqual(result.loc[(0, "7"), "norm(0-1)"], 121.)

    def test_cancel_or_failed_save_prevents_dialog_construction(self):
        for answer in [None, True]:
            self.edit("coordinates")
            with patch("launcher.messagebox.askyesnocancel", return_value=answer), \
                 patch("launcher.messagebox.showerror"), \
                 patch("launcher.file_inout.overwrite_track_file", side_effect=OSError("denied")), \
                 patch("launcher.tk.Toplevel") as dialog:
                self.app.launch_window(app_feature_copy.App, reload_pkl=True)
            dialog.assert_not_called()
            self.assertTrue(self.app.has_unsaved_changes())

    def test_jump_cancel_restores_selector_and_preserves_edits(self):
        self.edit("attrs")
        current = self.app.src_df
        self.app.pkl_selector.set_trk_path(str(self.other))
        with patch("launcher.messagebox.askyesnocancel", return_value=None):
            self.assertFalse(self.app.load())
        self.assertIs(self.app.src_df, current)
        self.assertEqual(self.app.pkl_selector.get_trk_path(), str(self.path))
        self.assertEqual(TempFile().data["trk_path"], str(self.path))

    def test_track_list_update_and_feature_copy_update_and_jump(self):
        def change_track_list(dialog):
            for row in dialog.tree.get_children(""):
                if dialog.tree.set(row, "track") == "target.pkl":
                    dialog.tree.set(row, "take", "updated")
                    dialog.tree.set(row, "part", "1")
            dialog.overwrite()
        self.close_dialog(change_track_list)
        self.app.launch_window(app_track_list.App, reload_pkl=True)
        self.assertEqual(self.app.src_df.attrs["take"], "updated")

        def change_feature_copy(dialog):
            for row in dialog.tree.get_children(""):
                if dialog.tree.set(row, "pkl_name") == "target.pkl":
                    dialog.tree.set(row, "take", "feature-updated")
                    dialog.tree.set(row, "part", "1")
            dialog._overwrite_track_attrs()
        self.close_dialog(change_feature_copy)
        self.app.launch_window(app_feature_copy.App, reload_pkl=True)
        self.assertEqual(self.app.src_df.attrs["take"], "feature-updated")

        def jump(dialog):
            dialog.jump_to_pkl_path = str(self.other)
        self.close_dialog(jump)
        self.app.launch_window(app_feature_copy.App, reload_pkl=True)
        self.assertEqual(self.app.pkl_path, str(self.other))

    def _check_export_restores_shared_capture(self, fail):
        alternate = Path(self.temp.name) / "alternate.avi"
        writer = cv2.VideoWriter(str(alternate), cv2.VideoWriter_fourcc(*"MJPG"), 10, (48, 32))
        self.assertTrue(writer.isOpened())
        for _ in range(3):
            writer.write(np.full((32, 48, 3), 160, dtype=np.uint8))
        writer.release()
        other = self.track.copy()
        other.attrs = copy.deepcopy(self.track.attrs)
        other.attrs.update(video_name=alternate.name, frame_size=(48, 32))
        other.attrs["scene_table"] = {"description": ["test"], "member": ["7"],
                                       "start": ["00:00:00.000"], "end": ["00:00:00.200"]}
        other.to_pickle(self.other)
        # Restore a MultiVcap too, while keeping the same underlying native capture.
        self.app.src_df.attrs["video_name"] = ["test.avi", "test.avi"]
        self.app._restore_track_video(100.)
        self.app.src_df.to_pickle(self.path)
        self.app._remember_saved_track()
        current = self.app.src_df
        captures = []

        def export(dialog):
            captures.append(dialog.video_cap)
            for row in dialog.tree.get_children(""):
                if dialog.tree.set(row, "pkl_name") == "other.pkl":
                    dialog.tree.focus(row)
                    dialog.tree.set(row, "scene", "test")
            with patch("app_feature_copy.messagebox.showerror") as error, \
                 patch("export_mp4.messagebox.showinfo"), patch("export_mp4.cv2.imshow"), \
                 patch("export_mp4.cv2.waitKey", return_value=-1):
                if fail:
                    with patch("export_mp4.MakeMp4.export", side_effect=OSError("export failure")):
                        dialog._export_selected_mp4()
                    error.assert_called_once()
                else:
                    dialog._export_selected_mp4()
                    error.assert_not_called()
        self.close_dialog(export)
        with patch.object(self.app, "load", wraps=self.app.load) as load:
            self.app.launch_window(app_feature_copy.App, reload_pkl=True)
        load.assert_not_called()
        self.assertEqual(captures, [self.app.vcap])
        self.assertEqual(self.capture_count, 1)
        self.assertTrue(self.app.vcap.isOpened())
        self.assertIs(self.app.src_df, current)
        self.assertIs(self.app.cap.vcap, self.app.vcap)
        self.assertEqual(self.app.vcap.get_frame_size(), (64, 64))
        self.assertAlmostEqual(self.app.vw.get_current_position(), 100.)
        ok, frame = self.app.cap.read_at(100.)
        self.assertTrue(ok)
        self.assertLess(frame.mean(), 5.)
        if not fail:
            result = Path(self.temp.name) / "mp4" / "other_yolo.mp4"
            self.assertTrue(result.is_file())
            self.app.vcap.open_file(str(result))
            ok, exported = self.app.vcap.read_at(0.)
            self.assertTrue(ok)
            self.assertGreater(exported.mean(), 50.)
            self.app._restore_track_video(100.)

    def test_export_restores_video_and_position_with_one_capture(self):
        self._check_export_restores_shared_capture(fail=False)

    def test_failed_export_restores_video_and_position_with_one_capture(self):
        self._check_export_restores_shared_capture(fail=True)

    def _check_scene_save_failure(self, count):
        def edit(dialog):
            rows = dialog.tree.get_children()[:count]
            for i, row in enumerate(rows):
                dialog.tree.set(row, "part", str(i + 3))
                dialog.tree.set(row, "scene", f"old scene {i}")
                dialog.tree.set(row, "member", f"old member {i}")
                dialog.options_by_item[row] = {"scenes": ["new"], "members_by_scene": {"new": [str(i + 10)]}}
            dialog.tree.selection_set(rows)
            before = {row: dialog.tree.set(row) for row in rows}
            dialog._save_feat_copy()
            saved = Path(dialog.feat_copy_path).read_bytes()

            def choose():
                child = next(w for w in dialog.winfo_children() if isinstance(w, app_feature_copy.RowEditDialog))
                child.scene_combo.set("new")
                child._ok()
            self.root.after(50, choose)
            with patch.object(dialog, "_save_feat_copy", side_effect=OSError("disk full")), \
                 patch("app_feature_copy.messagebox.showerror") as error:
                dialog._edit_selected()
                error.assert_called_once()
            self.assertEqual({row: dialog.tree.set(row) for row in rows}, before)
            self.assertEqual(Path(dialog.feat_copy_path).read_bytes(), saved)
        self.close_dialog(edit)
        self.app.launch_window(app_feature_copy.App, reload_pkl=True)

    def test_scene_save_failure_restores_single_row(self):
        self._check_scene_save_failure(1)

    def test_scene_save_failure_restores_each_selected_row(self):
        self._check_scene_save_failure(2)

    def test_release_edit_points_mix_csv_save_reload_smoke(self):
        import app_area_filter
        import app_feat_mix
        import app_member_edit
        import app_points_calc
        import app_scene_table
        import app_smoothing

        count = 240
        video = Path(self.temp.name) / "smoke.avi"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 60, (64, 64))
        self.assertTrue(writer.isOpened())
        for i in range(count):
            writer.write(np.full((64, 64, 3), i % 180, dtype=np.uint8))
        writer.release()
        index = pd.MultiIndex.from_product([range(count), ["7"], range(17)], names=["frame", "member", "keypoint"])
        times = np.arange(count) / 60
        track = pd.DataFrame({"x": np.tile(np.arange(17) + 1., count) + np.repeat(np.sin(times * 7), 17),
                              "y": np.tile(np.arange(17) + 1., count), "conf": 1.,
                              "timestamp": np.repeat(times * 1000., 17)}, index=index)
        track.loc[pd.IndexSlice[:, "7", 0], "conf"] = .01
        track.attrs = copy.deepcopy(self.track.attrs)
        track.attrs["video_name"] = video.name
        track.to_pickle(self.path)
        self.app.load(check_unsaved=False)
        self.app.vw.slider.set(100.)
        self.app.vw.on_slider_changed(100.)
        self.assertIsNotNone(self.app.vw.canvas.img_on_canvas)

        def remove(dialog):
            dialog.thinning_var.set(True)
            dialog.target_fps_var.set("15")
            dialog.low_score_var.set(True)
            dialog.score_threshold_var.set(.5)
            dialog.exec_remove()
            dialog.on_ok()
        self.close_dialog(remove)
        self.app.launch_window(app_area_filter.App, edit_df=True, grab=True)
        self.assertEqual(self.app.src_df.index.get_level_values("frame").nunique(), 60)
        self.assertTrue(self.app.src_df.loc[pd.IndexSlice[:, "7", 0], "x"].isna().all())

        def smooth(dialog):
            dialog.member_keypoints_combos.set("7", "5")
            dialog.smoothing_type_combo.set("moving average")
            dialog.window_size_entry.set(3)
            dialog.calc()
            dialog.on_ok()
        self.close_dialog(smooth)
        self.app.launch_window(app_smoothing.App, edit_df=True, grab=True)
        self.assertIn("smoothing", self.app.src_df.attrs["proc_history"])

        def rename(dialog):
            dialog.tar_member_label_var.set("7")
            dialog.new_member_name_entry.update("8")
            dialog.rename_member()
            dialog.on_ok()
        self.close_dialog(rename)
        self.app.launch_window(app_member_edit.App, edit_df=True, grab=True)
        self.assertEqual(self.app.src_df.index.get_level_values("member").unique().tolist(), ["8"])

        def scene(dialog):
            dialog.tree.insert(("00:00:00.000", "00:00:03.900", "00:00:03.900", "8", "test"))
            dialog._update()
            dialog.on_ok()
        self.close_dialog(scene)
        with patch("launcher.messagebox.showinfo"):
            self.app.launch_scene_table_window(app_scene_table.App)
        self.assertEqual(self.app.src_df.attrs["scene_table"]["description"], ["test"])

        def points(dialog):
            dialog.tree.insert(["distance (|AB|)", "8", "5", "6", "None"])
            dialog.draw()
            dialog.export()
        self.close_dialog(points)
        self.app.launch_window(app_points_calc.App)
        feat_path = Path(self.temp.name) / "calc" / self.app.calc_case_entry.get() / "target.feat"
        self.assertIn("norm(5-6)", DataFrameStorage(str(feat_path)).load_points_df())

        def mix(dialog):
            dialog.tree.insert(["distance", "8", "norm(5-6)", " ", " ", "No normalize", "0-5"])
            dialog.draw()
            dialog.export()
            dialog.tree.tree.selection_set(dialog.tree.tree.get_children())
            with patch("export_csv.messagebox.showinfo"):
                dialog.export_csv()
        self.close_dialog(mix)
        self.app.launch_window(app_feat_mix.App)
        result = DataFrameStorage(str(feat_path)).load_mixnorm_df()
        self.assertIn("distance", result)
        self.assertTrue(list((Path(self.temp.name) / "csv").glob("*.csv")))
        current = copy.deepcopy(self.app.src_df)
        with patch("launcher.messagebox.showinfo"):
            self.assertTrue(self.app.overwrite())
        self.assertTrue(self.app.load())
        self.assertTrue(self.app._tracks_equal(self.app.src_df, current))
        self.assertEqual(self.capture_count, 1)


class IsolatedLauncherCase(unittest.TestCase):
    """Each launcher owns the process's sole real VideoCapture."""

    def __init__(self, test_name):
        super().__init__()
        self.test_name = test_name

    def id(self):
        return f"{__name__}.LauncherDataProtectionTests.{self.test_name}"

    def __str__(self):
        return self.id()

    def runTest(self):
        env = dict(os.environ, BEHAVIOR_LAUNCHER_TEST_CHILD="1")
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "unittest", "-v",
             f"test_launcher_data_protection.LauncherDataProtectionTests.{self.test_name}"],
            cwd=os.path.dirname(os.path.abspath(__file__)), env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def load_tests(loader, tests, pattern):
    if os.environ.get("BEHAVIOR_LAUNCHER_TEST_CHILD") == "1":
        return tests
    return unittest.TestSuite(IsolatedLauncherCase(name) for name in loader.getTestCaseNames(LauncherDataProtectionTests))


if __name__ == "__main__":
    unittest.main()
