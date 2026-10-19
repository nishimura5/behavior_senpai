from mmdet.apis import inference_mot, init_track_model
from mmdet.utils import register_all_modules
from mmengine.registry import init_default_scope

from behavior_senpai.pose_video_processor import PoseVideoProcessor
from behavior_senpai.rtmpose_estimator import RTMPoseEstimator


class QDTrackDetector:
    """Detect and track people, returning bounding boxes and their track IDs."""

    def __init__(self, device="cuda:0"):
        register_all_modules(init_default_scope=True)
        # tracking
        track_config = "./mm_config/qdtrack_faster-rcnn_r50_fpn_8xb2-4e_mot17halftrain_test-mot17halfval.py"
        track_checkpoint = (
            "https://download.openmmlab.com/mmtracking/mot/qdtrack/mot_dataset/qdtrack_faster-rcnn_r50_fpn_4e_mot17_20220315_145635-76f295ef.pth"
        )
        self.track_model = init_track_model(track_config, track_checkpoint, device=device)

        self.det_cat_id = 0

    def detect(self, image, frame_id, video_len):
        """Return aligned boxes and track IDs from a BGR video frame."""
        scope = self.track_model.cfg.get("default_scope", "mmdet")
        if scope is not None:
            init_default_scope(scope)
        # bbox検出
        track_result = inference_mot(self.track_model, image, frame_id=frame_id, video_len=video_len)
        if isinstance(track_result, list):
            track_data_sample = track_result[0]
        else:
            track_data_sample = track_result
        det_sample = track_data_sample.video_data_samples[0]
        track_instances = det_sample.pred_track_instances
        bboxes = track_instances.bboxes.cpu().numpy()
        labels = track_instances.labels.cpu().numpy()
        track_ids = track_instances.instances_id.cpu().numpy()
        keep = labels == self.det_cat_id
        bboxes = bboxes[keep]
        track_ids = track_ids[keep]
        return bboxes, track_ids


class RTMPoseDetector(PoseVideoProcessor):
    """Existing video API, combining person tracking with top-down pose estimation."""

    def __init__(self, model_name, show=True):
        bbox_detector = QDTrackDetector()
        pose_estimator = RTMPoseEstimator(model_name)
        super().__init__(bbox_detector, pose_estimator, show=show)
