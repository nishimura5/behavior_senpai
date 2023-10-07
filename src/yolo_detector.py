import os

import cv2
from ultralytics import YOLO
import pandas as pd

video_path = "taiso.mp4"
file_name = os.path.splitext(os.path.basename(video_path))[0]
pkl_path = f"{file_name}.pkl"

cap = cv2.VideoCapture(video_path)
model = YOLO(model="yolov8x-pose-p6.pt")

total_frame_num = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

number_of_keypoints = 17
# データの初期化
data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "conf": [], "timestamp": []}
for i in range(total_frame_num):
    ret, frame = cap.read()
    result = model.track(frame, verbose=False, persist=True, classes=0, show=True)

    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)

    # 検出結果の取り出し
    result_keypoints = result[0].keypoints.data
    result_boxes = result[0].boxes.data
    for keypoints, boxes in zip(result_keypoints, result_boxes):
        member_id = int(boxes[4])
        for k in range(number_of_keypoints):
            keypoint_id = k
            x = float(keypoints[k][0])
            y = float(keypoints[k][1])
            conf = float(keypoints[k][2])

            # データの詰め込み
            data_dict["frame"].append(i)
            data_dict["member"].append(member_id)
            data_dict["keypoint"].append(keypoint_id)
            data_dict["x"].append(x)
            data_dict["y"].append(y)
            data_dict["conf"].append(conf)
            data_dict["timestamp"].append(timestamp)

dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
print(dst_df)
dst_df.attrs["model"] = "YOLOv8 x-pose-p6"
dst_df.to_pickle(pkl_path)
