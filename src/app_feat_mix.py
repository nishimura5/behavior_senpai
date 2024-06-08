import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
from gui_parts import Combobox, StrEntry, TempFile
from line_plotter import LinePlotter
from python_senpai import df_attrs, file_inout, keypoints_proc, time_format


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        start_str = time_format.msec_to_timestr(args["time_span_msec"][0])
        end_str = time_format.msec_to_timestr(args["time_span_msec"][1])
        master.title(f"Feature Mixer ({args['trk_pkl_name']} {start_str} to {end_str})")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.calc_case = temp.data["calc_case"]
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        load_frame = ttk.Frame(self)
        load_frame.pack(anchor=tk.NW, pady=5)
        feat_btn = ttk.Button(load_frame, text="Open Feature file", command=self.load_feat)
        feat_btn.pack(side=tk.LEFT, padx=(20, 0))
        self.feat_path_label = ttk.Label(load_frame, text="No Feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(5, 0))

        tar_frame = ttk.Frame(self)
        tar_frame.pack(anchor=tk.NW, side=tk.TOP, pady=5)
        self.name_entry = StrEntry(tar_frame, label="Name:", default="", width=20)
        self.name_entry.pack_horizontal(padx=5)
        self.member_combo = Combobox(tar_frame, label="Member:", values=[""], width=5)
        self.member_combo.pack_horizontal(padx=5)
        self.member_combo.set_selected_bind(self.selected_member)
        self.col_a_combo = Combobox(tar_frame, label="col A:", values=["Select column"], width=25)
        self.col_a_combo.pack_horizontal(padx=5)
        op_list = ["/", "-", "*", "+", " "]
        self.op_combo = Combobox(tar_frame, label="", values=op_list, width=3)
        self.op_combo.set_selected_bind(self.selected_op)

        self.op_combo.pack_horizontal(padx=5)
        self.col_b_combo = Combobox(tar_frame, label="col B:", values=["Select column"], width=25)
        self.col_b_combo.pack_horizontal(padx=5)
        self.normalize_list = ["No normalize", "MinMax", "Threshold50%"]
        self.normalize_combo = Combobox(tar_frame, label="Normalize:", values=self.normalize_list, width=15)
        self.normalize_combo.pack_horizontal(padx=5)
        self.add_btn = ttk.Button(tar_frame, text="Add", command=self.add_row, state="disabled")
        self.add_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(tar_frame, text="Delete Selected", command=self.delete_selected, state="disabled")
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        draw_frame = ttk.Frame(self)
        draw_frame.pack(anchor=tk.NW, pady=5)
        self.draw_btn = ttk.Button(draw_frame, text="Draw", command=self.draw, state="disabled")
        self.draw_btn.pack(side=tk.LEFT, padx=5)
        self.export_btn = ttk.Button(draw_frame, text="Export", command=self.export, state="disabled")
        self.export_btn.pack(side=tk.LEFT, padx=(5, 50))
        self.import_btn = ttk.Button(draw_frame, text="Import", command=self.import_feat, state="disabled")
        self.import_btn.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("feature name", "member", "col A", "op", "col B", "normalize")
        self.tree = ttk.Treeview(tree_frame, columns=cols, height=6, show="headings", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("feature name", width=200)
        self.tree.column("member", width=100)
        self.tree.column("col A", width=300)
        self.tree.column("op", width=50)
        self.tree.column("col B", width=300)
        self.tree.column("normalize", width=200)
        self.tree.pack(side=tk.LEFT)
        self.tree.bind("<<TreeviewSelect>>", self.select_tree_row)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)

    def _load(self, event, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args["time_span_msec"]

        self.pkl_dir = args["pkl_dir"]
        self.lineplot.set_trk_df(self.src_df)
        self.lineplot.set_vcap(self.cap)

    def load_feat(self):
        pl = file_inout.PickleLoader(self.calc_dir, "feature")
        pl.join_calc_case(self.calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        # update calc_case
        temp = TempFile()
        data = temp.data
        new_calc_case = pl.get_tar_parent()
        self.calc_case = new_calc_case
        data["calc_case"] = new_calc_case
        temp.save(data)

        self.feat_path = pl.get_tar_path()
        self.feat_path_label["text"] = self.feat_path.replace(os.path.dirname(self.pkl_dir), "..")
        self.feat_name = os.path.basename(self.feat_path)
        self.tar_df = pl.load_pkl()

        # timestampの範囲を抽出
        self.tar_df = keypoints_proc.filter_by_timerange(self.tar_df, self.time_min, self.time_max)
        self.tar_df = self.tar_df[~self.tar_df.index.duplicated(keep="last")]

        # update GUI
        self.member_combo.set_df(self.tar_df)
        self._set_col_combos(self.member_combo.get())
        self.add_btn["state"] = "normal"
        self.delete_btn["state"] = "normal"
        self.draw_btn["state"] = "normal"
        self.import_btn["state"] = "normal"

    def select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        feat_name, member, col_a, op, col_b, normalize = self.tree.item(selected, "values")
        self.name_entry.update(feat_name)
        self.member_combo.set(member)
        self.col_a_combo.set(col_a)
        self.op_combo.set(op)
        self.col_b_combo.set(col_b)
        self.normalize_combo.set(normalize)

    def add_row(self):
        feat_name = self.name_entry.get()
        if feat_name == "":
            return
        member = self.member_combo.get()
        col_a = self.col_a_combo.get()
        op = self.op_combo.get()
        col_b = self.col_b_combo.get()
        normalize = self.normalize_combo.get()
        tar_list = [k for k in self.tree.get_children("")]
        for i, tar in enumerate(tar_list):
            tree_feat_name, tree_member, tree_col_a, tree_op, tree_col_b, tree_normalize = self.tree.item(tar, "values")
            # skip if exactly same row
            if tree_feat_name == feat_name and tree_col_a == col_a and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                return
            # overwrite if feat_name is already used
            elif tree_feat_name == feat_name:
                self.tree.delete(self.tree.get_children("")[i])
                self.tree.insert("", "end", values=(feat_name, member, col_a, op, col_b, normalize))
                return
            # rename if except feat_name exactly same row
            elif tree_col_a == col_a and tree_member == member and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                self.tree.delete(self.tree.get_children("")[i])
                self.tree.insert("", "end", values=(feat_name, member, col_a, op, col_b, normalize))
                return

        self.tree.insert("", "end", values=(feat_name, member, col_a, op, col_b, normalize))

    def delete_selected(self):
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        self.tree.delete(selected)

    def selected_op(self, event):
        op = self.op_combo.get()
        if op == " ":
            self.col_b_combo.set_values([" "])
        else:
            self.col_b_combo.set_values(self.col_a_combo.get_values())

    def selected_member(self, event):
        self._set_col_combos(self.member_combo.get())

    def _set_col_combos(self, member):
        col_list = self.tar_df.loc[pd.IndexSlice[:, member], :].dropna(how="all", axis=1).columns.tolist()
        col_list.remove("timestamp")
        col_list.append(" ")
        self.col_a_combo.set_values(col_list)
        self.col_b_combo.set_values(col_list)

    def import_feat(self):
        """Open a file dialog to select a feature file.
        Import the contents of the attrs.
        """
        pl = file_inout.PickleLoader(self.calc_dir, "feature")
        pl.join_calc_case(self.calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        in_trk_df = pl.load_pkl()
        in_trk_attrs = df_attrs.DfAttrs(in_trk_df)
        in_trk_attrs.load_proc_history()
        if in_trk_attrs.validate_newest_history_proc("mix", self.src_attrs["model"]) is False:
            return
        for row in in_trk_attrs.get_source_cols():
            if row[2] not in self.tar_df.columns and row[2] != " ":
                print(f"Column not found: {row[2]}")
                continue
            if row[4] not in self.tar_df.columns and row[4] != " ":
                print(f"Column not found: {row[4]}")
                continue
            self.tree.insert("", "end", values=row)

    def draw(self):
        self.lineplot.clear_fig()
        self.feat_df = pd.DataFrame()
        rows = [self.tree.item(row, "values") for row in self.tree.get_children("")]
        self.source_cols = rows

        idx = self.tar_df.index
        self.tar_df.index = self.tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])

        row_num = len(rows)
        for i, row in enumerate(rows):
            feat_name, member, col_a, op, col_b, normalize = row
            member_df = self.tar_df.loc[pd.IndexSlice[:, member], :].drop("timestamp", axis=1)
            data_a = member_df[col_a]
            if op == "+":
                data_b = member_df[col_b]
                new_sr = data_a + data_b
            elif op == "-":
                data_b = member_df[col_b]
                new_sr = data_a - data_b
            elif op == "*":
                data_b = member_df[col_b]
                new_sr = data_a * data_b
            elif op == "/":
                data_b = member_df[col_b]
                new_sr = data_a / data_b
            elif op == " ":
                new_sr = data_a
            if normalize == "MinMax":
                new_sr = (new_sr - new_sr.min()) / (new_sr.max() - new_sr.min())
            elif normalize == "Threshold50%":
                new_sr = new_sr > new_sr.median()
            self.feat_df = pd.concat([self.feat_df, new_sr.to_frame(feat_name)], axis=1)
            plot_df = new_sr.to_frame(feat_name)
            plot_df["timestamp"] = self.tar_df["timestamp"]
            if plot_df.dtypes[feat_name] == "bool":
                plot_df[feat_name] = plot_df[feat_name].astype(int)
            self.lineplot.add_ax(row_num, 2, i)
            if i == row_num - 1:
                self.lineplot.set_plot_and_violin(plot_df, member=member, data_col_name=feat_name, is_last=True)
            else:
                self.lineplot.set_plot_and_violin(plot_df, member=member, data_col_name=feat_name)

        self.feat_df["timestamp"] = self.tar_df["timestamp"]
        self.lineplot.draw()
        self.export_btn["state"] = "normal"

    def export(self):
        """Export the calculated data to a file."""
        if len(self.feat_df) == 0:
            print("No data to export.")
            return
        file_name = os.path.basename(self.feat_path).split(".")[0]

        data_col_names = [col[0] for col in self.source_cols] + ["timestamp"]

        export_df = self.feat_df.loc[:, data_col_names]
        export_df.attrs = self.src_attrs
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + "_mix.feat.pkl")
        history_dict = df_attrs.make_history_dict("mix", self.source_cols, {})
        file_inout.save_pkl(dst_path, export_df, proc_history=history_dict)
