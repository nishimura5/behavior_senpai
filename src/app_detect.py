import sys
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import glob
import datetime

from python_senpai import vcap
import detector_proc
from python_senpai import windows_and_mac


class App(ttk.Frame):
    """
    動画からキーポイントを抽出するためのGUIです。
    以下の機能を有します
     - 動画ファイルまたはフォルダを選択してパスを取得する機能
     - 使用するモデルを選択する機能
     - ROI機能を使用するかどうかを選択する機能
     - detector_proc.pyのexec()を実行する機能
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Detect")
        self.pack(padx=14, pady=14)

        self.tar_path = ""

        self.bat_chk_val = tk.BooleanVar()
        self.bat_chk_val.set(False)
        bat_mode_frame = ttk.Frame(self)
        bat_mode_frame.pack(anchor=tk.W, side=tk.TOP)
        bat_chk = ttk.Checkbutton(bat_mode_frame, text="Bat mode", variable=self.bat_chk_val)
        bat_chk.pack(side=tk.LEFT)
        self.bat_chk_val.trace("w", self._on_bat_mode_changed)
        self.roi_chk_val = tk.BooleanVar()
        self.roi_chk = ttk.Checkbutton(bat_mode_frame, text="ROI", variable=self.roi_chk_val)
        self.roi_chk.pack(side=tk.LEFT, padx=(10, 15))
        self.model_cbox = ttk.Combobox(bat_mode_frame, values=["YOLOv8 x-pose-p6", "MediaPipe Holistic"], state='readonly')
        self.model_cbox.pack(side=tk.LEFT)
        self.model_cbox.current(0)

        top_btn_frame = ttk.Frame(self)
        top_btn_frame.pack(pady=14)
        select_video_btn = ttk.Button(top_btn_frame, text="Select", command=self.select_video)
        select_video_btn.pack(side=tk.LEFT)
        self.video_path_label = ttk.Label(top_btn_frame, text="No video selected")
        self.video_path_label.pack(side=tk.LEFT, padx=(5, 0))
        self.open_btn = ttk.Button(top_btn_frame, text="Open", command=lambda: windows_and_mac.open_file(self.tar_path))
        self.open_btn.pack(side=tk.LEFT, padx=(20, 10))
        self.open_btn['state'] = tk.DISABLED
        self.go_to_folder_btn = ttk.Button(top_btn_frame, text="Go to 'trk' folder", command=lambda: windows_and_mac.go_to_folder(self.tar_path, 'trk'))
        self.go_to_folder_btn.pack(side=tk.LEFT)
        self.go_to_folder_btn['state'] = tk.DISABLED

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack()
        self.exec_detector_btn = ttk.Button(bottom_frame, text="Start", command=self.exec_detector)
        self.exec_detector_btn.pack(side=tk.LEFT)
        self.exec_detector_btn['state'] = tk.DISABLED

        self.rcap = vcap.RoiCap()

    def select_video(self):
        init_dir = self._find_data_dir()
        if self.bat_chk_val.get() is True:
            self.tar_path = filedialog.askdirectory(initialdir=init_dir)
        else:
            self.tar_path = filedialog.askopenfilename(initialdir=init_dir)
        if self.tar_path:
            self.video_path_label["text"] = self.tar_path
        if self.tar_path == "":
            self.open_btn['state'] = tk.DISABLED
            self.go_to_folder_btn['state'] = tk.DISABLED
            self.exec_detector_btn['state'] = tk.DISABLED
            self.video_path_label["text"] = "No video selected"
        else:
            self.open_btn['state'] = tk.NORMAL
            self.go_to_folder_btn['state'] = tk.NORMAL
            self.exec_detector_btn['state'] = tk.NORMAL

    def exec_detector(self):
        if self.bat_chk_val.get() is True:
            self.exec_folder()
        else:
            self.exec_video(self.tar_path)

    def exec_folder(self):
        video_paths = glob.glob(os.path.join(self.tar_path, "*.mp4"))
        for video_path in video_paths:
            self.exec_video(video_path)
        print(f"{datetime.datetime.now()} Done")

    def exec_video(self, video_path):
        '''
        detector_proc.pyを実行
        連続実行するとmediapipeがNULLポインタ参照で落ちるので回避策としてsubprocessを使用
        '''
        print(f"{datetime.datetime.now()} {video_path}")
        if video_path == "":
            return
        model_name = self.model_cbox.get()
        use_roi = self.roi_chk_val.get()
        detector_proc.exec(self.rcap, model_name, video_path, use_roi)

    def _on_bat_mode_changed(self, *args):
        if self.bat_chk_val.get() is True:
            self.video_path_label["text"] = "No folder selected"
            self.roi_chk_val.set(False)
            self.roi_chk["state"] = tk.DISABLED
        else:
            self.video_path_label["text"] = "No video selected"
            self.roi_chk["state"] = tk.NORMAL
        self.tar_path = ""
        self.open_btn['state'] = tk.DISABLED
        self.go_to_folder_btn['state'] = tk.DISABLED
        self.exec_detector_btn['state'] = tk.DISABLED

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
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
