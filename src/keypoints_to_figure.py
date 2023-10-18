import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import pandas as pd

from keypoint_plotter import KeypointPlotter


class App(tk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Keypoints to Figure")
        self.pack(padx=10, pady=10)

        self.kp = KeypointPlotter()

        load_pkl_frame = tk.Frame(self)
        load_pkl_frame.pack(pady=5)
        load_pkl_btn = ttk.Button(load_pkl_frame, text="Load Track", command=self.load_pkl)
        load_pkl_btn.pack(side=tk.LEFT)
        self.pkl_path_label = ttk.Label(load_pkl_frame, text="No trk loaded")
        self.pkl_path_label.pack(side=tk.LEFT)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)
        self.member_cbox = ttk.Combobox(setting_frame, state='readonly', width=12)
        self.member_cbox.pack(side=tk.LEFT, padx=5)
        self.member_cbox.bind("<<ComboboxSelected>>", self._on_selected)
        self.keypoint_cbox = ttk.Combobox(setting_frame, state='readonly', width=10)
        self.keypoint_cbox.pack(side=tk.LEFT, padx=5)
        self.plot_style_cbox = ttk.Combobox(setting_frame, values=self.kp.plot_styles, state='readonly', width=10)
        self.plot_style_cbox.pack(side=tk.LEFT, padx=5)
        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.kp.pack(plot_frame)
 
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

    def draw(self):
        current_member = self.member_cbox.get()
        current_keypoint = self.keypoint_cbox.get()
        plot_style = self.plot_style_cbox.get()
        self.kp.draw(self.src_df, current_member, current_keypoint, plot_style)

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
