import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import PklSelector, TimeSpanEntry
from python_senpai import time_format


class App(ttk.Frame):
    """
    Trackファイルに保存するDataFrameのattrs['scene_table']を編集するためのGUIです。
    H:MM:SS.fffの形式でstartとendを入力してaddボタンを押すと、tree_viewに追加されます。
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Scene Table")
        self.pack(padx=10, pady=10)

        load_frame = ttk.Frame(self)
        load_frame.pack(pady=5, anchor=tk.W)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))
 
        entry_frame = ttk.Frame(self)
        entry_frame.pack(pady=5)
        add_btn = ttk.Button(entry_frame, text="add", command=self._add_row)
        add_btn.pack(side=tk.LEFT, padx=(10, 0))

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("start", "end", "duration")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")

        self.tree.pack()

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=5)
        delete_btn = ttk.Button(control_frame, text="Delete Selected", command=self._delete_selected)
        delete_btn.pack(side=tk.LEFT)
        update_btn = ttk.Button(control_frame, text="Write to Track", command=self._update)
        update_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.load_pkl()

    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = pd.read_pickle(pkl_path)
        
        if 'scene_table' not in self.src_df.attrs.keys():
            return
        
        scene_table = self.src_df.attrs['scene_table']
        # self.treeをクリアしてattrs['scene_table']の値を入れる
        for item in self.tree.get_children(''):
            self.tree.delete(item)
        for start, end in zip(scene_table['start'], scene_table['end']):
            duration = pd.to_timedelta(end) - pd.to_timedelta(start)
            duration_str = time_format.timedelta_to_str(duration)
            self.tree.insert("", "end", values=(start, end, duration_str))

    def _add_row(self):
        start_time, end_time = self.time_span_entry.get_start_end()

        start_td = pd.to_timedelta(start_time)
        end_td = pd.to_timedelta(end_time)
        # durationの計算、startとendが逆だったら入れ替える
        if end_td <= start_td:
            start_td, end_td = end_td, start_td
        duration = end_td - start_td

        duration_str = time_format.timedelta_to_str(duration)
        start_str = time_format.timedelta_to_str(start_td)
        end_str = time_format.timedelta_to_str(end_td)

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

    def _update(self):
        scene_table = {'start': [], 'end': []}
        for item in self.tree.get_children(''):
            scene_table['start'].append(self.tree.item(item)['values'][0])
            scene_table['end'].append(self.tree.item(item)['values'][1])

        self.src_df.attrs['scene_table'] = scene_table
        self.src_df.to_pickle(self.pkl_selector.get_trk_path())


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
