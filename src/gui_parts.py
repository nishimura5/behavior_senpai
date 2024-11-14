import os
import pickle
import re
import sys
import tkinter as tk
from tkinter import ttk

import pandas as pd

from behavior_senpai import keypoints_proc, time_format


class MemberKeypointComboboxes(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        combos_frame = ttk.Frame(master)
        combos_frame.pack(side=tk.LEFT)
        member_label = ttk.Label(combos_frame, text="Member:")
        member_label.pack(side=tk.LEFT, padx=(0, 3))
        self.member_combo = ttk.Combobox(combos_frame, state="readonly", width=12)
        self.member_combo.pack(side=tk.LEFT)
        self.member_combo.bind("<<ComboboxSelected>>", self._on_selected)
        keypoint_label = ttk.Label(combos_frame, text="Keypoint:")
        keypoint_label.pack(side=tk.LEFT, padx=(12, 3))
        self.keypoint_combo = ttk.Combobox(combos_frame, state="disabled", width=10)
        self.keypoint_combo.pack(side=tk.LEFT)

    def set_df(self, src_df):
        self.src_df = src_df
        combo_df = self.src_df
        if keypoints_proc.has_keypoint(self.src_df) is True:
            self.keypoint_combo["state"] = "readonly"
        else:
            self.keypoint_combo["state"] = "disabled"

        self.member_combo["values"] = combo_df.index.get_level_values("member").unique().astype(str).tolist()
        self.member_combo.current(0)
        self._on_selected()

    def _on_selected(self, event=None):
        if keypoints_proc.has_keypoint(self.src_df) is False:
            return
        current_member = self.member_combo.get()
        idx = pd.IndexSlice[:, current_member, :]
        keypoints = self.src_df.loc[idx, :].index.get_level_values("keypoint").unique().astype(str).tolist()
        self.keypoint_combo["values"] = keypoints
        self.keypoint_combo.current(0)

    def set(self, member, keypoint=None):
        self.member_combo.set(member)
        if keypoint is not None:
            self.keypoint_combo.set(keypoint)

    def get_selected(self):
        member = self.member_combo.get()
        keypoint = self.keypoint_combo.get()
        return member, keypoint


class StrEntry(ttk.Frame):
    def __init__(self, master, label: str, default="", width=10, allow_blank=False):
        super().__init__(master)
        self.default = default
        self.invalid_characters = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        self.frame = ttk.Frame(master)
        caption = ttk.Label(self.frame, text=label)
        caption.pack(side=tk.LEFT, padx=(0, 1))
        self.allow_blank = allow_blank
        self.entry = ttk.Entry(
            self.frame,
            width=width,
            validate="key",
            validatecommand=(self.register(self._validate), "%P"),
        )
        if self.allow_blank is False:
            self.entry.bind("<FocusOut>", self._set_default)
        self.entry.insert(tk.END, self.default)
        self.entry.pack(side=tk.LEFT)

    def pack_horizontal(self, anchor=tk.W, padx=0, pady=0):
        self.frame.pack(side=tk.LEFT, anchor=anchor, padx=padx, pady=pady)

    def pack_vertical(self, anchor=tk.E, padx=0, pady=0):
        self.frame.pack(side=tk.TOP, anchor=anchor, padx=padx, pady=pady)

    def get(self):
        return self.entry.get()

    def save_to_temp(self, key):
        tmp = TempFile()
        data = tmp.load()
        data[key] = self.entry.get()
        tmp.save(data)
        return data[key]

    def update(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(tk.END, text)

    def _validate(self, text):
        if self.allow_blank is True and text == "":
            return True
        else:
            return all(c not in text for c in self.invalid_characters) or text == ""

    def _set_default(self, event):
        if self.entry.get() == "":
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, self.default)


class CalcCaseEntry(ttk.Frame):
    def __init__(self, master, default=""):
        super().__init__(master)
        self.invalid_characters = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        caption = ttk.Label(master, text="Calc case:")
        caption.pack(side=tk.LEFT)
        desc = """Calc case will be used as the folder name under the 'calc' folder to save the .feat.pkl file.
If the specified folder doesn’t exist, a new one will be created when you press the Export button."""
        ToolTip(caption, desc)
        self.calc_case_entry = ttk.Entry(
            master,
            width=20,
            validate="key",
            validatecommand=(self.register(self._validate), "%P"),
        )
        self.calc_case_entry.insert(tk.END, default)
        self.calc_case_entry.pack(side=tk.LEFT, padx=(0, 5))

    def get_calc_case(self):
        tmp = TempFile()
        data = tmp.load()
        calc_case = self.calc_case_entry.get()
        data["calc_case"] = calc_case
        tmp.save(data)
        return calc_case

    def _validate(self, text):
        return all(c not in text for c in self.invalid_characters) or text == ""


class TimeSpanEntry(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.side = tk.LEFT
        desc = """Specify the time range.\nThe time format is 'h:mm:ss.fff'."""
        caption_time = ttk.Label(master, text="Time:")
        caption_time.pack(side=tk.LEFT, padx=(5, 1))
        ToolTip(caption_time, desc)
        vcmd = (self.register(self._validate), "%P")
        invcmd = (self.register(self._invalid_start), "%P")
        self.time_start_entry = ttk.Entry(
            master,
            validate="focusout",
            validatecommand=vcmd,
            invalidcommand=invcmd,
            width=10,
        )
        self.time_start_entry.pack(side=tk.LEFT)
        self.time_start_entry.bind("<FocusIn>", self._select_all)
        nyoro_time = ttk.Label(master, text="～")
        nyoro_time.pack(side=tk.LEFT, padx=1)
        invcmd = (self.register(self._invalid_end), "%P")
        self.time_end_entry = ttk.Entry(
            master,
            validate="focusout",
            validatecommand=vcmd,
            invalidcommand=invcmd,
            width=10,
        )
        self.time_end_entry.pack(side=tk.LEFT)
        self.time_end_entry.bind("<FocusIn>", self._select_all)
        self.reset_btn = ttk.Button(master, text="Reset", state="disable", command=self.reset, width=6)
        self.reset_btn.pack(side=tk.LEFT, padx=(5, 10))

    def get_start_end(self):
        start_str = self.time_start_entry.get()
        end_str = self.time_end_entry.get()
        start = time_format.timestr_to_msec(start_str)
        end = time_format.timestr_to_msec(end_str)
        return start, end

    def get_start_end_str(self):
        start_str = self.time_start_entry.get()
        end_str = self.time_end_entry.get()
        return start_str, end_str

    def update_entry(self, start_msec, end_msec):
        start = time_format.msec_to_timestr_with_fff(start_msec)
        end = time_format.msec_to_timestr_with_fff(end_msec)
        self.time_start_entry.delete(0, tk.END)
        self.time_start_entry.insert(tk.END, start)
        self.time_end_entry.delete(0, tk.END)
        self.time_end_entry.insert(tk.END, end)
        self.default_start = start
        self.default_end = end
        self.reset_btn["state"] = "normal"

    def reset(self):
        self.time_start_entry.delete(0, tk.END)
        self.time_start_entry.insert(tk.END, self.default_start)
        self.time_end_entry.delete(0, tk.END)
        self.time_end_entry.insert(tk.END, self.default_end)

    def _select_all(self, event):
        event.widget.select_range(0, tk.END)

    def _validate(self, text):
        p = r"\d+:(([0-5][0-9])|([0-9])):(([0-5][0-9])|([0-9])).[0-9]{3}$"
        m = re.match(p, text)
        return m is not None

    def _invalid_start(self, text):
        self.time_start_entry.delete(0, tk.END)

    def _invalid_end(self, text):
        self.time_end_entry.delete(0, tk.END)


class IntEntry(ttk.Frame):
    def __init__(self, master, label: str, default: str, width=5, description=None):
        super().__init__(master)
        self.default = default
        self.frame = ttk.Frame(master)
        caption = ttk.Label(self.frame, text=label)
        caption.pack(side=tk.LEFT, padx=(0, 1))
        if description is None:
            description = "Only integers are allowed."
        ToolTip(caption, description)

        self.entry = ttk.Entry(
            self.frame,
            width=width,
            validate="key",
            validatecommand=(self.register(self._validate), "%P"),
        )
        self.entry.bind("<FocusOut>", self._set_default)
        self.entry.insert(tk.END, self.default)
        self.entry.pack(side=tk.LEFT)

    def pack_horizontal(self, anchor=tk.E, padx=0, pady=0):
        self.frame.pack(side=tk.LEFT, anchor=anchor, padx=padx, pady=pady)

    def pack_vertical(self, anchor=tk.E, padx=0, pady=0):
        self.frame.pack(side=tk.TOP, anchor=anchor, padx=padx, pady=pady)

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(tk.END, value)

    def get(self):
        return int(self.entry.get())

    def save_to_temp(self, key):
        tmp = TempFile()
        data = tmp.load()
        data[key] = self.entry.get()
        tmp.save(data)
        return data[key]

    def set_state(self, state):
        self.entry["state"] = state

    def _validate(self, text):
        return text.isdigit() or text == ""

    def _set_default(self, event):
        if self.entry.get() == "":
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, self.default)


class Combobox(ttk.Frame):
    def __init__(self, master, label: str, values: list, width=5, current=0):
        super().__init__(master)
        self.frame = ttk.Frame(master)
        caption = ttk.Label(self.frame, text=label)
        caption.pack(side=tk.LEFT, padx=(0, 1))
        self.combobox = ttk.Combobox(self.frame, state="readonly", width=width)
        self.combobox["values"] = values
        self.combobox.current(current)
        self.combobox.pack(side=tk.LEFT)
        self.current_value = None

    def pack_horizontal(self, anchor=tk.E, padx=0, pady=0):
        self.frame.pack(side=tk.LEFT, anchor=anchor, padx=padx, pady=pady)

    def pack_vertical(self, anchor=tk.E, padx=0, pady=0):
        self.frame.pack(side=tk.TOP, anchor=anchor, padx=padx, pady=pady)

    def set_selected_bind(self, func):
        self.combobox.bind("<<ComboboxSelected>>", func)

    def get(self):
        """Get selected value of the combo box"""
        self.current_value = self.combobox.get()
        return self.combobox.get()

    def get_current_value(self):
        """Get the selected value when get() was called"""
        return self.current_value

    def get_values(self):
        return self.combobox["values"]

    def set(self, value=None):
        """Set value to the combo box"""
        if value is None:
            self.combobox.current(0)
        else:
            self.combobox.set(value)

    def set_df(self, src_df):
        self.combobox["values"] = src_df.index.get_level_values("member").unique().tolist()
        self.combobox.current(0)

    def set_values(self, values):
        self.combobox["values"] = values
        self.combobox.current(0)

    def set_state(self, state):
        self.combobox["state"] = state

    def save_to_temp(self, key):
        tmp = TempFile()
        data = tmp.load()
        thinning = self.combobox.get()
        data[key] = thinning
        tmp.save(data)
        return thinning


class Checkbutton(ttk.Frame):
    def __init__(self, master, label: str, default=False, description=None):
        super().__init__(master)
        self.var = tk.BooleanVar()
        self.var.set(default)
        self.checkbutton = ttk.Checkbutton(self, text=label, variable=self.var)
        self.checkbutton.pack(side=tk.LEFT)
        if description is not None:
            ToolTip(self.checkbutton, description)

    def pack_horizontal(self, anchor=tk.E, padx=0, pady=0):
        self.pack(side=tk.LEFT, anchor=anchor, padx=padx, pady=pady)

    def pack_vertical(self, anchor=tk.E, padx=0, pady=0):
        self.pack(side=tk.TOP, anchor=anchor, padx=padx, pady=pady)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def set_state(self, state):
        self.checkbutton["state"] = state

    def set_trace(self, func):
        self.var.trace("w", func)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.delay_id = None

        self.widget.bind("<Enter>", self.schedule_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def schedule_tooltip(self, event):
        self.delay_id = self.widget.after(600, self.show_tooltip, event)

    def show_tooltip(self, event):
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(tw, text=self.text, justify="left", background="#ffffe0", relief="solid", borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
        if self.delay_id:
            self.widget.after_cancel(self.delay_id)
            self.delay_id = None


class TempFile:
    def __init__(self):
        self.data = {
            "trk_path": "",
            "calc_case": "",
            "dt_span": 10,
            "thinning": 0,
            "draw_mask": False,
        }

        file_name = "temp.pkl"
        self.file_path = os.path.join(self._find_data_dir(), file_name)
        self.load()

    def save(self, data):
        self.data = data
        with open(self.file_path, "wb") as f:
            pickle.dump(self.data, f)

    def load(self):
        res = self.data
        if os.path.exists(self.file_path) is True:
            with open(self.file_path, "rb") as f:
                new_data_dict = pickle.load(f)
                self.data.update(new_data_dict)
                res = self.data
        return res

    def get_top_window_size(self):
        if "top_width" not in self.data.keys() or self.data["top_width"] == "":
            width = 900
        else:
            width = int(self.data["top_width"])
        if "top_height" not in self.data.keys() or self.data["top_height"] == "":
            height = 550
        else:
            height = int(self.data["top_height"])
        return width, height

    def get_scene_table_graph_size(self):
        if "scene_table_width" not in self.data.keys() or self.data["scene_table_width"] == "":
            width = 1600
        else:
            width = int(self.data["scene_table_width"])
        if "scene_table_height" not in self.data.keys() or self.data["scene_table_height"] == "":
            height = 260
        else:
            height = int(self.data["scene_table_height"])
        if "scene_table_dpi" not in self.data.keys() or self.data["scene_table_dpi"] == "":
            dpi = 100
        else:
            dpi = int(self.data["scene_table_dpi"])
        return width, height, dpi

    def get_window_size(self):
        if "width" not in self.data.keys() or self.data["width"] == "":
            width = 1600
        else:
            width = int(self.data["width"])
        if "height" not in self.data.keys() or self.data["height"] == "":
            height = 800
        else:
            height = int(self.data["height"])
        if "dpi" not in self.data.keys() or self.data["dpi"] == "":
            dpi = 72
        else:
            dpi = int(self.data["dpi"])
        return width, height, dpi

    def get_mp4_setting(self):
        if "mp4_scale" not in self.data.keys() or self.data["mp4_scale"] == "":
            mp4_scale = 0.5
        else:
            mp4_scale = float(self.data["mp4_scale"])
        return mp4_scale

    def get_draw_mask(self):
        return self.data["draw_mask"]

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir
