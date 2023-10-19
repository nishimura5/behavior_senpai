import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import pandas as pd
import cv2

from trajectory_plotter import TrajectoryPlotter


class App(tk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Keypoints to Figure")
        self.pack(padx=10, pady=10)

        self.traj = TrajectoryPlotter()

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
        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.traj.pack(plot_frame)
 
    def load_pkl(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        pkl_path = filedialog.askopenfilename(initialdir=init_dir)
        self.pkl_path_label["text"] = pkl_path
        self.src_df = pd.read_pickle(pkl_path)

        # memberとkeypointのインデックス値を文字列に変換
        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.member_cbox["values"] = self.src_df.index.get_level_values("member").unique().tolist()
        self.member_cbox.current(0)
        init_member = self.member_cbox.get()
        self.keypoint_cbox["values"] = self.src_df.loc[pd.IndexSlice[:, init_member, :], :].index.get_level_values("keypoint").unique().tolist()

        # mp4のパスを取得
        file_name = os.path.splitext(os.path.basename(pkl_path))[0]
        self.video_path = os.path.join(os.path.dirname(pkl_path), os.pardir, f"{file_name}.mp4")

    def load_video(self, video_path):
        cap = None
        if os.path.exists(video_path) is True:
            cap = cv2.VideoCapture(video_path)
        return cap

    def draw(self):
        # mp4を読み込む
        cap = self.load_video(self.video_path)

        current_member = self.member_cbox.get()
        current_keypoint = self.keypoint_cbox.get()
        self.traj.draw(self.src_df, current_member, current_keypoint, cap)

    def _on_selected(self, event):
        current_member = self.member_cbox.get()
        self.keypoint_cbox["values"] = self.src_df.loc[pd.IndexSlice[:, current_member, :], :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_cbox.current(0)


def quit(root):
    root.quit()
    root.destroy()


def main(args):
    root = tk.Tk()
    app = App(root, args)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":

    args = None

    main(args)
    exit()
