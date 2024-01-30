import operator
import tkinter as tk
from tkinter import ttk

import pandas as pd
from PIL import Image, ImageTk
import numpy as np
import cv2

from gui_parts import TempFile
from python_senpai import keypoints_proc


class App(ttk.Frame):
    """
    指定した四角形の中にkeypointが入っているかを判定するためのGUIです。
    以下の機能を有します
        - 四角形の位置を指定する機能
        - 以上の処理で得られたデータをpklに保存する機能
    """
    def __init__(self, master, args):
        super().__init__(master)
        master.title("Area Filter")
        self.pack(padx=10, pady=10)

        self.init_anchor_points = [
            {'point': (100, 100)},
            {'point': (100, 200)},
            {'point': (200, 200)},
            {'point': (200, 100)},
            ]

        temp = TempFile()
        width, self.height, dpi = temp.get_window_size()

        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        setting_frame = ttk.Frame(control_frame)
        setting_frame.pack(side=tk.LEFT)

        in_out_label = ttk.Label(setting_frame, text="Target:")
        in_out_label.pack(side=tk.LEFT)
        self.keypoint_member_combo = ttk.Combobox(setting_frame, state='readonly', width=18)
        self.keypoint_member_combo.pack(side=tk.LEFT, padx=5)
        self.keypoint_member_combo["values"] = ("only keyoints", "member")
        self.keypoint_member_combo.current(0)
        self.in_out_combo = ttk.Combobox(setting_frame, state='readonly', width=18)
        self.in_out_combo.pack(side=tk.LEFT, padx=5)
        self.in_out_combo["values"] = ("within area", "outside area")
        self.in_out_combo.current(0)

        calc_button = ttk.Button(setting_frame, text="Remove", command=self.calc_in_out)
        calc_button.pack(side=tk.LEFT)

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok)
        ok_btn.pack(pady=(0, 5))
        cancel_btn = ttk.Button(ok_frame, text="Cancel", command=self.cancel)
        cancel_btn.pack()

        self.canvas = tk.Canvas(self, width=width, height=self.height)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.select)
        self.canvas.bind("<Button1-Motion>", self.motion)

        self.img_on_canvas = None
        self.hull_id = None
        self.dst_df = None
        self.history = "area_filter"

        self.load(args)
        self.draw_convex_hull()
        self.reset_anchor_points()

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        src_attrs = self.src_df.attrs
        self.time_min, self.time_max = args['time_span_msec']

        # 動画のフレームを描画
        ratio = src_attrs["frame_size"][0] / src_attrs["frame_size"][1]
        width = int(self.height * ratio)
        self.scale = width / src_attrs["frame_size"][0]
        self.canvas.config(width=width, height=self.height)
        ok, image_rgb = self.cap.read_at(30*1000, scale=self.scale, rgb=True)
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

    def reset_anchor_points(self):
        self.anchor_points = self.init_anchor_points.copy()
        self.selected_id = None
        poly_points = sum([list(p['point']) for p in self.anchor_points], [])
        self.poly_id = self.canvas.create_polygon(*poly_points, fill="", outline="black")
        for point in self.anchor_points:
            x = point['point'][0]
            y = point['point'][1]
            point['id'] = self.canvas.create_rectangle(x-2, y-2, x+2, y+2, fill="white")

    def calc_in_out(self):
        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)

        poly_points = [p['point'] for p in self.anchor_points]

        isin_df = keypoints_proc.is_in_poly(tar_df, poly_points, 'is_remove', self.scale)
        # area内を削除したいときはboolを反転する
        if self.in_out_combo.get() == "within area":
            isin_df = isin_df.map(operator.not_)

        dst_df = pd.concat([self.src_df, isin_df], axis=1)
        k_m_bool = self.keypoint_member_combo.get() == "member"
        dst_df = keypoints_proc.remove_by_bool_col(dst_df, 'is_remove', k_m_bool)
        self.src_df = dst_df.drop(columns=['is_remove'])

        self.draw_convex_hull()

    def cancel(self):
        self.dst_df = None
        self.master.destroy()

    def on_ok(self):
        self.dst_df = self.src_df.copy()
        if len(self.dst_df) == 0:
            print("No data in DataFrame")
            self.dst_df = None
        self.master.destroy()

    def select(self, event):
        for point in self.anchor_points:
            x = point['point'][0]
            y = point['point'][1]
            if x-10 < event.x < x+10 and y-10 < event.y < y+10:
                self.selected_id = point['id']
                break
            else:
                self.selected_id = None

    def motion(self, event):
        if self.selected_id is None:
            return
        for point in self.anchor_points:
            if point['id'] == self.selected_id:
                point['point'] = (event.x, event.y)
                break
        poly_points = sum([list(p['point']) for p in self.anchor_points], [])
        self.canvas.coords(self.selected_id, event.x-2, event.y-2, event.x+2, event.y+2)
        self.canvas.coords(self.poly_id, *poly_points)
