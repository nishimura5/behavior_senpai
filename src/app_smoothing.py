import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import TempFile, MemberKeypointComboboxes
from line_plotter import LinePlotter
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    x,y座標の平滑化を実行します
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Smoothing")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.plot = LinePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(fill=tk.X, side=tk.LEFT, expand=True)
        draw_frame = ttk.Frame(setting_frame)
        draw_frame.pack(fill=tk.X, expand=True)

        self.member_keypoints_combos = MemberKeypointComboboxes(draw_frame)
        draw_button = ttk.Button(draw_frame, text="Draw", command=self.draw)
        draw_button.pack(side=tk.LEFT, padx=10)
        clear_button = ttk.Button(draw_frame, text="Clear", command=self.clear)
        clear_button.pack(side=tk.LEFT)

        calc_frame = ttk.Frame(setting_frame)
        calc_frame.pack(fill=tk.X, expand=True, pady=(5, 0))
        smoothing_type_label = ttk.Label(calc_frame, text="Smoothing type:")
        smoothing_type_label.pack(side=tk.LEFT, padx=(0, 10))
        self.smoothing_type_combo = ttk.Combobox(calc_frame, state='readonly', width=18)
        self.smoothing_type_combo["values"] = ["moving average"]
        self.smoothing_type_combo.current(0)
        self.smoothing_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        window_size_label = ttk.Label(calc_frame, text="Window size:")
        window_size_label.pack(side=tk.LEFT, padx=(0, 5))
        self.window_size_entry = ttk.Entry(calc_frame, width=5)
        self.window_size_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.window_size_entry.insert(0, "5")
        calc_button = ttk.Button(calc_frame, text="Calc", command=self.calc)
        calc_button.pack(side=tk.LEFT, padx=(10, 0))

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.plot.pack(plot_frame)

        self.dst_df = None
        self.current_df = None
        self.history = "smoothing"
        self.load(args)

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.member_keypoints_combos.set_df(self.src_df)
        self.current_dt_span = None
        self.clear()

        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])
        self.plot.set_vcap(self.cap)

        # memberの数をカウント
        members = self.src_df.dropna().index.get_level_values(1).unique()
        print(f"members: {len(members)}")

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # keypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])

        plot_df = tar_df.loc[pd.IndexSlice[:, :, current_keypoint], :]
        self.plot.set_trk_df(tar_df)
        self.plot.set_plot(plot_df, current_member, ['x', 'y'])
        self.plot.draw()

    def calc(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()
        smoothing_type = self.smoothing_type_combo.get()
        window_size = int(self.window_size_entry.get())

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # keypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(int)])

        if smoothing_type == "moving average":
            tar_df = keypoints_proc.calc_moving_average(tar_df, window_size)
        else:
            print("smoothing type is not supported")
            tar_df = None

        tar_df.attrs = self.src_df.attrs
        self.current_df = tar_df

        plot_df = tar_df.loc[pd.IndexSlice[:, :, int(current_keypoint)], :]
        new_x = f"x({window_size})"
        new_y = f"y({window_size})"
        plot_df = plot_df.rename(columns={"x": new_x, "y": new_y})
        self.plot.set_trk_df(tar_df)
        self.plot.set_plot(plot_df, current_member, [new_x, new_y])
        self.plot.draw()

    def on_ok(self):
        if self.current_df is None:
            return
        self.dst_df = self.current_df.copy()
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def cancel(self):
        self.dst_df = None
        self.master.destroy()

    def clear(self):
        self.plot.clear()
