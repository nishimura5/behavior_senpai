import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import pandas as pd
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from matplotlib import ticker

import keypoints_proc


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Another")
        self.pack(padx=10, pady=10)

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
        csv_btn = ttk.Button(setting_frame, text="To CSV", command=self.to_csv)
        csv_btn.pack(side=tk.LEFT)

    def load_pkl(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        pkl_path = filedialog.askopenfilename(initialdir=init_dir)
        self.pkl_path_label["text"] = pkl_path
        self.src_df = pd.read_pickle(pkl_path)

        # dt(速さ)を計算してsrc_dfに追加
        dt_df = keypoints_proc.calc_dt(self.src_df, 60)
        self.plot_df = pd.concat([self.src_df, dt_df], axis=1)
        dt_df = keypoints_proc.calc_dt(self.src_df, 120)
        self.plot_df = pd.concat([self.plot_df, dt_df], axis=1)
 
        self.plot_df.attrs = self.src_df.attrs

        # memberとkeypointのインデックス値を文字列に変換
        idx = self.plot_df.index
        self.plot_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.member_cbox["values"] = self.plot_df.index.get_level_values("member").unique().tolist()
        self.member_cbox.current(0)
        init_member = self.member_cbox.get()
        self.keypoint_cbox["values"] = self.plot_df.loc[pd.IndexSlice[:, init_member, :], :].index.get_level_values("keypoint").unique().tolist()

        # PKLが置かれているフォルダのパスを取得
        self.pkl_dir = os.path.dirname(pkl_path)

    def to_csv(self):
        current_member = self.member_cbox.get()
        current_keypoint = self.keypoint_cbox.get()
        idx = pd.IndexSlice[:, current_member, current_keypoint]
        dst_df = self.plot_df.loc[idx, :]
        dst_df.to_csv(os.path.join(self.pkl_dir, f"{current_member}_{current_keypoint}.csv"))

        dst_df = dst_df.dropna()
        # x,y,dtを次元削減し、timestampを横軸とした折れ線グラフを表示
        pca = PCA(n_components=1)
        pca.fit(dst_df[["dt_60", "dt_120"]])
        reduced = pca.transform(dst_df[["dt_60", "dt_120"]])
        plt.plot(dst_df["timestamp"], reduced)
        plt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(self.format_timedelta))
        plt.show()

    def _on_selected(self, event):
        current_member = self.member_cbox.get()
        # keypointの一覧を取得してコンボボックスにセット
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.plot_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_cbox["values"] = keypoints
        self.keypoint_cbox.current(0)

    def format_timedelta(self, x, pos):
        sec = x / 1000
        hours = sec // 3600
        remain = sec - (hours*3600)
        minutes = remain // 60
        seconds = remain - (minutes * 60)
        return f'{int(hours)}:{int(minutes):02}:{int(seconds):02}'


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
