import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
import numpy as np

from gui_parts import PklSelector, MemberKeypointComboboxes, ProcOptions, TempFile
from trajectory_plotter import TrajectoryPlotter
import keypoints_proc
import vcap


class App(tk.Frame):
    """
    軌跡の時系列グラフ(Trajectory Plot)を描画するためのGUIです。
    以下の機能を有します
     - Trackファイルを選択して読み込む機能
     - 描画するmemberとkeypointを指定する機能
     - 速さ計算と間引き処理を行う機能
     - 以上の処理で得られたデータをTrajectoryPlotterに渡す機能
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Trajectory Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.traj = TrajectoryPlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        load_frame = tk.Frame(self)
        load_frame.pack(pady=5)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)
        self.member_keypoints_combos = MemberKeypointComboboxes(setting_frame)
        self.proc_options = ProcOptions(setting_frame)

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.traj.pack(plot_frame)
 
        self.cap = vcap.VideoCap()
        self.load_pkl()

    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = pd.read_pickle(pkl_path)

        self.src_df['x'] = np.where(self.src_df['x'] == 0, np.nan, self.src_df['x'])
        self.src_df['y'] = np.where(self.src_df['y'] == 0, np.nan, self.src_df['y'])
 
        self.member_keypoints_combos.set_df(self.src_df)

        # PKLが置かれているフォルダのパスを取得
        pkl_dir = os.path.dirname(pkl_path)
        self.current_dt_span = None

        self.pkl_selector.set_prev_next(self.src_df.attrs)

        self.cap.set_frame_size(self.src_df.attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, self.src_df.attrs["video_name"]))
        self.traj.set_vcap(self.cap)

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()

        # speedを計算してsrc_dfに追加
        dt_span = self.proc_options.get_dt_span()
        if self.current_dt_span != dt_span:
            speed_df = keypoints_proc.calc_speed(self.src_df, int(dt_span))
            self.src_speed_df = pd.concat([self.src_df, speed_df], axis=1)
            self.current_dt_span = dt_span

        # thinningの値だけframeを間引く
        thinning = self.proc_options.get_thinning()
        plot_df = keypoints_proc.thinning(self.src_speed_df, int(thinning))

        # memberとkeypointのインデックス値を文字列に変換
        idx = plot_df.index
        plot_df.index = plot_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.traj.set_draw_param(kde_alpha=0.9, kde_adjust=0.4, kde_thresh=0.1, kde_levels=20)
        self.traj.draw(plot_df, current_member, current_keypoint, int(dt_span), int(thinning))

    def clear(self):
        self.traj.clear()
        self.current_dt_span = None


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
