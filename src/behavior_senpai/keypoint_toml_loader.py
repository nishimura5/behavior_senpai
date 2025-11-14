import os
import tomllib


class KeypointTOMLLoader:
    def __init__(self, kp_toml_name=None):
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