import os
import random

import cv2
import numpy as np
import pandas as pd


class Annotate:
    def set_pose(self, kps):
        self.kps = [(int(kps[i][0]), int(kps[i][1])) if ~np.isnan(kps[i][0]) else (0, 0) for i in range(len(kps))]
        self.line_color = (random.randint(180, 250), random.randint(180, 250), random.randint(180, 250))

    def set_track(self, member):
        self.member = member

    def set_img(self, src_img):
        self.dst_img = src_img

    def draw(self):
        if self.member in ["right_hand", "left_hand"]:
            cv2.line(self.dst_img, self.kps[0], self.kps[5], self.line_color, 1, cv2.LINE_AA)
            cv2.line(self.dst_img, self.kps[5], self.kps[9], self.line_color, 1, cv2.LINE_AA)
            cv2.line(self.dst_img, self.kps[9], self.kps[13], self.line_color, 1, cv2.LINE_AA)
            cv2.line(self.dst_img, self.kps[13], self.kps[17], self.line_color, 1, cv2.LINE_AA)
            cv2.line(self.dst_img, self.kps[17], self.kps[0], self.line_color, 1, cv2.LINE_AA)
        for i in range(len(self.kps)):
            if self.member in ["right_hand", "left_hand"]:
                cv2.circle(self.dst_img, self.kps[i], 2, (50, 250, 50), -1)
            elif self.member == "face":
                cv2.circle(self.dst_img, self.kps[i], 1, (150, 50, 150), -1)
            else:
                cv2.circle(self.dst_img, self.kps[i], 1, (150, 50, 150), -1)

        return self.dst_img


if __name__ == "__main__":
    video_path = "cup.mp4"
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    pkl_path = f"trk/{file_name}.pkl"

    # MP4の読み込み
    cap = cv2.VideoCapture(video_path)

    # さっきの結果の読み込み
    src_df = pd.read_pickle(pkl_path)
    total_frame_num = src_df.index.unique(level='frame').max() + 1
    print(src_df.attrs)

    anno = Annotate()

    frame_num_list = src_df.index.unique(level='frame')

    for i in range(int(total_frame_num)):
        ret, frame = cap.read()
        anno.set_img(frame)

        members = src_df.loc[pd.IndexSlice[i, :, :], :].index.unique(level='member')
        for member in members:
            keypoints = src_df.loc[pd.IndexSlice[i, member, :], :]
            kp_ids = keypoints.index.unique(level='keypoint')
            kps = keypoints.to_numpy()
            anno.set_pose(kps)
            anno.set_track(member)

            dst_img = anno.draw(member)
        cv2.imshow("dst", dst_img)
        if i == 0:
            cv2.waitKey(0)
        else:
            cv2.waitKey(30) 
