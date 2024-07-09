import operator
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
import pandas as pd
from gui_parts import Combobox, TempFile
from PIL import Image, ImageTk
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """Application for filtering keypoints by area."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Area Filter")
        self.pack(padx=10, pady=10)

        self.init_anchor_points = [
            {"point": (100, 100)},
            {"point": (100, 200)},
            {"point": (200, 200)},
            {"point": (200, 100)},
        ]

        temp = TempFile()
        width, self.height, dpi = temp.get_window_size()

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        self.filter_low_button = ttk.Button(control_frame, text="Filter Low", command=self.filter_low)
        self.filter_low_button.pack(side=tk.LEFT)
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(side=tk.LEFT)

        vals = ("only keyoints", "member")
        self.keypoint_member_combo = Combobox(setting_frame, "Target:", values=vals, width=18)
        self.keypoint_member_combo.pack_horizontal(padx=5)
        vals = ("within area", "outside area")
        self.in_out_combo = Combobox(setting_frame, "", values=vals, width=18)
        self.in_out_combo.pack_horizontal(padx=5)

        calc_button = ttk.Button(setting_frame, text="Remove", command=self.calc_in_out)
        calc_button.pack(side=tk.LEFT, padx=(10, 0))

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        self.canvas = tk.Canvas(self, width=width, height=self.height, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.select)
        self.canvas.bind("<Button1-Motion>", self.motion)

        self.img_on_canvas = None
        self.hull_id = None
        self.dst_df = None
        self.history = "area_filter"

        self._load(args)
        self.draw_convex_hull()
        self.reset_anchor_points()

    def _load(self, args):
        self.src_df = args["src_df"].copy()
        self.cap = args["cap"]
        current_position = args["current_position"]
        src_attrs = self.src_df.attrs

        # 動画のフレームを描画
        ratio = src_attrs["frame_size"][0] / src_attrs["frame_size"][1]
        width = int(self.height * ratio)
        self.scale = width / src_attrs["frame_size"][0]
        self.canvas.config(width=width, height=self.height)
        self.model_name = src_attrs["model"]
        ok, image_rgb = self.cap.read_at(current_position, scale=self.scale, rgb=True)
        if ok is False:
            return
        image_pil = Image.fromarray(image_rgb)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.canvas.itemconfig(self.img_on_canvas, image=self.image_tk)

    def draw_convex_hull(self):
        # src_dfのx,yから凸包を描画
        points = self.src_df[["x", "y"]].dropna().values * self.scale
        points = np.array(points, dtype=np.int32)
        hull = cv2.convexHull(points)
        flat_list = sum(sum(hull.tolist(), []), [])
        if self.hull_id is None:
            self.hull_id = self.canvas.create_polygon(*flat_list, fill="", outline="aqua", width=2)
        else:
            self.canvas.coords(self.hull_id, *flat_list)
        print(f"left={self.src_df['x'].min()}, right={self.src_df['x'].max()}")

    def reset_anchor_points(self):
        self.anchor_points = self.init_anchor_points.copy()
        self.selected_id = None
        poly_points = sum([list(p["point"]) for p in self.anchor_points], [])
        self.poly_id = self.canvas.create_polygon(*poly_points, fill="", outline="magenta")
        for point in self.anchor_points:
            x = point["point"][0]
            y = point["point"][1]
            point["id"] = self.canvas.create_rectangle(x - 2, y - 2, x + 2, y + 2, fill="white")

    def calc_in_out(self):
        poly_points = [p["point"] for p in self.anchor_points]

        isin_df = keypoints_proc.is_in_poly(self.src_df, poly_points, "is_remove", self.scale)
        # area内を削除したいときはboolを反転する
        if self.in_out_combo.get() == "within area":
            isin_df = isin_df.map(operator.not_)

        dst_df = pd.concat([self.src_df, isin_df], axis=1)
        k_m_bool = self.keypoint_member_combo.get() == "member"
        dst_df = keypoints_proc.remove_by_bool_col(dst_df, "is_remove", k_m_bool)
        self.src_df = dst_df.drop(columns=["is_remove"])

        self.draw_convex_hull()

    def filter_low(self):
        """Filter out the keypoints with low confidence or score."""
        low_thresh = 0.5
        if self.model_name == "MMPose RTMPose-x":
            col = "score"
        elif self.model_name == "YOLOv8 x-pose-p6":
            col = "conf"
        else:
            print(f"Unsupported model: {self.model_name}")
            return
        self.src_df.loc[self.src_df[col] < low_thresh, ["x", "y"]] = np.nan
        self.draw_convex_hull()

    def on_ok(self):
        """Perform the action when the 'OK' button is clicked."""
        self.dst_df = self.src_df.copy()
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def cancel(self):
        """Cancel the operation and destroy the window."""
        self.dst_df = None
        self.master.destroy()

    def select(self, event):
        """Handle the selection of anchor points on the canvas."""
        for point in self.anchor_points:
            x = point["point"][0]
            y = point["point"][1]
            if x - 10 < event.x < x + 10 and y - 10 < event.y < y + 10:
                self.selected_id = point["id"]
                break
            else:
                self.selected_id = None

    def motion(self, event):
        """Handle the motion event when the canvas is being dragged."""
        if self.selected_id is None:
            return
        for point in self.anchor_points:
            if point["id"] == self.selected_id:
                point["point"] = (event.x, event.y)
                break
        poly_points = sum([list(p["point"]) for p in self.anchor_points], [])
        self.canvas.coords(self.selected_id, event.x - 2, event.y - 2, event.x + 2, event.y + 2)
        self.canvas.coords(self.poly_id, *poly_points)
