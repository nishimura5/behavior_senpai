import os
import tomllib


class KeypointTOMLLoader:
    def __init__(self, kp_toml_name=None):
        if kp_toml_name is not None:
            self.open_toml(kp_toml_name)

    def open_toml_by_model_name(self, model_name):
        model_to_toml = {
            "MediaPipe Holistic": "mediapipe_holistic.toml",
            "YOLOv8 x-pose-p6": "coco17.toml",
            "YOLO11 x-pose": "coco17.toml",
            "MMPose RTMPose-x": "halpe26.toml",
            "RTMPose-x Halpe26": "halpe26.toml",
            "RTMPose-x WholeBody133": "coco133.toml",
            "RTMW-x WholeBody133": "coco133.toml",
        }
        kp_toml_name = model_to_toml.get(model_name, None)
        if kp_toml_name is None:
            print(f"Model name '{model_name}' not found in mapping.")
        else:
            self.open_toml(kp_toml_name)

    def open_toml(self, kp_toml_name):
        toml_path = os.path.join(os.path.dirname(__file__), "..", "keypoint", kp_toml_name)
        with open(toml_path, "rb") as f:
            self.data = tomllib.load(f)

    def get_data(self):
        return self.data

    def get_keypoint_idx_by_group(self, group_name: str):
        idx_list = self.data.get("keypoint_group").get(group_name, [])
        return idx_list

    def get_keypoint_idx_by_groups(self, group_names: list):
        idx_list = []
        for group_name in group_names:
            idxs = self.get_keypoint_idx_by_group(group_name)
            idx_list.extend(idxs)
        return idx_list

    def get_idx_by_name(self, name):
        tar_id = self.data.get("keypoints").get(name, None)
        if tar_id is None:
            raise ValueError(f"Keypoint name '{name}' not found in TOML.")
        return tar_id["id"]
