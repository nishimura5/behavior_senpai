import os

import cv2
import mediapipe as mp
import pandas as pd


class MediaPipeDetector:
    def __init__(self, cap):
        self.cap = cap
        self.model = mp.solutions.holistic.Holistic(model_complexity=2, refine_face_landmarks=True)

        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.number_of_keypoints = {'face': 468, 'right_hand': 21, 'left_hand': 21}

    def detect(self):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "z": [], "timestamp": []}
        for i in range(self.total_frame_num):
            ret, frame = self.cap.read()
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.model.process(rgb_img)

            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果の取り出し
            member_ids = ['face', 'right_hand', 'left_hand']
            for member_id in member_ids:
                keypoints = getattr(results, f'{member_id}_landmarks').landmark
                if keypoints is None:
                    continue
                for k in range(self.number_of_keypoints[member_id]):
                    keypoint_id = k
                    x = float(keypoints[k].x * self.frame_width)
                    y = float(keypoints[k].y * self.frame_height)
                    z = float(keypoints[k].z * self.frame_width)

                    # データの詰め込み
                    data_dict["frame"].append(i)
                    data_dict["member"].append(member_id)
                    data_dict["keypoint"].append(keypoint_id)
                    data_dict["x"].append(x)
                    data_dict["y"].append(y)
                    data_dict["z"].append(z)
                    data_dict["timestamp"].append(timestamp)

        self.dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])

    def get_result(self):
        return self.dst_df


if __name__ == "__main__":
    video_path = "cup.mp4"
    file_name = os.path.splitext(os.path.basename(video_path))[0]

    cap = cv2.VideoCapture(video_path)
    detector = MediaPipeDetector(cap)
    detector.detect()
    result_df = detector.get_result()
    result_df.attrs["model"] = "MediaPipe Holistic"

    pkl_path = f"{file_name}.pkl"
    result_df.to_pickle(pkl_path)
