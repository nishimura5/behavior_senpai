import random

import cv2
import numpy as np
import torch

from behavior_senpai import img_draw


class Annotate:
    def set_pose(self, kps):
        self.nose, self.nose_score = self._cvt_kp(kps, 0)
        self.left_eye, self.nose_score = self._cvt_kp(kps, 1)
        self.right_eye, self.nose_score = self._cvt_kp(kps, 2)
        self.left_ear, self.nose_score = self._cvt_kp(kps, 3)
        self.right_ear, self.nose_score = self._cvt_kp(kps, 4)
        self.left_shoulder, self.left_shoulder_score = self._cvt_kp(kps, 5)
        self.right_shoulder, self.right_shoulder_score = self._cvt_kp(kps, 6)
        self.left_elbow, self.left_elbow_score = self._cvt_kp(kps, 7)
        self.right_elbow, self.right_elbow_score = self._cvt_kp(kps, 8)
        self.left_wrist, self.left_wrist_score = self._cvt_kp(kps, 9)
        self.right_wrist, self.right_wrist_score = self._cvt_kp(kps, 10)
        self.left_hip, self.left_hip_score = self._cvt_kp(kps, 11)
        self.right_hip, self.right_hip_score = self._cvt_kp(kps, 12)
        self.left_knee, self.left_knee_score = self._cvt_kp(kps, 13)
        self.right_knee, self.right_knee_score = self._cvt_kp(kps, 14)
        self.left_ankle, self.left_ankle_score = self._cvt_kp(kps, 15)
        self.right_ankle, self.right_ankle_score = self._cvt_kp(kps, 16)
        self.head, self.head_score = self._cvt_kp(kps, 17)
        self.neck, self.neck_score = self._cvt_kp(kps, 18)
        self.hip, self.hip_score = self._cvt_kp(kps, 19)
        self.left_big_toe, self.left_big_toe_score = self._cvt_kp(kps, 20)
        self.right_big_toe, self.right_big_toe_score = self._cvt_kp(kps, 21)
        self.left_small_toe, self.left_small_toe_score = self._cvt_kp(kps, 22)
        self.right_small_toe, self.right_small_toe_score = self._cvt_kp(kps, 23)
        self.left_heel, self.left_heel_score = self._cvt_kp(kps, 24)
        self.right_heel, self.right_heel_score = self._cvt_kp(kps, 25)
        self.line_color = (random.randint(180, 250), random.randint(180, 250), random.randint(180, 250))

    def set_track(self, trk):
        if self.head[0] != 0 and self.head[1] != 0:
            self.pos = self.head
        else:
            self.pos = self.right_shoulder
        self.id = trk

    def set_img(self, src_img):
        self.dst_img = src_img.copy()

    # poseを描画
    def draw(self):
        thresh = 0.4
        center_color = (40, 40, 255)
        left_color = (250, 70, 70)
        right_color = (50, 250, 50)

        img_draw.draw_line(self.dst_img, self.left_shoulder, self.neck, self.line_color, 1)
        img_draw.draw_line(self.dst_img, self.neck, self.right_shoulder, self.line_color, 1)
        img_draw.draw_line(self.dst_img, self.left_shoulder, self.left_hip, self.line_color, 1)
        img_draw.draw_line(self.dst_img, self.right_shoulder, self.right_hip, self.line_color, 1)
        img_draw.draw_line(self.dst_img, self.left_hip, self.hip, self.line_color, 1)
        img_draw.draw_line(self.dst_img, self.hip, self.right_hip, self.line_color, 1)
        if self.left_shoulder_score > thresh and self.left_elbow_score > thresh:
            img_draw.draw_line(self.dst_img, self.left_shoulder, self.left_elbow, self.line_color, 1)
            img_draw.draw_line(self.dst_img, self.left_elbow, self.left_wrist, self.line_color, 1)
        if self.right_shoulder_score > thresh and self.right_elbow_score > thresh:
            img_draw.draw_line(self.dst_img, self.right_shoulder, self.right_elbow, self.line_color, 1)
            img_draw.draw_line(self.dst_img, self.right_elbow, self.right_wrist, self.line_color, 1)
        if self.left_hip_score > thresh and self.left_knee_score > thresh:
            img_draw.draw_line(self.dst_img, self.left_hip, self.left_knee, self.line_color, 1)
            img_draw.draw_line(self.dst_img, self.left_knee, self.left_ankle, self.line_color, 1)
        if self.right_hip_score > thresh and self.right_knee_score > thresh:
            img_draw.draw_line(self.dst_img, self.right_hip, self.right_knee, self.line_color, 1)
            img_draw.draw_line(self.dst_img, self.right_knee, self.right_ankle, self.line_color, 1)

        cv2.circle(self.dst_img, self.left_eye, 3, left_color, -1)
        cv2.circle(self.dst_img, self.left_shoulder, 3, left_color, -1)
        cv2.circle(self.dst_img, self.right_eye, 3, right_color, -1)
        cv2.circle(self.dst_img, self.right_shoulder, 3, right_color, -1)
        cv2.circle(self.dst_img, self.left_hip, 3, left_color, -1)
        cv2.circle(self.dst_img, self.right_hip, 3, right_color, -1)
        cv2.circle(self.dst_img, self.neck, 3, center_color, -1)
        cv2.circle(self.dst_img, self.hip, 3, center_color, -1)
        cv2.circle(self.dst_img, self.left_heel, 2, left_color, -1)
        cv2.circle(self.dst_img, self.left_big_toe, 2, left_color, -1)
        cv2.circle(self.dst_img, self.left_small_toe, 2, left_color, -1)
        cv2.circle(self.dst_img, self.right_heel, 2, right_color, -1)
        cv2.circle(self.dst_img, self.right_big_toe, 2, right_color, -1)
        cv2.circle(self.dst_img, self.right_small_toe, 2, right_color, -1)

        if self.right_ankle_score > thresh:
            cv2.circle(self.dst_img, self.left_ankle, 3, left_color, -1)
        if self.right_ankle_score > thresh:
            cv2.circle(self.dst_img, self.right_ankle, 3, right_color, -1)

        # トラッキングIDを描画
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
