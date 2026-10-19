import cv2
import numpy as np
import pandas as pd
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples

from behavior_senpai import img_draw, vcap


class PoseVideoProcessor:
    """Process video using a bbox detector and a pose estimator.

    The detector returns aligned (bboxes, track_ids) from detect(image,
    frame_id, video_len). The estimator returns one pose sample per bbox
    from estimate(image, bboxes), in the same order.
    """

    def __init__(self, bbox_detector, pose_estimator, show=True):
        self.bbox_detector = bbox_detector
        self.pose_estimator = pose_estimator
        self.number_of_keypoints = pose_estimator.number_of_keypoints
        self.visualizer = VISUALIZERS.build(pose_estimator.visualizer_config)
        self.visualizer.set_dataset_meta(pose_estimator.dataset_meta)
        self.pose_score_threshold = 0.3
        self.show = show
        self.frame_id = 0

    def set_cap(self, cap):
        self.cap = cap
        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        self.frame_id = 0

    def detect(self, roi=False):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "visible": [], "score": [], "timestamp": []}
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()
            if ret is False:
                print("Failed to read frame.")
                continue
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            bboxes, track_ids = self.bbox_detector.detect(
                rgb_img, frame_id=self.frame_id, video_len=self.total_frame_num
            )
            self.frame_id += 1

            # 何もなければ次のフレームへ
            if len(bboxes) == 0:
                continue

            # keypoint検出
            results = self.pose_estimator.estimate(rgb_img, bboxes)
            data_samples = merge_data_samples(results)
            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果を描画、xキーで途中終了
            if self.show is True:
                frame = self._draw(frame, data_samples)
                _, frame = vcap.resize_frame(frame)
                img_draw.put_frame_pos(frame, i, self.total_frame_num)
                img_draw.put_message(frame, "'x' key to exit.", font_size=1.5, y=55)
                cv2.imshow("dst", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("x"):
                    break

            for tid, keypoints in zip(track_ids, results):
                pred_instance = keypoints.pred_instances.cpu().numpy()
                pred_instance.keypoints[pred_instance.keypoint_scores < self.pose_score_threshold] = 0
                result_keypoints = np.concatenate(
                    (pred_instance.keypoints[0, :], pred_instance.keypoints_visible.T, pred_instance.keypoint_scores.T), axis=1
                )
                for k in range(self.number_of_keypoints):
                    keypoint_id = k
                    x = result_keypoints[k][0]
                    y = result_keypoints[k][1]
                    if roi is True:
                        x += self.cap.left_top_point[0]
                        y += self.cap.left_top_point[1]
                    visible = result_keypoints[k][2]
                    score = result_keypoints[k][3]

                    # データの詰め込み
                    data_dict["frame"].append(i)
                    data_dict["member"].append(str(tid))
                    data_dict["keypoint"].append(keypoint_id)
                    data_dict["x"].append(x)
                    data_dict["y"].append(y)
                    data_dict["visible"].append(visible)
                    data_dict["score"].append(score)
                    data_dict["timestamp"].append(timestamp)

        # keypointはここではintで保持する、indexでソートしたくなるかもしれないので
        self.dst_df = pd.DataFrame(data_dict).set_index(["frame", "member", "keypoint"])
        cv2.destroyAllWindows()

    def get_result(self):
        return self.dst_df

    def _draw(self, anno_img, data_samples):
        self.visualizer.add_datasample(
            "result",
            anno_img,
            data_sample=data_samples,
            show=False,
            draw_gt=False,
        )
        return self.visualizer.get_image()
