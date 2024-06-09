import os
import sys
import tkinter as tk
from tkinter import ttk

import pandas as pd
from gui_parts import CalcCaseEntry, Combobox, IntEntry, TempFile
from line_plotter import LinePlotter
from python_senpai import df_attrs, file_inout, keypoints_proc
from vector_gui_parts import MemberKeypointComboboxesFor3Point


class App(ttk.Frame):
    """Application for calculating vectors."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Points Calculation")
        self.pack(padx=10, pady=10)
        self.bind("<Map>", lambda event: self._load(event, args))

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        tar_frame = ttk.Frame(self)
        tar_frame.pack(pady=5)
        self.name_and_code = {
            "distance (|AB|)": "norm",
            "sin,cos (∠BAC)": "sin_cos",
            "xy_component (AB_x, AB_y)": "component",
            "cross_product (AB×AC)": "cross",
            "dot_product (AB・AC)": "dot",
            "plus (AB+AC)": "plus",
            "norms (|AB||AC|)": "norms",
        }
        self.point2_list = ["distance (|AB|)", "xy_component (AB_x, AB_y)"]
        self.point3_list = ["sin,cos (∠BAC)", "cross_product (AB×AC)", "dot_product (AB・AC)", "plus (AB+AC)", "norms (|AB||AC|)"]
        self.calc_type_combo = Combobox(tar_frame, label="Calc:", width=22, values=list(self.name_and_code.keys()))
        self.calc_type_combo.pack_horizontal(padx=5)
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", "vector.gif")
        self.img = tk.PhotoImage(file=img_path)
        self.img_label = ttk.Label(tar_frame, image=self.img)
        self.img_label.pack(side=tk.LEFT, padx=5)
        self.member_combo = MemberKeypointComboboxesFor3Point(tar_frame)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        add_btn = ttk.Button(tar_frame, text="Add", command=self.add_row)
        add_btn.pack(side=tk.LEFT, padx=5)
        delete_btn = ttk.Button(tar_frame, text="Delete Selected", command=self.delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=5)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        self.calc_case_entry = CalcCaseEntry(setting_frame, temp.data["calc_case"])
        self.calc_case_entry.pack(side=tk.LEFT, padx=5)

        self.thinning_entry = IntEntry(setting_frame, label="Thinning:", default=temp.data["thinning"])
        self.thinning_entry.pack_horizontal(padx=5)

        draw_btn = ttk.Button(setting_frame, text="Draw", command=self.draw)
        draw_btn.pack(side=tk.LEFT)
        self.export_btn = ttk.Button(setting_frame, text="Export", command=self.export, state="disabled")
        self.export_btn.pack(side=tk.LEFT, padx=(5, 50))
        import_btn = ttk.Button(setting_frame, text="Import", command=self.import_feat)
        import_btn.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("calc", "member", "A", "B", "C")
        self.tree = ttk.Treeview(tree_frame, columns=cols, height=6, show="headings", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("calc", width=300)
        self.tree.column("member", width=200)
        self.tree.column("A", width=50)
        self.tree.column("B", width=50)
        self.tree.column("C", width=50)
        self.tree.pack(side=tk.LEFT)
        self.tree.bind("<<TreeviewSelect>>", self.select_tree_row)

        scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)
        self.lineplot.set_single_ax()

    def _load(self, event, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.src_attrs = self.src_df.attrs
        self.tar_df = self.src_df[~self.src_df.index.duplicated(keep="last")]

        # update GUI
        self.member_combo.set_df(self.tar_df)
        self.lineplot.set_trk_df(self.src_df)
        self.lineplot.set_vcap(self.cap)

    def select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        calc, member, point_a, point_b, point_c = self.tree.item(selected, "values")
        self.calc_type_combo.set(calc)
        self.member_combo.set(member, point_a, point_b, point_c)

    def add_row(self):
        calc = self.calc_type_combo.get()
        member, point_a, point_b, point_c = self.member_combo.get_selected()
        # Ignore point_c if calc uses 2-point-vector.
        if calc in self.point2_list and point_c != " ":
            point_c = " "
        tar_list = [k for k in self.tree.get_children("")]
        for i, tar in enumerate(tar_list):
            tree_calc, tree_member, tree_point_a, tree_point_b, tree_point_c = self.tree.item(tar, "values")

            # skip if exactly same row
            if tree_calc == calc and tree_member == member and tree_point_a == point_a and tree_point_b == point_b and tree_point_c == point_c:
                return

        self.tree.insert("", "end", values=(calc, member, point_a, point_b, point_c))

    def delete_selected(self):
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        self.tree.delete(selected)

    def import_feat(self):
        """Open a file dialog to select a feature file.
        Import the contents of the attrs.
        """
        calc_case = self.calc_case_entry.get_calc_case()
        pl = file_inout.PickleLoader(self.calc_dir, pkl_type="feature")
        pl.join_calc_case(calc_case)
        is_file_selected = pl.show_open_dialog()
        if is_file_selected is False:
            return
        in_trk_df = pl.load_pkl()
        in_trk_attrs = df_attrs.DfAttrs(in_trk_df)
        in_trk_attrs.load_proc_history()
        if in_trk_attrs.validate_newest_history_proc("points", self.src_attrs["model"]) is False:
            return
        for row in in_trk_attrs.get_source_cols():
            self.tree.insert("", "end", values=row)

    def draw(self):
        self.lineplot.clear()
        self.feat_df = pd.DataFrame()
        rows = [self.tree.item(row, "values") for row in self.tree.get_children("")]
        self.source_cols = rows

        # thinning for plotting
        thinning = self.thinning_entry.get()
        self.thinning_entry.save_to_temp("thinning")
        thinned_df = keypoints_proc.thinning(self.tar_df, thinning)

        idx = thinned_df.index
        thinned_df.index = thinned_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2]])

        for calc, member, point_a, point_b, point_c in rows:
            code = self.name_and_code[calc]
            member_df = thinned_df.loc[pd.IndexSlice[:, member], :]
            point_a, point_b = int(point_a), int(point_b)
            if code == "norm":
                plot_df = keypoints_proc.calc_norm(member_df, point_a, point_b)
            elif code == "sin_cos":
                plot_df = keypoints_proc.calc_sin_cos(member_df, point_a, point_b, int(point_c))
            elif code == "component":
                plot_df = keypoints_proc.calc_xy_component(member_df, point_a, point_b)
            elif code == "cross":
                plot_df = keypoints_proc.calc_cross_product(member_df, point_a, point_b, int(point_c))
            elif code == "dot":
                plot_df = keypoints_proc.calc_dot_product(member_df, point_a, point_b, int(point_c))
            elif code == "plus":
                plot_df = keypoints_proc.calc_plus(member_df, point_a, point_b, int(point_c))
            elif code == "norms":
                plot_df = keypoints_proc.calc_norms(member_df, point_a, point_b, int(point_c))

            col_names = plot_df.columns.tolist()
            feat_col_names = self.feat_df.columns.tolist()
            duplicate_cols = [col for col in col_names if col in feat_col_names]
            if len(duplicate_cols) > 0:
                self.feat_df = pd.concat([self.feat_df, plot_df], axis=0)
            else:
                self.feat_df = pd.concat([self.feat_df, plot_df], axis=1)

            plot_df["timestamp"] = thinned_df.loc[pd.IndexSlice[:, :, point_a], :].droplevel(2)["timestamp"]
            self.lineplot.set_plot(plot_df, member, col_names)

        self.lineplot.draw()
        self.export_btn["state"] = "normal"

    def export(self):
        """Export the calculated data to a file."""
        if len(self.feat_df) == 0:
            print("No data to export.")
            return
        self.feat_df = self.feat_df.sort_index()
        file_name = os.path.splitext(self.src_attrs["video_name"])[0]
        first_keypoint_id = self.tar_df.index.get_level_values(2).values[0]
        timestamp_df = self.tar_df.loc[pd.IndexSlice[:, :, first_keypoint_id], :].droplevel(2)["timestamp"]
        timestamp_df = timestamp_df[~timestamp_df.index.duplicated(keep="last")]
        self.feat_df = self.feat_df[~self.feat_df.index.duplicated(keep="last")]
        export_df = pd.concat([self.feat_df, timestamp_df], axis=1)
        export_df = export_df.dropna(how="all")
        export_df.attrs = self.src_attrs
        calc_case = self.calc_case_entry.get_calc_case()
        dst_path = os.path.join(self.calc_dir, calc_case, file_name + "_pts.feat.pkl")
        history_dict = df_attrs.make_history_dict("points", self.source_cols, {})
        file_inout.save_pkl(dst_path, export_df, proc_history=history_dict)

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir
