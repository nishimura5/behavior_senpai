import tkinter as tk
from tkinter import ttk

import pandas as pd

from gui_parts import PklSelector
import time_format


class App(ttk.Frame):
    """
    Trackファイルに保存するDataFrameのmemberインデックスを編集するためのGUIです。
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Member Table")
        self.pack(padx=10, pady=10)

        load_frame = ttk.Frame(self)
        load_frame.pack(pady=5)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load_pkl)

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)
        rename_member_label = ttk.Label(setting_frame, text="Rename Member")
        rename_member_label.pack(side=tk.LEFT, pady=5)
        self.member_combo = ttk.Combobox(setting_frame, state='readonly', width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        to_label = ttk.Label(setting_frame, text="to")
        to_label.pack(side=tk.LEFT, padx=5)
        self.new_member_name_entry = ttk.Entry(setting_frame, width=12)
        self.new_member_name_entry.pack(side=tk.LEFT, padx=5)
        rename_btn = ttk.Button(setting_frame, text="Rename", command=self.rename_member)
        rename_btn.pack(side=tk.LEFT, padx=5)
        overwrite_btn = ttk.Button(setting_frame, text="Write to Track", command=self.overwrite)
        overwrite_btn.pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self)
        tree_frame.pack(pady=5)
        cols = ("member", "start", "end", "duration", "keypoints/frame")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("member", text="member")
        self.tree.heading("start", text="start")
        self.tree.heading("end", text="end")
        self.tree.heading("duration", text="duration")
        self.tree.heading("keypoints/frame", text="keypoints/frame")
        self.tree.column("start", width=100)
        self.tree.column("end", width=100)
        self.tree.column("duration", width=100)
        self.tree.pack()

        self.load_pkl()

    def load_pkl(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = pd.read_pickle(pkl_path)

        # memberとkeypointのインデックス値を文字列に変換
        idx = self.src_df.index
        self.src_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])

        self.update_tree() 
        self.member_combo["values"] = self.src_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        members = self.src_df.index.get_level_values(1).unique() 
        for member in members:
            sliced_df = self.src_df.loc[pd.IndexSlice[:, member, :], :]
            sliced_df = sliced_df.loc[(sliced_df['x'] != 0) & (sliced_df['y'] != 0)]
            kpf = len(sliced_df)/len(sliced_df.index.get_level_values(0).unique())
            head_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.head(1)['timestamp'].values[0])
            tail_timestamp = time_format.msec_to_timestr_with_fff(sliced_df.tail(1)['timestamp'].values[0])
            duration = sliced_df.tail(1)['timestamp'].values[0] - sliced_df.head(1)['timestamp'].values[0]
            duration_str = time_format.msec_to_timestr_with_fff(duration)
            self.tree.insert("", "end", values=(member, head_timestamp, tail_timestamp, duration_str, f"{kpf:.2f}"))
 
    def rename_member(self):
        old_member = self.member_combo.get()
        new_member = self.new_member_name_entry.get()
        print(f"rename {old_member} to {new_member}")
        if new_member == '':
            return
        self.src_df = self.src_df.rename(index={old_member: new_member}, level=1)
        self.update_tree()

    def overwrite(self):
        pkl_path = self.pkl_selector.get_trk_path()
        self.src_df.to_pickle(pkl_path)


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
