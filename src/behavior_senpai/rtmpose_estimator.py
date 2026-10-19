from pathlib import Path

from mmpose.apis import inference_topdown, init_model


MODEL_CONFIGS = {
    "RTMPose-x WholeBody133": {
        "config": "rtmpose-x_8xb32-270e_coco-wholebody-384x288.py",
        "checkpoint": "rtmposev1/rtmpose-x_simcc-coco-wholebody_pt-body7_270e-384x288-401dfc90_20230629.pth",
        "number_of_keypoints": 133,
    },
    "RTMPose-x Halpe26": {
        "config": "rtmpose-x_8xb256-700e_body8-halpe26-384x288.py",
        "checkpoint": "rtmposev1/rtmpose-x_simcc-body7_pt-body7-halpe26_700e-384x288-7fb6e239_20230606.pth",
        "number_of_keypoints": 26,
    },
    "RTMW-x WholeBody133": {
        "config": "rtmw-x_8xb320-270e_cocktail14-384x288.py",
        "checkpoint": "rtmw/rtmw-x_simcc-cocktail14_pt-ucoco_270e-384x288-f840f204_20231122.pth",
        "number_of_keypoints": 133,
    },
    "RTMPose-m Hand5": {
        "config": "rtmpose-m_8xb256-210e_hand5-256x256.py",
        "checkpoint": "rtmposev1/rtmpose-m_simcc-hand5_pt-aic-coco_210e-256x256-74fb594_20230320.pth",
        "number_of_keypoints": 21,
    },
}


class RTMPoseEstimator:
    """Estimate keypoints inside supplied bounding boxes, without detection or tracking."""

    def __init__(self, model_name, device="cuda:0"):
        if model_name not in MODEL_CONFIGS:
            raise ValueError(f"Unsupported pose model: {model_name}")

        self.model_name = model_name
        settings = MODEL_CONFIGS[model_name]
        config = str(Path(__file__).resolve().parents[2] / "mm_config" / settings["config"])
        checkpoint = "https://download.openmmlab.com/mmpose/v1/projects/" + settings["checkpoint"]
        self.number_of_keypoints = settings["number_of_keypoints"]

        self.model = init_model(config, checkpoint, device=device)
        self.visualizer_config = self.model.cfg.visualizer
        self.dataset_meta = self.model.dataset_meta

    def estimate(self, image, bboxes):
        """Estimate poses from a BGR image; the model handles color conversion."""
        if len(bboxes) == 0:
            return []
        return inference_topdown(self.model, image, bboxes)
