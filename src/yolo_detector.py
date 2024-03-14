import cv2
from ultralytics import YOLO
import pandas as pd

import yolo_drawer
from python_senpai import img_draw
from python_senpai import vcap


class YoloDetector:
    def __init__(self, show=True):
        self.model = YOLO(model="yolov8x-pose-p6.pt")

        self.number_of_keypoints = 17
        self.show = show

    def set_cap(self, cap):
        self.cap = cap
        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def detect(self, roi=False):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "conf": [], "timestamp": []}
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()

            result = self.model.track(frame, verbose=False, persist=True, classes=0)
            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果を描画、xキーで途中終了
            if self.show is True:
                anno_img = yolo_drawer.draw(frame, result)
                _, anno_img = vcap.resize_frame(anno_img)
                img_draw.put_frame_pos(anno_img, i, self.total_frame_num)
                img_draw.put_message(frame, "'x' key to exit.", font_size=1.5, y=55)
                cv2.imshow("dst", anno_img)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('x'):
                    break

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

        # memberとkeypointはここではintで保持する、indexでソートしたくなるかもしれないので
        self.dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
        cv2.destroyAllWindows()

    def get_result(self):
        return self.dst_df


def detect_from_picture(src_path):
    src_img = cv2.imread(src_path)

    model = YOLO(model="yolov8x-pose-p6.pt")
    result = model.track(src_img, verbose=False, persist=True, classes=0)

    anno_img = yolo_drawer.draw(src_img, result)
    cv2.imshow("dst", anno_img)
    cv2.waitKey(0)
