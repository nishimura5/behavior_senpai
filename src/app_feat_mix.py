import os
import tkinter as tk
from tkinter import ttk

import pandas as pd
import tqdm

from behavior_senpai import calc_features, df_attrs, feature_proc, file_inout, hdf_df
from gui_feat_mix import Tree
from gui_parts import Combobox, TempFile, ToolTip
from line_plotter import LinePlotter


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title(f"Feature mixer ({args['trk_pkl_name']})")
        master.geometry("1300x800")
        self.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.calc_case = temp.data["calc_case"]
        self.tar_df = None
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        self.name_and_code = feature_proc.get_calc_codes()

        load_frame = ttk.Frame(self)
        load_frame.pack(padx=10, pady=5, anchor=tk.NW, expand=False, fill=tk.X)
        feat_btn = ttk.Button(load_frame, text="Select feature file", command=self.open_feat)
        feat_btn.pack(side=tk.LEFT)
        self.feat_path_label = ttk.Label(load_frame, text="No feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(10, 0), expand=True, fill=tk.X)

        self.scene_combo = Combobox(load_frame, label="Scene:", values=[""], width=15)
        self.scene_combo.pack_horizontal(anchor=tk.E, padx=5)

        draw_frame = ttk.Frame(self)
        draw_frame.pack(padx=10, pady=5, expand=False, anchor=tk.NW)
        self.add_btn = ttk.Button(draw_frame, text="Add calc", command=self.add_row, state="disabled")
        self.add_btn.pack(padx=(0, 10), side=tk.LEFT)

        self.import_btn = ttk.Button(draw_frame, text="Import", command=self.import_feat, state="disabled")

        self.import_btn.pack(padx=(0, 60), side=tk.LEFT)
        description = "Import another feature file and add calc."
        ToolTip(self.import_btn, description)

        self.draw_btn = ttk.Button(draw_frame, text="Draw", command=self.draw, state="disabled")
        self.draw_btn.pack(side=tk.LEFT)
        self.export_btn = ttk.Button(draw_frame, text="Save", command=self.export, state="disabled")
        self.export_btn.pack(side=tk.LEFT, padx=5)

        tree_canvas_frame = ttk.Frame(self)
        tree_canvas_frame.pack(padx=10, pady=5, fill=tk.X, expand=False)

        cols = [
            {"name": "feature name", "width": 180},
            {"name": "member", "width": 100},
            {"name": "col A", "width": 150},
            {"name": "op", "width": 30},
            {"name": "col B", "width": 150},
            {"name": "normalize", "width": 140},
        ]
        self.tree = Tree(tree_canvas_frame, cols, height=12)
        self.tree.pack(side=tk.LEFT)
        self.tree.add_menu("Edit", self.tree.edit_calc)
        self.tree.add_row_copy(column=1)
        self.tree.add_menu("Remove", self.tree.delete_selected)

        self.canvas = tk.Canvas(tree_canvas_frame, width=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        plot_outer_frame = ttk.Frame(self)
        plot_outer_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.scroll_canvas = tk.Canvas(plot_outer_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(plot_outer_frame, orient=tk.VERTICAL, command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.plot_container = ttk.Frame(self.scroll_canvas)
        self.container_id = self.scroll_canvas.create_window((0, 0), window=self.plot_container, anchor="nw")
        self.scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lineplot.pack(self.plot_container)

        self.lineplot.set_img_canvas(self.canvas)

        # scroll control
        def _update_scrollregion(event=None):
            self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
            self.scroll_canvas.itemconfigure(self.container_id, width=self.scroll_canvas.winfo_width())

        self.plot_container.bind("<Configure>", _update_scrollregion)
        self.scroll_canvas.bind("<Configure>", _update_scrollregion)

        def _on_mousewheel(event):
            delta = -1 if event.delta > 0 else 1
            self.scroll_canvas.yview_scroll(delta, "units")

        self.scroll_canvas.bind("<Enter>", lambda e: self.scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        self.scroll_canvas.bind("<Leave>", lambda e: self.scroll_canvas.unbind_all("<MouseWheel>"))

    def _load(self, event, args):
        src_df = args["src_df"].copy()
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.pkl_dir = args["pkl_dir"]

        idx = src_df.index
        src_df.index = src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

        self.lineplot.set_trk_df(src_df)
        self.lineplot.set_vcap(args["cap"])
        self.track_name = args["trk_pkl_name"]
        self.src_attrs = df_attrs.DfAttrs(src_df)

        # Update GUI
        self.src_attrs.load_scene_table()
        menu = self.src_attrs.get_scene_descriptions(add_blank=True)
        self.scene_combo.set_values(menu)
        self.tree.set_members(src_df.index.levels[1].unique().tolist())

        expected_pts_file_name = f"{args['trk_pkl_name'].split('.')[0]}.feat"
        expected_pts_file_path = os.path.join(self.calc_dir, self.calc_case, expected_pts_file_name)
        if os.path.exists(expected_pts_file_path) is False:
            calc_features.execute_calc_features(args)

        pl = file_inout.PickleLoader(self.calc_dir)
        pl.set_tar_path(expected_pts_file_path)
        self.load_feat(pl)

        # load h5 file for tree
        self._import_source_cols(expected_pts_file_path)

    def open_feat(self):
        pl = file_inout.PickleLoader(self.calc_dir)
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

        self.load_feat(pl)

    def load_feat(self, pl: file_inout.PickleLoader):
        self.feat_path = pl.get_tar_path()
        h5 = hdf_df.DataFrameStorage(self.feat_path)
        tar_df = h5.load_points_df()
        feat_path = self.feat_path.replace(os.path.dirname(self.pkl_dir), "..")
        tar_df = tar_df[~tar_df.index.duplicated(keep="last")]

        self.tar_df = tar_df
        self.feat_path_label["text"] = feat_path

        # update GUI
        self.tree.set_df(self.tar_df)
        self.add_btn["state"] = "normal"
        self.draw_btn["state"] = "normal"
        self.import_btn["state"] = "normal"

    def add_row(self):
        self.tree.add_calc()

    def add_row_old(self):
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
            (
                tree_feat_name,
                tree_member,
                tree_col_a,
                tree_op,
                tree_col_b,
                tree_normalize,
            ) = tar
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

    def import_feat(self):
        """Open a file dialog to select a feature file.
        Import the contents of the attrs.
        """
        pl = file_inout.PickleLoader(self.calc_dir)
        pl.join_calc_case(self.calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        h5_path = pl.get_tar_path()
        self._import_source_cols(h5_path)

    def _import_source_cols(self, h5_path):
        if os.path.exists(h5_path) is True:
            hdf = hdf_df.DataFrameStorage(h5_path)
            source_cols = hdf.load_mixnorm_source_cols()
            for row in source_cols:
                if row[2] not in self.tar_df.columns and row[2] != " ":
                    print(f"Column not found: {row[2]}")
                    continue
                if row[4] not in self.tar_df.columns and row[4] != " ":
                    print(f"Column not found: {row[4]}")
                    continue

                row[1] = str(row[1])
                if row[1] not in self.tree.get_members():
                    print(f"Member not found: {row[1]} in {self.tree.get_members()}")
                    row[1] = self.tree.get_members()[0]
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

            #            for i, row in enumerate(self.source_cols):
            for i, row in tqdm.tqdm(enumerate(self.source_cols), total=row_num):
                feat_name, m, col_a, op, col_b, normalize = row
                if member != str(m):
                    continue
                normalize = self.name_and_code[normalize]
                new_sr = feature_proc.arithmetic_operations(member_df, op, col_a, col_b)
                new_sr = feature_proc.calc(new_sr, normalize)

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
        self.lineplot.set_file_name(os.path.basename(self.feat_path).split(".")[0])
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
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + ".feat")
        h5 = hdf_df.DataFrameStorage(dst_path)
        h5.save_mixnorm_df(export_df, self.track_name, self.source_cols)

    def close(self):
        self.lineplot.close()
