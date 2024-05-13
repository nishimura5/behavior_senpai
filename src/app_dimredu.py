import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
from dimredu_plotter import DimensionalReductionPlotter
from gui_parts import Combobox, IntEntry, MemberKeypointComboboxes, TempFile
from python_senpai import file_inout, keypoints_proc


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Dimensional Reduction Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.drp = DimensionalReductionPlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        left_frame = ttk.Frame(self)
        left_frame.pack(side=tk.LEFT, anchor=tk.NW)

        load_frame = ttk.Frame(left_frame)
        load_frame.pack(anchor=tk.NW, pady=5)
        self.feat_button = ttk.Button(load_frame, text="Open Feature file", command=self.load_feat)
        self.feat_button.pack(side=tk.LEFT, padx=(20, 0))
        self.feat_path_label = ttk.Label(load_frame, text="No Feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(5, 0))

        proc_frame = ttk.Frame(left_frame)
        proc_frame.pack(pady=5)
        self.member_keypoints_combos = MemberKeypointComboboxes(proc_frame)

        setting_frame = ttk.Frame(left_frame)
        setting_frame.pack(pady=5)

        # column選択リストボックス、複数選択
        self.column_listbox = tk.Listbox(setting_frame, height=12, selectmode=tk.EXTENDED, exportselection=False)
        self.column_listbox.pack(side=tk.LEFT, padx=(0, 5))

        combos_frame = ttk.Frame(setting_frame)
        combos_frame.pack(side=tk.LEFT, anchor=tk.NW, fill=tk.X, expand=True, padx=5)

        self.thinning_entry = IntEntry(combos_frame, label="Thinning:", default=temp.data["thinning"])
        self.thinning_entry.pack_vertical(pady=5)

        vals = [10, 20, 30, 40, 50, 100]
        self.n_neighbors_combobox = Combobox(combos_frame, label="N_neighbors:", values=vals)
        self.n_neighbors_combobox.pack_vertical(pady=5)

        draw_btn = ttk.Button(combos_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT, expand=True, pady=5, fill=tk.X)

        draw_frame = ttk.Frame(setting_frame)
        draw_frame.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5)
        vals = [1] + [str(i) for i in range(10, 51, 10)]
        self.picker_range_combobox = Combobox(draw_frame, label="Picker range:", values=vals)
        self.picker_range_combobox.set_selected_bind(self.combo_selected)
        self.picker_range_combobox.pack_vertical(pady=5)

        vals = [str(i) for i in range(0, 9)]
        self.number_combobox = Combobox(draw_frame, label="Cluster:", values=vals)
        self.number_combobox.set_selected_bind(self.combo_selected)
        self.number_combobox.pack_vertical(pady=5)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.LEFT, anchor=tk.NW)

        self.drp.pack(plot_frame)

        self._load(args)
        self.feat_df = None

    def _load(self, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.time_min, self.time_max = args["time_span_msec"]
        self.pkl_dir = args["pkl_dir"]
        self.drp.set_vcap(self.cap)

        # UIの更新
        self.member_keypoints_combos.set_df(self.src_df)
        self.current_dt_span = None

    def load_feat(self):
        pkl_path = file_inout.open_pkl(os.path.dirname(self.pkl_dir))
        if pkl_path is None:
            return
        self.feat_path_label["text"] = pkl_path.replace(os.path.dirname(self.pkl_dir), "..")
        self.feat_name = os.path.basename(pkl_path)
        self.feat_df = file_inout.load_track_file(pkl_path, allow_calculated_track_file=True)

        # UIの更新
        self.member_keypoints_combos.set_df(self.feat_df)
        self.column_listbox.delete(0, tk.END)
        for col in self.feat_df.columns:
            if col == "timestamp":
                continue
            self.column_listbox.insert(tk.END, col)
        self.drp.clear()

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()
        cols = self.column_listbox.curselection()
        if len(cols) == 0:
            return
        cols = [self.column_listbox.get(i) for i in cols]

        # timestampの範囲を抽出
        if self.feat_df is not None:
            tar_df = self.feat_df
        tar_df = keypoints_proc.filter_by_timerange(tar_df, self.time_min, self.time_max)

        idx = tar_df.index
        if "keypoint" in idx.names:
            levels = [idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)]
            idx = pd.IndexSlice[:, current_member, current_keypoint]
        else:
            levels = [idx.levels[0], idx.levels[1].astype(str)]
            idx = pd.IndexSlice[:, current_member]

        tar_df.index = tar_df.index.set_levels(levels)

        thinning = self.thinning_entry.get()
        self.thinning_entry.save_to_temp("thinning")
        plot_df = keypoints_proc.thinning(tar_df, thinning)

        plot_df = plot_df.loc[idx, :].dropna()
        timestamps = plot_df.loc[idx, "timestamp"].values
        print(plot_df[cols])

        n_neighbors = self.n_neighbors_combobox.get()
        reduced_arr = keypoints_proc.umap(plot_df, tar_cols=cols, n_components=2, n_neighbors=int(n_neighbors))

        self.drp.draw(reduced_arr, timestamps)

    def combo_selected(self, event):
        self.drp.set_picker_range(int(self.picker_range_combobox.get()))
        self.drp.set_cluster_number(int(self.number_combobox.get()))
