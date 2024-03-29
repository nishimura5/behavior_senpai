import cv2
import mediapipe as mp
import pandas as pd


class MediaPipeDetector:
    def __init__(self, show=True):
        self.mph = mp.solutions.holistic
        self.model = self.mph.Holistic(model_complexity=2, refine_face_landmarks=True)

        self.number_of_keypoints = {'face': 478, 'right_hand': 21, 'left_hand': 21}
        self.show = show
        if self.show is True:
            self.drawing = mp.solutions.drawing_utils

    def set_cap(self, cap):
        self.cap = cap
        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def detect(self, roi=False):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "z": [], "timestamp": []}
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.model.process(rgb_img)
            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果を描画、xキーで途中終了
            if self.show is True:
                self._draw(frame, results)
                self._put_frame_pos(frame, i)
                cv2.imshow("dst", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('x'):
                    break

            # 検出結果の取り出し
            member_ids = ['face', 'right_hand', 'left_hand']
            for member_id in member_ids:
                landmarks = getattr(results, f'{member_id}_landmarks')
                if landmarks is None:
                    continue
                keypoints = landmarks.landmark

                for k in range(self.number_of_keypoints[member_id]):
                    keypoint_id = k
                    if roi is True:
                        x = float(keypoints[k].x * self.cap.roi_width + self.cap.left_top_point[0])
                        y = float(keypoints[k].y * self.cap.roi_height + self.cap.left_top_point[1])
                        z = float(keypoints[k].z * self.cap.roi_width)
                    else:
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

        # keypointはここではintで保持する、indexでソートしたくなるかもしれないので
        self.dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
        cv2.destroyAllWindows()

    def get_result(self):
        return self.dst_df

    def _draw(self, anno_img, results):
        self.drawing.draw_landmarks(
            anno_img,
            results.face_landmarks,
            self.mph.FACEMESH_TESSELATION,
            self.drawing.DrawingSpec(color=(250, 0, 50), thickness=1, circle_radius=1),
            self.drawing.DrawingSpec(color=(180, 180, 180), thickness=1, circle_radius=1),
        )
        self.drawing.draw_landmarks(
            anno_img,
            results.right_hand_landmarks,
            self.mph.HAND_CONNECTIONS,
            self.drawing.DrawingSpec(color=(10, 190, 50), thickness=1, circle_radius=1),
            self.drawing.DrawingSpec(color=(180, 180, 180), thickness=1, circle_radius=1),
        )
        self.drawing.draw_landmarks(
            anno_img,
            results.left_hand_landmarks,
            self.mph.HAND_CONNECTIONS,
            self.drawing.DrawingSpec(color=(10, 50, 200), thickness=1, circle_radius=1),
            self.drawing.DrawingSpec(color=(180, 180, 180), thickness=1, circle_radius=1),
        )

    def _put_frame_pos(self, src_img, pos=0, font_size=2):
        txt_font = cv2.FONT_HERSHEY_PLAIN
        text_pos = (font_size*5, font_size*15)
        cv2.putText(src_img, f"{pos}/{self.total_frame_num}", text_pos, txt_font, font_size, (0, 0, 0), font_size*3)
        cv2.putText(src_img, f"{pos}/{self.total_frame_num}", text_pos, txt_font, font_size, (255, 255, 255), font_size)
