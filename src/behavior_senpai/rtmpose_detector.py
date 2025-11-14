import cv2
import numpy as np
import pandas as pd
from mmdet.apis import inference_detector, inference_mot, init_detector, init_track_model
from mmengine.registry import init_default_scope
from mmpose.apis import inference_topdown, init_model
from mmpose.evaluation.functional import nms
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples

from behavior_senpai import img_draw, vcap


class RTMPoseDetector:
    def __init__(self, model_name, show=True):
        if model_name == "RTMPose-x WholeBody133":
            config = "./mm_config/rtmpose-x_8xb32-270e_coco-wholebody-384x288.py"
            checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-x_simcc-coco-wholebody_pt-body7_270e-384x288-401dfc90_20230629.pth"
            self.number_of_keypoints = 133
        elif model_name == "RTMPose-x Halpe26":
            config = "./mm_config/rtmpose-x_8xb256-700e_body8-halpe26-384x288.py"
            checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-x_simcc-body7_pt-body7-halpe26_700e-384x288-7fb6e239_20230606.pth"
            self.number_of_keypoints = 26
        elif model_name == "RTMW-x WholeBody133":
            config = "./mm_config/rtmw-x_8xb320-270e_cocktail14-384x288.py"
            checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmw/rtmw-x_simcc-cocktail14_pt-ucoco_270e-384x288-f840f204_20231122.pth"
            self.number_of_keypoints = 133

        # detection
        det_config = "./mm_config/rtmdet_m_640-8xb32_coco-person.py"
        det_checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_m_8xb32-100e_coco-obj365-person-235e8209.pth"
        self.det_model = init_detector(det_config, det_checkpoint, device="cuda:0")

        # tracking
        track_config = "./mm_config/qdtrack_faster-rcnn_r50_fpn_8xb2-4e_mot17halftrain_test-mot17halfval.py"
        track_checkpoint = (
            "https://download.openmmlab.com/mmtracking/mot/qdtrack/mot_dataset/qdtrack_faster-rcnn_r50_fpn_4e_mot17_20220315_145635-76f295ef.pth"
        )
        self.track_model = init_track_model(track_config, track_checkpoint, device="cuda:0")

        self.pose_model = init_model(config, checkpoint, device="cuda:0")
        self.visualizer = VISUALIZERS.build(self.pose_model.cfg.visualizer)
        self.visualizer.set_dataset_meta(self.pose_model.dataset_meta)

        self.det_score_threshold = 0.1
        self.pose_score_threshold = 0.3
        self.retain_threshold = 0.3
        self.det_cat_id = 0
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

            scope = self.track_model.cfg.get("default_scope", "mmdet")
            if scope is not None:
                init_default_scope(scope)
            # bbox検出
            track_result = inference_mot(self.track_model, rgb_img, frame_id=self.frame_id, video_len=self.total_frame_num)
            self.frame_id += 1
            if isinstance(track_result, list):
                track_data_sample = track_result[0]
            else:
                track_data_sample = track_result
            det_sample = track_data_sample.video_data_samples[0]
            track_instances = det_sample.pred_track_instances
            bboxes = track_instances.bboxes.cpu().numpy()
            scores = track_instances.scores.cpu().numpy()
            labels = track_instances.labels.cpu().numpy()
            track_ids = track_instances.instances_id.cpu().numpy()
            # 人クラスだけ＆スコアしきい値で絞る
            keep = (labels == self.det_cat_id) & (scores > self.det_score_threshold)
            bboxes = bboxes[keep]
            track_ids = track_ids[keep]
            scores = scores[keep]

            # 何もなければ次のフレームへ
            if len(bboxes) == 0:
                continue

            # keypoint検出
            results = inference_topdown(self.pose_model, rgb_img, bboxes)
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

            # 検出結果の取り出し
            for member_id, keypoints in enumerate(results):
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
                    data_dict["member"].append(member_id)
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
