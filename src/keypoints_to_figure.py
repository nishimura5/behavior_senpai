import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import pandas as pd

from trajectory_plotter import TrajectoryPlotter
import keypoints_proc


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Figure")
        self.pack(padx=10, pady=10)

        self.traj = TrajectoryPlotter()
        self.current_dt_span = None

        load_frame = tk.Frame(self)
        load_frame.pack(pady=5)
        load_pkl_btn = ttk.Button(load_frame, text="Load Track", command=self.load_pkl)
        load_pkl_btn.pack(side=tk.LEFT)
        self.pkl_path_label = ttk.Label(load_frame, text="No trk loaded")
        self.pkl_path_label.pack(side=tk.LEFT)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)
        self.member_cbox = ttk.Combobox(setting_frame, state='readonly', width=12)
        self.member_cbox.pack(side=tk.LEFT, padx=5)
        self.member_cbox.bind("<<ComboboxSelected>>", self._on_selected)
        self.keypoint_cbox = ttk.Combobox(setting_frame, state='readonly', width=10)
        self.keypoint_cbox.pack(side=tk.LEFT, padx=5)
 
        dt_span_label = ttk.Label(setting_frame, text="diff period:")
        dt_span_label.pack(side=tk.LEFT)
        self.dt_span_entry = ttk.Entry(setting_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.dt_span_entry.insert(tk.END, '10')
        self.dt_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        thinning_label = ttk.Label(setting_frame, text="thinning:")
        thinning_label.pack(side=tk.LEFT)
        self.thinning_entry = ttk.Entry(setting_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.thinning_entry.insert(tk.END, '0')
        self.thinning_entry.pack(side=tk.LEFT, padx=(0, 5))

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.traj.pack(plot_frame)
 
    def load_pkl(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        pkl_path = filedialog.askopenfilename(initialdir=init_dir)
        self.pkl_path_label["text"] = pkl_path
        self.src_df = pd.read_pickle(pkl_path)

        combo_df = self.src_df
        # memberとkeypointのインデックス値を文字列に変換
        idx = combo_df.index
        combo_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.member_cbox["values"] = combo_df.index.get_level_values("member").unique().tolist()
        self.member_cbox.current(0)
        init_member = self.member_cbox.get()
        self.keypoint_cbox["values"] = combo_df.loc[pd.IndexSlice[:, init_member, :], :].index.get_level_values("keypoint").unique().tolist()

        # PKLが置かれているフォルダのパスを取得
        self.pkl_dir = os.path.dirname(pkl_path)

    def draw(self):
        current_member = self.member_cbox.get()
        current_keypoint = self.keypoint_cbox.get()

        # dt(速さ)を計算してsrc_dfに追加
        dt_span = self.dt_span_entry.get()
        if self.current_dt_span != dt_span:
            speed_df = keypoints_proc.calc_speed(self.src_df, int(dt_span))
            self.src_speed_df = pd.concat([self.src_df, speed_df], axis=1)
            self.current_dt_span = dt_span

        # thinningの値だけframeを間引く
        thinning = self.thinning_entry.get()
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

    def _on_selected(self, event):
        current_member = self.member_cbox.get()
        # keypointの一覧を取得してコンボボックスにセット
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_cbox["values"] = keypoints
        self.keypoint_cbox.current(0)

    def _validate(self, text):
        return text.isdigit()


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
