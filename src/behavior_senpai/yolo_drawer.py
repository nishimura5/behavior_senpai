import os
import random

import cv2
import numpy as np
import pandas as pd
import torch

from behavior_senpai import img_draw


def draw(src_img, result):
    anno = Annotate()
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


class Annotate:
    def set_pose(self, kps):
        self.nose, self.nose_conf = self._cvt_kp(kps, 0)
        self.left_eye, self.nose_conf = self._cvt_kp(kps, 1)
        self.right_eye, self.nose_conf = self._cvt_kp(kps, 2)
        self.left_ear, self.nose_conf = self._cvt_kp(kps, 3)
        self.right_ear, self.nose_conf = self._cvt_kp(kps, 4)
        self.left_shoulder, self.left_shoulder_conf = self._cvt_kp(kps, 5)
        self.right_shoulder, self.right_shoulder_conf = self._cvt_kp(kps, 6)
        self.left_elbow, self.left_elbow_conf = self._cvt_kp(kps, 7)
        self.right_elbow, self.right_elbow_conf = self._cvt_kp(kps, 8)
        self.left_wrist, self.left_wrist_conf = self._cvt_kp(kps, 9)
        self.right_wrist, self.right_wrist_conf = self._cvt_kp(kps, 10)
        self.left_hip, self.left_hip_conf = self._cvt_kp(kps, 11)
        self.right_hip, self.right_hip_conf = self._cvt_kp(kps, 12)
        self.left_knee, self.left_knee_conf = self._cvt_kp(kps, 13)
        self.right_knee, self.right_knee_conf = self._cvt_kp(kps, 14)
        self.left_ankle, self.left_ankle_conf = self._cvt_kp(kps, 15)
        self.right_ankle, self.right_ankle_conf = self._cvt_kp(kps, 16)
        self.line_color = (random.randint(180, 250), random.randint(180, 250), random.randint(180, 250))

    def set_track(self, trk):
        if self.nose[0] != 0 and self.nose[1] != 0:
            self.pos = self.nose
        elif self.left_ear[0] != 0 and self.left_ear[1] != 0 and self.right_ear[0] != 0 and self.right_ear[1] != 0:
            self.pos = ((self.left_ear[0] + self.right_ear[0]) // 2, (self.left_ear[1] + self.right_ear[1]) // 2)
        elif self.left_ear[0] != 0 and self.left_ear[1] != 0:
            self.pos = self.left_ear
        elif self.right_ear[0] != 0 and self.right_ear[1] != 0:
            self.pos = self.right_ear
        else:
            self.pos = self.right_shoulder
        self.id = trk

    def set_img(self, src_img):
        self.dst_img = src_img.copy()

    def mosaic(self, size):
        self.dst_img = img_draw.mosaic(self.dst_img, self.pos, size)
        return self.dst_img

    # poseを描画
    def draw(self):
        thresh = 0.4
        left_color = (250, 70, 70)
        right_color = (50, 250, 50)

        self._draw_line(self.left_shoulder, self.right_shoulder, self.line_color, 1)
        self._draw_line(self.left_shoulder, self.left_hip, self.line_color, 1)
        self._draw_line(self.right_shoulder, self.right_hip, self.line_color, 1)
        self._draw_line(self.left_hip, self.right_hip, self.line_color, 1)
        if self.left_shoulder_conf > thresh and self.left_elbow_conf > thresh:
            self._draw_line(self.left_shoulder, self.left_elbow, self.line_color, 1)
            self._draw_line(self.left_elbow, self.left_wrist, self.line_color, 1)
        if self.right_shoulder_conf > thresh and self.right_elbow_conf > thresh:
            self._draw_line(self.right_shoulder, self.right_elbow, self.line_color, 1)
            self._draw_line(self.right_elbow, self.right_wrist, self.line_color, 1)
        if self.left_hip_conf > thresh and self.left_knee_conf > thresh:
            self._draw_line(self.left_hip, self.left_knee, self.line_color, 1)
            self._draw_line(self.left_knee, self.left_ankle, self.line_color, 1)
        if self.right_hip_conf > thresh and self.right_knee_conf > thresh:
            self._draw_line(self.right_hip, self.right_knee, self.line_color, 1)
            self._draw_line(self.right_knee, self.right_ankle, self.line_color, 1)

        cv2.circle(self.dst_img, self.left_eye, 3, left_color, -1)
        cv2.circle(self.dst_img, self.left_shoulder, 3, left_color, -1)
        cv2.circle(self.dst_img, self.right_eye, 3, right_color, -1)
        cv2.circle(self.dst_img, self.right_shoulder, 3, right_color, -1)
        cv2.circle(self.dst_img, self.left_hip, 3, left_color, -1)
        cv2.circle(self.dst_img, self.right_hip, 3, right_color, -1)
        if self.left_ankle_conf > thresh:
            cv2.circle(self.dst_img, self.left_ankle, 3, left_color, -1)
        if self.right_ankle_conf > thresh:
            cv2.circle(self.dst_img, self.right_ankle, 3, right_color, -1)

        # トラッキングIDを描画
        cv2.putText(self.dst_img, str(self.id), [self.pos[0] - 10, self.pos[1] - 35], cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.line(self.dst_img, self.pos, (self.pos[0], self.pos[1] - 25), (50, 50, 255), 1, cv2.LINE_AA)
        return self.dst_img

    def _draw_line(self, start, end, color, thickness):
        if (start[0] == 0 and start[1] == 0) or (end[0] == 0 and end[1] == 0):
            return
        cv2.line(self.dst_img, start, end, color, thickness, cv2.LINE_AA)

    def _cvt_kp(self, kp, idx):
        x = kp[idx][0]
        y = kp[idx][1]
        if isinstance(x, torch.Tensor):
            x = x.cpu()
            y = y.cpu()
        if np.isnan(x) or np.isnan(y):
            return (0, 0), 0
        return (int(kp[idx][0]), int(kp[idx][1])), kp[idx][2]


if __name__ == "__main__":
    video_path = "manzai.mp4"
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    pkl_path = f"trk/{file_name}.pkl"

    # MP4の読み込み
    cap = cv2.VideoCapture(video_path)

    # さっきの結果の読み込み
    src_df = pd.read_pickle(pkl_path)
    total_frame_num = src_df.index.unique(level="frame").max() + 1
    print(src_df.attrs)

    anno = Annotate()

    for i in range(int(total_frame_num)):
        ret, frame = cap.read()
        anno.set_img(frame)

        members = src_df.loc[pd.IndexSlice[i, :, :], :].index.unique(level="member")
        for member in members:
            keypoints = src_df.loc[pd.IndexSlice[i, member, :], :]
            kps = keypoints.to_numpy()
            anno.set_pose(kps)
            anno.set_track(member)

            dst_img = anno.draw()
        cv2.imshow("dst", dst_img)
        if i == 0:
            cv2.waitKey(0)
        else:
            cv2.waitKey(30)
