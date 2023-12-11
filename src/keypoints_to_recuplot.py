import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import PklSelector, MemberKeypointComboboxes, ProcOptions, TimeSpanEntry, TempFile
from recurrence_plotter import RecurrencePlotter
import keypoints_proc
import time_format
import vcap


class App(ttk.Frame):
    """
    リカレンスプロット(Recurrence Plot)を描画するためのGUIです。
    以下の機能を有します
     - Trackファイルを選択して読み込む機能
     - 描画するmemberとkeypointを指定する機能
     - 速さ計算と間引き処理を行う機能
     - 計算対象の時間帯の指定を行う機能
     - Recurrence Plotの閾値を指定して、計算する機能
     - 以上の処理で得られたデータをRecurrencePlotterに渡す機能
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Keypoints to Recurrence Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.recu = RecurrencePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        load_frame = ttk.Frame(self)
        load_frame.pack(pady=5, anchor=tk.W)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        proc_frame = ttk.Frame(self)
        proc_frame.pack(pady=5)
        self.member_keypoints_combos = MemberKeypointComboboxes(proc_frame)
        self.proc_options = ProcOptions(proc_frame)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        eps_label = ttk.Label(setting_frame, text="threshold:")
        eps_label.pack(side=tk.LEFT)
        self.eps_entry = ttk.Entry(setting_frame, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.eps_entry.insert(tk.END, '0')
        self.eps_entry.pack(side=tk.LEFT, padx=(0, 5))

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)

        self.recu.pack(plot_frame)

        self.cap = vcap.VideoCap()
        self.load_pkl()
 
    def load_pkl(self):
        # ファイルのロード
        pkl_path = self.pkl_selector.get_trk_path()
        if os.path.exists(pkl_path) is False:
            return
        self.src_df = pd.read_pickle(pkl_path)
        pkl_dir = os.path.dirname(pkl_path)
        self.cap.set_frame_size(self.src_df.attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, self.src_df.attrs["video_name"]))

        # UIの更新
        self.current_dt_span = None
        self.member_keypoints_combos.set_df(self.src_df)
        self.time_span_entry.update_entry(
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].min()),
            time_format.msec_to_timestr_with_fff(self.src_df["timestamp"].max())
        )
        self.pkl_selector.set_prev_next(self.src_df.attrs)

        self.recu.set_vcap(self.cap)
        print('load_pkl() done.')
        
    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()
        idx = self.src_df.index

        if 'keypoint' in idx.names:
            dt_span = self.proc_options.get_dt_span()
            if self.current_dt_span != dt_span:
                # speedとaccelerationを計算してsrc_dfに追加
                speed_df = keypoints_proc.calc_speed(self.src_df, int(dt_span))
                acc_df = keypoints_proc.calc_acceleration(speed_df, int(dt_span))
                self.src_speed_df = pd.concat([self.src_df, speed_df, acc_df], axis=1)
                self.current_dt_span = dt_span

            plot_df = self.src_speed_df
            levels = [idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)]
            idx = pd.IndexSlice[:, current_member, current_keypoint]
            cols = ['x', 'y', f'spd_{dt_span}', f'acc_{dt_span}']
        else:
            # そのまま計算、一番右にあるカラム(timestamp)だけ除外する
            plot_df = self.src_df
            levels = [idx.levels[0], idx.levels[1].astype(str)]
            idx = pd.IndexSlice[:, current_member]
            cols = plot_df.columns[:-1]

        # timestampの範囲を抽出
        time_min, time_max = self.time_span_entry.get_start_end()
        time_min_msec = self._timedelta_to_msec(time_min)
        time_max_msec = self._timedelta_to_msec(time_max)
        plot_df = plot_df.loc[plot_df["timestamp"].between(time_min_msec, time_max_msec), :]

        plot_df.index = plot_df.index.set_levels(levels)

        # thinningの値だけframeを間引く
        thinning = self.proc_options.get_thinning()
        plot_df = keypoints_proc.thinning(plot_df, int(thinning))

        timestamps = plot_df.loc[idx, 'timestamp'].dropna().values
        plot_df = plot_df.loc[idx, cols].dropna()
        reduced_arr = keypoints_proc.pca(plot_df, tar_cols=cols)

        threshold = self.eps_entry.get()
        if threshold == "":
            self.eps_entry.insert(tk.END, '0')
            threshold = self.eps_entry.get()
        recu_mat = keypoints_proc.calc_recurrence(reduced_arr, threshold=float(threshold))
        self.recu.draw(recu_mat, timestamps)

    def clear(self):
        self.recu.clear()
        self.current_dt_span = None

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
