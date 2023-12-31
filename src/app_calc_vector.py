import sys
import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import PklSelector, TimeSpanEntry, MemberKeypointComboboxesForCross, ThinningOption, TempFile
from line_plotter import LinePlotter
from python_senpai import keypoints_proc
from python_senpai import vcap
from python_senpai import file_inout


class App(ttk.Frame):
    """
    外積の結果を描画するためのGUIです。
    以下の機能を有します
     - Trackファイルを選択して読み込む機能
     - 計算対象の時間帯の指定を行う機能
     - 以上の処理で得られたデータをLinePlotterに渡す機能
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Calc Vector")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.lineplot = LinePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        load_frame = ttk.Frame(self)
        load_frame.pack(pady=5, anchor=tk.W)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        cross_frame = ttk.Frame(self)
        cross_frame.pack(pady=5)
        calc_type_label = ttk.Label(cross_frame, text="Calc:")
        calc_type_label.pack(side=tk.LEFT, padx=5)
        self.calc_type_combo = ttk.Combobox(cross_frame, state='readonly', width=18)
        self.calc_type_combo["values"] = ["all", "cross_product (AB×AC)", "dot_product (AB・AC)", "plus (AB+AC)", "norms (|AB||AC|)"]
        self.calc_type_combo.current(0)
        self.calc_type_combo.pack(side=tk.LEFT, padx=5)
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", "vector.gif")
        self.img = tk.PhotoImage(file=img_path)
        self.img_label = ttk.Label(cross_frame, image=self.img)
        self.img_label.pack(side=tk.LEFT, padx=5)
        self.member_combo = MemberKeypointComboboxesForCross(cross_frame)
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

        self.cap = vcap.VideoCap()
        self.load_pkl()

    def load_pkl(self):
        # ファイルのロード
        self.pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = file_inout.load_track_file(self.pkl_path)
        pkl_dir = os.path.dirname(self.pkl_path)
        self.cap.set_frame_size(self.src_df.attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, self.src_df.attrs["video_name"]))

        # UIの更新
        self.member_combo.set_df(self.src_df)
        self.time_span_entry.update_entry(self.src_df["timestamp"].min(), self.src_df["timestamp"].max())
        self.pkl_selector.set_prev_next(self.src_df.attrs)
        self.lineplot.set_vcap(self.cap)
        self.clear()
        print('load_pkl() done.')

    def draw(self):
        current_member, kp0, kp1, kp2 = self.member_combo.get_selected()

        # timestampの範囲を抽出
        time_min, time_max = self.time_span_entry.get_start_end()
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, time_min, time_max)
        # 重複インデックス削除
        tar_df = tar_df.reset_index().drop_duplicates(subset=['frame', 'member', 'keypoint'], keep='last').set_index(['frame', 'member', 'keypoint'])

        # memberとkeypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        if self.calc_type_combo.get() == 'cross_product (AB×AC)':
            prod_df = keypoints_proc.calc_cross_product(tar_df, kp0, kp1, kp2)
        elif self.calc_type_combo.get() == 'dot_product (AB・AC)':
            prod_df = keypoints_proc.calc_dot_product(tar_df, kp0, kp1, kp2)
        elif self.calc_type_combo.get() == 'plus (AB+AC)':
            prod_df = keypoints_proc.calc_plus(tar_df, kp0, kp1, kp2)
        elif self.calc_type_combo.get() == 'norms (|AB||AC|)':
            prod_df = keypoints_proc.calc_norms(tar_df, kp0, kp1, kp2)
        elif self.calc_type_combo.get() == 'all':
            prod_df = keypoints_proc.calc_cross_dot_plus_angle(tar_df, kp0, kp1, kp2)

        col_names = prod_df.columns

        self.timestamp_df = tar_df.loc[:, 'timestamp'].droplevel(2).to_frame()
        plot_df = pd.concat([prod_df, self.timestamp_df], axis=1)

        for col_name in col_names:
            if col_name not in self.dst_df.columns:
                add_df = plot_df.loc[:, col_name].to_frame()
                self.dst_df = pd.concat([self.dst_df, add_df], axis=1)

        # thinningの値だけframeを間引く
        thinning = self.thinnig_option.get_thinning()
        plot_df = keypoints_proc.thinning(plot_df, int(thinning))

        self.lineplot.draw(plot_df, current_member, col_names, int(thinning))

    def export(self):
        if len(self.dst_df) == 0:
            print("No data to export.")
            return
        timestamp_df = self.timestamp_df
        timestamp_df = timestamp_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        self.dst_df = self.dst_df.reset_index().drop_duplicates(subset=['frame', 'member'], keep='last').set_index(['frame', 'member'])
        export_df = pd.concat([self.dst_df, timestamp_df], axis=1)
        export_df.attrs = self.src_df.attrs
        file_inout.save_pkl(self.pkl_path, export_df, proc_history="vector")

    def clear(self):
        self.lineplot.clear()
        self.dst_df = pd.DataFrame()

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir


def quit(root):
    root.quit()
    root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
