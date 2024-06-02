import tkinter as tk
from tkinter import ttk

import pandas as pd


class MemberKeypointComboboxesFor3Point(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.member_combo = ttk.Combobox(master, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_selected)

        kp_frame = ttk.Frame(master)
        kp_frame.pack(side=tk.LEFT)
        b_frame = ttk.Frame(kp_frame)
        b_frame.pack(side=tk.TOP, pady=5)
        b_label = ttk.Label(b_frame, text="B:")
        b_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_b = ttk.Combobox(b_frame, state="readonly", width=10)
        self.keypoint_combo_b.pack()
        a_frame = ttk.Frame(kp_frame)
        a_frame.pack(side=tk.TOP, pady=5)
        a_label = ttk.Label(a_frame, text="A:")
        a_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_a = ttk.Combobox(a_frame, state="readonly", width=10)
        self.keypoint_combo_a.pack()
        c_frame = ttk.Frame(kp_frame)
        c_frame.pack(side=tk.TOP, pady=5)
        c_label = ttk.Label(c_frame, text="C:")
        c_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_c = ttk.Combobox(c_frame, state="readonly", width=10)
        self.keypoint_combo_c.pack()

    def set_df(self, src_df):
        combo_df = src_df.copy()

        self.member_combo["values"] = combo_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)
        init_member = self.member_combo.get()
        idx = combo_df.index
        combo_df.index = combo_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])
        idx_slice = pd.IndexSlice[:, init_member, :]
        keypoints = combo_df.loc[idx_slice, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo_a["values"] = keypoints
        self.keypoint_combo_a.current(0)
        self.keypoint_combo_b["values"] = keypoints
        self.keypoint_combo_b.current(0)
        self.keypoint_combo_c["values"] = keypoints
        self.keypoint_combo_c.current(0)

    def _on_selected(self, event):
        current_member = self.member_combo.get()
        # keypointの一覧を取得してコンボボックスにセット
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo_a["values"] = keypoints
        self.keypoint_combo_b["values"] = keypoints
        self.keypoint_combo_c["values"] = keypoints

    def get_selected(self):
        member = self.member_combo.get()
        keypoint_a = self.keypoint_combo_a.get()
        keypoint_b = self.keypoint_combo_b.get()
        keypoint_c = self.keypoint_combo_c.get()
        return member, keypoint_a, keypoint_b, keypoint_c


class MemberKeypointComboboxesFor2Point(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.member_combo = ttk.Combobox(master, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_selected)

        kp_frame = ttk.Frame(master)
        kp_frame.pack(side=tk.LEFT)
        a_frame = ttk.Frame(kp_frame)
        a_frame.pack(side=tk.TOP, pady=5)
        a_label = ttk.Label(a_frame, text="A:")
        a_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_a = ttk.Combobox(a_frame, state="readonly", width=10)
        self.keypoint_combo_a.pack()
        b_frame = ttk.Frame(kp_frame)
        b_frame.pack(side=tk.TOP, pady=5)
        b_label = ttk.Label(b_frame, text="B:")
        b_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_b = ttk.Combobox(b_frame, state="readonly", width=10)
        self.keypoint_combo_b.pack()

    def set_df(self, src_df):
        combo_df = src_df.copy()

        self.member_combo["values"] = combo_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)
        init_member = self.member_combo.get()
        idx = combo_df.index
        combo_df.index = combo_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])
        idx_slice = pd.IndexSlice[:, init_member, :]
        keypoints = combo_df.loc[idx_slice, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo_a["values"] = keypoints
        self.keypoint_combo_a.current(0)
        self.keypoint_combo_b["values"] = keypoints
        self.keypoint_combo_b.current(0)

    def _on_selected(self, event):
        current_member = self.member_combo.get()
        # keypointの一覧を取得してコンボボックスにセット
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo_a["values"] = keypoints
        self.keypoint_combo_b["values"] = keypoints

    def get_selected(self):
        member = self.member_combo.get()
        keypoint_a = self.keypoint_combo_a.get()
        keypoint_b = self.keypoint_combo_b.get()
        return member, keypoint_a, keypoint_b

    def set(self, member, point_a, point_b):
        self.member_combo.set(member)
        self.keypoint_combo_a.set(point_a)
        self.keypoint_combo_b.set(point_b)
