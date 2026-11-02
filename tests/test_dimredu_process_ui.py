import os
import sys
import tkinter as tk
import unittest
from tkinter import ttk
from unittest.mock import Mock, patch

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app_dimredu import App
from behavior_senpai.umap_process import UmapProcessError


class DimreduProcessUiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = App.__new__(App)
        ttk.Frame.__init__(self.app, self.root)
        self.app._controls_frame = ttk.Frame(self.app)
        self.app.draw_button = ttk.Button(self.app._controls_frame, text="Draw")
        self.app.save_button = ttk.Button(self.app._controls_frame, state=tk.DISABLED)
        self.combo = ttk.Combobox(self.app._controls_frame, state="readonly")
        self.app.tree = ttk.Treeview(self.app._controls_frame)
        self.app.tree.insert("", "end", iid="0")
        self.app._busy_widgets = []
        self.app._umap_after = None
        self.app._umap_job = Mock()
        self.app.drp = Mock(plot_df=None)
        self.app.bind("<Destroy>", self.app._on_destroy, add="+")
        self.root.update_idletasks()

    def tearDown(self):
        self.root.destroy()

    def test_waiting_keeps_tk_event_loop_responsive_and_restores_states(self):
        self.app._set_umap_busy(True)
        self.assertEqual(str(self.combo.cget("state")), "disabled")
        self.app._umap_job.poll.return_value = None
        self.app._poll_umap("animal", None)
        heartbeat = []
        self.root.after(0, lambda: heartbeat.append(True))
        self.root.update()
        self.assertEqual(heartbeat, [True])
        self.assertIsNotNone(self.app._umap_after)
        self.app._stop_umap()
        self.app._set_umap_busy(False)
        self.assertEqual(str(self.combo.cget("state")), "readonly")
        self.assertEqual(str(self.app.save_button.cget("state")), "disabled")

    def test_failure_restores_controls_and_reports_error(self):
        self.app._set_umap_busy(True)
        self.app._umap_job.poll.side_effect = UmapProcessError("worker crashed")
        with patch("app_dimredu.messagebox.showerror") as showerror:
            self.app._poll_umap("animal", None)
        self.assertIsNone(self.app._umap_job)
        self.assertEqual(str(self.app.draw_button.cget("state")), "normal")
        self.assertEqual(str(self.app.save_button.cget("state")), "disabled")
        showerror.assert_called_once()

    def test_success_draws_on_gui_and_enables_save(self):
        result = pd.DataFrame({"umap_0": [0.], "umap_1": [1.]})
        self.app._umap_job.poll.return_value = result
        self.app._set_umap_busy(True)
        self.app._poll_umap("animal", None)
        self.app.drp.draw.assert_called_once_with(result, None)
        self.assertIsNone(self.app._umap_job)
        self.assertEqual(str(self.app.save_button.cget("state")), "normal")

    def test_destroy_cancels_pending_callback_and_stops_worker(self):
        job = self.app._umap_job
        self.app._umap_after = self.app.after(1000, lambda: self.fail("Callback survived destruction"))
        self.app.destroy()
        job.close.assert_called_once()
        self.assertIsNone(self.app._umap_after)
        self.assertIsNone(self.app._umap_job)


if __name__ == "__main__":
    unittest.main()
