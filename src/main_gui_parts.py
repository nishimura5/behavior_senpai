import os
import tkinter as tk
from tkinter import ttk

import numpy as np
import pandas as pd
from PIL import Image, ImageTk

from behavior_senpai import file_inout, img_draw, mediapipe_drawer, pose_drawer, time_format
from gui_parts import TempFile


class PklSelector(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # 一時ファイルからtrkのパスを取得
        tmp = TempFile()
        data = tmp.load()
        self.trk_path = data["trk_path"]

        self.side = tk.LEFT
        self.prev_pkl_btn = ttk.Button(master, text="<", width=1, state=tk.DISABLED)
        self.prev_pkl_btn.pack(side=tk.LEFT)
        self.next_pkl_btn = ttk.Button(master, text=">", width=1, state=tk.DISABLED)
        self.next_pkl_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.load_pkl_btn = ttk.Button(master, text="Select track file")
        self.load_pkl_btn.pack(side=tk.LEFT)
        self.pkl_path_label = ttk.Label(master, text="No track file loaded")
        self.pkl_path_label.pack(side=tk.LEFT, padx=(5, 0))

        if self.trk_path != "":
            self.pkl_path_label["text"] = self.trk_path

    def _select_trk(self):
        init_dir = os.path.dirname(self.trk_path)
        pl = file_inout.PickleLoader(init_dir=init_dir, org_path=self.trk_path, filetype="pkl")
        is_file_selected = pl.show_open_dialog()
        if is_file_selected:
            self.trk_path = pl.tar_path
            self.pkl_path_label["text"] = self.trk_path
            temp = TempFile()
            data = temp.load()
            data["trk_path"] = pl.tar_path
            temp.save(data)
        else:
            self.trk_path = ""
            self.pkl_path_label["text"] = "No track file loaded"

    def _load_pkl(self):
        if self.trk_path:
            self.pkl_path_label["text"] = self.trk_path
            tmp = TempFile()
            data = tmp.load()
            data["trk_path"] = self.trk_path
            tmp.save(data)
        else:
            self.trk_path = ""
            self.pkl_path_label["text"] = "No track file loaded"

    def rename_pkl_path_label(self, new_name):
        self.pkl_path_label["text"] = new_name

    def set_prev_next(self, attr_dict):
        dir_path = os.path.dirname(self.trk_path)
        if "prev" in attr_dict and attr_dict["prev"] != "" and attr_dict["prev"] is not None:
            self.prev_pkl_btn["state"] = tk.NORMAL
            self.prev_path = os.path.join(dir_path, attr_dict["prev"])
        else:
            self.prev_path = ""
            self.prev_pkl_btn["state"] = tk.DISABLED
        if "next" in attr_dict and attr_dict["next"] != "" and attr_dict["next"] is not None:
            self.next_path = os.path.join(dir_path, attr_dict["next"])
            self.next_pkl_btn["state"] = tk.NORMAL
        else:
            self.next_path = ""
            self.next_pkl_btn["state"] = tk.DISABLED

    def _load_prev_pkl(self):
        self.trk_path = self.prev_path
        self._load_pkl()

    def _load_next_pkl(self):
        self.trk_path = self.next_path
        self._load_pkl()

    def get_trk_path(self):
        if os.path.exists(self.trk_path) is False:
            print(f'"{self.trk_path}" is not found.')
        return self.trk_path

    def set_command(self, cmd):
        self.load_pkl_btn["command"] = lambda: [self._select_trk(), cmd()]
        self.prev_pkl_btn["command"] = lambda: [self._load_prev_pkl(), cmd()]
        self.next_pkl_btn["command"] = lambda: [self._load_next_pkl(), cmd()]


class VideoViewer(ttk.Frame):
    def __init__(self, master, width, height):
        super().__init__(master)
        self.pack()

        self.canvas = CapCanvas(self, width=width, height=height)
        self.canvas.pack()

        self.time_min = 0
        self.time_max = 100

        self.slider = ttk.Scale(self, from_=self.time_min, to=self.time_max, orient=tk.HORIZONTAL, command=self.on_slider_changed)
        self.slider.pack(fill=tk.X, padx=5)
        self.time_max = None

        # add mouse scroll event
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)

    def set_cap(self, cap, frame_size, anno_trk=None):
        # frame_size : [width, height]
        if anno_trk is not None:
            self.time_min = anno_trk["timestamp"].min()
            self.time_max = anno_trk["timestamp"].max()
            self.canvas.set_trk(anno_trk)
        else:
            self.time_min = 0
            self.time_max = cap.get_max_msec()

        self.canvas.set_cap(cap, frame_size)
        self.canvas.set_area()
        self.canvas.scale_trk()
        self.slider.config(from_=self.time_min, to=self.time_max)
        self.canvas.update(self.time_min)
        self.slider.set(0)

    def set_trk(self, anno_trk):
        self.canvas.set_trk(anno_trk)
        self.canvas.scale_trk()

    def on_slider_changed(self, msec):
        msec = float(msec)
        self.canvas.update(msec)

    def _on_mouse_wheel(self, event):
        if event.delta > 0:
            self.slider.set(self.slider.get() + 500)
        else:
            self.slider.set(self.slider.get() - 500)
        self.on_slider_changed(self.slider.get())

    def get_current_position(self):
        return self.slider.get()


