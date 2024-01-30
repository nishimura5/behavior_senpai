import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import MemberKeypointComboboxes, ProcOptions, TempFile
from trajectory_plotter import TrajectoryPlotter
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    軌跡の時系列グラフ(Trajectory Plot)を描画するためのGUIです。
    以下の機能を有します
     - 描画するmemberとkeypointを指定する機能
     - 速さ計算と間引き処理を行う機能
     - 以上の処理で得られたデータをTrajectoryPlotterに渡す機能
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Keypoints to Trajectory Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.traj = TrajectoryPlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        setting_frame = ttk.Frame(self)
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

        self.load(args)

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.member_keypoints_combos.set_df(self.src_df)
        self.current_dt_span = None

        self.traj.set_vcap(self.cap)
        print('load() done.')

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
