import tkinter as tk
from tkinter import ttk

from behavior_senpai import time_format
from gui_parts import StrEntry, TimeSpanEntry


class Tree(ttk.Frame):
    def __init__(self, master, columns: list, height: int, right_click=False):
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
        if right_click is True:
            self.tree.bind("<Button-3>", self._right_click_tree)
            self.menu = tk.Menu(self, tearoff=0)

    def add_member_rename_to_menu(self, column):
        self.member_column = column
        self.add_menu("Rename member", self._rename_member)

    def add_row_copy(self, column):
        self.member_column = column
        self.add_menu("Copy", self._copy_row)

    def add_rename(self, column):
        self.member_column = column
        self.add_menu("Rename", self.rename_item)

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

    def get_selected_one(self, selected=None, force_str=False):
        if selected is None:
            selected = self.tree.selection()
            if len(selected) == 0:
                return None
            selected = selected[0]
        if force_str is True:
            ret = [str(self.tree.item(selected)["values"][i]) for i in range(len(self.tree.item(selected)["values"]))]
        else:
            ret = self.tree.item(selected)["values"]
        return ret

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

    def rename_item(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        default = self.tree.item(selected[0])["values"][self.member_column]
        dialog = MemberEntryDialog(self, default=default)
        self.wait_window(dialog.dialog)
        new_name = dialog.new_name
        if new_name is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            values[self.member_column] = new_name
            self.tree.item(item, values=values)

    def scene_table_add(self):
        dialog = SceneTableTreeDialog(self, self.member_list)
        self.wait_window(dialog.dialog)
        new_member = dialog.selected_member
        new_timespan = dialog.new_timespan
        new_description = dialog.new_description

        if new_member is None:
            return
        duration = time_format.timestr_to_msec(new_timespan[1]) - time_format.timestr_to_msec(new_timespan[0])
        duration_str = time_format.msec_to_timestr_with_fff(duration)
        values = list(new_timespan) + [duration_str, new_member, new_description]
        self.tree.insert("", tk.END, values=values)

    def scene_table_edit(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        if len(selected) > 1:
            default_timespan = ["", ""]
        elif len(selected) == 1:
            default_timespan = self.tree.item(selected[0])["values"][:2]
        default_description = self.tree.item(selected[0])["values"][4]
        dialog = SceneTableTreeDialog(self, self.member_list, default_timespan, default_description)
        self.wait_window(dialog.dialog)
        new_member = dialog.selected_member
        new_timespan = dialog.new_timespan
        new_description = dialog.new_description

        if new_member is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            if new_timespan[0] != "":
                values[0] = new_timespan[0]
            if new_timespan[1] != "":
                values[1] = new_timespan[1]
            duration = time_format.timestr_to_msec(values[1]) - time_format.timestr_to_msec(values[0])
            values[2] = time_format.msec_to_timestr_with_fff(duration)
            if new_member != "":
                values[3] = new_member
            if new_description != "":
                values[4] = new_description
            self.tree.item(item, values=values)

    def scene_table_copy(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            self.tree.insert("", tk.END, values=values)

    def feat_mix_edit(self):
        selected = self.tree.selection()
        if len(selected) == 0:
            return
        default_feat_name = self.tree.item(selected[0])["values"][0]
        dialog = FeatMixTreeDialog(self, default_feat_name, self.member_list)
        self.wait_window(dialog.dialog)
        new_name = dialog.new_name
        new_member = dialog.selected_member
        print(f"{new_member},'{new_name}'is new value")

        if new_member is None:
            return
        for item in selected:
            values = self.tree.item(item)["values"]
            if new_member != "":
                values[1] = new_member
            if new_name != "":
                values[0] = new_name
            self.tree.item(item, values=values)

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


class SceneTableTreeDialog(ttk.Frame):
    def __init__(self, master, member_list, default_timespan=["", ""], default_description=""):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Scene")
        dialog.geometry("500x200")
        dialog.resizable(0, 0)

        time_frame = ttk.Frame(dialog)
        time_frame.pack(side=tk.TOP, pady=(5, 10))
        self.time_entry = TimeSpanEntry(time_frame)

        if default_timespan[0] != "" and default_timespan[1] != "":
            start_msec = time_format.timestr_to_msec(default_timespan[0])
            end_msec = time_format.timestr_to_msec(default_timespan[1])
            self.time_entry.update_entry(start_msec=start_msec, end_msec=end_msec)

        combo_frame = ttk.Frame(dialog)
        combo_frame.pack(side=tk.TOP, pady=(5, 10))
        label = ttk.Label(combo_frame, text="Member:")
        label.pack(side=tk.LEFT, padx=5)
        self.member_combo = ttk.Combobox(combo_frame, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo["values"] = member_list + [""]
        self.member_combo.current(0)

        self.member_entry = StrEntry(combo_frame, "Description:", default=default_description, width=14, allow_blank=True)
        self.member_entry.pack_horizontal(padx=5)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.TOP, pady=(10, 5))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.LEFT)

        self.dialog = dialog
        self.selected_member = None
        self.new_timespan = None
        self.new_description = None

    def on_ok(self):
        self.selected_member = self.member_combo.get()
        self.new_timespan = self.time_entry.get_start_end_str()
        self.new_description = self.member_entry.get()
        self.dialog.destroy()

    def cancel(self):
        self.selected_member = None
        self.new_timespan = None
        self.new_description = None
        self.dialog.destroy()


class FeatMixTreeDialog(ttk.Frame):
    def __init__(self, master, default_name, member_list):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title("Feature")
        dialog.geometry("300x160")
        dialog.resizable(0, 0)

        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(side=tk.TOP, pady=(5, 10))
        self.member_entry = StrEntry(entry_frame, "Name:", default=default_name, width=14, allow_blank=True)
        self.member_entry.pack_horizontal(padx=5)

        combo_frame = ttk.Frame(dialog)
        combo_frame.pack(side=tk.TOP, pady=(5, 10))

        label = ttk.Label(combo_frame, text="Member:")
        label.pack(side=tk.LEFT, padx=5)
        self.member_combo = ttk.Combobox(combo_frame, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo["values"] = member_list + [""]
        self.member_combo.current(0)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.TOP, pady=(10, 5))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.LEFT)

        dialog.grab_set()
        self.dialog = dialog
        self.new_name = None
        self.selected_member = None

    def on_ok(self):
        self.new_name = self.member_entry.get()
        self.selected_member = self.member_combo.get()
        self.dialog.destroy()

    def cancel(self):
        self.new_name = None
        self.selected_member = None
        self.dialog.destroy()


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


class MemberEntryDialog(ttk.Frame):
    def __init__(self, master, title="Rename", label="New Value", default=""):
        super().__init__(master)
        dialog = tk.Toplevel(master)
        dialog.focus_set()
        dialog.title(title)
        dialog.geometry("300x100")
        dialog.resizable(0, 0)

        entry_frame = ttk.Frame(dialog)
        entry_frame.pack(side=tk.TOP, pady=(5, 10))
        self.member_entry = StrEntry(entry_frame, label, default=default, width=14)
        self.member_entry.pack_horizontal(padx=5)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.TOP, pady=(10, 5))
        ok_btn = ttk.Button(button_frame, text="OK", command=self.on_ok)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack(side=tk.LEFT)

        dialog.grab_set()
        self.dialog = dialog
        self.new_name = None
        self.member_entry.entry.focus_set()

    def on_ok(self):
        self.new_name = self.member_entry.get()
        self.dialog.destroy()

    def cancel(self):
        self.new_name = None
        self.dialog.destroy()