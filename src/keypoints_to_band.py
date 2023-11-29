import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
import numpy as np

from gui_parts import PklSelector, TimeSpanEntry, TempFile
from band_plotter import BandPlotter
import time_format
import vcap


class App(tk.Frame):
    """
    帯プロット(Band Plot)を描画するためのGUIです。
    以下の機能を有します
     - Trackファイルを選択して読み込む機能
     - 計算対象の時間帯の指定を行う機能
     - 以上の処理で得られたデータをBandPlotterに渡す機能
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Band Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.band = BandPlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        load_frame = tk.Frame(self)
        load_frame.pack(pady=5)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)

        setting_frame = tk.Frame(self)
        setting_frame.pack(pady=5)

        caption_time = tk.Label(setting_frame, text='time:')
        caption_time.pack(side=tk.LEFT, padx=(10, 0))
        self.time_span_entry = TimeSpanEntry(setting_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        rename_frame = ttk.Frame(self)
        rename_frame.pack(pady=5)
        rename_member_label = ttk.Label(rename_frame, text="Rename Member")
        rename_member_label.pack(side=tk.LEFT, pady=5)
        self.tar_member_label_var = tk.StringVar()
        self.tar_member_label_var.set("None")
        tar_member_label = ttk.Label(rename_frame, textvariable=self.tar_member_label_var)
        tar_member_label.pack(side=tk.LEFT, padx=5)
        to_label = ttk.Label(rename_frame, text="to")
        to_label.pack(side=tk.LEFT, padx=5)
        self.new_member_name_entry = ttk.Entry(rename_frame, width=12)
        self.new_member_name_entry.pack(side=tk.LEFT, padx=5)
        rename_btn = ttk.Button(rename_frame, text="Rename", command=self.rename_member)
        rename_btn.pack(side=tk.LEFT, padx=5)
        overwrite_btn = ttk.Button(rename_frame, text="Write to Track", command=self.overwrite)
        overwrite_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("member", "start", "end", "duration", "keypoints/frame")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("member", text="member")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")
        self.tree.heading("keypoints/frame", text="keypoints/frame")
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("duration", width=100)
        self.tree.pack()
        # rowを選択したときのイベントを設定
        self.tree.bind("<<TreeviewSelect>>", self._select_tree_row)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.band.pack(plot_frame)

        self.cap = vcap.VideoCap()
        self.load_pkl()
 
    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        if os.path.exists(pkl_path) is False:
            print(f"{pkl_path} is not found")
            return
        self.src_df = pd.read_pickle(pkl_path)

        self.src_df['x'] = np.where(self.src_df['x'] == 0, np.nan, self.src_df['x'])
        self.src_df['y'] = np.where(self.src_df['y'] == 0, np.nan, self.src_df['y'])
        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

        # PKLが置かれているフォルダのパスを取得
        pkl_dir = os.path.dirname(pkl_path)
        self.current_dt_span = None

        # timestampの範囲を取得
        self.time_span_entry.update_entry(
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].min()),
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].max())
        )

        self.pkl_selector.set_prev_next(self.src_df.attrs)

        self.update_tree() 

        self.cap.set_frame_size(self.src_df.attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, self.src_df.attrs["video_name"]))
        self.band.set_vcap(self.cap)
        
    def draw(self):
        # treeから選択した行のmemberを取得
        current_member = str(self.tree.item(self.tree.selection()[0])["values"][0])
        plot_df = self.src_df.copy()

        # timestampの範囲を抽出
        time_min, time_max = self.time_span_entry.get_start_end()
        time_min_msec = self._timedelta_to_msec(time_min)
        time_max_msec = self._timedelta_to_msec(time_max)
        plot_df = plot_df.loc[plot_df["timestamp"].between(time_min_msec, time_max_msec), :]

        # keypointのインデックス値を文字列に変換
        idx = plot_df.index
        plot_df.index = plot_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])
        self.band.draw(plot_df, current_member, time_min_msec, time_max_msec)

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        members = self.src_df.index.get_level_values(1).unique()
        for member in members:
            sliced_df = self.src_df.loc[pd.IndexSlice[:, member, :], :]
            sliced_df = sliced_df.loc[~(sliced_df['x'].isna()) & (~sliced_df['y'].isna())]
            kpf = len(sliced_df)/len(sliced_df.index.get_level_values(0).unique())
            head_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.head(1)['timestamp'].values[0])
            tail_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.tail(1)['timestamp'].values[0])
            duration = sliced_df.tail(1)['timestamp'].values[0] - sliced_df.head(1)['timestamp'].values[0]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            self.tree.insert("", "end", values=(member, head_timestamp, tail_timestamp, duration_str, f"{kpf:.2f}"))
 
    def rename_member(self):
        old_member = self.tar_member_label_var.get()
        new_member = self.new_member_name_entry.get()
        if new_member == "":
            print("new member name is empty")
            return
        # indexのtypeを表示
        print(type(old_member), type(new_member), self.src_df.index.dtype)
        self.src_df = self.src_df.rename(index={old_member: new_member}, level=1)
        self.update_tree()
        print(f"renamed {old_member} to {new_member}")

    def overwrite(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df.to_pickle(pkl_path)
        self.load_pkl()

    def clear(self):
        self.band.clear()

    def _select_tree_row(self, event):
        # 選択した行のmemberを取得
        if len(self.tree.selection()) == 0:
            return
        current_member = str(self.tree.item(self.tree.selection()[0])["values"][0])
        self.tar_member_label_var.set(current_member)

    def _timedelta_to_msec(self, timedelta):
        # strをtimedeltaに変換
        timedelta = pd.to_timedelta(timedelta)
        sec = timedelta.total_seconds()
        return sec * 1000

    def _validate(self, text):
        return (text.replace(".", "").isdigit() or text == "")


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
