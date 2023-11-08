import tkinter as tk
from tkinter import ttk

import video_to_keypoints as v2k
import keypoints_to_figure as k2f
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

        # keypoints_to_figureのボタン 
        k2f_button = ttk.Button(buttons_frame, text="keypoints_to_figure.py", command=self.launch_k2f)
        k2f_button.pack(side=tk.TOP, pady=5)

        # keypoints_to_recuplotのボタン
        k2r_button = ttk.Button(buttons_frame, text="keypoints_to_recuplot.py", command=self.launch_k2r)
        k2r_button.pack(side=tk.TOP, pady=5)

    def launch_v2k(self):
        v2k.main()

    def launch_k2f(self):
        k2f.main()

    def launch_k2r(self):
        k2r.main()


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
