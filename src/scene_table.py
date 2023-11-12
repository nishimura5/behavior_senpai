import os
import tkinter as tk
from tkinter import ttk
import re

import pandas as pd

import time_format


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Scene table")
        self.pack(padx=10, pady=10)

        entry_frame = ttk.Frame(self)
        entry_frame.pack(pady=5)
        self.time_entry = TimeEntry(entry_frame)
        self.time_entry.pack()
        add_btn = ttk.Button(entry_frame, text="add", command=self._add_row)
        add_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.rows = {'start': [], 'end': [], 'duration': []}

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("start", "end", "duration")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")

        self.tree.pack()

        delete_btn = ttk.Button(tree_frame, text="Delete Selected", command=self._delete_selected)
        delete_btn.pack()

    def _add_row(self):
        start_time, end_time = self.time_entry.get_start_end()

        start_td = pd.to_timedelta(start_time)
        end_td = pd.to_timedelta(end_time)
        # durationの計算、startとendが逆だったら入れ替える
        if end_td <= start_td:
            start_td, end_td = end_td, start_td
        duration = end_td - start_td

        duration_str = time_format.timedelta_to_str(duration)
        start_str = time_format.timedelta_to_str(start_td)
        end_str = time_format.timedelta_to_str(end_td)\

        # 重複していたらaddしない
        tar_list = [k for k in self.tree.get_children('')]
        for tar in tar_list:
            if start_str == self.tree.item(tar)['values'][0] and end_str == self.tree.item(tar)['values'][1]:
                return
        self.tree.insert("", "end", values=(start_str, end_str, duration_str))

        # tree_viewをstartカラムでソート
        self._treeview_sort_column(self.tree, "start")
    
    def _treeview_sort_column(self, tv, col):
        tar_list = [(tv.set(k, col), k) for k in tv.get_children('')]
        tar_list.sort()
        for index, (val, k) in enumerate(tar_list):
            tv.move(k, '', index)

    def _delete_selected(self):
        selected = self.tree.selection()
        for item in selected:
            self.tree.delete(item)


class TimeEntry(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        vcmd = (self.register(self._validate), '%P')
        invcmd = (self.register(self._invalid_start), '%P')
        self.time_start_entry = ttk.Entry(master, validate='focusout', validatecommand=vcmd, invalidcommand=invcmd, width=10)
        self.time_start_entry.pack(side=tk.LEFT, padx=0)
        nyoro_time = tk.Label(master, text='～')
        nyoro_time.pack(side=tk.LEFT, padx=1)
        invcmd = (self.register(self._invalid_end), '%P')
        self.time_end_entry = ttk.Entry(master, validate='focusout', validatecommand=vcmd, invalidcommand=invcmd, width=10)
        self.time_end_entry.pack(side=tk.LEFT, padx=0)

    def get_start_end(self):
        start_val = self.time_start_entry.get()
        end_val = self.time_end_entry.get()
        return start_val, end_val

    def _validate(self, text):
        p = r'\d+:(([0-5][0-9])|([0-9])):(([0-5][0-9])|([0-9])).[0-9]{3}$'
        m = re.match(p, text)
        return m is not None

    def _invalid_start(self, text):
        self.time_start_entry.delete(0, tk.END)

    def _invalid_end(self, text):
        self.time_end_entry.delete(0, tk.END)


def quit(root):
    root.quit()
    root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
