import sys
import os
import tkinter as tk
from tkinter import ttk

import cv2

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

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack()

        detect_label = ttk.Label(buttons_frame, text="Detection")
        detect_label.pack(side=tk.TOP, pady=(4, 0))
        v2k_button = ttk.Button(buttons_frame, text="app_detect.py", command=lambda: self.launch_window(v2k.App, grab=True), width=26)
        v2k_button.pack(side=tk.TOP, pady=4)

        edit_label = ttk.Label(buttons_frame, text="Edit")
        edit_label.pack(side=tk.TOP, pady=(8, 0))
        tl_button = ttk.Button(buttons_frame, text="app_track_list.py", command=lambda: self.launch_window(tl.App, grab=True), width=26)
        tl_button.pack(side=tk.TOP, pady=4)
        k2b_button = ttk.Button(buttons_frame, text="app_member_edit.py", command=lambda: self.launch_window(k2b.App), width=26)
        k2b_button.pack(side=tk.TOP, pady=4)
        scene_table_button = ttk.Button(buttons_frame, text="scene_table.py", command=lambda: self.launch_window(app_scene_table.App), width=26)
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
        af_button = ttk.Button(buttons_frame, text="app_area_filter.py", command=lambda: self.launch_window(af.App), width=26)
        af_button.pack(side=tk.TOP, pady=4)
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

    def launch_window(self, app, grab=False):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        if grab is True:
            dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        app(dlg_modal)
        dlg_modal.protocol("WM_DELETE_WINDOW", lambda: [dlg_modal.destroy(), cv2.destroyAllWindows()])
        self.wait_window(dlg_modal)

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
