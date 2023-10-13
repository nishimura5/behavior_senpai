import cv2
from ultralytics import YOLO
import pandas as pd


class YoloDetector:
    def __init__(self, cap, show=True):
        self.cap = cap
        self.model = YOLO(model="yolov8x-pose-p6.pt")

        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.number_of_keypoints = 17
        self.show = show

    def detect(self, roi=False):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "conf": [], "timestamp": []}
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()
            result = self.model.track(frame, verbose=False, persist=True, classes=0, show=self.show)

            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果の取り出し
            result_keypoints = result[0].keypoints.data
            result_boxes = result[0].boxes.data
            for keypoints, boxes in zip(result_keypoints, result_boxes):
                member_id = int(boxes[4])
                for k in range(self.number_of_keypoints):
                    keypoint_id = k
                    x = float(keypoints[k][0])
                    y = float(keypoints[k][1])
                    if roi is True:
                        x += self.cap.left_top_point[0]
                        y += self.cap.left_top_point[1]
                    conf = float(keypoints[k][2])

                    # データの詰め込み
                    data_dict["frame"].append(i)
                    data_dict["member"].append(member_id)
                    data_dict["keypoint"].append(keypoint_id)
                    data_dict["x"].append(x)
                    data_dict["y"].append(y)
                    data_dict["conf"].append(conf)
                    data_dict["timestamp"].append(timestamp)

        self.dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
        cv2.destroyAllWindows()

    def get_result(self):
        return self.dst_df
