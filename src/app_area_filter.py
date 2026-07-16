import operator
import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk

from behavior_senpai import df_attrs, keypoint_toml_loader, keypoints_proc
from gui_parts import Combobox, TempFile


class App(ttk.Frame):
    """Application for removing keypoints."""

    def __init__(self, master, args):
        super().__init__(master)
        master.title("Remove Keypoints")
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
        control_frame.pack(fill=tk.X, pady=(0, 20), side=tk.TOP)
        param_frame = ttk.Frame(control_frame)
        param_frame.pack(side=tk.LEFT, anchor=tk.W)

        # score_threshold
        low_score_frame = ttk.Frame(param_frame)
        low_score_frame.pack(side=tk.TOP, anchor=tk.W)
        self.low_score_var = tk.BooleanVar()
        self.low_score_checkbox = ttk.Checkbutton(low_score_frame, text="Low Score", variable=self.low_score_var)
        self.low_score_checkbox.pack(side=tk.LEFT)
        threshold_label = ttk.Label(low_score_frame, text="Less than:")
        threshold_label.pack(side=tk.LEFT, padx=(10, 0))
        self.score_threshold_var = tk.DoubleVar()
        threshold_entry = ttk.Entry(low_score_frame, textvariable=self.score_threshold_var, width=10)
        threshold_entry.pack(side=tk.LEFT)

        # keypoint groups
        keypoint_group_frame = ttk.Frame(param_frame)
        keypoint_group_frame.pack(side=tk.TOP, anchor=tk.W, pady=(5, 5))
        self.head_check_var = tk.BooleanVar(value=False)
        self.face_check_var = tk.BooleanVar(value=False)
        self.body_check_var = tk.BooleanVar(value=False)
        self.arm_check_var = tk.BooleanVar(value=False)
        self.leg_check_var = tk.BooleanVar(value=False)
        self.hand_check_var = tk.BooleanVar(value=False)
        head_check = ttk.Checkbutton(keypoint_group_frame, text="Head", variable=self.head_check_var)
        head_check.pack(side=tk.LEFT)
        self.face_check = ttk.Checkbutton(keypoint_group_frame, text="Face", variable=self.face_check_var)
        self.face_check.pack(side=tk.LEFT)
        body_check = ttk.Checkbutton(keypoint_group_frame, text="Body", variable=self.body_check_var)
        body_check.pack(side=tk.LEFT)
        arm_check = ttk.Checkbutton(keypoint_group_frame, text="Arms", variable=self.arm_check_var)
        arm_check.pack(side=tk.LEFT, padx=(10, 0))
        leg_check = ttk.Checkbutton(keypoint_group_frame, text="Legs", variable=self.leg_check_var)
        leg_check.pack(side=tk.LEFT, padx=(10, 0))
        self.hand_check = ttk.Checkbutton(keypoint_group_frame, text="Hands", variable=self.hand_check_var)
        self.hand_check.pack(side=tk.LEFT, padx=(10, 0))

        # area
        area_frame = ttk.Frame(param_frame)
        area_frame.pack(side=tk.TOP, anchor=tk.W)
        self.area_var = tk.BooleanVar()
        area_check = ttk.Checkbutton(area_frame, text="Area", variable=self.area_var)
        area_check.pack(side=tk.LEFT)
        vals = ("only keypoints", "member")
        self.keypoint_member_combo = Combobox(area_frame, "Target:", values=vals, width=18)
        self.keypoint_member_combo.pack_horizontal(padx=5)
        vals = ("within area", "outside area")
        self.in_out_combo = Combobox(area_frame, "", values=vals, width=18)
        self.in_out_combo.pack_horizontal(padx=5)

        calc_button = ttk.Button(area_frame, text="Remove", command=self.exec_remove)
        calc_button.pack(side=tk.LEFT, padx=(10, 0))

        ok_frame = ttk.Frame(control_frame)
        ok_frame.pack(anchor=tk.NE, padx=(20, 0))
        self.ok_btn = ttk.Button(ok_frame, text="OK", command=self.on_ok, state=tk.DISABLED)
        self.ok_btn.pack(pady=(0, 5))
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

    #        self._add_rotate_button(control_frame)

    def _load(self, args):
        self.src_df = args["src_df"].copy()
        self.cap = args["cap"]
        current_position = args["current_position"]
        src_attrs = df_attrs.DfAttrs(self.src_df)

        ratio = src_attrs.get_ratio()
        width = int(self.height * ratio)
        self.scale = width / src_attrs.get_width()
        self.canvas.config(width=width, height=self.height)
        self.model_name = src_attrs.get_model_name()
        ok, image_rgb = self.cap.read_at(current_position, scale=self.scale, rgb=True)
        if ok is False:
            return
        image_pil = Image.fromarray(image_rgb)
        self.image_pil = image_pil
        self.image_tk = ImageTk.PhotoImage(image_pil)
        if self.img_on_canvas is None:
            self.img_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)
        else:
            self.canvas.itemconfig(self.img_on_canvas, image=self.image_tk)

        self.kp_loader = keypoint_toml_loader.KeypointTOMLLoader()
        self.kp_loader.open_toml_by_model_name(self.model_name)

        # 画像の回転状態を反映
        if hasattr(self, "image_pil") and self.img_on_canvas is not None:
            self._update_canvas_image()

    def _update_canvas_image(self):
        """attrs['rotate']の値に応じてself.image_pilを回転し、canvasに反映"""
        angle = self.src_df.attrs.get("rotate", 0)
        img = self.image_pil
        if angle == 90:
            img = img.transpose(Image.ROTATE_270)
        elif angle == 180:
            img = img.transpose(Image.ROTATE_180)
        elif angle == 270:
            img = img.transpose(Image.ROTATE_90)
        w, h = img.size
        self.image_tk = ImageTk.PhotoImage(img)
        self.canvas.config(width=w, height=h)
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

    def exec_remove(self):
        keypoint_groups = []
        if self.head_check_var.get():
            keypoint_groups.append("head")
        if self.face_check_var.get():
            keypoint_groups.append("face")
        if self.body_check_var.get():
            keypoint_groups.append("body")
        if self.arm_check_var.get():
            keypoint_groups.append("arms")
        if self.leg_check_var.get():
            keypoint_groups.append("legs")
        if self.hand_check_var.get():
            keypoint_groups.append("hands")
        if len(keypoint_groups) > 0:
            self.remove_keypoint_group(keypoint_groups)

        if self.low_score_var.get():
            self.filter_low()
        if self.area_var.get():
            self.calc_in_out()

        self.draw_convex_hull()
        self.ok_btn.config(state=tk.NORMAL)

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

    def filter_low(self):
        """Filter out the keypoints with low confidence or score."""
        low_thresh = self.score_threshold_var.get()
        # numeric check
        try:
            low_thresh = float(low_thresh)
        except ValueError:
            print("Invalid threshold value")
            return
        if low_thresh <= 0:
            return

        if self.model_name in ["RTMW-x WholeBody133", "MMPose RTMPose-x", "RTMPose-x Halpe26", "RTMPose-x WholeBody133"]:
            col = "score"
        elif self.model_name in ["YOLOv8 x-pose-p6", "YOLO11 x-pose"]:
            col = "conf"
        elif self.model_name in ["DeepLabCut"]:
            col = "likelihood"
        else:
            print(f"Unsupported model: {self.model_name}")
            return
        self.src_df.loc[self.src_df[col] < low_thresh, ["x", "y"]] = np.nan

    def remove_keypoint_group(self, group_names: list):
        idx_list = self.kp_loader.get_keypoint_idx_by_groups(group_names)
        print(f"Removing keypoints with indices: {idx_list}")

        # Mediapipe Holisticはmember(face, pose, left_hand, right_hand)ごとにkeypoint indexが異なる
        if self.model_name == "MediaPipe Holistic":
            grp = set(group_names)
            if {"head", "body", "arms", "legs"} & grp:
                self.src_df.loc[pd.IndexSlice[:, "pose", idx_list], ["x", "y"]] = np.nan
            if "hands" in grp:
                self.src_df.loc[pd.IndexSlice[:, ["left_hand", "right_hand"], range(21)], ["x", "y"]] = np.nan
            if "face" in grp:
                self.src_df.loc[pd.IndexSlice[:, "face", range(468)], ["x", "y"]] = np.nan
        else:
            # multiindex frame, member keypoints
            self.src_df.loc[self.src_df.index.get_level_values("keypoint").isin(idx_list), ["x", "y"]] = np.nan

    def on_ok(self):
        """Perform the action when the 'OK' button is clicked."""
        self.dst_df = self.src_df.copy()
        self.dst_df.attrs = self.src_df.attrs.copy()
        print(self.dst_df.attrs)
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

    def _add_rotate_button(self, parent):
        rotate_frame = ttk.Frame(parent)
        rotate_frame.pack(side=tk.LEFT, padx=(10, 0))
        rotate_cw_btn = ttk.Button(rotate_frame, text="Rotate CW", command=self.rotate_cw)
        rotate_cw_btn.pack(side=tk.LEFT)

    def rotate_cw(self):
        """CW方向に90度回転。attrs['rotate']を0→90→180→270→0で更新し、画像・座標も回転。"""
        # 現在の回転角度を取得
        angle = self.src_df.attrs.get("rotate", 0)
        new_angle = (angle + 90) % 360
        self._apply_rotation(new_angle)

    def _apply_rotation(self, new_angle):
        """指定した角度(new_angle: 0,90,180,270)にself.src_df, self.image_pil, frame_sizeを揃える"""
        # 現在の角度
        current_angle = self.src_df.attrs.get("rotate", 0)
        # 差分回転回数
        diff = (new_angle - current_angle) % 360
        if diff == 0:
            return  # 変化なし
        # frame_size取得
        w, h = self.src_df.attrs.get("frame_size", (None, None))
        if w is None or h is None:
            print("frame_size not found in attrs")
            return
        # x, y座標をdiff回転
        for _ in range(diff // 90):
            x = self.src_df["x"].copy()
            y = self.src_df["y"].copy()
            self.src_df["x"] = h - y
            self.src_df["y"] = x
            w, h = h, w
        self.src_df.attrs["frame_size"] = (w, h)
        self.src_df.attrs["rotate"] = new_angle
        # 画像も回転
        if hasattr(self, "image_pil") and self.img_on_canvas is not None:
            self._update_canvas_image()
        self.draw_convex_hull()

    def close(self):
        pass