class CapCanvas(tk.Canvas):
    def __init__(self, master, width, height):
        super().__init__(master, width=width, height=height, highlightthickness=0)
        self.height = height
        self.img_on_canvas = None
        self.anno_df = None
        self.current_msec = 0
        self.is_crop = True

        # set click event
        self.bind("<Button-1>", self._on_click)

    def set_cap(self, cap, frame_size):
        self.cap = cap
        self.frame_size = frame_size

    def set_trk(self, src_df):
        if src_df.attrs["model"] in ["YOLOv8 x-pose-p6", "YOLO11 x-pose"]:
            self.anno = pose_drawer.Annotate("coco17.toml")
            cols_for_anno = ["x", "y", "conf"]
        elif src_df.attrs["model"] == "MediaPipe Holistic":
            self.anno = mediapipe_drawer.Annotate()
            cols_for_anno = ["x", "y", "z"]
        # "MMPose RTMPos-x" <- To maintain backward compatibility (ver 1.3)
        elif src_df.attrs["model"] in ["MMPose RTMPose-x", "RTMPose-x Halpe26"]:
            self.anno = pose_drawer.Annotate("halpe26.toml")
            cols_for_anno = ["x", "y", "score"]
        elif src_df.attrs["model"] == "RTMPose-x WholeBody133":
            self.anno = pose_drawer.Annotate("coco133.toml")
            cols_for_anno = ["x", "y", "score"]
        elif src_df.attrs["model"] == "DeepLabCut":
            self.anno = pose_drawer.Annotate("deeplabcut.toml")
            cols_for_anno = ["x", "y", "likelihood"]
        self.anno_df = src_df.reset_index().set_index(["timestamp", "member", "keypoint"]).loc[:, cols_for_anno]
        self.org_anno_df = self.anno_df.copy()
        self.timestamps = self.anno_df.index.get_level_values("timestamp").unique().to_numpy()

    def set_area(self):
        if self.is_crop is False:
            ratio = self.frame_size[0] / self.frame_size[1]
            canvas_width = int(self.height * ratio)
            self.scale = canvas_width / self.frame_size[0]
            x_min = 0
            y_min = 0
            x_max = self.frame_size[0]
            y_max = self.frame_size[1]
        else:
            # get least x and y
            x_min = self.org_anno_df["x"].min().astype(int)
            y_min = self.org_anno_df["y"].min().astype(int)
            # get max x and y
            x_max = self.org_anno_df["x"].max().astype(int)
            y_max = self.org_anno_df["y"].max().astype(int)
            # frame_size
            crop_width = x_max - x_min
            crop_height = y_max - y_min

            ratio = crop_width / crop_height
            canvas_width = int(self.height * ratio)
            if canvas_width > 1000:
                canvas_width = 1000
            self.scale = canvas_width / crop_width

        self.x_min = int(x_min * self.scale)
        self.y_min = int(y_min * self.scale)
        self.x_max = int(x_max * self.scale)
        self.y_max = int(y_max * self.scale)

        self.config(width=canvas_width, height=self.height)

    def scale_trk(self):
        self.anno_df.loc[:, ["x", "y"]] = self.org_anno_df.loc[:, ["x", "y"]] * self.scale

    def update(self, msec):
        msec = self.timestamps[np.fabs(self.timestamps - msec).argsort()[:1]][0]
        ok, image_rgb = self.cap.read_at(msec, scale=self.scale, rgb=True)
        if ok is False:
            return
        if self.anno_df is not None:
            tar_df = self.anno_df.loc[pd.IndexSlice[msec, :, :], :]
            members = tar_df.index.get_level_values("member").unique().tolist()
            for member in members:
                member_df = tar_df.loc[pd.IndexSlice[:, member, :], :]
                kps = member_df.to_numpy()
                self.anno.set_img(image_rgb)
                self.anno.set_pose(kps)
                self.anno.set_track(member)
                image_rgb = self.anno.draw()

        # crop
        image_rgb = img_draw.crop_img(image_rgb, self.x_min, self.y_min, self.x_max, self.y_max)

        time_str = time_format.msec_to_timestr_with_fff(msec)
        img_draw.put_message(image_rgb, f"{time_str}", font_size=2, y=self.height - 15)

        image_pil = Image.fromarray(image_rgb)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.itemconfig(self.img_on_canvas, image=self.image_tk)

        self.current_msec = msec

    def _on_click(self, event):
        if self.is_crop:
            self.is_crop = False
        else:
            self.is_crop = True
        self.set_area()
        self.scale_trk()
        self.update(self.current_msec)
        #        print(f"scale: {self.scale:.2f}")
