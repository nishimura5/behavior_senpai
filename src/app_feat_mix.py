import os
import tkinter as tk
from tkinter import ttk

import pandas as pd

from behavior_senpai import df_attrs, file_inout
from gui_parts import Combobox, StrEntry, TempFile
from gui_tree import Tree
from line_plotter import LinePlotter


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title(f"Feature Mixer ({args['trk_pkl_name']})")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.calc_case = temp.data["calc_case"]
        self.tar_df = None
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        load_frame = ttk.Frame(self)
        load_frame.pack(anchor=tk.NW, expand=True, fill=tk.X, pady=5)
        self.load_combo = Combobox(load_frame, label="Load:", values=["Initial", "Add right"], width=15)
        self.load_combo.pack_horizontal(padx=5)
        self.load_combo.set_state("disabled")
        feat_btn = ttk.Button(load_frame, text="Select feature file", command=self.load_feat)
        feat_btn.pack(side=tk.LEFT, padx=5)
        self.feat_path_label = ttk.Label(load_frame, text="No feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(5, 0), expand=True, fill=tk.X)

        self.scene_combo = Combobox(load_frame, label="Scene:", values=[""], width=10)
        self.scene_combo.pack_horizontal(anchor=tk.E, padx=5)

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
        self.name_and_code = {
            "No normalize": "non",
            "MinMax": "minmax",
            "Threshold75%": "thresh75",
            "Threshold50%": "thresh50",
            "Threshold25%": "thresh25",
        }
        self.normalize_list = ["No normalize", "MinMax", "Threshold75%", "Threshold50%", "Threshold25%"]
        self.normalize_combo = Combobox(tar_frame, label="Normalize:", values=self.normalize_list, width=15)
        self.normalize_combo.pack_horizontal(padx=5)
        self.add_btn = ttk.Button(tar_frame, text="Add", command=self.add_row, state="disabled")
        self.add_btn.pack(side=tk.LEFT, padx=5)

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
        cols = [
            {"name": "feature name", "width": 200},
            {"name": "member", "width": 100},
            {"name": "col A", "width": 300},
            {"name": "op", "width": 50},
            {"name": "col B", "width": 300},
            {"name": "normalize", "width": 200},
        ]
        self.tree = Tree(tree_frame, cols, height=6, right_click=True)
        self.tree.pack(side=tk.LEFT)
        self.tree.tree.bind("<<TreeviewSelect>>", self.select_tree_row)
        self.tree.add_menu("Edit", self.edit)
        self.tree.add_menu("Remove", self.remove)
        self.tree.add_row_copy(column=1)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)

    def _load(self, event, args):
        src_df = args["src_df"].copy()
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.pkl_dir = args["pkl_dir"]

        idx = src_df.index
        src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

        self.lineplot.set_trk_df(src_df)
        self.lineplot.set_vcap(args["cap"])
        self.src_attrs = df_attrs.DfAttrs(src_df)

        # Update GUI
        self.src_attrs.load_scene_table()
        menu = self.src_attrs.get_scene_descriptions(add_blank=True)
        self.scene_combo.set_values(menu)
        self.tree.set_members(src_df.index.levels[1].unique().tolist())

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
        feat_path = self.feat_path.replace(os.path.dirname(self.pkl_dir), "..")
        tar_df = pl.load_pkl()
        tar_df = tar_df[~tar_df.index.duplicated(keep="last")]
        tar_attrs = df_attrs.DfAttrs(tar_df)
        tar_attrs.load_proc_history()
        if "track_name" in tar_attrs.newest_proc_history:
            track_name = tar_attrs.newest_proc_history["track_name"]
        else:
            track_name = None

        load_option = self.load_combo.get()
        if load_option == "Initial":
            self.tar_df = tar_df
            self.feat_path_label["text"] = feat_path
            self.load_combo.set_values(["Initial", "Add right"])
        elif load_option == "Add right":
            if len(self.tar_df) != len(tar_df):
                print("The length of the dataframes are not the same.")
                return
            tar_df = tar_df.drop("timestamp", axis=1)
            self.tar_df = pd.concat([self.tar_df, tar_df], axis=1)
            self.feat_path_label["text"] = f"{self.feat_path_label['text']}, {feat_path}"
            self.load_combo.set_values(["Add right", "Initial"])
            print(f"New width: {len(self.tar_df.columns)}")

        # update GUI
        self.member_combo.set_df(self.tar_df)
        self._set_col_combos(self.member_combo.get())
        self.add_btn["state"] = "normal"
        self.draw_btn["state"] = "normal"
        self.import_btn["state"] = "normal"
        self.load_combo.set_state("readonly")

    def select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        selected = self.tree.get_selected_one()
        if selected is None:
            return
        feat_name, member, col_a, op, col_b, normalize = selected
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
        tar_list = self.tree.get_all()
        for i, tar in enumerate(tar_list):
            tree_feat_name, tree_member, tree_col_a, tree_op, tree_col_b, tree_normalize = tar
            # skip if exactly same row
            if tree_feat_name == feat_name and tree_col_a == col_a and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                return
            # overwrite if feat_name is already used
            elif tree_feat_name == feat_name:
                self.tree.tree.delete(self.tree.tree.get_children("")[i])
                break
            # rename if except feat_name exactly same row
            elif tree_col_a == col_a and tree_member == member and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                self.tree.tree.delete(self.tree.tree.get_children("")[i])
                break

        values = (feat_name, member, col_a, op, col_b, normalize)
        self.tree.insert(values)

    def selected_op(self, event):
        op = self.op_combo.get()
        if op == " ":
            self.col_b_combo.set_values([" "])
        else:
            self.col_b_combo.set_values(self.col_a_combo.get_values())

    def selected_member(self, event):
        self._set_col_combos(self.member_combo.get())

    def _set_col_combos(self, member):
        # print(self.tar_df.loc[pd.IndexSlice[:, member], :])
        col_list = self.tar_df.loc[pd.IndexSlice[:, member], :].dropna(how="all", axis=1).columns.tolist()
        col_list.remove("timestamp")
        col_list.append(" ")
        self.col_a_combo.set_values(col_list)
        self.col_b_combo.set_values(col_list)

    def edit(self):
        self.tree.feat_mix_edit()

    def remove(self):
        self.tree.delete_selected()

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
        if in_trk_attrs.validate_model(self.src_attrs) is False:
            return
        if in_trk_attrs.validate_newest_history_proc("mix") is False:
            return
        for row in in_trk_attrs.get_source_cols():
            if row[2] not in self.tar_df.columns and row[2] != " ":
                print(f"Column not found: {row[2]}")
                continue
            if row[4] not in self.tar_df.columns and row[4] != " ":
                print(f"Column not found: {row[4]}")
                continue
            self.tree.insert(row)

    def draw(self):
        self.lineplot.clear_fig()
        self.feat_df = pd.DataFrame()
        self.source_cols = self.tree.get_all()

        tar_scene = self.scene_combo.get()
        scenes = self.src_attrs.get_scenes(tar_scene)

        scene_filtered_df = self.tar_df.copy()
        if scenes is not None:
            condition_sr = pd.Series(False, index=self.tar_df.index)
            for scene in scenes:
                condition_sr |= self.tar_df["timestamp"].between(scene[0] - 1, scene[1] + 1)
            scene_filtered_df.loc[~condition_sr, :] = pd.NA
        row_num = len(self.source_cols)
        if row_num == 0:
            print("No data to draw.")
            return
        members = list(set([str(x[1]) for x in self.source_cols]))
        for member in members:
            member_df = scene_filtered_df.loc[pd.IndexSlice[:, member], :].drop("timestamp", axis=1)
            member_feat_df = pd.DataFrame()

            for i, row in enumerate(self.source_cols):
                feat_name, m, col_a, op, col_b, normalize = row
                if member != str(m):
                    continue
                normalize = self.name_and_code[normalize]
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
                if normalize == "minmax":
                    new_sr = (new_sr - new_sr.min()) / (new_sr.max() - new_sr.min())
                elif normalize == "thresh75":
                    new_sr = new_sr > new_sr.quantile(0.75)
                    new_sr = new_sr.astype(int)
                elif normalize == "thresh50":
                    new_sr = new_sr > new_sr.median()
                    new_sr = new_sr.astype(int)
                elif normalize == "thresh25":
                    new_sr = new_sr > new_sr.quantile(0.25)
                    new_sr = new_sr.astype(int)

                # concat right
                member_feat_df = pd.concat([member_feat_df, new_sr.to_frame(feat_name)], axis=1)
                plot_df = new_sr.to_frame(feat_name)

                plot_df["timestamp"] = self.tar_df["timestamp"]
                self.lineplot.add_ax(row_num, 2, i)
                if i == row_num - 1:
                    self.lineplot.set_plot_and_violin(plot_df, member=member, data_col_name=feat_name, is_last=True)
                else:
                    self.lineplot.set_plot_and_violin(plot_df, member=member, data_col_name=feat_name)
            # concat bottom
            self.feat_df = pd.concat([self.feat_df, member_feat_df], axis=0)

        self.feat_df["timestamp"] = self.tar_df["timestamp"]
        self.feat_df = self.feat_df.sort_index()
        self.lineplot.draw()
        self.lineplot.set_members_to_draw(members)
        self.export_btn["state"] = "normal"

    def export(self):
        """Export the calculated data to a file."""
        if len(self.feat_df) == 0:
            print("No data to export.")
            return
        file_name = os.path.basename(self.feat_path).split(".")[0]

        export_df = self.feat_df
        export_df.attrs = self.src_attrs.attrs
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + "_mix.feat.pkl")
        history_dict = df_attrs.make_history_dict("mix", self.source_cols, {})
        file_inout.save_pkl(dst_path, export_df, proc_history=history_dict)

    def close(self):
        self.lineplot.close()
