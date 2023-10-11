import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

import cv2

from yolo_detector import YoloDetector
from mediapipe_detector import MediaPipeDetector


class App(tk.Frame):
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Video to Keypoints")
        self.pack(padx=10, pady=10)

        select_video_btn = ttk.Button(self, text="Select video", command=self.select_video)
        select_video_btn.pack()
        self.video_path_label = ttk.Label(self, text="No video selected")
        self.video_path_label.pack()
        self.model_cbox = ttk.Combobox(self, values=["YOLOv8 x-pose-p6", "MediaPipe Holistic"], state='readonly')
        self.model_cbox.pack()

        bottom_btn_frame = tk.Frame(self)
        bottom_btn_frame.pack(side=tk.BOTTOM)
        open_btn = ttk.Button(bottom_btn_frame, text="Open", command=lambda: self.open_file(self.video_path))
        open_btn.pack(side=tk.LEFT)
        exec_detector_btn = ttk.Button(bottom_btn_frame, text="Detect", command=self.exec_detector)
        exec_detector_btn.pack(side=tk.LEFT)
        go_to_folder_btn = ttk.Button(bottom_btn_frame, text="Go to 'trk' Folder", command=self.go_to_folder)
        go_to_folder_btn.pack(side=tk.LEFT)

    def select_video(self):
        init_dir = os.path.abspath(os.path.dirname(__file__))
        self.video_path = filedialog.askopenfilename(initialdir=init_dir)
        self.video_path_label["text"] = self.video_path

    def exec_detector(self):
        model_name = self.model_cbox.get()

        file_name = os.path.splitext(os.path.basename(self.video_path))[0]
        trk_dir = os.path.join(os.path.dirname(self.video_path), "trk")
        os.makedirs(trk_dir, exist_ok=True)
        pkl_path = os.path.join(trk_dir, f"{file_name}.pkl")

        cap = cv2.VideoCapture(self.video_path)

        if model_name == "YOLOv8 x-pose-p6":
            detector = YoloDetector(cap)
        elif model_name == "MediaPipe Holistic":
            detector = MediaPipeDetector(cap)

        detector.detect()
        result_df = detector.get_result()

        result_df.attrs["model"] = model_name

        result_df.to_pickle(pkl_path)

    def open_file(self, filepath):
        # Windows
        if sys.platform.startswith('win32'):
            subprocess.Popen(['start', filepath], shell=True)
        # Mac
        elif sys.platform.startswith('darwin'):
            subprocess.call(['open', filepath])

    def go_to_folder(self):
        trk_dir = os.path.join(os.path.dirname(self.video_path), "trk")
        if os.path.exists(trk_dir) is False:
            trk_dir = os.path.dirname(self.video_path)
        # Windows
        if sys.platform.startswith('win32'):
            subprocess.Popen(['explorer', trk_dir.replace('/', '\\')], shell=True)
        # Mac
        elif sys.platform.startswith('darwin'):
            subprocess.call(['open', trk_dir])


def quit(root):
    root.quit()
    root.destroy()


def main(args):
    root = tk.Tk()
    app = App(root, args)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":

    args = None

    main(args)
    exit()
