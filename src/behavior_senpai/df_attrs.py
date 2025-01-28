from behavior_senpai import time_format


class DfAttrs:
    def __init__(self, src_df):
        self.attrs = src_df.attrs

    def load_scene_table(self):
        if "scene_table" not in self.attrs.keys():
            self.scene_table = {}
            print("scene_table not found.")
            return
        self.scene_table = self.attrs["scene_table"]

    def get_scene_descriptions(self, add_blank=False):
        if "scene_table" not in self.attrs.keys():
            print("scene_table not found.")
            return [""]
        if "description" not in self.scene_table.keys():
            print("description not found.")
            return [""]
        descriptions = list(set(self.scene_table["description"]))
        if add_blank:
            return [""] + descriptions
        return descriptions

    def get_scenes(self, description):
        if description == "":
            return None
        if "description" not in self.scene_table.keys():
            return []
        idx_list = [idx for idx, d in enumerate(self.scene_table["description"]) if d == description]
        start_and_end_list = [
            (time_format.timestr_to_msec(self.scene_table["start"][idx]), time_format.timestr_to_msec(self.scene_table["end"][idx]))
            for idx in idx_list
        ]
        return start_and_end_list

    def get_prev(self):
        if "take" not in self.attrs.keys():
            return None
        if "prev" in self.attrs.keys() and self.attrs["prev"] is not None:
            return self.attrs["prev"]
        return False

    def get_next(self):
        if "take" not in self.attrs.keys():
            print("take not found.")
            return None
        if "next" in self.attrs.keys() and self.attrs["next"] is not None:
            return self.attrs["next"]
        return False


def make_history_dict(feat_type, source_cols, params, track_name=None):
    history_dict = {"type": feat_type, "source_cols": source_cols, "params": params, "track_name": track_name}
    return history_dict
