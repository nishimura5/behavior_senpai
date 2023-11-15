import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import glob
import subprocess

import windows_and_mac


class App(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Video to Keypoints")
        self.pack(padx=10, pady=10)

        self.video_path = ""
        self.folder_path = ""

        # bat処理モード
        self.bat_chk_val = tk.BooleanVar()
        self.bat_chk_val.set(False)
        bat_mode_frame = ttk.Frame(self)
        bat_mode_frame.pack(side=tk.TOP)
        bat_chk = ttk.Checkbutton(bat_mode_frame, text="Bat mode", variable=self.bat_chk_val)
        bat_chk.pack(side=tk.LEFT)
        self.bat_chk_val.trace("w", self._on_bat_mode_changed)
 
        # ファイル/フォルダ選択
        top_btn_frame = ttk.Frame(self)
        top_btn_frame.pack(pady=10)
        select_video_btn = ttk.Button(top_btn_frame, text="Select video", command=self.select_video)
        select_video_btn.pack(side=tk.LEFT)
        self.video_path_label = ttk.Label(top_btn_frame, text="No video selected")
        self.video_path_label.pack(side=tk.LEFT)

        middle_btn_frame = ttk.Frame(self)
        middle_btn_frame.pack()
        self.model_cbox = ttk.Combobox(middle_btn_frame, values=["YOLOv8 x-pose-p6", "MediaPipe Holistic"], state='readonly')
        self.model_cbox.pack(side=tk.LEFT, padx=15)
        self.roi_chk_val = tk.BooleanVar()
        self.roi_chk = ttk.Checkbutton(middle_btn_frame, text="ROI", variable=self.roi_chk_val)
        self.roi_chk.pack(side=tk.LEFT)

        bottom_btn_frame = ttk.Frame(self)
        bottom_btn_frame.pack(pady=10)
        open_btn = ttk.Button(bottom_btn_frame, text="Open", command=lambda: windows_and_mac.open_file(self.video_path))
        open_btn.pack(side=tk.LEFT)
        exec_detector_btn = ttk.Button(bottom_btn_frame, text="Detect", command=self.exec_detector)
        exec_detector_btn.pack(side=tk.LEFT)
        go_to_folder_btn = ttk.Button(bottom_btn_frame, text="Go to 'trk' Folder", command=lambda: windows_and_mac.go_to_folder(self.video_path, 'trk'))
        go_to_folder_btn.pack(side=tk.LEFT)

    def select_video(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        if self.bat_chk_val.get() is True:
            self.folder_path = filedialog.askdirectory(initialdir=init_dir)
            if self.folder_path:
                self.video_path_label["text"] = self.folder_path
        else:
            self.video_path = filedialog.askopenfilename(initialdir=init_dir)
            if self.video_path:
                self.video_path_label["text"] = self.video_path

    def exec_detector(self):
        if self.bat_chk_val.get() is True:
            self.exec_folder()
        else:
            self.exec_video()

    def exec_folder(self):
        video_paths = glob.glob(os.path.join(self.folder_path, "*.mp4"))
        for video_path in video_paths:
            print(f"executing {video_path}")
            self.video_path = video_path
            self.exec_video()

    def exec_video(self):
        '''
        detector_proc.pyを実行
        連続実行するとmediapipeがNULLポインタ参照で落ちるので回避策としてsubprocessを使用
        '''
        if self.video_path == "":
            return
        model_name = self.model_cbox.get()
        use_roi = self.roi_chk_val.get()
        script_path = os.path.join(os.path.dirname(__file__), "detector_proc.py")
        cmd = f"python {script_path} --model_name \"{model_name}\" --video_path \"{self.video_path}\""
        if use_roi is True:
            cmd += " --use_roi"
        subprocess.run(cmd, shell=True)

    def _on_bat_mode_changed(self, *args):
        if self.bat_chk_val.get() is True:
            self.video_path_label["text"] = "No folder selected"
            self.folder_path = ""
            self.roi_chk_val.set(False)
            self.roi_chk["state"] = "disabled"
        else:
            self.video_path_label["text"] = "No video selected"
            self.video_path = ""
            self.roi_chk["state"] = "enabled"


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
