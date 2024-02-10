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
            kps = [self.kps[0], self.kps[5], self.kps[9], self.kps[13], self.kps[17]]
            self.lines(kps, True)
            kps = [self.kps[0], self.kps[1], self.kps[2], self.kps[3], self.kps[4]]
            self.lines(kps, False)
            kps = [self.kps[5], self.kps[6], self.kps[7], self.kps[8]]
            self.lines(kps, False)
            kps = [self.kps[9], self.kps[10], self.kps[11], self.kps[12]]
            self.lines(kps, False)
            kps = [self.kps[13], self.kps[14], self.kps[15], self.kps[16]]
            self.lines(kps, False)
            kps = [self.kps[17], self.kps[18], self.kps[19], self.kps[20]]
            self.lines(kps, False)
        elif self.member == "face":
            kps = [self.kps[33], self.kps[7], self.kps[163], self.kps[144], self.kps[145], self.kps[153], self.kps[154], self.kps[155], self.kps[133], self.kps[173], self.kps[157], self.kps[158], self.kps[159], self.kps[160], self.kps[161], self.kps[246]]
            self.lines(kps, True)
            kps = [self.kps[263], self.kps[249], self.kps[390], self.kps[373], self.kps[374], self.kps[380], self.kps[381], self.kps[382], self.kps[362], self.kps[398], self.kps[384], self.kps[385], self.kps[386], self.kps[387], self.kps[388], self.kps[466]]
            self.lines(kps, True)
            kps = [self.kps[13], self.kps[312], self.kps[311], self.kps[310], self.kps[415], self.kps[308], self.kps[324], self.kps[318], self.kps[402], self.kps[317], self.kps[14], self.kps[87], self.kps[178], self.kps[88], self.kps[95], self.kps[78], self.kps[191], self.kps[80], self.kps[81], self.kps[82]]
            self.lines(kps, True)
            kps = [self.kps[0], self.kps[267], self.kps[269], self.kps[270], self.kps[409], self.kps[291], self.kps[375], self.kps[321], self.kps[405], self.kps[314], self.kps[17], self.kps[84], self.kps[181], self.kps[91], self.kps[146], self.kps[61], self.kps[185], self.kps[40], self.kps[39], self.kps[37]]
            self.lines(kps, True)
            kps = [self.kps[10], self.kps[151], self.kps[9], self.kps[8], self.kps[168], self.kps[6], self.kps[197], self.kps[195], self.kps[5], self.kps[4], self.kps[1], self.kps[19], self.kps[94], self.kps[2], self.kps[164], self.kps[0]]
            self.lines(kps, False)
            kps = [self.kps[17], self.kps[18], self.kps[200], self.kps[175], self.kps[152]]
            self.lines(kps, False)
            kps = [self.kps[129], self.kps[209], self.kps[198], self.kps[236], self.kps[3], self.kps[195], self.kps[248], self.kps[456], self.kps[420], self.kps[429], self.kps[358]]
            self.lines(kps, False)
            kps = [self.kps[98], self.kps[64], self.kps[48], self.kps[115], self.kps[220], self.kps[45], self.kps[4], self.kps[275], self.kps[440], self.kps[344], self.kps[278], self.kps[294], self.kps[327]]
            self.lines(kps, False)
#            kps = [self.kps[238], self.kps[20], self.kps[60], self.kps[75], self.kps[59], self.kps[166], self.kps[79], self.kps[239]]
#            self.lines(kps, True)
#            kps = [self.kps[458], self.kps[250], self.kps[290], self.kps[305], self.kps[289], self.kps[392], self.kps[309], self.kps[459]]
#            self.lines(kps, True)
        for i in range(len(self.kps)):
            if self.member == "left_hand":
                cv2.circle(self.dst_img, self.kps[i], 2, (250, 70, 70), -1)
            elif self.member == "right_hand":
                cv2.circle(self.dst_img, self.kps[i], 2, (50, 250, 50), -1)
#            elif self.member == "face":
#                cv2.circle(self.dst_img, self.kps[i], 1, (150, 50, 150), -1)
#            else:
#                cv2.circle(self.dst_img, self.kps[i], 1, (150, 50, 150), -1)

        return self.dst_img

    def lines(self, kps, close):
        pts = np.array(kps, np.int32)
        pts = np.reshape(pts, (-1, 1, 2))
        cv2.polylines(self.dst_img, [pts], close, self.line_color, 1, cv2.LINE_AA)

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
