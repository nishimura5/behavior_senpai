import tkinter as tk
from tkinter import ttk

import pandas as pd
from PIL import Image, ImageTk
import cv2
import numpy as np

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

        temp = TempFile()
        width, self.height, dpi = temp.get_window_size()

        setting_frame = ttk.Frame(self)
        setting_frame.pack(pady=5)

        in_out_label = ttk.Label(setting_frame, text="remove")
        in_out_label.pack(side=tk.LEFT)
        self.keypoint_member_combo = ttk.Combobox(setting_frame, state='readonly', width=18)
        self.keypoint_member_combo.pack(side=tk.LEFT, padx=5)
        self.keypoint_member_combo["values"] = ("only keyoints", "member")
        self.keypoint_member_combo.current(0)
        self.in_out_combo = ttk.Combobox(setting_frame, state='readonly', width=18)
        self.in_out_combo.pack(side=tk.LEFT, padx=5)
        self.in_out_combo["values"] = ("within area", "outside area")
        self.in_out_combo.current(0)

        calc_button = ttk.Button(setting_frame, text="remove", command=self.calc_in_out)
        calc_button.pack(side=tk.LEFT)

        export_frame = ttk.Frame(self)
        export_frame.pack(pady=5)

        clear_btn = ttk.Button(export_frame, text="Clear", command=self.clear)
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))

        export_btn = ttk.Button(export_frame, text="OK", command=self.on_ok)
        export_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.canvas = tk.Canvas(self, width=width, height=self.height)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.select)
        self.canvas.bind("<Button1-Motion>", self.motion)

        self.img_on_canvas = None
        self.dst_df = None
        self.load(args)

        self.anchor_points = [
            {'point': (100, 100)},
            {'point': (100, 200)},
            {'point': (200, 200)},
            {'point': (200, 100)},
            ]
        self.selected_id = None
        poly_points = sum([list(p['point']) for p in self.anchor_points], [])
        self.poly_id = self.canvas.create_polygon(*poly_points, fill="", outline="black")
        for point in self.anchor_points:
            x = point['point'][0]
            y = point['point'][1]
            point['id'] = self.canvas.create_rectangle(x-2, y-2, x+2, y+2, fill="white")

    def load(self, args):
        self.src_df = args['src_df']
        self.cap = args['cap']
        self.src_attrs = args['src_attrs']
        self.time_min, self.time_max = args['time_span_msec']

        # UIの更新
        ratio = self.src_attrs["frame_size"][0] / self.src_attrs["frame_size"][1]
        width = int(self.height * ratio)
        self.scale = width / self.src_attrs["frame_size"][0]
        self.canvas.config(width=width, height=self.height)

        ok, image_rgb = self.cap.read_at(10, rgb=True)
        if ok is False:
            return
        image_rgb = cv2.resize(image_rgb, None, fx=self.scale, fy=self.scale)
        image_pil = Image.fromarray(image_rgb)
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.canvas.itemconfig(self.img_on_canvas, image=self.image_tk)
        self.clear()

    def calc_in_out(self):
        # timestampの範囲を抽出
        tar_df = keypoints_proc.filter_by_timerange(self.src_df, self.time_min, self.time_max)

        poly_points = [p['point'] for p in self.anchor_points]
        left, top = self.src_attrs["roi_left_top"]
        # tar_dfのx,yが両方ともzero_pointと同じならnp.nanに置換する
        tar_df.loc[(tar_df["x"] == left) & (tar_df["y"] == top), ["x", "y"]] = [np.nan, np.nan]

        isin_df = keypoints_proc.is_in_poly(tar_df, poly_points, 'is_remove', self.scale)
        # area外を削除したいときはboolを反転する
        if self.in_out_combo.get() == "within area":
            isin_df = isin_df.applymap(lambda x: not x)

        dst_df = pd.concat([self.src_df, isin_df], axis=1)
        k_m_bool = self.keypoint_member_combo.get() == "member"
        dst_df = keypoints_proc.remove_by_bool_col(dst_df, 'is_remove', k_m_bool)
        self.src_df = dst_df.drop(columns=['is_remove'])

    def clear(self):
        print("clear()")

    def on_ok(self):
        self.dst_df = self.src_df
        if "proc_history" not in self.src_attrs.keys():
            self.src_attrs["proc_history"] = []
        self.src_attrs["proc_history"].append("area_filter")
        self.dst_df['attrs'] = self.src_attrs
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
