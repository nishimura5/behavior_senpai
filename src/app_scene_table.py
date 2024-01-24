import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import TempFile, TimeSpanEntry
from line_plotter import LinePlotter
from python_senpai import time_format
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    Trackファイルに保存するDataFrameのattrs['scene_table']を編集するためのGUIです。
    H:MM:SS.fffの形式でstartとendを入力してaddボタンを押すと、tree_viewに追加されます。
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Scene Table")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.plot = LinePlotter(fig_size=(width/dpi, height/dpi), dpi=dpi)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        member_label = ttk.Label(setting_frame, text="member")
        member_label.pack(side=tk.LEFT)
        self.member_combo = ttk.Combobox(setting_frame, state='readonly', width=18)
        self.member_combo.pack(side=tk.LEFT, padx=5)

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)

        clear_btn = ttk.Button(setting_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT)

        entry_frame = ttk.Frame(self)
        entry_frame.pack(pady=5)
        self.time_span_entry = TimeSpanEntry(entry_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))
        description_label = ttk.Label(entry_frame, text="description")
        description_label.pack(side=tk.LEFT)
        self.description_entry = ttk.Entry(entry_frame, width=40)
        self.description_entry.pack(side=tk.LEFT, padx=(0, 5))

        add_btn = ttk.Button(entry_frame, text="add", command=self._add_row)
        add_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = ttk.Button(entry_frame, text="Delete Selected", command=self._delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=5)
        update_btn = ttk.Button(entry_frame, text="OK", command=self.on_ok)
        update_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("start", "end", "duration", "description")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended", height=10)
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")
        self.tree.heading("description", text="description")
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("duration", width=100)
        self.tree.column("description", width=350)
        self.tree.pack()
        # rowを選択したときのイベントを設定
        self.tree.bind("<<TreeviewSelect>>", self._select_tree_row)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.plot.pack(plot_frame)

        self.dst_df = None
        self.load(args)

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        self.member_combo["values"] = self.src_df.index.get_level_values(1).unique().tolist()
        self.member_combo.current(0)
        self.time_span_entry.update_entry(self.time_min, self.time_max)

        self.tree.delete(*self.tree.get_children())
        self.clear()
        self.plot.set_vcap(self.cap)

        if 'scene_table' not in src_attrs.keys():
            print("scene_table is not in attrs")
            return

        scene_table = src_attrs['scene_table']
        # self.treeをクリアしてattrs['scene_table']の値を入れる
        for item in self.tree.get_children(''):
            self.tree.delete(item)

        # attrsにdescriptionがなかったら空のリストを入れる
        if 'description' not in scene_table.keys():
            scene_table['description'] = [''] * len(scene_table['start'])

        for start, end, description in zip(scene_table['start'], scene_table['end'], scene_table['description']):
            duration = pd.to_timedelta(end) - pd.to_timedelta(start)
            duration_str = time_format.timedelta_to_str(duration)
            self.tree.insert("", "end", values=(start, end, duration_str, description))

    def draw(self):
        current_member = self.member_combo.get()

        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)
        # keypointのインデックス値を文字列に変換
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1], idx.levels[2].astype(str)])
        plot_df = tar_df

        if 'scene_table' not in self.src_df.attrs.keys():
            print("scene_table is not in attrs")
            return
        rects = self.src_df.attrs['scene_table']

        self.plot.set_trk_df(plot_df)
        self.plot.set_plot_rect(plot_df, current_member, rects, self.time_min, self.time_max)
        self.plot.draw()

    def on_ok(self):
        self.dst_df = self.src_df.copy()
        if "proc_history" not in self.dst_df.attrs.keys():
            self.dst_df.attrs["proc_history"] = []
        self.dst_df.attrs["proc_history"].append("scene_table_edit")
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def _add_row(self):
        start_time, end_time = self.time_span_entry.get_start_end_str()
        start_td = pd.to_timedelta(start_time)
        end_td = pd.to_timedelta(end_time)
        # durationの計算、startとendが逆だったら入れ替える
        if end_td <= start_td:
            start_td, end_td = end_td, start_td
        duration = end_td - start_td

        duration_str = time_format.timedelta_to_str(duration)
        start_str = time_format.timedelta_to_str(start_td)
        end_str = time_format.timedelta_to_str(end_td)

        # 重複していたらaddしない
        tar_list = [k for k in self.tree.get_children('')]
        for tar in tar_list:
            if start_str == self.tree.item(tar)['values'][0] and end_str == self.tree.item(tar)['values'][1]:
                return
        self.tree.insert("", "end", values=(start_str, end_str, duration_str, self.description_entry.get()))

        # tree_viewをstartカラムでソート
        self._treeview_sort_column(self.tree, "start")

    def _treeview_sort_column(self, tv, col):
        tar_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tar_list.sort()
        for index, (val, k) in enumerate(tar_list):
            tv.move(k, '', index)

    def _delete_selected(self):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)

    def _update(self):
        scene_table = {'start': [], 'end': [], 'description': []}
        for item in self.tree.get_children(''):
            scene_table['start'].append(self.tree.item(item)['values'][0])
            scene_table['end'].append(self.tree.item(item)['values'][1])
            scene_table['description'].append(self.tree.item(item)['values'][3])
        self.src_df.attrs['scene_table'] = scene_table

    def clear(self):
        self.plot.clear()

    def _select_tree_row(self, event):
        # 選択した行のmemberを取得
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        start = self.tree.item(selected)['values'][0]
        end = self.tree.item(selected)['values'][1]
        start_msec = time_format.timestr_to_msec(start)
        end_msec = time_format.timestr_to_msec(end)
        self.time_span_entry.update_entry(start_msec, end_msec)
        description = self.tree.item(selected)['values'][3]
        self.description_entry.delete(0, tk.END)
        self.description_entry.insert(0, description)
