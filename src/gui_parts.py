import sys
import os
import re
import pickle
import tkinter as tk
from tkinter import ttk

import pandas as pd

from python_senpai import keypoints_proc
from python_senpai import file_inout


class PklSelector(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # 一時ファイルからtrkのパスを取得
        tmp = TempFile()
        data = tmp.load()
        self.trk_path = data['trk_path']

        self.prev_pkl_btn = ttk.Button(master, text="<", width=1, state=tk.DISABLED)
        self.prev_pkl_btn.pack(side=tk.LEFT)
        self.next_pkl_btn = ttk.Button(master, text=">", width=1, state=tk.DISABLED)
        self.next_pkl_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.load_pkl_btn = ttk.Button(master, text="Load Track")
        self.load_pkl_btn.pack(side=tk.LEFT)
        self.pkl_path_label = ttk.Label(master, text="No Track file loaded")
        self.pkl_path_label.pack(side=tk.LEFT)

        if self.trk_path != '':
            self.pkl_path_label["text"] = self.trk_path

    def _select_trk(self):
        self.trk_path = file_inout.open_pkl(self.trk_path)
        self._load_pkl()

    def _load_pkl(self):
        if self.trk_path:
            self.pkl_path_label["text"] = self.trk_path
            tmp = TempFile()
            data = tmp.load()
            data['trk_path'] = self.trk_path
            tmp.save(data)
        else:
            self.trk_path = ''
            self.pkl_path_label["text"] = "No Track file loaded"

    def set_prev_next(self, attr_dict):
        dir_path = os.path.dirname(self.trk_path)
        if 'prev' in attr_dict and attr_dict['prev'] != '' and attr_dict['prev'] is not None:
            self.prev_pkl_btn["state"] = tk.NORMAL
            self.prev_path = os.path.join(dir_path, attr_dict['prev'])
        else:
            self.prev_path = ''
            self.prev_pkl_btn["state"] = tk.DISABLED
        if 'next' in attr_dict and attr_dict['next'] != '' and attr_dict['next'] is not None:
            self.next_path = os.path.join(dir_path, attr_dict['next'])
            self.next_pkl_btn["state"] = tk.NORMAL
        else:
            self.next_path = ''
            self.next_pkl_btn["state"] = tk.DISABLED

    def _load_prev_pkl(self):
        self.trk_path = self.prev_path
        self._load_pkl()

    def _load_next_pkl(self):
        self.trk_path = self.next_path
        self._load_pkl()

    def get_trk_path(self):
        if os.path.exists(self.trk_path) is False:
            print(f"\"{self.trk_path}\" is not found.")
        return self.trk_path

    def set_command(self, cmd):
        self.load_pkl_btn["command"] = lambda: [self._select_trk(), cmd()]
        self.prev_pkl_btn["command"] = lambda: [self._load_prev_pkl(), cmd()]
        self.next_pkl_btn["command"] = lambda: [self._load_next_pkl(), cmd()]


class MemberKeypointComboboxes(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        combos_frame = ttk.Frame(master)
        combos_frame.pack(side=tk.LEFT)
        self.member_combo = ttk.Combobox(combos_frame, state='readonly', width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_selected)
        self.keypoint_combo = ttk.Combobox(combos_frame, state='readonly', width=10)
        self.keypoint_combo.pack(side=tk.LEFT, padx=5)

    def set_df(self, src_df):
        self.src_df = src_df
        combo_df = self.src_df

        if keypoints_proc.has_keypoint(self.src_df) is True:
            # memberとkeypointのインデックス値を文字列に変換
            idx = combo_df.index
            combo_df.index = self.src_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(str)])
            self.keypoint_combo.state(['readonly'])
        else:
            self.keypoint_combo.state(['disabled'])

        self.member_combo["values"] = combo_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)
        if keypoints_proc.has_keypoint(self.src_df) is True:
            init_member = self.member_combo.get()
            self.keypoint_combo["values"] = combo_df.loc[pd.IndexSlice[:, init_member, :], :].index.get_level_values("keypoint").unique().tolist()
            self.keypoint_combo.current(0)

    def _on_selected(self, event):
        if keypoints_proc.has_keypoint(self.src_df) is False:
            return
        current_member = self.member_combo.get()
        # keypointの一覧を取得してコンボボックスにセット
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
        self.keypoint_combo["values"] = keypoints
        self.keypoint_combo.current(0)

    def get_selected(self):
        member = self.member_combo.get()
        keypoint = self.keypoint_combo.get()
        return member, keypoint


