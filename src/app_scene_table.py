import itertools
import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
from gui_parts import StrEntry, TempFile, TimeSpanEntry
from line_plotter import LinePlotter
from python_senpai import file_inout, time_format


class App(ttk.Frame):
    """Application for editing the scene table in the DataFrame."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Scene Table")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_scene_table_graph_size()
        self.calc_case = temp.data["calc_case"]
        self.plot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

        import_frame = ttk.Frame(setting_frame)
        import_frame.pack(pady=5)
        import_btn = ttk.Button(import_frame, text="Import Behavioral coding file", command=self.import_bool_pkl)
        import_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.bool_col_combo = ttk.Combobox(import_frame, state="disable", width=18)
        self.bool_col_combo["values"] = ["bool_col"]
        self.bool_col_combo.current(0)
        self.bool_col_combo.pack(side=tk.LEFT, padx=(0, 5))
        add_import_bool_btn = ttk.Button(import_frame, text="Add", command=self._add_import_bool)
        add_import_bool_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.import_label = ttk.Label(import_frame, text="")
        self.import_label.pack(side=tk.LEFT)
        self.bool_df = None

        draw_frame = ttk.Frame(setting_frame)
        draw_frame.pack(pady=5)
        member_label = ttk.Label(draw_frame, text="Member:")
        member_label.pack(side=tk.LEFT)
        self.member_combo = ttk.Combobox(draw_frame, state="readonly", width=18)
        self.member_combo.pack(side=tk.LEFT)
        self.member_combo.bind("<<ComboboxSelected>>", self.select_member)

        # Connect nearby scenes button
        self.connect_btn = ttk.Button(draw_frame, text="Connect nearby scenes", command=self._connect_nearby_scenes)
        self.connect_btn.pack(side=tk.LEFT, padx=(10, 0))

        entry_frame = ttk.Frame(setting_frame)
        entry_frame.pack(pady=5)
        self.time_span_entry = TimeSpanEntry(entry_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.description_entry = StrEntry(entry_frame, label="Description:", width=40)
        self.description_entry.pack_horizontal(padx=5)

        add_btn = ttk.Button(entry_frame, text="Add", command=self._add_row)
        add_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = ttk.Button(entry_frame, text="Delete Selected", command=self._delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=5)
        delete_all_btn = ttk.Button(entry_frame, text="Delete All", command=self._delete_all)
        delete_all_btn.pack(side=tk.LEFT, padx=5)

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("start", "end", "duration", "description")
        self.tree = ttk.Treeview(tree_frame, columns=cols, height=6, show="headings", selectmode="extended")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")
        self.tree.heading("description", text="description")
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("duration", width=100)
        self.tree.column("description", width=350)
        self.tree.pack(side=tk.LEFT)
        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)
        # rowを選択したときのイベントを設定
        self.tree.bind("<<TreeviewSelect>>", self.select_tree_row)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.plot.pack(plot_frame)
        self.plot.set_single_ax(bottom=0.12)

        self.dst_df = None
        # app_scene_table is not appended to proc_history
        self.history = None

    def _load(self, event, args):
        self.src_df = args["src_df"]
        src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args["time_span_msec"]
        self.pkl_dir = args["pkl_dir"]

        # UIの更新
        self.member_combo["values"] = self.src_df.index.get_level_values(1).unique().tolist()
        self.member_combo.current(0)
        self.time_span_entry.update_entry(self.time_min, self.time_max)

        self.tree.delete(*self.tree.get_children())
        self.clear()
        self.plot.set_vcap(args["cap"])

        if "scene_table" in src_attrs.keys():
            self.scene_table = src_attrs["scene_table"]
        else:
            self.scene_table = {"start": [], "end": [], "description": []}

        # self.treeをクリアしてattrs['scene_table']の値を入れる
        for item in self.tree.get_children(""):
            self.tree.delete(item)

        # attrsにdescriptionがなかったら空のリストを入れる
        if "description" not in self.scene_table.keys():
            self.scene_table["description"] = [""] * len(self.scene_table["start"])

        for start, end, description in zip(self.scene_table["start"], self.scene_table["end"], self.scene_table["description"], strict=False):
            duration = pd.to_timedelta(end) - pd.to_timedelta(start)
            duration_str = time_format.timedelta_to_str(duration)
            self.tree.insert("", "end", values=(start, end, duration_str, description))
        self._update()

    def import_bool_pkl(self):
        init_dir = os.path.join(os.path.dirname(self.pkl_dir), "calc")
        pl = file_inout.PickleLoader(init_dir, "behavioral_coding")
        pl.join_calc_case(self.calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        bool_df = pl.load_pkl()
        bool_pkl_path = pl.get_tar_path()

        # bool型 or column名がtimestampじゃないカラムは削除
        self.bool_df = bool_df.loc[:, (bool_df.dtypes == "bool") | (bool_df.columns == "timestamp")]
        cols = self.bool_df.columns.tolist()
        cols.remove("timestamp")
        self.bool_col_combo["values"] = cols
        self.bool_col_combo["state"] = "readonly"
        self.bool_col_combo.current(0)
        self.import_label["text"] = os.path.basename(bool_pkl_path)

    def _add_import_bool(self):
        if self.bool_df is None:
            return
        bool_df = self.bool_df.copy()
        tar_col_name = self.bool_col_combo.get()

        # groupby('member')でmemberごとに処理、1行前/1行後との差分を取る
        diff_prev_sr = bool_df.groupby("member")[tar_col_name].diff().astype(bool)
        diff_follow_sr = bool_df.groupby("member")[tar_col_name].diff(-1).astype(bool)
        # ラベリング、-1とNaNはastypeでTrueになる
        starts = bool_df.loc[(bool_df[tar_col_name] & diff_prev_sr), "timestamp"].values.tolist()
        ends = bool_df.loc[(bool_df[tar_col_name] & diff_follow_sr), "timestamp"].values.tolist()
        # 要素の先頭を比較してstartsの先頭にtime_minを追加
        if starts[0] > ends[0]:
            starts.insert(0, self.time_min)
        for start, end in itertools.zip_longest(starts, ends, fillvalue=self.time_max):
            start_str = time_format.msec_to_timestr_with_fff(start)
            end_str = time_format.msec_to_timestr_with_fff(end)
            duration = end - start
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            self.tree.insert("", "end", values=(start_str, end_str, duration_str, tar_col_name))
        self._update()

    def draw(self):
        tar_df = self.src_df.copy()
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])
        plot_df = tar_df

        rects = self.scene_table

        self.plot.set_trk_df(plot_df)
        self.plot.set_plot_rect(plot_df, rects, self.time_min, self.time_max)
        self.plot.set_member(self.member_combo.get())
        self.plot.draw()

    def _connect_nearby_scenes(self):
        """self.scene_tableのstartとendを比較して近いものを結合する
        update tree and scene_table and draw
        """
        nearby_time_ms = 1000
        scene_df = pd.DataFrame(self.scene_table)
        scene_df["start"] = pd.to_timedelta(scene_df["start"]).dt.total_seconds() * 1000
        scene_df["end"] = pd.to_timedelta(scene_df["end"]).dt.total_seconds() * 1000
        scene_df = scene_df.sort_values("start")
        scene_df = scene_df.reset_index(drop=True)
        scene_df["diff"] = scene_df.groupby("description")["end"].shift(1) - scene_df["start"]
        scene_df["diff"] = scene_df["diff"].fillna(0)
        scene_df["label"] = scene_df["diff"] < -nearby_time_ms
        scene_df["label"] = scene_df.groupby("description")["label"].cumsum()
        merged_df = scene_df.groupby(["description", "label"]).agg({"start": "first", "end": "last"}).reset_index()

        # treeをクリアしてscene_tableを更新
        self.tree.delete(*self.tree.get_children())
        self.scene_table = {"start": [], "end": [], "description": []}
        for i, row in merged_df.iterrows():
            start = time_format.msec_to_timestr_with_fff(row["start"])
            end = time_format.msec_to_timestr_with_fff(row["end"])
            duration = row["end"] - row["start"]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            self.tree.insert("", "end", values=(start, end, duration_str, row["description"]))
            self.scene_table["start"].append(start)
            self.scene_table["end"].append(end)
            self.scene_table["description"].append(row["description"])
        self._update()

    def on_ok(self):
        """Perform the action when the 'OK' button is clicked."""
        self.dst_df = self.src_df.copy()
        self.dst_df.attrs["scene_table"] = self.scene_table
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def cancel(self):
        """Cancel the operation and destroy the window."""
        self.dst_df = None
        self.master.destroy()

    def select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        # 選択した行のmemberを取得
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        start = self.tree.item(selected)["values"][0]
        end = self.tree.item(selected)["values"][1]
        start_msec = time_format.timestr_to_msec(start)
        end_msec = time_format.timestr_to_msec(end)
        self.time_span_entry.update_entry(start_msec, end_msec)
        description = self.tree.item(selected)["values"][3]
        self.description_entry.update(description)
        self.plot.jump_to(start_msec)

    def select_member(self, event):
        self.plot.set_member(self.member_combo.get())

    def clear(self):
        """Clear the plot."""
        self.plot.clear()

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
        tar_list = [k for k in self.tree.get_children("")]
        for tar in tar_list:
            if start_str == self.tree.item(tar)["values"][0] and end_str == self.tree.item(tar)["values"][1]:
                return
        self.tree.insert("", "end", values=(start_str, end_str, duration_str, self.description_entry.get()))

        # tree_viewをstartカラムでソート
        self._treeview_sort_column(self.tree, "start")
        self._update()

    def _treeview_sort_column(self, tv, col):
        tar_list = [(tv.set(k, col), k) for k in tv.get_children("")]
        tar_list.sort()
        for index, (_val, k) in enumerate(tar_list):
            tv.move(k, "", index)

    def _delete_selected(self):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)
        self._update()

    def _delete_all(self):
        self.tree.delete(*self.tree.get_children())
        self._update()

    def _update(self):
        self.clear()
        scene_table = {"start": [], "end": [], "description": []}
        for item in self.tree.get_children(""):
            scene_table["start"].append(self.tree.item(item)["values"][0])
            scene_table["end"].append(self.tree.item(item)["values"][1])
            scene_table["description"].append(self.tree.item(item)["values"][3])
        self.scene_table = scene_table
        self.draw()
