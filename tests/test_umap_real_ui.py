"""Real Tk controls, HDF5, and actual UMAP subprocesses; no capture or worker doubles."""
import os
import io
import sys
import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app_dimredu import App
from behavior_senpai import file_inout
from behavior_senpai.hdf_df import DataFrameStorage
from gui_parts import TempFile


class UmapRealUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        settings = patch.object(TempFile, "_find_data_dir", return_value=self.temp.name)
        settings.start()
        self.addCleanup(settings.stop)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = App(self.root, {"trk_pkl_name": "target.pkl"})
        self.app.unbind("<Map>")
        self.addCleanup(self.app.close)
        self.app.calc_case = "case"
        self.app.pkl_dir = os.path.join(self.temp.name, "trk")
        os.makedirs(self.app.pkl_dir)
        self.app.calc_dir = os.path.join(self.temp.name, "calc")
        self.app.track_name = "target.pkl"
        index = pd.MultiIndex.from_product([range(40), ["7"]], names=["frame", "member"])
        rng = np.random.default_rng(42)
        self.frame = pd.DataFrame(rng.normal(size=(40, 2)), index=index, columns=["a", "b"])
        self.frame["timestamp"] = np.arange(40) * 100.
        self.path = Path(self.app.calc_dir) / "case" / "target.feat"
        DataFrameStorage(str(self.path)).save_points_df(self.frame, "target.pkl", [["distance (|AB|)", "7", "0", "1", "None"]])
        loader = file_inout.PickleLoader(self.app.calc_dir)
        loader.set_tar_path(str(self.path))
        self.app.load_feat(loader)
        for name in self.app.cluster_names:
            self.app.tree.insert("", "end", values=(name, name))
        self.app.column_listbox.selection_set(0, 1)
        self.app.n_neighbors_combobox.set(5)
        self.app.min_dist_combobox.set(.1)
        self.app.umap_seed_combobox.set("fixed")

    def wait_for_worker(self):
        deadline = time.monotonic() + 180
        while self.app._umap_job is not None and time.monotonic() < deadline:
            self.root.update()
            time.sleep(.02)
        self.assertIsNone(self.app._umap_job, "Real UMAP subprocess exceeded 180 seconds")

    def test_real_failure_recovery_completion_and_hdf_save(self):
        self.app.n_neighbors_combobox.set(1)
        with patch("app_dimredu.messagebox.showerror") as error:
            self.app._draw()
            failed_process = self.app._umap_job._process
            heartbeat = []
            self.root.after(1, lambda: heartbeat.append(True))
            self.wait_for_worker()
            error.assert_called_once()
        self.assertTrue(heartbeat)
        self.assertIsNotNone(failed_process.poll())
        self.assertEqual(str(self.app.draw_button["state"]), "normal")
        self.assertEqual(self.app._busy_widgets, [])
        self.app.n_neighbors_combobox.set(5)
        with patch("app_dimredu.messagebox.showerror") as error:
            self.app._draw()
            process = self.app._umap_job._process
            # Exercise real UTF-8 progress logs on a strict Japanese Windows console.
            with io.TextIOWrapper(io.BytesIO(), encoding="cp932") as console, patch("sys.stdout", console):
                self.wait_for_worker()
            error.assert_not_called()
        self.assertEqual(process.returncode, 0)
        self.assertEqual(str(self.app.save_button["state"]), "normal")
        self.assertTrue(np.isfinite(self.app.drp.plot_df[["umap_0", "umap_1"]]).all().all())
        pd.testing.assert_index_equal(self.app.drp.plot_df.index, self.frame.index)
        pd.testing.assert_series_equal(self.app.drp.plot_df["timestamp"], self.frame["timestamp"])
        self.app.export()
        stored = DataFrameStorage(str(self.path)).load_dimredu_df()
        self.assertEqual(len(stored), len(self.frame))
        self.assertIn("class", stored)

    def test_destroy_while_real_worker_runs_terminates_child_and_cleans_files(self):
        self.app._draw()
        job = self.app._umap_job
        process = job._process
        directory = Path(job._temp.name)
        self.assertIsNone(process.poll())
        self.app.destroy()
        self.root.update()
        self.assertIsNotNone(process.poll())
        self.assertIsNone(self.app._umap_job)
        self.assertIsNone(self.app._umap_after)
        self.assertFalse(directory.exists())


if __name__ == "__main__":
    unittest.main()
