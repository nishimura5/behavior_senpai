import sys
import os
import tkinter as tk
from tkinter import ttk

import cv2

from gui_parts import PklSelector, TimeSpanEntry, TempFile
from main_gui_parts import VideoViewer
from python_senpai import file_inout
from python_senpai import vcap
import app_detect as v2k
import app_track_list as tl
import app_member_edit as k2b
import app_make_mp4 as k2m
import app_trajplot as k2t
import app_recuplot as k2r
import app_area_filter as af
import app_calc_vector as k2v
import app_scene_table
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
        self.pack(padx=10, pady=10)

        temp = TempFile()
        w_width, w_height, dpi = temp.get_window_size()
        self.w_height = int(w_height * 0.5)

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(side=tk.LEFT, anchor=tk.NW)

        detect_label = ttk.Label(buttons_frame, text="Preparation")
        detect_label.pack(side=tk.TOP, pady=(4, 0))
        v2k_button = ttk.Button(buttons_frame, text="app_detect.py", command=lambda: self.launch_window(v2k.App, grab=True), width=26)
        v2k_button.pack(side=tk.TOP, pady=4)
        tl_button = ttk.Button(buttons_frame, text="app_track_list.py", command=lambda: self.launch_window(tl.App, grab=True), width=26)
        tl_button.pack(side=tk.TOP, pady=4)

        edit_label = ttk.Label(buttons_frame, text="Edit")
        edit_label.pack(side=tk.TOP, pady=(8, 0))
        k2b_button = ttk.Button(
            buttons_frame,
            text="member",
            command=lambda: self.launch_window(k2b.App, edit_df=True, grab=True),
            width=26)
        k2b_button.pack(side=tk.TOP, pady=4)
        af_button = ttk.Button(
            buttons_frame,
            text="area filter",
            command=lambda: self.launch_window(af.App, edit_df=True, grab=True),
            width=26)
        af_button.pack(side=tk.TOP, pady=4)
        scene_table_button = ttk.Button(
            buttons_frame,
            text="scene table",
            command=lambda: self.launch_window(app_scene_table.App, edit_df=True, grab=True),
            width=26)
        scene_table_button.pack(side=tk.TOP, pady=4)

        vis_label = ttk.Label(buttons_frame, text="Visualization")
        vis_label.pack(side=tk.TOP, pady=(8, 0))
        k2m_button = ttk.Button(buttons_frame, text="app_make_mp4.py", command=lambda: self.launch_window(k2m.App, grab=True), width=26)
        k2m_button.pack(side=tk.TOP, pady=4)
        k2f_button = ttk.Button(buttons_frame, text="app_trajplot.py", command=lambda: self.launch_window(k2t.App), width=26)
        k2f_button.pack(side=tk.TOP, pady=4)
        k2r_button = ttk.Button(buttons_frame, text="app_recuplot.py", command=lambda: self.launch_window(k2r.App), width=26)
        k2r_button.pack(side=tk.TOP, pady=4)

        calc_label = ttk.Label(buttons_frame, text="Calculation")
        calc_label.pack(side=tk.TOP, pady=(8, 0))
        k2c_button = ttk.Button(buttons_frame, text="app_calc_vector.py", command=lambda: self.launch_window(k2v.App), width=26)
        k2c_button.pack(side=tk.TOP, pady=4)

        pref_label = ttk.Label(buttons_frame, text="MISC")
        pref_label.pack(side=tk.TOP, pady=(8, 0))
        pref_list_button = ttk.Button(buttons_frame, text="pref_list.py", command=lambda: self.launch_window(pref_list.App), width=26)
        pref_list_button.pack(side=tk.TOP, pady=4)

        # srcにlicense.jsonがある場合はボタンを表示
        license_path = os.path.join(self._find_data_dir(), 'license.json')
        if os.path.exists(license_path):
            license_button = ttk.Button(buttons_frame, text="license_view.py", command=lambda: self.launch_window(license_view.App), width=26)
            license_button.pack(side=tk.TOP, pady=4)

        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.RIGHT, anchor=tk.NE, padx=10)
        load_frame = ttk.Frame(main_frame)
        load_frame.pack(pady=5, anchor=tk.W)
        self.pkl_selector = PklSelector(load_frame)
        self.pkl_selector.set_command(cmd=self.load)
        self.time_span_entry = TimeSpanEntry(load_frame)
        self.time_span_entry.pack(side=tk.LEFT, padx=(0, 5))

        save_frame = ttk.Frame(main_frame)
        save_frame.pack(pady=5, anchor=tk.E)
        self.save_button = ttk.Button(save_frame, text="Overwrite", command=self.overwrite)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        self.save_button["state"] = "disable"

        view_frame = ttk.Frame(main_frame)
        view_frame.pack(pady=5, anchor=tk.W)

        video_frame = ttk.Frame(view_frame)
        video_frame.pack(side=tk.LEFT, anchor=tk.N)
        self.canvas = VideoViewer(video_frame, width=w_width, height=self.w_height)
        self.canvas.pack()

        attrs_frame = ttk.Frame(view_frame)
        attrs_frame.pack(side=tk.RIGHT, anchor=tk.N)
        self.attrs_textbox = tk.Text(attrs_frame, relief=tk.FLAT, padx=10, pady=10)
        self.attrs_textbox.pack(fill=tk.BOTH, expand=True, padx=(10, 0))

        self.img_on_canvas = None
        self.cap = vcap.VideoCap()
        self.load()

    def load(self):
        self.pkl_path = self.pkl_selector.get_trk_path()
        self.src_df = file_inout.load_track_file(self.pkl_path)
        if self.src_df is None:
            return
        src_attrs = self.src_df.attrs
        pkl_dir = os.path.dirname(self.pkl_path)
        self.cap.set_frame_size(src_attrs["frame_size"])
        self.cap.open_file(os.path.join(pkl_dir, os.pardir, src_attrs["video_name"]))

        # UIの更新
        self.time_span_entry.update_entry(self.src_df["timestamp"].min(), self.src_df["timestamp"].max())
        self.time_span_msec = self.time_span_entry.get_start_end()
        self.pkl_selector.set_prev_next(src_attrs)

        self.canvas.set_cap(self.cap, src_attrs["frame_size"], anno_trk=self.src_df)
        self.update_attrs()

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
        args = {"src_df": self.src_df, "time_span_msec": self.time_span_msec, "cap": self.cap}
        self.a = app(dlg_modal, args)
        dlg_modal.protocol("WM_DELETE_WINDOW", lambda: [dlg_modal.destroy(), cv2.destroyAllWindows()])
        self.wait_window(dlg_modal)

        # ダイアログを閉じた後の処理
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
        self.canvas.set_trk(self.src_df)

        self.save_button["state"] = "normal"
        member_count = self.src_df.index.get_level_values(1).unique().size
        print(member_count)

    def overwrite(self):
        file_inout.overwrite_track_file(self.pkl_path, self.src_df)
        print("overwrite done.")

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
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: [quit(root), exit()])
    app.mainloop()


if __name__ == "__main__":
    main()
