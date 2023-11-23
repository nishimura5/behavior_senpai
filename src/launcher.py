import tkinter as tk
from tkinter import ttk

import video_to_keypoints as v2k
import track_list as tl
import keypoints_to_mp4 as k2m
import keypoints_to_trajplot as k2t
import keypoints_to_recuplot as k2r
import member_table
import scene_table


class App(ttk.Frame):
    """
    Launcherに並ぶボタンを押すとそのアプリケーションのGUIが起動します。
    各アプリケーションは独立しているため、このLauncherを経由しなくても起動できます。
    """
    def __init__(self, master):
        super().__init__(master)
        master.title("Launcher")
        self.pack(padx=10, pady=10)

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack()

        # video_to_keypointsのボタン
        v2k_button = ttk.Button(buttons_frame, text="video_to_keypoints.py", command=lambda: self.launch_window(v2k.App, grab=True), width=26)
        v2k_button.pack(side=tk.TOP, pady=5)

        # track_listのボタン
        tl_button = ttk.Button(buttons_frame, text="track_list.py", command=lambda: self.launch_window(tl.App, grab=True), width=26)
        tl_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_mp4のボタン 
        k2m_button = ttk.Button(buttons_frame, text="keypoints_to_mp4.py", command=lambda: self.launch_window(k2m.App, grab=True), width=26)
        k2m_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_trajplotのボタン 
        k2f_button = ttk.Button(buttons_frame, text="keypoints_to_trajplot.py", command=lambda: self.launch_window(k2t.App), width=26)
        k2f_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_recuplotのボタン
        k2r_button = ttk.Button(buttons_frame, text="keypoints_to_recuplot.py", command=lambda: self.launch_window(k2r.App), width=26)
        k2r_button.pack(side=tk.TOP, pady=5)

        # member_tableのボタン
        member_table_button = ttk.Button(buttons_frame, text="member_table.py", command=lambda: self.launch_window(member_table.App), width=26)
        member_table_button.pack(side=tk.TOP, pady=5)

        # scene_tableのボタン
        scene_table_button = ttk.Button(buttons_frame, text="scene_table.py", command=lambda: self.launch_window(scene_table.App), width=26)
        scene_table_button.pack(side=tk.TOP, pady=5)

    def launch_window(self, app, grab=False):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        if grab is True:
            dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        app(dlg_modal)
        self.wait_window(dlg_modal)


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
