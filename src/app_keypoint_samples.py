import os
import sys
import tkinter as tk
from tkinter import ttk

from behavior_senpai import windows_and_mac
from gui_parts import Combobox


class App(tk.Toplevel):
    """Application for showing images."""

    def __init__(self, master, dataset_name):
        super().__init__(master)
        self.focus_set()
        self.title("Keypoint samples")

        img_name = ""
        if dataset_name == "MediaPipe Holistic":
            img_name = "facemesh"
        elif dataset_name in ["YOLOv8 x-pose-p6", "YOLO11 x-pose"]:
            img_name = "body_coco"
        elif dataset_name in ["MMPose RTMPose-x", "RTMPose-x Halpe26"]:
            img_name = "body_halpe26"
        elif dataset_name in ["RTMPose-x WholeBody133"]:
            img_name = "body_wholebody133"

        head_frame = ttk.Frame(self)
        head_frame.pack(pady=5, side=tk.TOP)
        img_list = ["hands", "facemesh", "facemesh2", "body_coco", "body_halpe26", "body_wholebody133", "face_wholebody133"]
        self.keypoints_combo = Combobox(head_frame, label="Keypoints:", width=17, values=img_list)
        self.keypoints_combo.pack_horizontal(padx=5, anchor=tk.N)
        self.keypoints_combo.set_selected_bind(self._change_img)
        self.keypoints_combo.set(img_name)

        toml_btn = ttk.Button(head_frame, text="Open toml folder", command=self._open_toml)
        toml_btn.pack(side=tk.LEFT, padx=(20, 0))

        img_frame = ttk.Frame(self)
        img_frame.pack()
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", f"{img_name}.png")
        self.img = tk.PhotoImage(file=img_path)
        self.img = self.img.subsample(2)
        self.img_label = ttk.Label(img_frame, image=self.img)
        self.img_label.pack(side=tk.LEFT)

    def _change_img(self, event):
        img_name = self.keypoints_combo.get()
        data_dir = self._find_data_dir()
        img_path = os.path.join(data_dir, "img", f"{img_name}.png")
        self.img = tk.PhotoImage(file=img_path)
        self.img = self.img.subsample(2)
        self.img_label.configure(image=self.img)
        self.img_label.image = self.img

    def _open_toml(self):
        data_dir = self._find_data_dir()
        tar_path = os.path.join(data_dir, "keypoint")
        windows_and_mac.open_file(tar_path)

    def _find_data_dir(self):
        if getattr(sys, "frozen", False):
            # The application is frozen
            datadir = os.path.dirname(sys.executable)
        else:
            # The application is not frozen
            # Change this bit to match where you store your data files:
            datadir = os.path.dirname(__file__)
        return datadir

    def close(self):
        pass
