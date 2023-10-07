import os

import cv2
import mediapipe as mp
import pandas as pd

video_path = "cup.mp4"
file_name = os.path.splitext(os.path.basename(video_path))[0]
pkl_path = f"{file_name}.pkl"

cap = cv2.VideoCapture(video_path)
mp_holistic = mp.solutions.holistic.Holistic(model_complexity=2, refine_face_landmarks=True)

total_frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

number_of_keypoints = {'face': 468, 'right_hand': 21, 'left_hand': 21}
# データの初期化
data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "z": [], "timestamp": []}
for i in range(total_frame_num):
    ret, frame = cap.read()
    rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_holistic.process(rgb_img)

    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)

    # 検出結果の取り出し
    member_ids = ['face', 'right_hand', 'left_hand']
    for member_id in member_ids:
        keypoints = getattr(results, f'{member_id}_landmarks').landmark
        if keypoints is None:
            continue
        for k in range(number_of_keypoints[member_id]):
            keypoint_id = k
            x = float(keypoints[k].x * frame_width)
            y = float(keypoints[k].y * frame_height)
            z = float(keypoints[k].z * frame_width)

            # データの詰め込み
            data_dict["frame"].append(i)
            data_dict["member"].append(member_id)
            data_dict["keypoint"].append(keypoint_id)
            data_dict["x"].append(x)
            data_dict["y"].append(y)
            data_dict["z"].append(z)
            data_dict["timestamp"].append(timestamp)

dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
print(dst_df)
dst_df.attrs["model"] = "MediaPipe Holistic"
dst_df.to_pickle(pkl_path)
