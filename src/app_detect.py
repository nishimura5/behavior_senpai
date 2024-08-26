import datetime
import glob
import os
import tkinter as tk
from tkinter import filedialog, ttk

import ttkthemes

import detector_proc
from behavior_senpai import vcap, windows_and_mac
from gui_parts import Combobox


class App(ttk.Frame):
    """Application for detecting keypoints in a video or folder of videos."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Detect")
        self.pack(padx=14, pady=14)

        self.tar_path = ""

        self.bat_chk_val = tk.BooleanVar()
        self.bat_chk_val.set(False)
        bat_mode_frame = ttk.Frame(self)
        bat_mode_frame.pack(anchor=tk.W, side=tk.TOP)
        bat_chk = ttk.Checkbutton(bat_mode_frame, text="Appy to all files", variable=self.bat_chk_val)
        bat_chk.pack(side=tk.LEFT)
        self.bat_chk_val.trace("w", self._on_bat_mode_changed)
        self.roi_chk_val = tk.BooleanVar()
        self.roi_chk = ttk.Checkbutton(bat_mode_frame, text="ROI", variable=self.roi_chk_val)
        self.roi_chk.pack(side=tk.LEFT, padx=(10, 15))

        yolo_ok, mmpose_ok = detector_proc.check_gpu()
        if yolo_ok and mmpose_ok:
            combo_list = ["YOLOv8 x-pose-p6", "MediaPipe Holistic", "MMPose RTMPose-x"]
        else:
            combo_list = ["MediaPipe Holistic"]
        self.engine_combo = Combobox(bat_mode_frame, "Engine:", values=combo_list, width=24)
        self.engine_combo.pack_horizontal(padx=(10, 0))

        top_btn_frame = ttk.Frame(self)
        top_btn_frame.pack(pady=14)
        self.select_video_btn = ttk.Button(top_btn_frame, text="Select video file", command=self.select_video, width=20)
        self.select_video_btn.pack(side=tk.LEFT)
        self.video_path_label = ttk.Label(top_btn_frame, text="No video selected")
        self.video_path_label.pack(side=tk.LEFT, padx=(5, 0))
        self.open_btn = ttk.Button(
            top_btn_frame,
            text="Open",
            command=lambda: windows_and_mac.open_file(self.tar_path),
        )
        self.open_btn.pack(side=tk.LEFT, padx=(20, 10))
        self.open_btn["state"] = tk.DISABLED
        self.go_to_folder_btn = ttk.Button(
            top_btn_frame,
            text="Go to 'trk' folder",
            command=lambda: windows_and_mac.go_to_folder(self.tar_path, "trk"),
        )
        self.go_to_folder_btn.pack(side=tk.LEFT)
        self.go_to_folder_btn["state"] = tk.DISABLED

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack()
        self.exec_detector_btn = ttk.Button(bottom_frame, text="Start", command=self.exec_detector)
        self.exec_detector_btn.pack(side=tk.LEFT)
        self.exec_detector_btn["state"] = tk.DISABLED

        self.rcap = vcap.RoiCap()

    def select_video(self):
        """Open a file dialog to select a video file or folder.
        Update the UI elements based on the selected path.
        """
        if self.bat_chk_val.get() is True:
            self.tar_path = filedialog.askdirectory(initialdir="~")
        else:
            self.tar_path = filedialog.askopenfilename(initialdir="~")
        if self.tar_path:
            self.video_path_label["text"] = self.tar_path
        if self.tar_path == "":
            self.open_btn["state"] = tk.DISABLED
            self.go_to_folder_btn["state"] = tk.DISABLED
            self.exec_detector_btn["state"] = tk.DISABLED
            self.video_path_label["text"] = "No video selected"
        else:
            self.open_btn["state"] = tk.NORMAL
            self.go_to_folder_btn["state"] = tk.NORMAL
            self.exec_detector_btn["state"] = tk.NORMAL

    def exec_detector(self):
        """Execute the detector for the selected video or folder.
        If in batch mode, executes the detector for all video files in the selected folder.
        If not in batch mode, executes the detector for the selected video file.
        """
        if self.bat_chk_val.get() is True:
            self.exec_folder()
        else:
            self.exec_video(self.tar_path)

    def exec_folder(self):
        """Execute the detector for all video files in the selected folder."""
        video_paths = glob.glob(os.path.join(self.tar_path, "*.mp4"))
        video_paths += glob.glob(os.path.join(self.tar_path, "*.mov"))
        for video_path in video_paths:
            self.exec_video(video_path)
        print(f"{datetime.datetime.now()} Done")

    def exec_video(self, video_path):
        """Execute the detector for the selected video file.
        連続実行するとmediapipeがNULLポインタ参照で落ちるので回避策としてsubprocessを使用.
        """
        print(f"{datetime.datetime.now()} {video_path}")
        if video_path == "":
            return
        model_name = self.engine_combo.get()
        use_roi = self.roi_chk_val.get()
        detector_proc.exec(self.rcap, model_name, video_path, use_roi)

    def _on_bat_mode_changed(self, *args):
        if self.bat_chk_val.get() is True:
            self.select_video_btn["text"] = "Select folder"
            self.video_path_label["text"] = "No folder selected"
            self.roi_chk_val.set(False)
            self.roi_chk["state"] = tk.DISABLED
        else:
            self.select_video_btn["text"] = "Select video file"
            self.video_path_label["text"] = "No video selected"
            self.roi_chk["state"] = tk.NORMAL
        self.tar_path = ""
        self.open_btn["state"] = tk.DISABLED
        self.go_to_folder_btn["state"] = tk.DISABLED
        self.exec_detector_btn["state"] = tk.DISABLED

    def close(self):
        pass


def quit(root):
    """Quit the application and destroy the root window."""
    root.quit()
    root.destroy()


def main():
    """Entry point of the application."""
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.configure(background=bg_color)
    root.option_add("*background", bg_color)
    root.option_add("*Canvas.background", bg_color)
    root.option_add("*Text.background", "#fcfcfc")
    s = ttk.Style(root)
    s.configure(".", background=bg_color)
    app = App(root, None)
    root.protocol("WM_DELETE_WINDOW", lambda: [quit(root), exit()])
    app.mainloop()


if __name__ == "__main__":
    main()
