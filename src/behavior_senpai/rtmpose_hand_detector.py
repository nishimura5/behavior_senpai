from pathlib import Path

import numpy as np
from mmdet.apis import inference_detector, init_detector
from mmdet.utils import register_all_modules
from mmengine.registry import init_default_scope

from behavior_senpai.bbox_iou_tracker import BBoxIoUTracker
from behavior_senpai.pose_video_processor import PoseVideoProcessor
from behavior_senpai.rtmpose_estimator import RTMPoseEstimator


class RTMHandDetector:
    """Detect hand boxes with RTMDet and assign hand track IDs using IoU."""

    def __init__(self, device="cuda:0", bbox_threshold=0.5, iou_threshold=0.3, max_age=30):
        if not 0 <= bbox_threshold <= 1:
            raise ValueError("bbox_threshold must be in [0, 1].")
        self.bbox_threshold = bbox_threshold
        self.tracker = BBoxIoUTracker(iou_threshold=iou_threshold, max_age=max_age)
        register_all_modules(init_default_scope=True)
        config = str(Path(__file__).resolve().parents[2] / "mm_config" / "rtmdet_nano_320-8xb32_hand.py")
        checkpoint = (
            "https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/"
            "rtmdet_nano_8xb32-300e_hand-267f9c8f.pth"
        )
        self.model = init_detector(config, checkpoint, device=device)

    def detect(self, image, frame_id, video_len):
        """Return (xyxy boxes, IDs) for a BGR video frame, in matching order."""
        scope = self.model.cfg.get("default_scope", "mmdet")
        if scope is not None:
            init_default_scope(scope)
        result = inference_detector(self.model, image)
        instances = result.pred_instances.cpu().numpy()
        bboxes = instances.bboxes
        keep = (
            (instances.labels == 0)
            & np.isfinite(instances.scores)
            & (instances.scores >= self.bbox_threshold)
            & np.isfinite(bboxes).all(axis=1)
            & (bboxes[:, 2] > bboxes[:, 0])
            & (bboxes[:, 3] > bboxes[:, 1])
        )
        bboxes = bboxes[keep]
        return bboxes, self.tracker.update(bboxes, frame_id)


class RTMPoseHandDetector(PoseVideoProcessor):
    """Video hand poses with one member ID per tracked hand (not per person).

    Uses the existing set_cap(), detect(roi=...), get_result() API.
    Left/right classification and association with a person are not performed.
    """

    def __init__(self, show=True, device="cuda:0", bbox_threshold=0.5, iou_threshold=0.3, max_age=30):
        bbox_detector = RTMHandDetector(
            device=device, bbox_threshold=bbox_threshold, iou_threshold=iou_threshold, max_age=max_age
        )
        pose_estimator = RTMPoseEstimator("RTMPose-m Hand5", device=device)
        super().__init__(bbox_detector, pose_estimator, show=show)
