import os
import tkinter as tk
from tkinter import ttk
import datetime

import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib import ticker
import seaborn as sns
import pandas as pd
import ttkthemes

from gui_parts import TempFile
from main_gui_parts import PklSelector
from python_senpai import keypoints_proc, windows_and_mac, file_inout, vcap
from python_senpai import time_format


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Behavior Senpai Insight")
        self.pack(padx=14, pady=14)

        temp = TempFile()
        w_width, w_height = temp.get_top_window_size()
        w_height = int(w_height)

        # ボタンのフレーム
        load_frame = ttk.Frame(self)
        load_frame.pack(side=tk.TOP, anchor=tk.NW)

        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.pack(side=tk.LEFT)
        self.pkl_selector.set_command(cmd=self.load_trk)

        self.feat_button = ttk.Button(load_frame, text="Select Feature file", command=self.load_feat)
        self.feat_button.pack(side=tk.LEFT, padx=(20, 0))
        self.feat_path_label = ttk.Label(load_frame, text="No Feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(5, 0))

        graph_setting_frame = ttk.Frame(self)
        graph_setting_frame.pack(side=tk.TOP, anchor=tk.NW, pady=(6, 0))

        fig_size_label = ttk.Label(graph_setting_frame, text="Figure size:")
        fig_size_label.pack(side=tk.LEFT)
        self.fig_width_entry = ttk.Entry(graph_setting_frame, width=5)
        self.fig_width_entry.insert(tk.END, '24')
        self.fig_width_entry.pack(side=tk.LEFT)
        fig_height_label = ttk.Label(graph_setting_frame, text="x")
        fig_height_label.pack(side=tk.LEFT)
        self.fig_height_entry = ttk.Entry(graph_setting_frame, width=5)
        self.fig_height_entry.insert(tk.END, '8')
        self.fig_height_entry.pack(side=tk.LEFT)

        # hline entry
        hline_label = ttk.Label(graph_setting_frame, text="Horizontal line at:")
        hline_label.pack(side=tk.LEFT, padx=(15, 0))
        self.hline_entry = ttk.Entry(graph_setting_frame, width=5)
        self.hline_entry.insert(tk.END, '0')
        self.hline_entry.pack(side=tk.LEFT)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(side=tk.TOP, anchor=tk.NW, pady=(6, 0))
        # member選択コンボボックス、初期値はmember
        self.member_combo = ttk.Combobox(setting_frame, state="disabled")
        self.member_combo.pack(side=tk.LEFT)
        self.member_combo["values"] = ["member"]
        self.member_combo.current(0)

        # scene filterコンボボックス、初期値はAll
        self.filter_combo = ttk.Combobox(setting_frame, state="readonly")
        self.filter_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.filter_combo["values"] = ["All scenes.", "Longer than 5sec.", "Longer than 10sec."]
        self.filter_dict = {"All scenes.": 0, "Longer than 5sec.": 5000, "Longer than 10sec.": 10000}
        self.filter_combo.current(0)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self.load_trk())

        # column選択リストボックス、複数選択
        self.column_listbox = tk.Listbox(setting_frame, selectmode=tk.EXTENDED, exportselection=False)
        self.column_listbox.pack(side=tk.LEFT, padx=(5, 0))

        # scene選択リストボックス、複数選択
        self.scene_listbox = tk.Listbox(setting_frame, selectmode=tk.EXTENDED, exportselection=False)
        self.scene_listbox.pack(side=tk.LEFT, padx=(5, 0))

        self.test_button = ttk.Button(setting_frame, text="Draw", command=self.draw)
        self.test_button.pack(side=tk.LEFT, padx=(5, 0))
        self.vcap = vcap.VideoCap()

        self.load_trk()

    def load_trk(self):
        pkl_path = self.pkl_selector.get_trk_path()
        load_df = file_inout.load_track_file(pkl_path)
        if load_df is None:
            self.pkl_selector.rename_pkl_path_label(self.pkl_path)
            return
        self.pkl_path = pkl_path
        self.trk_df = load_df
        self.trk_df = keypoints_proc.zero_point_to_nan(self.trk_df)
        self.trk_df = self.trk_df[~self.trk_df.index.duplicated(keep="first")]
        src_attrs = self.trk_df.attrs
        self.pkl_dir = os.path.dirname(self.pkl_path)
        self.vcap.set_frame_size(src_attrs["frame_size"])
        self.video_name = src_attrs["video_name"]
        self.vcap.open_file(os.path.join(self.pkl_dir, os.pardir, self.video_name))

        # UIの更新
        self.pkl_selector.set_prev_next(src_attrs)
        raw_dict = self.trk_df.attrs['scene_table']
        self.scene_listbox.delete(0, tk.END)
        self.scene_dict = {'description': [], 'start': [], 'end': []}
        filter_value = self.filter_dict[self.filter_combo.get()]
        for scene, start, end in zip(raw_dict['description'], raw_dict['start'], raw_dict['end']):
            duration = time_format.timestr_to_msec(end) - time_format.timestr_to_msec(start)
            if duration > filter_value:
                self.scene_dict['description'].append(scene)
                self.scene_dict['start'].append(start)
                self.scene_dict['end'].append(end)
                self.scene_listbox.insert(tk.END, f"{scene} ({duration/1000:.1f}sec)")

    def load_feat(self):
        pkl_path = file_inout.open_pkl(os.path.dirname(self.pkl_dir))
        if pkl_path is None:
            return
        self.feat_path_label["text"] = pkl_path
        self.feat_name = os.path.basename(pkl_path)
        self.feat_df = file_inout.load_track_file(pkl_path, allow_calculated_track_file=True)

        # UIの更新
        self.member_combo['state'] = 'readonly'
        self.member_combo["values"] = self.feat_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)
        self.column_listbox.delete(0, tk.END)
        for col in self.feat_df.columns:
            if col == 'timestamp':
                continue
            self.column_listbox.insert(tk.END, col)

    def draw(self):
        tar_member = self.member_combo.get()
        scene_selected = self.scene_listbox.curselection()
        # self.scene_dict['description']のvalueに重複があったらnumber suffixを付与
        # ['a', 'a', 'b'] -> ['a', 'a_1', 'b']
        scene_desc = self.scene_dict['description']
        scene_desc = pd.Series(scene_desc)
        scene_suffix = scene_desc.groupby(scene_desc).cumcount().astype(str)
        scene_desc = scene_desc.str.cat(scene_suffix, sep='_').tolist()
        self.scene_dict['description'] = scene_desc

        scenes = [{"description": self.scene_dict['description'][idx],
                   "start": self.scene_dict['start'][idx],
                   "end": self.scene_dict['end'][idx]} for idx in scene_selected]
        scene_num = len(scenes)
        if scene_num == 0:
            return
        total_duration = time_format.timestr_to_msec(scenes[-1]["end"]) - time_format.timestr_to_msec(scenes[0]["start"])
        column_selected = self.column_listbox.curselection()
        columns = [self.column_listbox.get(idx) for idx in column_selected]

        margin = 0.1
        hspace = 0.05
        width_ratios = [3, 1]
        gridspec_kw = {'hspace': hspace, 'wspace': 0.1, 'top': 1-margin, 'bottom': margin, 'right': 0.95, 'width_ratios': width_ratios}
        fig_width = int(self.fig_width_entry.get())
        fig_height = int(self.fig_height_entry.get())
        hline_value = float(self.hline_entry.get())
        self.fig, axes = plt.subplots(scene_num, 2, sharex='col', sharey='all', num=self.feat_name, gridspec_kw=gridspec_kw)
        self.fig.set_size_inches(fig_width, fig_height)
        self.fig.canvas.mpl_connect("button_press_event", self._click_graph)

        # durationによってx軸のメモリ間隔を変更
        interval = 5*60*1000
        if total_duration < 60*1000:
            interval = 10*1000
        elif total_duration < 5*60*1000:
            interval = 30*1000
        elif total_duration < 10*60*1000:
            interval = 60*1000
        axes[0][0].xaxis.set_major_locator(ticker.MultipleLocator(interval))

        self.vlines = []
        idx = pd.IndexSlice
        duration_sum = 0
        for i, scene in enumerate(scenes):
            start_ms = time_format.timestr_to_msec(scene["start"])
            end_ms = time_format.timestr_to_msec(scene["end"])
            duration = end_ms - start_ms
            duration_sum += duration
            scene_df = keypoints_proc.filter_by_timerange(self.feat_df, start_ms, end_ms)
            scene_df = scene_df.loc[idx[:, tar_member], columns+['timestamp']]
            # level=1のindexを削除
            scene_df = scene_df.reset_index(level=1, drop=True)
            scene_dfm = scene_df.melt(id_vars='timestamp', var_name='column', value_name='value')

            vline = axes[i][0].axvline(0, color='gray', linewidth=0.5)
            self.vlines.append(vline)
            axes[i][0].axhline(hline_value, color='gray', linewidth=0.5)

            # グラフの外側(左側)に複数行のtextを表示
            text_content = f"{scene['description']}\n{scene['start']}-{scene['end']}\n{duration/1000:.1f}sec"
            axp = axes[i][0].get_position()
            text_pos = axp.y1 - (axp.y1 - axp.y0) * 0.1
            axes[i][0].text(0.03, text_pos, text_content, ha='left', va='top', transform=self.fig.transFigure, fontsize=8, linespacing=1.5)
            plot = sns.lineplot(data=scene_dfm, x='timestamp', y='value', hue='column', ax=axes[i][0], linewidth=0.8)
            plot.set_ylabel(None)
            plot.set_xlabel(None)
            scene_df = scene_df.drop(columns='timestamp')
            violin = sns.violinplot(data=scene_df, ax=axes[i][1], linewidth=0.1)

            # 縦線
            axes[i][0].grid(which='major', axis='x', linewidth=0.3)

            # i=0だけlegendを表示
            if i > 0:
                axes[i][0].get_legend().remove()
            else:
                axes[0][0].legend(loc='upper right', fontsize=8, title='feature')

        # ヘッダテキスト
        today = datetime.date.today()
        head_text = f"{self.feat_name} (duration_sum:{duration_sum/1000:.1f}sec, draw_date:{today}, video_name:{self.video_name})"
        axes[0][0].text(0.5, 0.95, head_text, ha='center', va='top', transform=self.fig.transFigure, fontsize=10)
        axes[0][0].xaxis.set_major_formatter(ticker.FuncFormatter(self._format_timedelta))

        self.timestamps = self.feat_df['timestamp'].unique()
        plt.show()

    def _format_timedelta(self, x, pos):
        return time_format.msec_to_timestr(x)

    def _click_graph(self, event):
        if event.button == 1:
            x = event.xdata
            if x is None:
                return
            timestamp_msec = float(x)

        elif event.button == 3:
            timestamp_msec = self.vcap.get(cv2.CAP_PROP_POS_MSEC)
            timestamp_msec += 100

        timestamp_msec = self.timestamps[np.fabs(self.timestamps-timestamp_msec).argsort()[:1]][0]

        for vline in self.vlines:
            vline.set_xdata([timestamp_msec])

        time_format.copy_to_clipboard(timestamp_msec)
        ret, frame = self.vcap.read_at(timestamp_msec)
        if ret is False:
            return

        if frame.shape[0] >= 1080:
            resize_height = 720
            resize_width = int(frame.shape[1] * resize_height / frame.shape[0])
            frame = cv2.resize(frame, (resize_width, resize_height))
        if ret is True:
            cv2.imshow("frame", frame)
            cv2.waitKey(1)
        self.fig.canvas.draw()


def quit(root):
    root.quit()
    root.destroy()


def main():
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.configure(background=bg_color)
    root.option_add("*background", bg_color)
    root.option_add("*Canvas.background", bg_color)
    root.option_add("*Text.background", "#fcfcfc")
    windows_and_mac.set_app_icon(root)
    s = ttk.Style(root)
    s.configure(".", background=bg_color)
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
