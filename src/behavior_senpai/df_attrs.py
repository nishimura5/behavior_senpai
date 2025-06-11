from behavior_senpai import time_format


class DfAttrs:
    def __init__(self, src_df):
        self.attrs = src_df.attrs

    def load_scene_table(self):
        default_scene_table = {"description": [], "start": [], "end": []}
        self.scene_table = self.attrs.get("scene_table", default_scene_table)

    def get_scene_descriptions(self, add_blank=False):
        descriptions = self.scene_table.get("description", None)
        if descriptions is None:
            return [""]
        if isinstance(descriptions, list):
            descriptions = list(set(descriptions))
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

    def get_take_prev_next(self):
        take = self.attrs.get("take", "")
        prev_name = self.attrs.get("prev", None)
        next_name = self.attrs.get("next", None)
        return take, prev_name, next_name

    def get_model_video(self):
        model_name = self.attrs.get("model", "")
        video_name = self.attrs.get("video_name", None)
        return model_name, video_name

    def get_video_name(self):
        video_name = self.attrs.get("video_name", None)
        return video_name

    def get_rotate_size(self):
        rotate = self.attrs.get("rotate", 0)
        frame_size = self.attrs.get("frame_size", None)
        if rotate != 0:
            print(f"rotate={rotate}")
        return rotate, frame_size


def make_history_dict(feat_type, source_cols, track_name=None):
    history_dict = {"type": feat_type, "source_cols": source_cols, "track_name": track_name}
    return history_dict
