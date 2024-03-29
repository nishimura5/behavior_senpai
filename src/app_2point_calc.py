import sys
import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from vector_gui_parts import MemberKeypointComboboxesFor2Point
from gui_parts import ThinningOption, TempFile
from line_plotter import LinePlotter
from python_senpai import keypoints_proc
from python_senpai import file_inout


class App(ttk.Frame):
    """
    以下の機能を有します
     - 2点の座標からベクトルを計算
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("2 Point Calculation")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.lineplot = LinePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        cross_frame = ttk.Frame(self)
        cross_frame.pack(pady=5)
        calc_type_label = ttk.Label(cross_frame, text="Calc:")
        calc_type_label.pack(side=tk.LEFT, padx=5)
        self.calc_type_combo = ttk.Combobox(cross_frame, state='readonly', width=22)
        self.calc_type_combo["values"] = ["all", "xy_component (AB_x, AB_y)", "norm (|AB|)"]
        self.calc_type_combo.current(0)
        self.calc_type_combo.pack(side=tk.LEFT, padx=5)
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", "vector_2.gif")
        self.img = tk.PhotoImage(file=img_path)
        self.img_label = ttk.Label(cross_frame, image=self.img)
        self.img_label.pack(side=tk.LEFT, padx=5)
        self.member_combo = MemberKeypointComboboxesFor2Point(cross_frame)
        self.member_combo.pack(side=tk.LEFT, padx=5)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        self.thinnig_option = ThinningOption(setting_frame)
        self.thinnig_option.pack(side=tk.LEFT, padx=5)

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        export_btn = ttk.Button(setting_frame, text="Export", command=self.export)
        export_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)

        self.load(args)

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.pkl_dir = args['pkl_dir']
        self.src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.member_combo.set_df(self.src_df)
        self.lineplot.set_vcap(self.cap)
        self.clear()

    def draw(self):
        current_member, kp0, kp1 = self.member_combo.get_selected()

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # 重複インデックス削除
        tar_df = tar_df.reset_index().drop_duplicates(subset=['frame', 'member', 'keypoint'], keep='last').set_index(['frame', 'member', 'keypoint'])

        # memberとkeypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        if self.calc_type_combo.get() == 'xy_component (AB_x, AB_y)':
            prod_df = keypoints_proc.calc_xy_component(tar_df, kp0, kp1)
        elif self.calc_type_combo.get() == 'norm (|AB|)':
            prod_df = keypoints_proc.calc_norm(tar_df, kp0, kp1)
        elif self.calc_type_combo.get() == 'all':
            xy_df = keypoints_proc.calc_xy_component(tar_df, kp0, kp1)
            norm_df = keypoints_proc.calc_norm(tar_df, kp0, kp1)
            prod_df = pd.concat([xy_df, norm_df], axis=1)

        col_names = prod_df.columns

        self.timestamp_df = tar_df.loc[:, 'timestamp'].droplevel(2).to_frame()
        plot_df = pd.concat([prod_df, self.timestamp_df], axis=1)

        for col_name in col_names:
            if col_name not in self.calc_df.columns:
                add_df = plot_df.loc[:, col_name].to_frame()
                self.calc_df = pd.concat([self.calc_df, add_df], axis=1)

        # thinningの値だけframeを間引く
        thinning = self.thinnig_option.get_thinning()
        plot_df = keypoints_proc.thinning(plot_df, int(thinning))

        self.lineplot.set_trk_df(self.src_df)
        self.lineplot.set_plot(plot_df, current_member, col_names)
        self.lineplot.draw()

    def export(self):
        if len(self.calc_df) == 0:
            print("No data to export.")
            return
        file_name = os.path.splitext(self.src_attrs['video_name'])[0]
        timestamp_df = self.timestamp_df
        timestamp_df = timestamp_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        self.calc_df = self.calc_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        export_df = pd.concat([self.calc_df, timestamp_df], axis=1)
        export_df.attrs = self.src_attrs
        dst_path = os.path.join(self.pkl_dir, file_name + "_2p.pkl")
        file_inout.save_pkl(dst_path, export_df, proc_history="2p_vector")

    def clear(self):
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
