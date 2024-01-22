import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import MemberKeypointComboboxes, ProcOptions, TempFile
from recurrence_plotter import RecurrencePlotter
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    リカレンスプロット(Recurrence Plot)を描画するためのGUIです。
    以下の機能を有します
     - 描画するmemberとkeypointを指定する機能
     - 速さ計算と間引き処理を行う機能
     - Recurrence Plotの閾値を指定して、計算する機能
     - 以上の処理で得られたデータをRecurrencePlotterに渡す機能
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Recurrence Plot")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.recu = RecurrencePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

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

        self.reload(args)

    def reload(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.src_attrs = args['src_attrs']
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.member_keypoints_combos.set_df(self.src_df)
        self.current_dt_span = None

        if "roi_left_top" in self.src_attrs:
            zero_point = self.src_attrs['roi_left_top']
        else:
            zero_point = (0, 0)
        self.src_df = keypoints_proc.zero_point_to_nan(self.src_df, zero_point)
        self.recu.set_vcap(self.cap)
        print('reload() done.')

    def draw(self):
        current_member, current_keypoint = self.member_keypoints_combos.get_selected()

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)

        idx = tar_df.index
        if 'keypoint' in idx.names:
            dt_span = self.proc_options.get_dt_span()
            if self.current_dt_span != dt_span:
                # speedとaccelerationを計算してsrc_dfに追加
                speed_df = keypoints_proc.calc_speed(tar_df, int(dt_span))
                acc_df = keypoints_proc.calc_acceleration(speed_df, int(dt_span))
                tar_df = pd.concat([tar_df, speed_df, acc_df], axis=1)
                self.current_dt_span = dt_span

            levels = [idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)]
            idx = pd.IndexSlice[:, current_member, current_keypoint]
            cols = ['x', 'y', f'spd_{dt_span}', f'acc_{dt_span}']
        else:
            # そのまま計算、一番右にあるカラム(timestamp)だけ除外する
            levels = [idx.levels[0], idx.levels[1].astype(str)]
            idx = pd.IndexSlice[:, current_member]
            cols = tar_df.columns[:-1]

        tar_df.index = tar_df.index.set_levels(levels)

        # thinningの値だけframeを間引く
        thinning = self.proc_options.get_thinning()
        plot_df = keypoints_proc.thinning(tar_df, int(thinning))

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
