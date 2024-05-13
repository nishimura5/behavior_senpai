import os
import re
import sys
import tkinter as tk
from tkinter import ttk

import pandas as pd
from gui_parts import CalcCaseEntry, Combobox, IntEntry, TempFile
from line_plotter import LinePlotter
from python_senpai import file_inout, keypoints_proc
from vector_gui_parts import MemberKeypointComboboxesFor2Point


class App(ttk.Frame):
    """Application for calculating 2-point vectors."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("2 Point Calculation")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        cross_frame = ttk.Frame(self)
        cross_frame.pack(pady=5)
        self.calc_case_entry = CalcCaseEntry(cross_frame, temp.data["calc_case"])
        self.calc_case_entry.pack(side=tk.LEFT, padx=5)
        vals = ["all", "xy_component (AB_x, AB_y)", "norm (|AB|)"]
        self.calc_type_combo = Combobox(cross_frame, label="Calc:", width=22, values=vals)
        self.calc_type_combo.pack_horizontal(padx=5)
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", "vector_2.gif")
        self.img = tk.PhotoImage(file=img_path)
        self.img_label = ttk.Label(cross_frame, image=self.img)
        self.img_label.pack(side=tk.LEFT, padx=5)
        self.member_combo = MemberKeypointComboboxesFor2Point(cross_frame)
        self.member_combo.pack(side=tk.LEFT, padx=5)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        self.thinning_entry = IntEntry(setting_frame, label="Thinning:", default=temp.data["thinning"])
        self.thinning_entry.pack_horizontal(padx=5)

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.manual_draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(5, 0))

        export_btn = ttk.Button(setting_frame, text="Export", command=self.export)
        export_btn.pack(side=tk.LEFT, padx=(5, 50))

        repeat_btn = ttk.Button(setting_frame, text="Repeat Draw", command=self.repeat_draw)
        repeat_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)

        self._load(args)

    def _load(self, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args["time_span_msec"]

        # UIの更新
        self.member_combo.set_df(self.src_df)
        self.lineplot.set_vcap(self.cap)
        self.clear()

    def _combo_to_calc_code(self):
        code = ""
        if self.calc_type_combo.get() == "xy_component (AB_x, AB_y)":
            code = "component"
        elif self.calc_type_combo.get() == "norm (|AB|)":
            code = "norm"
        elif self.calc_type_combo.get() == "all":
            code = "all"
        return code

    def manual_draw(self):
        """Call _draw based on the selected member and calculation code."""
        current_member, kp0, kp1 = self.member_combo.get_selected()
        code = self._combo_to_calc_code()
        self._draw(current_member, code, kp0, kp1)

    def repeat_draw(self):
        """Open a file dialog to select a feature file.
        Extract the column names from the selected file.
        Call _draw based on the selected member and extracted calculation codes.
        """
        current_member, _, _ = self.member_combo.get_selected()
        calc_case = self.calc_case_entry.get_calc_case()
        init_dir = os.path.join(self.calc_dir, calc_case)
        in_trk_path = file_inout.open_pkl(init_dir)
        if in_trk_path is None:
            return
        in_trk_df = file_inout.load_track_file(in_trk_path, allow_calculated_track_file=True)
        pattern = r"(\w+)\((\w+)-(\w+)\)"
        cols = in_trk_df.columns.tolist()

        # suffix '_x'と'_y'があるときは'_y'を削除、片方しかないときは削除しない
        contains_x = any(map(lambda x: x.endswith("_x"), cols))
        contains_y = any(map(lambda x: x.endswith("_y"), cols))
        if contains_x and contains_y:
            cols = [item for item in cols if not item.endswith("_y")]

        for col in cols:
            if col == "timestamp":
                continue
            match = re.match(pattern, col)
            if not match:
                continue
            calc_code = match.group(1)
            kp_a = match.group(2)
            kp_b = match.group(3)
            self._draw(current_member, calc_code, kp_a, kp_b)

    def _draw(self, current_member, calc_code, kp0, kp1):
        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # 重複インデックス削除
        tar_df = tar_df[~tar_df.index.duplicated(keep="last")]
        # current_memberのみ抽出
        tar_df = tar_df.loc[pd.IndexSlice[:, current_member, :], :]

        # memberとkeypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        if calc_code == "component":
            prod_df = keypoints_proc.calc_xy_component(tar_df, kp0, kp1)
        elif calc_code == "norm":
            prod_df = keypoints_proc.calc_norm(tar_df, kp0, kp1)
        elif calc_code == "all":
            xy_df = keypoints_proc.calc_xy_component(tar_df, kp0, kp1)
            norm_df = keypoints_proc.calc_norm(tar_df, kp0, kp1)
            prod_df = pd.concat([xy_df, norm_df], axis=1)

        col_names = prod_df.columns

        self.timestamp_df = tar_df.loc[:, "timestamp"].droplevel(2).to_frame()
        plot_df = pd.concat([prod_df, self.timestamp_df], axis=1)

        for col_name in col_names:
            if col_name not in self.calc_df.columns:
                add_df = plot_df.loc[:, col_name].to_frame()
                self.calc_df = pd.concat([self.calc_df, add_df], axis=1)

        # thinningの値だけframeを間引く
        thinning = self.thinning_entry.get()
        self.thinning_entry.save_to_temp("thinning")
        plot_df = keypoints_proc.thinning(plot_df, thinning)

        self.lineplot.set_trk_df(self.src_df)
        self.lineplot.set_plot(plot_df, current_member, col_names)
        self.lineplot.draw()

    def export(self):
        """Export the calculated data to a file."""
        if len(self.calc_df) == 0:
            print("No data to export.")
            return
        file_name = os.path.splitext(self.src_attrs["video_name"])[0]
        timestamp_df = self.timestamp_df
        timestamp_df = timestamp_df[~timestamp_df.index.duplicated(keep="last")]
        self.calc_df = self.calc_df[~self.calc_df.index.duplicated(keep="last")]
        export_df = pd.concat([self.calc_df, timestamp_df], axis=1)
        export_df.attrs = self.src_attrs
        calc_case = self.calc_case_entry.get_calc_case()
        dst_path = os.path.join(self.calc_dir, calc_case, file_name + "_2p.pkl")
        file_inout.save_pkl(dst_path, export_df, proc_history="2p_vector")

    def clear(self):
        """Clear the lineplot and reset the calc_df."""
        self.lineplot.clear()
        self.calc_df = pd.DataFrame()

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir
