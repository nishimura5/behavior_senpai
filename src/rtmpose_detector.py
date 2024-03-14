import cv2
import pandas as pd
import numpy as np
from mmengine.registry import init_default_scope
from mmdet.apis import inference_detector, init_detector
from mmpose.apis import inference_topdown, init_model
from mmpose.evaluation.functional import nms
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples

from python_senpai import img_draw
from python_senpai import vcap


class RTMPoseDetector:
    def __init__(self, show=True):
        config = "./mm_config/rtmpose-x_8xb256-700e_body8-halpe26-384x288.py"
        checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-x_simcc-body7_pt-body7-halpe26_700e-384x288-7fb6e239_20230606.pth"
        det_config = "./mm_config/rtmdet_m_640-8xb32_coco-person.py"
        det_checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/rtmpose/rtmdet_m_8xb32-100e_coco-obj365-person-235e8209.pth"
        self.det_model = init_detector(det_config, det_checkpoint, device='cuda:0')
        self.pose_model = init_model(config, checkpoint, device='cuda:0')
        self.visualizer = VISUALIZERS.build(self.pose_model.cfg.visualizer)
        self.visualizer.set_dataset_meta(self.pose_model.dataset_meta)

        self.number_of_keypoints = 26
        self.det_score_threshold = 0.3
        self.pose_score_threshold = 0.3
        self.retain_threshold = 0.3
        self.det_cat_id = 0
        self.show = show

    def set_cap(self, cap):
        self.cap = cap
        self.total_frame_num = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def detect(self, roi=False):
        # データの初期化
        data_dict = {"frame": [], "member": [], "keypoint": [], "x": [], "y": [], "visible": [], "score": [], "timestamp": []}
        for i in range(self.total_frame_num):
            if roi is True:
                ret, frame = self.cap.get_roi_frame()
            else:
                ret, frame = self.cap.read()
            rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            scope = self.det_model.cfg.get('default_scope', 'mmdet')
            if scope is not None:
                init_default_scope(scope)
            # bbox検出
            det_result = inference_detector(self.det_model, rgb_img)
            pred_instance = det_result.pred_instances.cpu().numpy()
            bboxes = np.concatenate((pred_instance.bboxes, pred_instance.scores[:, None]), axis=1)
            bboxes = bboxes[np.logical_and(pred_instance.labels == self.det_cat_id, pred_instance.scores > self.det_score_threshold)]
            bboxes = bboxes[nms(bboxes, self.retain_threshold), :4]
            # x座標でソート
            bboxes = bboxes[bboxes[:, 0].argsort()]
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
                if key == ord('x'):
                    break

            # 検出結果の取り出し
            for member_id, keypoints in enumerate(results):
                pred_instance = keypoints.pred_instances.cpu().numpy()
                pred_instance.keypoints[pred_instance.keypoint_scores < self.pose_score_threshold] = 0
                result_keypoints = np.concatenate((pred_instance.keypoints[0, :], pred_instance.keypoints_visible.T, pred_instance.keypoint_scores.T), axis=1)
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
            'result',
            anno_img,
            data_sample=data_samples,
            show=False,
            draw_gt=False,
        )
        return self.visualizer.get_image()
