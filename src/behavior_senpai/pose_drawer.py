import os
import random
import tomllib

import cv2
import numpy as np
import torch

from behavior_senpai import img_draw
from gui_parts import TempFile


class Annotate:
    def __init__(self, kp_toml_name=None):
        temp = TempFile()
        self.draw_mask = temp.get_draw_mask()
        toml_path = os.path.join(os.path.dirname(__file__), "..", "keypoint", kp_toml_name)
        with open(toml_path, "rb") as f:
            self.data = tomllib.load(f)

    def set_pose(self, kps):
        self.keypoints = {}
        self.keypoint_colors = {}
        self.keypoint_scores = {}
        self.bones = self.data["bones"]["bones"]
        for key, val in self.data["keypoints"].items():
            self.keypoints[key], self.keypoint_scores[key] = self._cvt_kp(kps, val["id"])
            self.keypoint_colors[key] = val["color"]
        self.line_color = (random.randint(180, 250), random.randint(180, 250), random.randint(180, 250))
        self.label_keypoints = self.data["draw"]["labels"]
        self.mask_points = self.data["draw"]["mask"]
        self.draw_threshold = self.data["bones"]["threshold"]

    def set_track(self, trk):
        if self.keypoints[self.label_keypoints[0]] != (0, 0):
            self.pos = self.keypoints[self.label_keypoints[0]]
        else:
            self.pos = self.keypoints[self.label_keypoints[1]]
        self.id = trk

    def set_img(self, src_img):
        self.dst_img = src_img.copy()

    def draw(self):
        # draw mask
        if self.draw_mask:
            center_x = [self.keypoints[key][0] for key in self.mask_points if self.keypoints[key][0] != 0]
            center_y = [self.keypoints[key][1] for key in self.mask_points if self.keypoints[key][1] != 0]
            center = (int(sum(center_x) / len(center_x)), int(sum(center_y) / len(center_y)))
            size = max(max(center_x) - min(center_x), max(center_y) - min(center_y))
            img_draw.mosaic(self.dst_img, center, size)

        for bone in self.bones:
            score_a = self.keypoint_scores[bone[0]]
            score_b = self.keypoint_scores[bone[1]]
            if score_a > self.draw_threshold and score_b > self.draw_threshold:
                img_draw.draw_line(self.dst_img, self.keypoints[bone[0]], self.keypoints[bone[1]], self.line_color, 1)

        for key, val in self.keypoints.items():
            if val[0] != 0 and val[1] != 0:
                cv2.circle(self.dst_img, val, 3, self.keypoint_colors[key], -1)

        # draw label
        cv2.putText(self.dst_img, str(self.id), [self.pos[0] - 10, self.pos[1] - 35], cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.line(self.dst_img, self.pos, (self.pos[0], self.pos[1] - 25), (50, 50, 255), 1, cv2.LINE_AA)
        return self.dst_img

    def _cvt_kp(self, kp, idx):
        x = kp[idx][0]
        y = kp[idx][1]
        if isinstance(x, torch.Tensor):
            x = x.cpu()
            y = y.cpu()
        if np.isnan(x) or np.isnan(y):
            return (0, 0), 0
        return (int(kp[idx][0]), int(kp[idx][1])), kp[idx][2]


def yolo_draw(src_img, result):
    anno = Annotate("coco17.toml")
    anno.set_img(src_img)
    result_keypoints = result[0].keypoints.data
    result_boxes = result[0].boxes.data
    dst_img = src_img
    for keypoints, boxes in zip(result_keypoints, result_boxes, strict=False):
        member = int(boxes[4])
        anno.set_pose(keypoints)
        anno.set_track(member)
        dst_img = anno.draw()
    return dst_img
