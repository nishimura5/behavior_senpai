import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from behavior_senpai import keypoints_proc
from behavior_senpai.umap_process import UmapJob, UmapProcessError


class UmapProcessTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(12)
        index = pd.MultiIndex.from_product([range(24), ["animal"]], names=["frame", "member"])
        self.data = pd.DataFrame(rng.normal(size=(24, 3)), index=index, columns=["a", "b", "unused"])
        self.data["timestamp"] = np.arange(24) * 100.
        self.data.loc[(3, "animal"), "a"] = np.nan
        self.params = dict(tar_cols=["a", "b"], n_components=2, n_neighbors=5, min_dist=0.1, seed=42)

    def wait_result(self, job):
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            result = job.poll()
            if result is not None:
                return result
            time.sleep(0.05)
        self.fail("UMAP worker did not finish within 180 seconds")

    def test_process_matches_existing_calculation_and_cleans_up(self):
        # Unpickleable GUI-like metadata must never be sent to the child.
        self.data.attrs["callback"] = lambda: None
        job = UmapJob(self.data, **self.params)
        root = Path(job._temp.name)
        try:
            result = self.wait_result(job)
            expected = keypoints_proc.umap(self.data, **self.params)
            pd.testing.assert_frame_equal(result, expected)
            self.assertTrue(result.loc[(3, "animal"), ["umap_0", "umap_1", "umap_t"]].isna().all())
            self.assertFalse(root.exists())
        finally:
            job.close()

    def test_worker_exception_is_reported_and_cleans_up(self):
        params = {**self.params, "n_neighbors": 1}
        job = UmapJob(self.data, **params)
        root = Path(job._temp.name)
        try:
            with self.assertRaisesRegex(UmapProcessError, "n_neighbors"):
                self.wait_result(job)
            self.assertFalse(root.exists())
        finally:
            job.close()

    def test_random_seed_with_approximate_parallel_neighbor_search(self):
        # Above UMAP's small-data threshold, exercise the NNDescent path in the log.
        rng = np.random.default_rng(19)
        data = pd.DataFrame(rng.normal(size=(4100, 3)), columns=["a", "b", "timestamp"])
        with patch.dict(os.environ, {"NUMBA_NUM_THREADS": "2"}):
            job = UmapJob(data, **{**self.params, "seed": None})
        try:
            result = self.wait_result(job)
            self.assertEqual(result.shape, (4100, 4))
            pd.testing.assert_series_equal(result["timestamp"], data["timestamp"])
            self.assertTrue(np.isfinite(result[["umap_0", "umap_1"]].to_numpy()).all())
        finally:
            job.close()

    def start_stub(self, code):
        import subprocess

        popen = subprocess.Popen

        def start(command, **kwargs):
            return popen([sys.executable, "-c", code], **kwargs)

        with patch("behavior_senpai.umap_process.subprocess.Popen", side_effect=start):
            return UmapJob(self.data, **self.params)

    def test_abrupt_exit_is_reported_and_parent_can_start_another_job(self):
        job = self.start_stub("import os; os._exit(23)")
        root = Path(job._temp.name)
        try:
            with self.assertRaisesRegex(UmapProcessError, "code 23"):
                self.wait_result(job)
            self.assertFalse(root.exists())
        finally:
            job.close()
        next_job = self.start_stub("import time; time.sleep(60)")
        next_job.close()
        self.assertIsNotNone(next_job._process.poll())

    def test_close_terminates_running_worker_and_is_idempotent(self):
        job = self.start_stub("import time; time.sleep(60)")
        root = Path(job._temp.name)
        self.assertIsNone(job.poll())
        job.close()
        job.close()
        self.assertIsNotNone(job._process.poll())
        self.assertFalse(root.exists())


if __name__ == "__main__":
    unittest.main()
