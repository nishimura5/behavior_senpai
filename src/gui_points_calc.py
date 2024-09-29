import os
import sys
import tkinter as tk
from tkinter import ttk

from gui_parts import Combobox
from vector_gui_parts import MemberKeypointComboboxesFor3Point

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

    def add_member_rename_to_menu(self, column):
        self.member_column = column
        self.add_menu("Rename member", self._rename_member)

    def add_row_copy(self, column):
        self.member_column = column
        self.add_menu("Copy", self._copy_row)

    def set_members(self, members):
        self.member_list = members

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

    def _rename_member(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        dialog = MemberComboDialog(self, self.member_list)
        self.wait_window(dialog.dialog)
        selected_member = dialog.selected_member
        if selected_member is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            values[self.member_column] = selected_member
            self.tree.item(item, values=values)

    def set_df(self, df):
        self.tar_df = df

    def add_calc(self):
        dialog = PointsCalcTreeDialog(self, self.member_list, contain_blank=False)
        dialog.set_df(self.tar_df)
        self.wait_window(dialog.dialog)
        new_calc_code = dialog.selected_calc_code
        new_member = dialog.selected_member
        new_point_a = dialog.selected_point_a
        new_point_b = dialog.selected_point_b
        new_point_c = dialog.selected_point_c

        if new_member is None:
            return
        if new_calc_code in dialog.point2_list:
            new_point_c = ""
        values = [new_calc_code, new_member, new_point_a, new_point_b, new_point_c]
        self.tree.insert("", tk.END, values=values)

    def edit_calc(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        dialog = PointsCalcTreeDialog(self, self.member_list, contain_blank=True)
        dialog.set_df(self.tar_df)
        self.wait_window(dialog.dialog)
        new_calc_code = dialog.selected_calc_code
        new_member = dialog.selected_member
        new_point_a = dialog.selected_point_a
        new_point_b = dialog.selected_point_b
        new_point_c = dialog.selected_point_c

        if new_member is None:
            return
        if new_calc_code in dialog.point2_list:
            new_point_c = ""
        values = [new_calc_code, new_member, new_point_a, new_point_b, new_point_c]
        for item in selected:
            values = self.tree.item(item)["values"]
            if new_member != "":
                values[1] = new_member
            if new_calc_code != "":
                values[0] = new_calc_code
            if new_point_a != "":
                values[2] = new_point_a
            if new_point_b != "":
                values[3] = new_point_b
            if new_point_c != "":
                values[4] = new_point_c
            self.tree.item(item, values=values)

    def get_name_and_code(self, key):
        name_and_code = {
            "distance (|AB|)": "norm",
            "sin,cos (∠BAC)": "sin_cos",
            "direction (∠BAx)": "direction",
            "xy_component (AB_x, AB_y)": "component",
            "cross_product (AB×AC)": "cross",
            "dot_product (AB・AC)": "dot",
            "plus (AB+AC)": "plus",
            "norms (|AB||AC|)": "norms",
        }
        return name_and_code[key]

    def _copy_row(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        dialog = MemberComboDialog(self, self.member_list)
        self.wait_window(dialog.dialog)
        selected_member = dialog.selected_member
        if selected_member is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            values[self.member_column] = selected_member
            self.tree.insert("", tk.END, values=values)


class PointsCalcTreeDialog(ttk.Frame):
    def __init__(self, master, member_list, contain_blank=False):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Points calculation")
        dialog.geometry("700x180")
        dialog.resizable(0, 0)

        tar_frame = ttk.Frame(dialog)
        tar_frame.pack(side=tk.TOP, pady=(5, 10))
        calc_select_frame = ttk.Frame(tar_frame)
        calc_select_frame.pack(side=tk.LEFT, padx=5)
        self.point_num_combo = Combobox(calc_select_frame, label="Point num:", width=25, values=["2", "3"])
        self.point_num_combo.pack_vertical(pady=5)
        self.point_num_combo.set_selected_bind(lambda event: self.change_point_num(event))
        self.name_and_code = {
            "distance (|AB|)": "norm",
            "sin,cos (∠BAC)": "sin_cos",
            "direction (∠BAx)": "direction",
            "xy_component (AB_x, AB_y)": "component",
            "cross_product (AB×AC)": "cross",
            "dot_product (AB・AC)": "dot",
            "plus (AB+AC)": "plus",
            "norms (|AB||AC|)": "norms",
        }
        self.point2_list = [
            "distance (|AB|)",
            "direction (∠BAx)",
            "xy_component (AB_x, AB_y)",
        ]
        self.point3_list = [
            "sin,cos (∠BAC)",
            "cross_product (AB×AC)",
            "dot_product (AB・AC)",
            "plus (AB+AC)",
            "norms (|AB||AC|)",
        ]
        if contain_blank:
            self.point2_list.insert(0, "")
            self.point3_list.insert(0, "")
        self.calc_type_combo = Combobox(calc_select_frame, label="Calc:", width=25, values=self.point2_list)
        self.calc_type_combo.pack_vertical(pady=5)
        data_dir = self._find_data_dir()
        img_3_path = os.path.join(data_dir, "img", "vector3.png")
        self.img_3 = tk.PhotoImage(file=img_3_path)
        img_2_path = os.path.join(data_dir, "img", "vector2.png")
        self.img_2 = tk.PhotoImage(file=img_2_path)
        self.img_label = ttk.Label(tar_frame, image=self.img_2)
        self.img_label.pack(side=tk.LEFT, padx=5)
        self.member_combo = MemberKeypointComboboxesFor3Point(tar_frame)
        self.member_combo.pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.TOP, pady=(10, 5))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_btn.pack(side=tk.LEFT)

        dialog.grab_set()
        self.dialog = dialog
        self.selected_calc_code = None
        self.selected_member = None
        self.selected_point_a = None
        self.selected_point_b = None
        self.selected_point_c = None

    def set_df(self, df):
        self.member_combo.set_df(df)

    def on_ok(self):
        self.selected_calc_code = self.calc_type_combo.get()
        (
            self.selected_member,
            self.selected_point_a,
            self.selected_point_b,
            self.selected_point_c,
        ) = self.member_combo.get_selected()
        self.dialog.destroy()

    def on_cancel(self):
        self.selected_member = None
        self.dialog.destroy()

    def change_point_num(self, event):
        point_num = self.point_num_combo.get()
        if point_num == "2":
            self.calc_type_combo.set_values(self.point2_list)
            self.img_label["image"] = self.img_2
        elif point_num == "3":
            self.calc_type_combo.set_values(self.point3_list)
            self.img_label["image"] = self.img_3

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir


class MemberComboDialog(ttk.Frame):
    def __init__(self, master, member_list):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Select member")
        dialog.geometry("300x100")
        dialog.resizable(0, 0)

        combo_frame = ttk.Frame(dialog)
        combo_frame.pack(side=tk.TOP, pady=(5, 10))
        label = ttk.Label(combo_frame, text="Member:")
        label.pack(side=tk.LEFT, padx=5)
        self.member_combo = ttk.Combobox(combo_frame, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo["values"] = member_list
        self.member_combo.current(0)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.TOP, pady=(10, 5))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.LEFT)

        dialog.grab_set()
        self.dialog = dialog
        self.selected_member = None

    def on_ok(self):
        self.selected_member = self.member_combo.get()
        self.dialog.destroy()

    def cancel(self):
        self.selected_member = None
        self.dialog.destroy()
