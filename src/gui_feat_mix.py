import os
import sys
import tkinter as tk
from tkinter import ttk

import pandas as pd

from behavior_senpai import feature_proc
from gui_parts import Combobox, StrEntry

IS_DARWIN = sys.platform.startswith("darwin")


class Tree(ttk.Frame):
    def __init__(self, master, columns: list, height: int):
        super().__init__(master)
        cols = [col["name"] for col in columns]
        self.tree = ttk.Treeview(self, columns=cols, height=height, show="headings", selectmode="extended")
        for column in columns:
            self.tree.heading(column["name"], text=column["name"])
            self.tree.column(column["name"], width=column["width"])
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)
        if not IS_DARWIN:
            self.tree.bind("<Button-3>", self._right_click_tree)
        else:
            self.tree.bind("<Button-2>", self._right_click_tree)
        self.menu = tk.Menu(self, tearoff=0)

    def add_row_copy(self, column):
        self.member_column = column
        self.add_menu("Copy", self._copy_row)

    def set_members(self, members):
        self.member_list = members

    def get_members(self):
        return self.member_list

    def add_menu(self, label, command):
        self.menu.add_command(label=label, command=command)

    def insert(self, values: list):
        self.tree.insert("", tk.END, values=values)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def selection(self):
        return self.tree.selection()

    def set_select(self, col, value):
        items = self.tree.get_children("")
        for item in items:
            if str(self.tree.item(item)["values"][col]) == value:
                self.tree.selection_set(item)

    def get_all(self):
        return [self.tree.item(item)["values"] for item in self.tree.get_children("")]

    def _right_click_tree(self, event):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        self.menu.post(event.x_root, event.y_root)

    def delete_selected(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        for item in selected:
            self.tree.delete(item)

    def set_df(self, df):
        self.tar_df = df

    def add_calc(self):
        dialog = FeatMixTreeDialog(self, self.member_list, contain_blank=False)
        dialog.set_df(self.tar_df)
        self.wait_window(dialog)
        new_feature_name = dialog.selected_feature_name
        new_member = dialog.selected_member
        new_col_a = dialog.selected_col_a
        new_op = dialog.selected_op
        new_col_b = dialog.selected_col_b
        new_normalize = dialog.selected_normalize

        if new_member is None:
            return
        values = [new_feature_name, new_member, new_col_a, new_op, new_col_b, new_normalize]
        self.tree.insert("", tk.END, values=values)

    def edit_calc(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        dialog = FeatMixTreeDialog(self, self.member_list, contain_blank=True)
        dialog.set_df(self.tar_df)
        if len(selected) == 1:
            dialog.set_default(*self.tree.item(selected[0])["values"])
        self.wait_window(dialog)
        new_feature_name = dialog.selected_feature_name
        new_member = dialog.selected_member
        new_col_a = dialog.col_a
        new_op = dialog.op
        new_col_b = dialog.col_b
        new_normalize = dialog.normalize

        if new_member is None:
            return
        values = [new_feature_name, new_member, new_col_a, new_op, new_col_b, new_normalize]
        for item in selected:
            values = self.tree.item(item)["values"]
            if new_member != "":
                values[1] = new_member
            if new_feature_name != "":
                values[0] = new_feature_name
            if new_col_a != " ":
                values[2] = new_col_a
            if new_op != " ":
                values[3] = new_op
            if new_col_b != " ":
                values[4] = new_col_b
            if new_normalize != " ":
                values[5] = new_normalize
            self.tree.item(item, values=values)

    def _copy_row(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        dialog = MemberComboDialog(self, self.member_list)
        self.wait_window(dialog)
        selected_member = dialog.selected_member
        if selected_member is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            values[self.member_column] = selected_member
            self.tree.insert("", tk.END, values=values)


class FeatMixTreeDialog(tk.Toplevel):
    def __init__(self, master, member_list, contain_blank=False):
        super().__init__(master)
        self.focus_set()
        self.title("Feature mixer")
        self.resizable(0, 0)

        tar_frame = ttk.Frame(self)
        tar_frame.pack(side=tk.TOP, padx=20, pady=(20, 10))
        calc_select_frame = ttk.Frame(tar_frame)
        calc_select_frame.pack(pady=5, side=tk.TOP, fill=tk.X)
        self.feature_name_entry = StrEntry(calc_select_frame, label="Feature name:", width=20)
        self.feature_name_entry.pack_horizontal(padx=5)
        self.feature_name_entry.update("new_feature")
        self.member_combo = Combobox(calc_select_frame, label="Member:", width=20, values=member_list)
        self.member_combo.pack_horizontal(padx=5)
        self.member_combo.set_selected_bind(self.on_select_member)

        calc_frame = ttk.Frame(tar_frame)
        calc_frame.pack(pady=5, side=tk.TOP, fill=tk.X)
        self.col_a_combo = Combobox(calc_frame, label="col A:", width=20, values=["Select column"])
        self.col_a_combo.pack_horizontal(padx=5)
        op_list = ["/", "-", "*", "+", " "]
        self.op_combo = Combobox(calc_frame, label="op:", width=6, values=op_list)
        self.op_combo.pack_horizontal(padx=5)
        self.op_combo.set_selected_bind(self.selected_op)
        self.col_b_combo = Combobox(calc_frame, label="col B:", width=20, values=["Select column"])
        self.col_b_combo.pack_horizontal(padx=5)

        norm_frame = ttk.Frame(tar_frame)
        norm_frame.pack(pady=5, side=tk.TOP, fill=tk.X)
        self.name_and_code = feature_proc.get_calc_codes()
        self.normalize_list = list(self.name_and_code.keys())
        self.normalize_combo = Combobox(norm_frame, label="Normalize:", values=self.normalize_list, width=25)
        self.normalize_combo.pack_horizontal(padx=5)

        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, pady=(10, 20))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT)

        self.grab_set()
        self.selected_feature_name = None
        self.selected_member = None
        self.selected_col_a = None
        self.selected_op = None
        self.selected_col_b = None
        self.selected_normalize = None

    def set_df(self, df):
        self.tar_df = df
        self.member_combo.set_df(df)
        self.member_combo.set()
        self._set_col_combos(self.member_combo.get())

    def on_select_member(self, event):
        self._set_col_combos(self.member_combo.get())

    def _set_col_combos(self, member):
        # print(self.tar_df.loc[pd.IndexSlice[:, member], :])
        col_list = self.tar_df.loc[pd.IndexSlice[:, member], :].dropna(how="all", axis=1).columns.tolist()
        col_list.remove("timestamp")
        col_list.append(" ")
        self.col_a_combo.set_values(col_list)
        self.col_b_combo.set_values(col_list)
        self.op_combo.set(" ")
        self.col_b_combo.set(" ")

    def set_default(self, feature_name, member, col_a, op_b, col_b, normalize):
        self.feature_name_entry.update(feature_name)
        self.member_combo.set(member)
        self.col_a_combo.set(col_a)
        self.op_combo.set(op_b)
        self.col_b_combo.set(col_b)
        self.normalize_combo.set(normalize)

    def on_ok(self):
        self.selected_feature_name = self.feature_name_entry.get()
        self.selected_member = self.member_combo.get()
        self.selected_col_a = self.col_a_combo.get()
        self.selected_op = self.op_combo.get()
        self.selected_col_b = self.col_b_combo.get()
        self.selected_normalize = self.normalize_combo.get()
        self.destroy()

    def on_cancel(self):
        self.selected_member = None
        self.destroy()

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir

    def selected_op(self, event):
        op = self.op_combo.get()
        if op == " ":
            self.col_b_combo.set_values([" "])
        else:
            self.col_b_combo.set_values(self.col_a_combo.get_values())


class MemberComboDialog(tk.Toplevel):
    def __init__(self, master, member_list):
        super().__init__(master)
        self.focus_set()
        self.title("Select member")
        self.resizable(0, 0)

        tar_frame = ttk.Frame(self)
        tar_frame.pack(side=tk.TOP, padx=20, pady=(20, 10))
        combo_frame = ttk.Frame(tar_frame)
        combo_frame.pack(side=tk.TOP, pady=5)
        label = ttk.Label(combo_frame, text="Member:")
        label.pack(side=tk.LEFT, padx=5)
        self.member_combo = ttk.Combobox(combo_frame, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo["values"] = member_list
        self.member_combo.current(0)

        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, padx=20, pady=(10, 20))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT)

        self.grab_set()
        self.selected_member = None

    def on_ok(self):
        self.selected_member = self.member_combo.get()
        self.destroy()

    def on_cancel(self):
        self.selected_member = None
        self.destroy()
