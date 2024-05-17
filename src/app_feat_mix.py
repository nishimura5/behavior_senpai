import os
import tkinter as tk
from tkinter import ttk

from gui_parts import Combobox, StrEntry, TempFile
from line_plotter import LinePlotter
from python_senpai import file_inout


class App(ttk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Feature Mixer")
        self.pack(padx=10, pady=10)

        temp = TempFile()
        width, height, dpi = temp.get_window_size()
        self.calc_case = temp.data["calc_case"]
        self.lineplot = LinePlotter(fig_size=(width / dpi, height / dpi), dpi=dpi)

        load_frame = ttk.Frame(self)
        load_frame.pack(anchor=tk.NW, pady=5)
        self.feat_button = ttk.Button(load_frame, text="Open Feature file", command=self.load_feat)
        self.feat_button.pack(side=tk.LEFT, padx=(20, 0))
        self.feat_path_label = ttk.Label(load_frame, text="No Feature file loaded.")
        self.feat_path_label.pack(side=tk.LEFT, padx=(5, 0))
        self.member_combo = Combobox(load_frame, label="Member:", values=[""], width=5)
        self.member_combo.pack_horizontal(padx=5)

        tar_frame = ttk.Frame(self)
        tar_frame.pack(anchor=tk.NW, side=tk.TOP, pady=5)
        self.name_entry = StrEntry(tar_frame, label="Name:", default="", width=20)
        self.name_entry.pack_horizontal(padx=5)
        self.col_a_combo = Combobox(tar_frame, label="col A:", values=["Select column A"], width=25)
        self.col_a_combo.pack_horizontal(padx=5)
        op_list = ["/", "-", "*", "+"]
        self.op_combo = Combobox(tar_frame, label="", values=op_list, width=3)
        self.op_combo.pack_horizontal(padx=5)
        self.col_b_combo = Combobox(tar_frame, label="col B:", values=["Select column B"], width=25)
        self.col_b_combo.pack_horizontal(padx=5)
        self.normalize_list = ["No normalize", "MinMax"]
        self.normalize_combo = Combobox(tar_frame, label="Normalize:", values=self.normalize_list, width=15)
        self.normalize_combo.pack_horizontal(padx=5)
        self.add_button = ttk.Button(tar_frame, text="Add", command=self.add_row, state="disabled")
        self.add_button.pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(tar_frame, text="Delete Selected", command=self.delete_selected, state="disabled")
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        draw_frame = ttk.Frame(self)
        draw_frame.pack(anchor=tk.NW, pady=5)
        self.draw_button = ttk.Button(draw_frame, text="Draw", command=self.manual_draw, state="disabled")
        self.draw_button.pack(side=tk.LEFT, padx=5)
        self.export_button = ttk.Button(draw_frame, text="Export", command=self.export, state="disabled")
        self.export_button.pack(side=tk.LEFT, padx=(5, 50))
        self.repeat_draw_button = ttk.Button(draw_frame, text="Repeat Draw", command=self.repeat_draw)
        self.repeat_draw_button.pack(side=tk.LEFT)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("feature name", "col A", "op", "col B", "normalize")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("feature name", width=200)
        self.tree.column("col A", width=300)
        self.tree.column("op", width=50)
        self.tree.column("col B", width=300)
        self.tree.column("normalize", width=200)
        self.tree.pack()
        self.tree.bind("<<TreeviewSelect>>", self.select_tree_row)

        plot_frame = ttk.Frame(self)
        plot_frame.pack(pady=5)
        self.lineplot.pack(plot_frame)

        self._load(args)

    def _load(self, args):
        self.src_df = args["src_df"]
        self.cap = args["cap"]
        self.time_min, self.time_max = args["time_span_msec"]
        self.pkl_dir = args["pkl_dir"]
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.lineplot.set_vcap(self.cap)

    def load_feat(self):
        init_dir = os.path.join(self.calc_dir, self.calc_case)
        if os.path.exists(init_dir) is False:
            init_dir = self.calc_dir
        pkl_path = file_inout.open_pkl(init_dir)
        if pkl_path is None:
            return
        # update calc_case
        new_calc_case = os.path.basename(os.path.dirname(pkl_path))
        temp = TempFile()
        data = temp.data
        self.calc_case = new_calc_case
        data["calc_case"] = new_calc_case
        temp.save(data)

        self.feat_path = pkl_path
        self.feat_path_label["text"] = pkl_path.replace(os.path.dirname(self.pkl_dir), "..")
        self.feat_name = os.path.basename(pkl_path)
        self.feat_df = file_inout.load_track_file(pkl_path, allow_calculated_track_file=True)

        # update GUI
        cols = self.feat_df.columns.tolist()
        self.col_a_combo.set_values(cols)
        self.col_b_combo.set_values(cols)
        self.add_button["state"] = "normal"
        self.delete_btn["state"] = "normal"
        self.draw_button["state"] = "normal"
        self.member_combo.set_df(self.src_df)

    def select_tree_row(self, event):
        """Handle the selection of a row in the tree."""
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        feat_name = self.tree.item(selected, "values")[0]
        col_a = self.tree.item(selected, "values")[1]
        op = self.tree.item(selected, "values")[2]
        col_b = self.tree.item(selected, "values")[3]
        normalize = self.tree.item(selected, "values")[4]
        self.name_entry.update(feat_name)
        self.col_a_combo.set(col_a)
        self.op_combo.set(op)
        self.col_b_combo.set(col_b)
        self.normalize_combo.set(normalize)

    def add_row(self):
        feat_name = self.name_entry.get()
        if feat_name == "":
            return
        col_a = self.col_a_combo.get()
        op = self.op_combo.get()
        col_b = self.col_b_combo.get()
        normalize = self.normalize_combo.get()
        tar_list = [k for k in self.tree.get_children("")]
        for i, tar in enumerate(tar_list):
            tree_feat_name = self.tree.item(tar, "values")[0]
            tree_col_a = self.tree.item(tar, "values")[1]
            tree_op = self.tree.item(tar, "values")[2]
            tree_col_b = self.tree.item(tar, "values")[3]
            tree_normalize = self.tree.item(tar, "values")[4]
            # skip if exactly same row
            if tree_feat_name == feat_name and tree_col_a == col_a and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                return
            # overwrite if feat_name is already used
            elif tree_feat_name == feat_name:
                self.tree.delete(self.tree.get_children("")[i])
                self.tree.insert("", "end", values=(feat_name, col_a, op, col_b, normalize))
                return
            # rename if except feat_name exactly same row
            elif tree_col_a == col_a and tree_op == op and tree_col_b == col_b and tree_normalize == normalize:
                self.tree.delete(self.tree.get_children("")[i])
                self.tree.insert("", "end", values=(feat_name, col_a, op, col_b, normalize))
                return

        self.tree.insert("", "end", values=(feat_name, col_a, op, col_b, normalize))

    def delete_selected(self):
        if len(self.tree.selection()) == 0:
            return
        selected = self.tree.selection()[0]
        self.tree.delete(selected)

    def manual_draw(self):
        self.lineplot.clear()
        idx = self.feat_df.index
        self.feat_df.index = self.feat_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str)])
        mix_ops = []
        for tar in self.tree.get_children(""):
            mix_ops.append(self.tree.item(tar, "values"))
        self._draw(mix_ops)

    def repeat_draw(self):
        init_dir = os.path.join(self.calc_dir, self.calc_case)
        in_trk_path = file_inout.open_pkl(init_dir)
        if in_trk_path is None:
            return
        in_trk_df = file_inout.load_track_file(in_trk_path, allow_calculated_track_file=True)
        proc_history = in_trk_df.attrs["proc_history"]
        for history in proc_history:
            if isinstance(history, dict) and history["proc"] == "mix":
                mix_ops = history["source_cols"]
                break
        for row in mix_ops:
            self.tree.insert("", "end", values=row)
        self._draw(mix_ops)

    def _draw(self, mix_ops):
        data_col_names = []
        self.source_cols = []
        for row in mix_ops:
            feat_name = row[0]
            col_a = row[1]
            op = row[2]
            col_b = row[3]
            normalize = row[4]
            data_a = self.feat_df[col_a]
            data_b = self.feat_df[col_b]
            if op == "+":
                new_sr = data_a + data_b
            elif op == "-":
                new_sr = data_a - data_b
            elif op == "*":
                new_sr = data_a * data_b
            elif op == "/":
                new_sr = data_a / data_b
            if normalize == "MinMax":
                new_sr = (new_sr - new_sr.min()) / (new_sr.max() - new_sr.min())
            self.feat_df[feat_name] = new_sr
            data_col_names.append(feat_name)
            self.source_cols.append((feat_name, col_a, op, col_b, normalize))

        current_member = self.member_combo.get()
        self.lineplot.set_trk_df(self.src_df)
        self.lineplot.set_plot(self.feat_df, member=current_member, data_col_names=data_col_names)
        self.lineplot.draw()
        self.export_button["state"] = "normal"

    def export(self):
        """Export the calculated data to a file."""
        if self.feat_df is None:
            print("No data to export.")
            return
        file_name = os.path.basename(os.path.splitext(self.feat_path)[0])
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + "_featmix.pkl")

        data_col_names = [col[0] for col in self.source_cols] + ["timestamp"]

        export_df = self.feat_df.loc[:, data_col_names]
        export_df.attrs = self.feat_df.attrs
        history_dict = {"proc": "mix", "source_cols": self.source_cols}
        file_inout.save_pkl(dst_path, export_df, proc_history=history_dict)

    def clear(self):
        """Clear the lineplot."""
        self.lineplot.clear()
        self.source_cols = []
