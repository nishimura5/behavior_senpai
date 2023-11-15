import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import PklSelector, MemberKeypointComboboxes, ProcOptions
from trajectory_plotter import TrajectoryPlotter
import keypoints_proc


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Figure")
        self.pack(padx=10, pady=10)

        self.traj = TrajectoryPlotter(fig_size=(900/72, 700/72), dpi=72)

        load_frame = tk.Frame(self)
        self.pkl_selector = PklSelector(load_frame)
        load_frame.pack(pady=5)
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
 
        self.load_pkl()

    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = pd.read_pickle(pkl_path)

        self.member_keypoints_combos.set_df(self.src_df)

        # PKLが置かれているフォルダのパスを取得
        self.pkl_dir = os.path.dirname(pkl_path)
        self.current_dt_span = None

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

        plot_df.attrs = self.src_df.attrs

        # memberとkeypointのインデックス値を文字列に変換
        idx = plot_df.index
        plot_df.index = plot_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.traj.set_draw_param(kde_alpha=0.9, kde_adjust=0.4, kde_thresh=0.1, kde_levels=20)
        self.traj.draw(plot_df, current_member, current_keypoint, int(dt_span), int(thinning), self.pkl_dir)

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
