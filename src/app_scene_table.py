import itertools
import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

import export_mp4
from behavior_senpai import file_inout, hdf_df, time_format
from gui_parts import IntEntry, TempFile
from gui_tree import Tree
from line_plotter import LinePlotter


class App(ttk.Frame):
    """Application for editing the scene table in the DataFrame."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Scene Table")
        master.geometry("1200x700")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))
        self.export = export_mp4.MakeMp4()
        self.export.load(args)

        temp = TempFile()
        width, height, dpi = temp.get_scene_table_graph_size()
        self.calc_case = temp.data["calc_case"]
        self.plot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        control_frame = ttk.Frame(self)
        control_frame.pack(padx=10, pady=(0, 5), fill=tk.X, expand=True)
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

        import_frame = ttk.Frame(setting_frame)
        import_frame.pack(pady=5, expand=True, anchor=tk.W)
        import_btn = ttk.Button(import_frame, text="Select feature file", command=self.import_bool_pkl)
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
        draw_frame.pack(pady=5, expand=True, anchor=tk.W)
        add_btn = ttk.Button(draw_frame, text="Add scene", command=self.add)
        add_btn.pack(side=tk.LEFT, padx=(0, 150))

        self.connect_msec_entry = IntEntry(draw_frame, "Threshold (msec)", 1000, 6)
        self.connect_msec_entry.pack_horizontal(padx=(10, 0))
        connect_btn = ttk.Button(draw_frame, text="Connect", command=self._connect_nearby_scenes)
        connect_btn.pack(side=tk.LEFT, padx=5)
        remove_btn = ttk.Button(draw_frame, text="Remove", command=self._remove_short_scenes)
        remove_btn.pack(side=tk.LEFT)

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        tree_canvas_frame = ttk.Frame(self)
        tree_canvas_frame.pack(padx=5, pady=5, fill=tk.X, expand=True)

        cols = [
            {"name": "start", "width": 100},
            {"name": "end", "width": 100},
            {"name": "duration", "width": 100},
            {"name": "member", "width": 150},
            {"name": "description", "width": 200},
        ]
        self.tree = Tree(tree_canvas_frame, cols, height=12, right_click=True)
        self.tree.pack(side=tk.LEFT)
        self.tree.add_menu("Edit", self.edit)
        self.tree.add_menu("Copy", self.copy)
        self.tree.add_menu("Remove", self.remove)
        self.tree.add_menu("Extract MP4", self.extract_mp4)
        self.tree.add_menu("Export MP4", self.export_mp4)
        self.tree.tree.bind("<Button-1>", self.left_click_tree)

        self.canvas = tk.Canvas(tree_canvas_frame, width=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.plot.pack(plot_frame)
        self.plot.set_single_ax(bottom=0.12)

        self.plot.set_img_canvas(self.canvas)

        # app_scene_table is not appended to proc_history
        self.history = None

    def _load(self, event, args):
        self.src_df = args["src_df"]
        src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args["time_span_msec"]
        self.pkl_dir = args["pkl_dir"]
        # string型に変換してmemberを取得
        members = self.src_df.index.get_level_values(1).unique().astype(str).tolist()
        self.plot.set_members_to_draw(members)
        self.tree.set_members(members)

        self.tree.clear()
        self.clear()
        self.plot.set_vcap(args["cap"])

        if "scene_table" in src_attrs.keys():
            self.scene_table = src_attrs["scene_table"]
        else:
            self.scene_table = {"start": [], "end": [], "member": [], "description": []}

        # attrsにdescriptionがなかったら空のリストを入れる
        if "description" not in self.scene_table.keys():
            self.scene_table["description"] = [""] * len(self.scene_table["start"])
        if "member" not in self.scene_table.keys():
            self.scene_table["member"] = [""] * len(self.scene_table["start"])

        for start, end, member, description in zip(
            self.scene_table["start"], self.scene_table["end"], self.scene_table["member"], self.scene_table["description"], strict=False
        ):
            duration = pd.to_timedelta(end) - pd.to_timedelta(start)
            duration_str = time_format.timedelta_to_str(duration)
            vals = (start, end, duration_str, member, description)
            self.tree.insert(values=vals)
        self._update()

        h5_path = os.path.join(self.pkl_dir, "..", "calc", self.calc_case, f"{src_attrs['video_name'].split('.')[0]}.feat")
        if os.path.exists(h5_path):
            self._import_h5(h5_path)

    def import_bool_pkl(self):
        init_dir = os.path.join(os.path.dirname(self.pkl_dir), "calc")
        pl = file_inout.PickleLoader(init_dir)
        pl.join_calc_case(self.calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        bool_pkl_path = pl.get_tar_path()
        self._import_h5(bool_pkl_path)

    def _import_h5(self, h5_path):
        h5 = hdf_df.DataFrameStorage(h5_path)
        bool_df = h5.load_dimredu_df()
        if bool_df is None:
            return
        # bool型 or column名がtimestampじゃないカラムは削除
        self.bool_df = bool_df.loc[:, (bool_df.dtypes == "bool") | (bool_df.columns == "timestamp")]
        cols = self.bool_df.columns.tolist()
        cols.remove("timestamp")
        self.bool_col_combo["values"] = cols
        self.bool_col_combo["state"] = "readonly"
        self.bool_col_combo.current(0)
        self.import_label["text"] = os.path.basename(h5_path)

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
        members = bool_df.loc[(bool_df[tar_col_name] & diff_follow_sr), "timestamp"].index.get_level_values(1).astype(str).tolist()

        # 要素の先頭を比較してstartsの先頭にtime_minを追加
        if starts[0] > ends[0]:
            starts.insert(0, self.time_min)
        for start, end, member in itertools.zip_longest(starts, ends, members, fillvalue=self.time_max):
            start_str = time_format.msec_to_timestr_with_fff(start)
            end_str = time_format.msec_to_timestr_with_fff(end)
            duration = end - start
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            values = (start_str, end_str, duration_str, member, tar_col_name)
            self.tree.insert(values)
        self._update()

    def draw(self):
        tar_df = self.src_df.copy()
        idx = tar_df.index
        tar_df.index = tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])
        plot_df = tar_df

        rects = self.scene_table.copy()
        # concat member and description
        rects["description"] = [f"{m}|{d}" for m, d in zip(rects["member"], rects["description"])]

        self.plot.set_trk_df(plot_df)
        self.plot.set_plot_rect(rects, self.time_min, self.time_max)
        self.plot.set_file_name(self.src_df.attrs["video_name"])
        self.plot.draw()

    def _connect_nearby_scenes(self):
        nearby_time_ms = self.connect_msec_entry.get()
        scene_df = pd.DataFrame(self.scene_table)
        scene_df["start"] = pd.to_timedelta(scene_df["start"]).dt.total_seconds() * 1000
        scene_df["end"] = pd.to_timedelta(scene_df["end"]).dt.total_seconds() * 1000
        scene_df = scene_df.sort_values("start")
        scene_df = scene_df.reset_index(drop=True)
        scene_df["diff"] = scene_df.groupby("description")["end"].shift(1) - scene_df["start"]
        scene_df["diff"] = scene_df["diff"].fillna(0)
        scene_df["label"] = scene_df["diff"] < -nearby_time_ms
        scene_df["label"] = scene_df.groupby("description")["label"].cumsum()
        merged_df = scene_df.groupby(["member", "description", "label"]).agg({"start": "min", "end": "max"}).reset_index()
        self._update_new_scene_df(merged_df)

    def _remove_short_scenes(self):
        short_time_ms = self.connect_msec_entry.get()
        scene_df = pd.DataFrame(self.scene_table)
        scene_df["start"] = pd.to_timedelta(scene_df["start"]).dt.total_seconds() * 1000
        scene_df["end"] = pd.to_timedelta(scene_df["end"]).dt.total_seconds() * 1000
        scene_df["diff"] = scene_df["end"] - scene_df["start"]
        scene_df = scene_df[scene_df["diff"] > short_time_ms]
        self._update_new_scene_df(scene_df)

    def on_ok(self):
        """Perform the action when the 'OK' button is clicked."""
        self.master.destroy()

    def cancel(self):
        """Cancel the operation and destroy the window."""
        self.scene_table = None
        self.master.destroy()

    def left_click_tree(self, event):
        """Handle the selection of a row in the tree."""
        row = self.tree.tree.identify_row(event.y)
        col = self.tree.tree.identify_column(event.x)
        if row == "" or col == "":
            return

        start = self.tree.get_selected_one(row)[0]
        end = self.tree.get_selected_one(row)[1]
        start_msec = time_format.timestr_to_msec(start)
        end_msec = time_format.timestr_to_msec(end)

        if col == "#2":
            self.plot.jump_to(end_msec)
        else:
            self.plot.jump_to(start_msec)

    def export_mp4(self):
        row = self.tree.tree.selection()[0]
        start = self.tree.get_selected_one(row)[0]
        end = self.tree.get_selected_one(row)[1]
        start_msec = time_format.timestr_to_msec(start)
        end_msec = time_format.timestr_to_msec(end)
        self.export.set_time_range(start_msec, end_msec)
        self.export.export()

    def extract_mp4(self):
        row = self.tree.tree.selection()[0]
        start = self.tree.get_selected_one(row)[0]
        end = self.tree.get_selected_one(row)[1]
        start_msec = time_format.timestr_to_msec(start)
        end_msec = time_format.timestr_to_msec(end)
        self.export.set_time_range(start_msec, end_msec)
        self.export.extract()

    def add(self):
        min_time = time_format.msec_to_timestr_with_fff(self.time_min)
        max_time = time_format.msec_to_timestr_with_fff(self.time_max)
        self.tree.scene_table_add(min_time, max_time)
        self._update()

    def edit(self):
        self.tree.scene_table_edit()
        self._update()

    def copy(self):
        self.tree.scene_table_copy()
        self._update()

    def remove(self):
        self.tree.delete_selected()
        self._update()

    def clear(self):
        """Clear the plot."""
        self.plot.clear()

    def _treeview_sort_column(self, tv, col):
        tar_list = [(tv.set(k, col), k) for k in tv.get_children("")]
        tar_list.sort()
        for index, (_val, k) in enumerate(tar_list):
            tv.move(k, "", index)

    def _update(self):
        self._treeview_sort_column(self.tree.tree, "start")
        self.clear()
        scene_table = {"start": [], "end": [], "member": [], "description": []}
        for item in self.tree.tree.get_children(""):
            scene_table["start"].append(self.tree.get_selected_one(item)[0])
            scene_table["end"].append(self.tree.get_selected_one(item)[1])
            scene_table["member"].append(self.tree.get_selected_one(item)[3])
            scene_table["description"].append(self.tree.get_selected_one(item)[4])
        self.scene_table = scene_table
        self.draw()

    def _update_new_scene_df(self, new_scene_df):
        self.clear()
        self.tree.clear()
        self.scene_table = {"start": [], "end": [], "member": [], "description": []}
        print(new_scene_df)
        for i, row in new_scene_df.iterrows():
            start = time_format.msec_to_timestr_with_fff(row["start"])
            end = time_format.msec_to_timestr_with_fff(row["end"])
            duration = row["end"] - row["start"]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            values = (start, end, duration_str, row["member"], row["description"])
            self.tree.insert(values)
            self.scene_table["start"].append(start)
            self.scene_table["end"].append(end)
            self.scene_table["member"].append(row["member"])
            self.scene_table["description"].append(row["description"])
        self.draw()

    def close(self):
        self.plot.close()
