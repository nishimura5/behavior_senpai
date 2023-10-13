import os

import cv2
import pandas as pd


class Annotate:
    def set_keypoints(self, kps):
        self.kps = [(int(kps[i][0]), int(kps[i][1])) for i in range(len(kps))]

    def set_img(self, src_img):
        self.dst_img = src_img

    def draw(self, member):
        for i in range(len(self.kps)):
            if member == "right_hand":
                cv2.circle(self.dst_img, self.kps[i], 3, (50, 250, 50), -1)
            elif member == "left_hand":
                cv2.circle(self.dst_img, self.kps[i], 3, (250, 70, 70), -1)
            else:
                cv2.circle(self.dst_img, self.kps[i], 1, (50, 50, 250), -1)

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
            anno.set_keypoints(kps)

            dst_img = anno.draw(member)
        cv2.imshow("dst", dst_img)
        if i == 0:
            cv2.waitKey(0)
        else:
            cv2.waitKey(30) 
