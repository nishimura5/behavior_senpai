import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
import numpy as np

from gui_parts import PklSelector, MemberKeypointComboboxes, ProcOptions
from recurrence_plotter import RecurrencePlotter
import keypoints_proc


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Recuplot")
        self.pack(padx=10, pady=10)

        self.recu = RecurrencePlotter()

        load_frame = tk.Frame(self)
        load_frame.pack(pady=5)

        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)

        proc_frame = tk.Frame(self)
        proc_frame.pack(pady=5)

        self.member_keypoints_combos = MemberKeypointComboboxes(proc_frame)
        self.proc_options = ProcOptions(proc_frame)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)

        eps_label = ttk.Label(setting_frame, text="threshold:")
        eps_label.pack(side=tk.LEFT)
        self.eps_entry = ttk.Entry(setting_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.eps_entry.insert(tk.END, '1')
        self.eps_entry.pack(side=tk.LEFT, padx=(0, 5))

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.recu.pack(plot_frame)
 
    def load_pkl(self):
        pkl_path = self.pkl_selector.pkl_path
        self.src_df = pd.read_pickle(pkl_path)

        self.member_keypoints_combos.set_df(self.src_df)

        # PKLが置かれているフォルダのパスを取得
        self.pkl_dir = os.path.dirname(pkl_path)
        self.current_dt_span = None

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()

        # dt(速さ)を計算してsrc_dfに追加
        dt_span = self.proc_options.get_dt_span()
        if self.current_dt_span != dt_span:
            speed_df = keypoints_proc.calc_speed(self.src_df, int(dt_span))
            self.src_speed_df = pd.concat([self.src_df, speed_df], axis=1)
            self.current_dt_span = dt_span

        # thinningの値だけframeを間引く
        thinning = self.proc_options.get_thinning()
        plot_df = keypoints_proc.thinning(self.src_speed_df, int(thinning))

        video_path = os.path.join(self.pkl_dir, os.pardir, self.src_df.attrs["video_name"])

        # memberとkeypointのインデックス値を文字列に変換
        idx = plot_df.index
        plot_df.index = plot_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        threshold = self.eps_entry.get()
        plot_df = plot_df.loc[pd.IndexSlice[:, current_member, current_keypoint], [f'dt_{dt_span}']].dropna()
        recu_arr = keypoints_proc.calc_recurrence(plot_df, threshold=float(threshold))

        self.recu.draw(recu_arr, current_member, current_keypoint, int(dt_span), int(thinning), video_path)

    def clear(self):
        self.recu.clear()
        self.current_dt_span = None

    def _validate(self, text):
        return text.replace(".", "").isdigit()


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
