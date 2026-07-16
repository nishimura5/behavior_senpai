import datetime
import glob
import os
import tkinter as tk
from tkinter import filedialog, ttk

import ttkthemes

import detector_proc
from behavior_senpai import vcap, windows_and_mac
from gui_parts import Checkbutton, Combobox


class App(ttk.Frame):
    """Application for detecting keypoints in a video or folder of videos."""

    def __init__(self, master):
        super().__init__(master)
        master.title("Detect")
        self.pack(padx=20, pady=20)

        self.tar_path = ""
        self.trk_path = ""

        bat_mode_frame = ttk.Frame(self)
        bat_mode_frame.pack(anchor=tk.W, side=tk.TOP)

        bat_chk_desc = "If checked, applies the detector to all video files in the selected folder (not recursively)."
        self.bat_chk = Checkbutton(bat_mode_frame, "Apply all", description=bat_chk_desc)
        self.bat_chk.pack_horizontal(padx=(0, 10))
        self.bat_chk.set_trace(self._on_bat_mode_changed)

        move_chk_desc = move_chk_desc = (
            'If checked, moves the original video file to the "~/Videos/BehaviorSenpai_YYYYMMDD" directory before processing.\nYou can rename the "BehaviorSenpai_YYYYMMDD" folder later.'
        )
        self.move_chk = Checkbutton(bat_mode_frame, 'Move to "Videos"', description=move_chk_desc)
        self.move_chk.pack_horizontal(padx=(0, 10))

        roi_desc = "If checked, enables defining a region of interest (ROI) for the detector before starting."
        self.roi_chk = Checkbutton(bat_mode_frame, "ROI", description=roi_desc)
        self.roi_chk.pack_horizontal(padx=(0, 10))

        suffix_desc = "If checked, adds a suffix to the output video file indicating the engine used."
        self.add_suffix_chk = Checkbutton(bat_mode_frame, "Add suffix", description=suffix_desc)
        self.add_suffix_chk.pack_horizontal(padx=(0, 15))

        yolo_ok, mmpose_ok = detector_proc.check_gpu()
        if yolo_ok and mmpose_ok:
            combo_list = [
                "YOLO11 x-pose",
                "YOLOv8 x-pose-p6",
                "MediaPipe Holistic",
                "RTMPose-x Halpe26",
                "RTMW-x WholeBody133",
            ]
        elif mmpose_ok:
            combo_list = [
                "MediaPipe Holistic",
                "RTMPose-x Halpe26",
                "RTMW-x WholeBody133",
            ]
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
        if self.bat_chk.get() is True:
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
        self.start_datetime = datetime.datetime.now()
        if self.bat_chk.get() is True:
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
        if self.move_chk.get() is True:
            datetime_str = self.start_datetime.strftime("%Y_%m_%d")
            video_path = windows_and_mac.move_to_videos(video_path, f"BehaviorSenpai_{datetime_str}")
        model_name = self.engine_combo.get()
        use_roi = self.roi_chk.get()
        add_suffix = self.add_suffix_chk.get()
        self.trk_path = detector_proc.exec(self.rcap, model_name, video_path, use_roi, add_suffix)

    def _on_bat_mode_changed(self, *args):
        if self.bat_chk.get() is True:
            self.select_video_btn["text"] = "Select folder"
            self.video_path_label["text"] = "No folder selected"
            self.roi_chk.set(False)
            self.roi_chk.set_state(tk.DISABLED)
        else:
            self.select_video_btn["text"] = "Select video file"
            self.video_path_label["text"] = "No video selected"
            self.roi_chk.set_state(tk.NORMAL)
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
