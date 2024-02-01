import sys
import os
import tkinter as tk
from tkinter import ttk

import cv2
import ttkthemes

from gui_parts import TimeSpanEntry, TempFile
from main_gui_parts import PklSelector, VideoViewer
from python_senpai import keypoints_proc, file_inout, vcap
import export_mp4
import app_detect
import app_track_list
import app_member_edit
import app_area_filter
import app_smoothing
import app_scene_table
import app_trajplot as k2t
import app_recuplot as k2r
import app_calc_vector as k2v
import pref_list
import license_view


class App(ttk.Frame):
    """
    Launcherに並ぶボタンを押すとそのアプリケーションのGUIが起動します。
    各アプリケーションは独立しているため、このLauncherを経由しなくても起動できます。
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Behavior Senpai")
        self.pack(padx=14, pady=14)

        temp = TempFile()
        w_width, w_height = temp.get_top_window_size()
        w_height = int(w_height)

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(side=tk.LEFT, anchor=tk.NW)

        detect_label = ttk.Label(buttons_frame, text="Preparation")
        detect_label.pack(side=tk.TOP)
        v2k_button = ttk.Button(buttons_frame, text="Detect", command=lambda: self.launch_window(app_detect.App, grab=True), width=20)
        v2k_button.pack(side=tk.TOP, pady=4)
        tl_button = ttk.Button(buttons_frame, text="Track list", command=lambda: self.launch_window(app_track_list.App, grab=True), width=20)
        tl_button.pack(side=tk.TOP, pady=4)

        edit_label = ttk.Label(buttons_frame, text="Edit")
        edit_label.pack(side=tk.TOP, pady=(8, 0))
        member_edit_button = ttk.Button(
            buttons_frame,
            text="Member",
            command=lambda: self.launch_window(app_member_edit.App, edit_df=True, grab=True),
            width=20)
        member_edit_button.pack(side=tk.TOP, pady=4)
        area_filter_button = ttk.Button(
            buttons_frame,
            text="Area",
            command=lambda: self.launch_window(app_area_filter.App, edit_df=True, grab=True),
            width=20)
        area_filter_button.pack(side=tk.TOP, pady=4)
        smooth_button = ttk.Button(
            buttons_frame,
            text="Smooth",
            command=lambda: self.launch_window(app_smoothing.App, edit_df=True, grab=True),
            width=20)
        smooth_button.pack(side=tk.TOP, pady=4)
        scene_table_button = ttk.Button(
            buttons_frame,
            text="Scene table",
            command=lambda: self.launch_window(app_scene_table.App, edit_df=True, grab=True),
            width=20)
        scene_table_button.pack(side=tk.TOP, pady=4)

        vis_label = ttk.Label(buttons_frame, text="Visualization")
        vis_label.pack(side=tk.TOP, pady=(8, 0))
        k2f_button = ttk.Button(buttons_frame, text="Trajplot", command=lambda: self.launch_window(k2t.App), width=20)
        k2f_button.pack(side=tk.TOP, pady=4)
        k2r_button = ttk.Button(buttons_frame, text="Recuplot", command=lambda: self.launch_window(k2r.App), width=20)
        k2r_button.pack(side=tk.TOP, pady=4)

        calc_label = ttk.Label(buttons_frame, text="Calculation")
        calc_label.pack(side=tk.TOP, pady=(8, 0))
        k2c_button = ttk.Button(buttons_frame, text="Vector.py", command=lambda: self.launch_window(k2v.App), width=20)
        k2c_button.pack(side=tk.TOP, pady=4)

        pref_label = ttk.Label(buttons_frame, text="MISC")
        pref_label.pack(side=tk.TOP, pady=(8, 0))
        pref_list_button = ttk.Button(buttons_frame, text="Preference", command=lambda: self.launch_window(pref_list.App), width=20)
        pref_list_button.pack(side=tk.TOP, pady=4)

        # srcにlicense.jsonがある場合はボタンを表示
        license_path = os.path.join(self._find_data_dir(), 'license.json')
        if os.path.exists(license_path):
            license_button = ttk.Button(buttons_frame, text="License", command=lambda: self.launch_window(license_view.App), width=20)
            license_button.pack(side=tk.TOP, pady=4)

        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=(24, 0))
        head_frame = ttk.Frame(main_frame)
        head_frame.pack(anchor=tk.N, expand=True, fill=tk.X)
        load_frame = ttk.Frame(head_frame)
        load_frame.pack(side=tk.LEFT, anchor=tk.W, pady=(0, 20))
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.pack()
        self.pkl_selector.set_command(cmd=self.load)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT)

        save_frame = ttk.Frame(head_frame)
        save_frame.pack(anchor=tk.E)
        self.save_button = ttk.Button(save_frame, text="Overwrite", command=self.overwrite)
        self.save_button.pack()
        self.save_button["state"] = tk.DISABLED

        self.mp4_button = ttk.Button(save_frame, text="Export MP4", command=self.export_mp4)
        self.mp4_button.pack(pady=(5, 0))

        view_frame = ttk.Frame(main_frame)
        view_frame.pack(pady=(10, 0), anchor=tk.W)

        video_frame = ttk.Frame(view_frame)
        video_frame.pack(side=tk.LEFT, anchor=tk.N)
        self.vw = VideoViewer(video_frame, width=w_width, height=w_height)
        self.vw.pack()

        attrs_frame = ttk.Frame(view_frame)
        attrs_frame.pack(side=tk.RIGHT, anchor=tk.N)
        self.attrs_textbox = tk.Text(attrs_frame, relief=tk.FLAT, width=40, padx=10, pady=10)
        self.attrs_textbox.pack(fill=tk.BOTH, expand=True, padx=(10, 0))

        self.k2m = export_mp4.MakeMp4()
        self.cap = vcap.VideoCap()
        self.time_span_msec = None
        self.pkl_dir = None
        self.load()

    def load(self):
        self.pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = file_inout.load_track_file(self.pkl_path)
        if self.src_df is None:
            return
        self.src_df = keypoints_proc.zero_point_to_nan(self.src_df)
        self.src_df = self.src_df[~self.src_df.index.duplicated(keep="first")]
        src_attrs = self.src_df.attrs
        self.pkl_dir = os.path.dirname(self.pkl_path)
        self.cap.set_frame_size(src_attrs["frame_size"])
        self.cap.open_file(os.path.join(self.pkl_dir, os.pardir, src_attrs["video_name"]))

        # UIの更新
        self.time_span_entry.update_entry(self.src_df["timestamp"].min(), self.src_df["timestamp"].max())
        self.time_span_msec = self.time_span_entry.get_start_end()
        self.pkl_selector.set_prev_next(src_attrs)

        self.vw.set_cap(self.cap, src_attrs["frame_size"], anno_trk=self.src_df)
        self.update_attrs()
        args = {"src_df": self.src_df, "time_span_msec": self.time_span_msec, "cap": self.cap, "pkl_dir": self.pkl_dir}
        self.k2m.load(args)

    def update_attrs(self):
        src_attrs = self.src_df.attrs
        self.attrs_textbox.delete("1.0", tk.END)
        print_str = ""
        for key, value in src_attrs.items():
            if isinstance(value, dict):
                print_str += f"{key}:\n"
                for key2, value2 in value.items():
                    print_str += f"  {key2}: {value2}\n"
            else:
                print_str += f"{key}: {value}\n"
        self.attrs_textbox.insert(tk.END, print_str)

    def launch_window(self, app, edit_df=False, grab=False):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        if grab is True:
            dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        args = {"src_df": self.src_df, "time_span_msec": self.time_span_msec, "cap": self.cap, "pkl_dir": self.pkl_dir}
        self.a = app(dlg_modal, args)
        dlg_modal.protocol("WM_DELETE_WINDOW", lambda: [dlg_modal.destroy(), cv2.destroyAllWindows()])
        self.wait_window(dlg_modal)

        # ダイアログを閉じた後の処理
        cv2.destroyAllWindows()
        if edit_df is False:
            return
        if hasattr(self.a, "dst_df") is False:
            return
        if self.a.dst_df is None:
            return
        if self.src_df.equals(self.a.dst_df) is True and self.src_df.attrs == self.a.dst_df.attrs:
            return

        print("DataFrame Update")
        self.src_df = self.a.dst_df
        if "proc_history" not in self.src_df.attrs.keys():
            self.src_df.attrs["proc_history"] = []
        self.src_df.attrs["proc_history"].append(self.a.history)

        self.update_attrs()
        self.vw.set_trk(self.src_df)

        self.save_button["state"] = "normal"
        args['src_df'] = self.src_df
        self.k2m.load(args)

        member_count = self.src_df.index.get_level_values(1).unique().size
        print(member_count)

    def overwrite(self):
        file_inout.overwrite_track_file(self.pkl_path, self.src_df)
        print("overwrite done.")

    def export_mp4(self):
        self.k2m.export()

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir


def quit(root):
    root.quit()
    root.destroy()


def main():
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.configure(background=bg_color)
    root.option_add("*background", bg_color)
    root.option_add("*Canvas.background", bg_color)
    root.option_add("*Text.background", "#fcfcfc")
    s = ttk.Style(root)
    s.configure(".", background=bg_color)
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [quit(root), exit()])
    app.mainloop()


if __name__ == "__main__":
    main()
