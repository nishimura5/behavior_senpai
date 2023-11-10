import tkinter as tk
from tkinter import ttk

import video_to_keypoints as v2k
import keypoints_to_figure as k2f
import keypoints_to_mp4 as k2m
import keypoints_to_recuplot as k2r


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Launcher")
        self.pack(padx=10, pady=10)

        # ボタンのフレーム
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack()

        # video_to_keypointsのボタン
        v2k_button = ttk.Button(buttons_frame, text="video_to_keypoints.py", command=self.launch_v2k)
        v2k_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_mp4のボタン 
        k2m_button = ttk.Button(buttons_frame, text="keypoints_to_mp4.py", command=self.launch_k2m)
        k2m_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_figureのボタン 
        k2f_button = ttk.Button(buttons_frame, text="keypoints_to_figure.py", command=self.launch_k2f)
        k2f_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_recuplotのボタン
        k2r_button = ttk.Button(buttons_frame, text="keypoints_to_recuplot.py", command=self.launch_k2r)
        k2r_button.pack(side=tk.TOP, pady=5)

    def launch_v2k(self):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        v2k.App(dlg_modal)
        self.wait_window(dlg_modal) 

    def launch_k2m(self):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        dlg_modal.grab_set()
        dlg_modal.transient(self.master)
        k2m.App(dlg_modal)
        self.wait_window(dlg_modal)

    def launch_k2f(self):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        dlg_modal.transient(self.master)
        k2f.App(dlg_modal)
        self.wait_window(dlg_modal) 

    def launch_k2r(self):
        dlg_modal = tk.Toplevel(self)
        dlg_modal.focus_set()
        dlg_modal.transient(self.master)
        k2r.App(dlg_modal)
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
