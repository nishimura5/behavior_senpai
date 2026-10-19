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
    from estimate(image, bboxes), in the same order. Both receive BGR images
    directly from the video capture; model preprocessors handle color conversion.
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
        frames_read = 0
        frames_with_detections = 0
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()
            if ret is False:
                print("Failed to read frame.")
                continue
            frames_read += 1
            bboxes, track_ids = self.bbox_detector.detect(
                frame, frame_id=self.frame_id, video_len=self.total_frame_num
            )
            self.frame_id += 1

            # 何もなければ次のフレームへ
            # keypoint検出
            results = []
            if len(bboxes) > 0:
                frames_with_detections += 1
                results = self.pose_estimator.estimate(frame, bboxes)
            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC)

            # 検出結果を描画、xキーで途中終了
            if self.show is True:
                if results:
                    frame = self._draw(frame, merge_data_samples(results))
                frame = self._draw_bboxes(frame, bboxes, track_ids)
                _, frame = vcap.resize_frame(frame)
                img_draw.put_frame_pos(frame, i, self.total_frame_num)
                img_draw.put_message(frame, "'x' key to exit.", font_size=1.5, y=55)
                if len(bboxes) == 0:
                    img_draw.put_message(frame, "No detections", font_size=1.5, y=80)
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
        print(
            f"Processed {frames_read}/{self.total_frame_num} frames; "
            f"frames with detections: {frames_with_detections}; keypoint rows: {len(self.dst_df)}"
        )
        if frames_read == 0:
            print("No video frames were read. Check the video file and frame count.")
        elif frames_with_detections == 0:
            print("No bounding boxes were detected. Keypoint estimation was skipped. Check the target size and ROI.")

    def get_result(self):
        return self.dst_df

    def _draw_bboxes(self, frame, bboxes, track_ids):
        frame = frame.copy()
        color = (0, 255, 0)
        for bbox, track_id in zip(bboxes, track_ids):
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame, f"ID: {track_id}", (max(0, x1), max(15, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA,
            )
        return frame

    def _draw(self, anno_img, data_samples):
        self.visualizer.add_datasample(
            "result",
            anno_img,
            data_sample=data_samples,
            show=False,
            draw_gt=False,
        )
        return self.visualizer.get_image()
