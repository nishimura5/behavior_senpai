import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from behavior_senpai import df_attrs, hdf_df, keypoints_proc
from gui_parts import IntEntry, MemberKeypointComboboxes, TempFile
from trajectory_plotter import TrajectoryPlotter


class App(ttk.Frame):
    """Application for plotting keypoints to trajectory."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Trajectory Plot")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.calc_case = temp.data["calc_case"]
        self.traj = TrajectoryPlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        top_frame = ttk.Frame(self)
        top_frame.pack(pady=5, fill=tk.X, anchor=tk.W)

        self.member_keypoints_combos = MemberKeypointComboboxes(top_frame)

        self.diff_entry = IntEntry(top_frame, label="Diff period:", default=temp.data["dt_span"])
        self.diff_entry.pack_horizontal(padx=5)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5, fill=tk.X, anchor=tk.W)

        self.thinning_entry = IntEntry(setting_frame, label="Thinning:", default=temp.data["thinning"])
        self.thinning_entry.pack_horizontal(padx=(0, 5))

        draw_btn = ttk.Button(setting_frame, text="Add and draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))

        export_btn = ttk.Button(setting_frame, text="Save", command=self.export)
        export_btn.pack(side=tk.LEFT, padx=(5, 50))

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.traj.pack(plot_frame)

    def _load(self, event, args):
        src_df = args["src_df"].copy()
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.tar_df = src_df[~src_df.index.duplicated(keep="last")]

        idx = self.tar_df.index
        self.tar_df.index = self.tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(int)])

        self.traj.set_vcap(args["cap"])
        self.track_name = args["trk_pkl_name"]
        self.src_attrs = df_attrs.DfAttrs(src_df)

        # Update GUI
        self.member_keypoints_combos.set_df(self.tar_df)
        self.feat_df = pd.DataFrame()

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()
        self.timestamp_df = self.tar_df.loc[:, "timestamp"].droplevel(2).to_frame()

        # speedを計算してsrc_dfに追加
        dt_span = self.diff_entry.get()
        speed_df = keypoints_proc.calc_speed(self.tar_df, int(dt_span))
        plot_df = pd.concat([self.tar_df, speed_df], axis=1)
        self.current_dt_span = dt_span

        # make export data
        calc_df = plot_df.loc[pd.IndexSlice[:, :, int(current_keypoint)], :].droplevel(2)
        calc_df = calc_df.drop(columns="timestamp").add_suffix(f"({current_keypoint})")
        self.feat_df = pd.concat([self.feat_df, calc_df], axis=1)

        # thinning for plotting
        thinning = self.thinning_entry.get()
        plot_df = keypoints_proc.thinning(plot_df, int(thinning))

        idx = plot_df.index
        plot_df.index = plot_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

        self.traj.set_draw_param(kde_alpha=0.9, kde_adjust=0.4, kde_thresh=0.1, kde_levels=20)
        self.traj.draw(plot_df, current_member, int(current_keypoint), int(dt_span), int(thinning))

    def clear(self):
        """Clear the trajplot and reset the calc_df."""
        self.traj.clear()
        self.current_dt_span = None
        self.feat_df = pd.DataFrame()

    def export(self):
        """Export the calculated data to a file."""
        if len(self.feat_df) == 0:
            print("No data to export.")
            return
        file_name = os.path.splitext(self.track_name)[0]
        timestamp_df = self.timestamp_df
        timestamp_df = timestamp_df[~timestamp_df.index.duplicated(keep="last")]
        self.feat_df = self.feat_df[~self.feat_df.index.duplicated(keep="last")]
        export_df = pd.concat([self.feat_df, timestamp_df], axis=1)
        export_df.attrs = self.src_attrs.attrs
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + ".feat")
        history_dict = df_attrs.make_history_dict("trajectory", [], {}, self.track_name)
        h5 = hdf_df.DataFrameStorage(dst_path)
        h5.save_traj_df(export_df, history_dict["track_name"])

    def close(self):
        self.traj.close()