class MemberKeypointComboboxesForCross(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.member_combo = ttk.Combobox(master, state='readonly', width=12)
        self.member_combo.pack(side=tk.LEFT, padx=5)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_selected)

        kp_frame = ttk.Frame(master)
        kp_frame.pack(side=tk.LEFT)
        b_frame = ttk.Frame(kp_frame)
        b_frame.pack(side=tk.TOP, pady=5)
        b_label = ttk.Label(b_frame, text="B:")
        b_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_b = ttk.Combobox(b_frame, state='readonly', width=10)
        self.keypoint_combo_b.pack()
        a_frame = ttk.Frame(kp_frame)
        a_frame.pack(side=tk.TOP, pady=5)
        a_label = ttk.Label(a_frame, text="A:")
        a_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_a = ttk.Combobox(a_frame, state='readonly', width=10)
        self.keypoint_combo_a.pack()
        c_frame = ttk.Frame(kp_frame)
        c_frame.pack(side=tk.TOP, pady=5)
        c_label = ttk.Label(c_frame, text="C:")
        c_label.pack(side=tk.LEFT, padx=(5, 0))
        self.keypoint_combo_c = ttk.Combobox(c_frame, state='readonly', width=10)
        self.keypoint_combo_c.pack()

    def set_df(self, src_df):
        self.src_df = src_df
        combo_df = self.src_df
        idx = combo_df.index

        self.member_combo["values"] = combo_df.index.get_level_values("member").unique().tolist()
        self.member_combo.current(0)
        init_member = self.member_combo.get()
        idx = pd.IndexSlice[:, init_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().tolist()
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


class ProcOptions(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # 一時ファイルからdt_spanとthinningを取得
        tmp = TempFile()
        data = tmp.load()

        dt_span_label = ttk.Label(master, text="diff period:")
        dt_span_label.pack(side=tk.LEFT)
        self.dt_span_entry = ttk.Entry(master, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.dt_span_entry.insert(tk.END, data['dt_span'])
        self.dt_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        thinning_label = ttk.Label(master, text="thinning:")
        thinning_label.pack(side=tk.LEFT)
        self.thinning_entry = ttk.Entry(master, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.thinning_entry.insert(tk.END, data['thinning'])
        self.thinning_entry.pack(side=tk.LEFT, padx=(0, 5))

    def get_dt_span(self):
        tmp = TempFile()
        data = tmp.load()
        dt_span = self.dt_span_entry.get()
        data['dt_span'] = dt_span
        tmp.save(data)
        return dt_span

    def get_thinning(self):
        tmp = TempFile()
        data = tmp.load()
        thinning = self.thinning_entry.get()
        data['thinning'] = thinning
        tmp.save(data)
        return thinning

    def _validate(self, text):
        return (text.isdigit() or text == "")


class ThinningOption(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # 一時ファイルからdt_spanとthinningを取得
        tmp = TempFile()
        data = tmp.load()

        thinning_label = ttk.Label(master, text="thinning:")
        thinning_label.pack(side=tk.LEFT)
        self.thinning_entry = ttk.Entry(master, width=5, validate="key", validatecommand=(self.register(self._validate), "%P"))
        self.thinning_entry.insert(tk.END, data['thinning'])
        self.thinning_entry.pack(side=tk.LEFT, padx=(0, 5))

    def get_thinning(self):
        tmp = TempFile()
        data = tmp.load()
        thinning = self.thinning_entry.get()
        data['thinning'] = thinning
        tmp.save(data)
        return thinning

    def _validate(self, text):
        return (text.isdigit() or text == "")


class TimeSpanEntry(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        caption_time = tk.Label(master, text='time:')
        caption_time.pack(side=tk.LEFT, padx=(10, 0))
        vcmd = (self.register(self._validate), '%P')
        invcmd = (self.register(self._invalid_start), '%P')
        self.time_start_entry = ttk.Entry(master, validate='focusout', validatecommand=vcmd, invalidcommand=invcmd, width=10)
        self.time_start_entry.pack(side=tk.LEFT, padx=0)
        self.time_start_entry.bind("<FocusIn>", self._select_all)
        nyoro_time = tk.Label(master, text='～')
        nyoro_time.pack(side=tk.LEFT, padx=1)
        invcmd = (self.register(self._invalid_end), '%P')
        self.time_end_entry = ttk.Entry(master, validate='focusout', validatecommand=vcmd, invalidcommand=invcmd, width=10)
        self.time_end_entry.pack(side=tk.LEFT, padx=0)
        self.time_end_entry.bind("<FocusIn>", self._select_all)

    def get_start_end(self):
        start_val = self.time_start_entry.get()
        end_val = self.time_end_entry.get()
        return start_val, end_val

    def update_entry(self, start, end):
        self.time_start_entry.delete(0, tk.END)
        self.time_start_entry.insert(tk.END, start)
        self.time_end_entry.delete(0, tk.END)
        self.time_end_entry.insert(tk.END, end)

    def _select_all(self, event):
        event.widget.select_range(0, tk.END)

    def _validate(self, text):
        p = r'\d+:(([0-5][0-9])|([0-9])):(([0-5][0-9])|([0-9])).[0-9]{3}$'
        m = re.match(p, text)
        return m is not None

    def _invalid_start(self, text):
        self.time_start_entry.delete(0, tk.END)

    def _invalid_end(self, text):
        self.time_end_entry.delete(0, tk.END)


class TempFile:
    def __init__(self):
        self.data = {'trk_path': '', 'dt_span': 10, 'thinning': 0}

        file_name = 'temp.pkl'
        self.file_path = os.path.join(self._find_data_dir(), file_name)
        self.load()

    def save(self, data):
        self.data = data
        with open(self.file_path, 'wb') as f:
            pickle.dump(self.data, f)

    def load(self):
        res = self.data
        if os.path.exists(self.file_path) is True:
            with open(self.file_path, 'rb') as f:
                self.data = pickle.load(f)
                res = self.data
        return res

    def get_window_size(self):
        if 'width' not in self.data.keys() or self.data['width'] == '':
            width = 900
        else:
            width = int(self.data['width'])
        if 'height' not in self.data.keys() or self.data['height'] == '':
            height = 700
        else:
            height = int(self.data['height'])
        if 'dpi' not in self.data.keys() or self.data['dpi'] == '':
            dpi = 72
        else:
            dpi = int(self.data['dpi'])
        return width, height, dpi

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir
