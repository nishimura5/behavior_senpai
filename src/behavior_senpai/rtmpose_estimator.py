from mmpose.apis import inference_topdown, init_model


class RTMPoseEstimator:
    """Estimate keypoints inside supplied bounding boxes, without detection or tracking."""

    def __init__(self, model_name, device="cuda:0"):
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
        else:
            raise ValueError(f"Unsupported pose model: {model_name}")

        self.model = init_model(config, checkpoint, device=device)
        self.visualizer_config = self.model.cfg.visualizer
        self.dataset_meta = self.model.dataset_meta

    def estimate(self, image, bboxes):
        if len(bboxes) == 0:
            return []
        return inference_topdown(self.model, image, bboxes)
