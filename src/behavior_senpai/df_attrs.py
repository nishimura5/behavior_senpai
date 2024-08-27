import os

import pandas as pd

from behavior_senpai import time_format


class DfAttrs:
    def __init__(self, src_df):
        self.attrs = src_df.attrs

        # The newest item in the attrs["proc_history"] list
        self.newest_proc_history = None

    def load_proc_history(self):
        if "proc_history" not in self.attrs.keys():
            print("proc_history not found.")
            return
        if isinstance(self.attrs["proc_history"], list) is False:
            print("proc_history is not list.")
            return
        proc_history_list = []
        for history in self.attrs["proc_history"]:
            if isinstance(history, dict) and "type" in history.keys() and "source_cols" in history.keys():
                proc_history_list.append(history)
        if len(proc_history_list) == 0:
            print("proc_history not found.")
            return
        self.newest_proc_history = proc_history_list[-1]

    def load_scene_table(self):
        if "scene_table" not in self.attrs.keys():
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
        idx_list = [idx for idx, d in enumerate(self.scene_table["description"]) if d == description]
        start_and_end_list = [
            (time_format.timestr_to_msec(self.scene_table["start"][idx]), time_format.timestr_to_msec(self.scene_table["end"][idx]))
            for idx in idx_list
        ]
        return start_and_end_list

    def validate_model(self, tar_attrs_dict):
        if isinstance(tar_attrs_dict, dict) is True:
            model_name = tar_attrs_dict["model"]
            video_name = tar_attrs_dict["video_name"]
        else:
            model_name = tar_attrs_dict.attrs["model"]
            video_name = tar_attrs_dict.attrs["video_name"]
        if self.attrs["video_name"] != video_name and video_name != "":
            print(f'warning: video_name "{video_name}", expected "{self.attrs["video_name"]}".')
        if self.attrs["model"] != model_name:
            print(f'model_name "{model_name}", expected "{self.attrs["model"]}".')
            return False
        return True

    def validate_newest_history_proc(self, proc_name):
        if self.newest_proc_history["type"] != proc_name:
            print(f'proc_name "{proc_name}", expected "{self.newest_proc_history["type"]}".')
            return False
        if len(self.newest_proc_history["source_cols"]) == 0:
            print("source_cols is empty.")
            return False
        return True

    def get_source_cols(self):
        return self.newest_proc_history["source_cols"]

    def get_params(self):
        return self.newest_proc_history["params"]

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
