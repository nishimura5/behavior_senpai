import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk
import cv2
import pandas as pd


class VideoViewer(ttk.Frame):
    def __init__(self, master, width, height):
        super().__init__(master)
        self.pack()

        self.canvas = CapCanvas(self, width=width, height=height)
        self.canvas.pack()

        self.time_min = 0
        self.time_max = 100

        self.slider = ttk.Scale(
            self,
            from_=self.time_min,
            to=self.time_max,
            orient=tk.HORIZONTAL,
            command=self.on_slider_changed)
        self.slider.pack(fill=tk.X, padx=5)
        self.time_max = None

    def set_cap(self, cap, frame_size, anno_trk=None):
        if anno_trk is not None:
            self.time_max = anno_trk["timestamp"].max()
            self.canvas.set_trk(anno_trk)
        else:
            self.time_max = cap.get_max_msec()

        self.canvas.set_cap(cap, frame_size)
        self.canvas.scale_trk()
        self.time_min = 0
        self.slider.config(from_=self.time_min, to=self.time_max)
        self.canvas.update(self.time_min)
        self.slider.set(0)

    def set_trk(self, anno_trk):
        self.canvas.set_trk(anno_trk)
        self.canvas.scale_trk()

    def on_slider_changed(self, msec):
        msec = float(msec)
        self.canvas.update(msec)


class CapCanvas(tk.Canvas):
    def __init__(self, master, width, height):
        super().__init__(master, width=width, height=height, highlightthickness=0)
        self.height = height
        self.img_on_canvas = None
        self.anno_df = None

    def set_cap(self, cap, frame_size):
        self.cap = cap
        ratio = frame_size[0] / frame_size[1]
        canvas_width = int(self.height * ratio)
        self.scale = canvas_width / frame_size[0]
        self.config(width=canvas_width, height=self.height)

    def set_trk(self, src_df):
        import yolo_drawer
        import mediapipe_drawer

        if src_df.attrs['model'] == "YOLOv8 x-pose-p6":
            self.anno = yolo_drawer.Annotate()
            cols_for_anno = ['x', 'y', 'conf']
        elif src_df.attrs['model'] == "MediaPipe Holistic":
            self.anno = mediapipe_drawer.Annotate()
            cols_for_anno = ['x', 'y', 'z']
        self.anno_df = src_df.reset_index().set_index(['timestamp', 'member', 'keypoint']).loc[:, cols_for_anno]

    def scale_trk(self):
        self.anno_df.loc[:, ['x', 'y']] *= self.scale

    def update(self, msec):
        ok, image_rgb = self.cap.read_at(msec, scale=self.scale, rgb=True)
        if ok is False:
            return
        if self.anno_df is not None:
            msec = self.cap.get(cv2.CAP_PROP_POS_MSEC)
            # msecの有無判定
            if msec in self.anno_df.index.get_level_values("timestamp"):
                tar_df = self.anno_df.loc[pd.IndexSlice[msec, :, :], :]
                members = tar_df.index.get_level_values("member").unique().tolist()
                for member in members:
                    member_df = tar_df.loc[pd.IndexSlice[:, member, :], :]
                    kps = member_df.to_numpy()
                    self.anno.set_img(image_rgb)
                    self.anno.set_pose(kps)
                    self.anno.set_track(member)
                    image_rgb = self.anno.draw()

        image_pil = Image.fromarray(image_rgb)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.itemconfig(self.img_on_canvas, image=self.image_tk)
