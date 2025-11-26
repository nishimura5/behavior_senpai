import os

import pandas as pd

from behavior_senpai import hdf_df, keypoint_toml_loader, keypoints_proc
from gui_parts import TempFile


class CalcFeatures:
    def __init__(self, args):
        src_df = args["src_df"].copy()
        self.model_name = src_df.attrs["model"]
        self.calc_dir = os.path.join(os.path.dirname(args["pkl_dir"]), "calc")
        self.tar_df = src_df[~src_df.index.duplicated(keep="last")]

        idx = self.tar_df.index
        self.tar_df.index = self.tar_df.index.set_levels([idx.levels[0], idx.levels[1].astype(str), idx.levels[2].astype(int)])

        self.track_name = args["trk_pkl_name"]
        self.src_attrs = src_df.attrs
        temp = TempFile()
        self.calc_case = temp.data["calc_case"]

    def load_keypoint_toml(self):
        kpl = keypoint_toml_loader.KeypointTOMLLoader()
        kpl.open_toml_by_model_name(self.model_name)

        self.source_cols_dict = {
            "left_forearm": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("left_elbow"), kpl.get_idx_by_name("left_wrist"), None],
            "right_forearm": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("right_elbow"), kpl.get_idx_by_name("right_wrist"), None],
            "left_upper_arm": [
                "angle2 (∠BAx)",
                self.member,
                kpl.get_idx_by_name("left_shoulder"),
                kpl.get_idx_by_name("left_elbow"),
                None,
            ],
            "right_upper_arm": [
                "angle2 (∠BAx)",
                self.member,
                kpl.get_idx_by_name("right_shoulder"),
                kpl.get_idx_by_name("right_elbow"),
                None,
            ],
            "left_thigh": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("left_hip"), kpl.get_idx_by_name("left_knee"), None],
            "right_thigh": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("right_hip"), kpl.get_idx_by_name("right_knee"), None],
            "left_shin": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("left_knee"), kpl.get_idx_by_name("left_ankle"), None],
            "right_shin": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("right_knee"), kpl.get_idx_by_name("right_ankle"), None],
            "left_body": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("left_shoulder"), kpl.get_idx_by_name("left_hip"), None],
            "right_body": ["angle2 (∠BAx)", self.member, kpl.get_idx_by_name("right_shoulder"), kpl.get_idx_by_name("right_hip"), None],
            "left_elbow": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("left_elbow"),
                kpl.get_idx_by_name("left_wrist"),
                kpl.get_idx_by_name("left_shoulder"),
            ],
            "right_elbow": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("right_elbow"),
                kpl.get_idx_by_name("right_wrist"),
                kpl.get_idx_by_name("right_shoulder"),
            ],
            "left_shoulder": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("left_shoulder"),
                kpl.get_idx_by_name("left_elbow"),
                kpl.get_idx_by_name("left_hip"),
            ],
            "right_shoulder": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("right_shoulder"),
                kpl.get_idx_by_name("right_elbow"),
                kpl.get_idx_by_name("right_hip"),
            ],
            "left_knee": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("left_knee"),
                kpl.get_idx_by_name("left_hip"),
                kpl.get_idx_by_name("left_ankle"),
            ],
            "right_knee": [
                "angle3 (∠BAC)",
                self.member,
                kpl.get_idx_by_name("right_knee"),
                kpl.get_idx_by_name("right_hip"),
                kpl.get_idx_by_name("right_ankle"),
            ],
        }

    def set_member(self):
        if self.model_name == "MediaPipe Holistic":
            self.member = "pose"
        else:
            members = self.tar_df.index.get_level_values(1).unique().tolist()
            self.member = members[0]

    def calc_features(self):
        self.feat_df = pd.DataFrame()
        member_df = self.tar_df.loc[pd.IndexSlice[:, self.member], :].drop("timestamp", axis=1)
        member_feat_df = pd.DataFrame()
        kps = member_df.dropna().index.get_level_values(2).unique().astype(int).tolist()

        # points features
        self.source_cols_for_points = []
        remove_keys = []
        for key, params in self.source_cols_dict.items():
            calc, member, point_a, point_b, point_c = params

            if int(point_a) not in kps or int(point_b) not in kps:
                remove_keys.append(key)
                continue
            self.source_cols_for_points.append(params)

            if calc == "angle2 (∠BAx)":
                feat_df = keypoints_proc.calc_angle2(member_df, point_a, point_b)
            elif calc == "angle3 (∠BAC)":
                feat_df = keypoints_proc.calc_angle3(member_df, point_a, point_b, point_c)

            col_names = feat_df.columns.tolist()[0]
            self.source_cols_dict[key].append(col_names)

            member_feat_df = pd.concat([member_feat_df, feat_df], axis=1)

            feat_df["timestamp"] = self.tar_df.loc[pd.IndexSlice[:, :, point_a], :].droplevel(2)["timestamp"]
        self.feat_df = pd.concat([self.feat_df, member_feat_df], axis=1)

        for key in remove_keys:
            del self.source_cols_dict[key]

    def export_points(self):
        if len(self.feat_df) == 0:
            print("No data to export.")
            return
        self.feat_df = self.feat_df.sort_index()
        members = self.feat_df.index.get_level_values(1).unique()

        first_keypoint_id = self.tar_df.index.get_level_values(2).values[0]
        timestamp_df = self.tar_df.loc[pd.IndexSlice[:, members, first_keypoint_id], :].droplevel(2)["timestamp"]
        timestamp_df = timestamp_df[~timestamp_df.index.duplicated(keep="last")]
        self.feat_df = self.feat_df[~self.feat_df.index.duplicated(keep="last")]
        export_df = pd.concat([self.feat_df, timestamp_df], axis=1)
        export_df = export_df.dropna(how="all")
        export_df.attrs = self.src_attrs

        file_name = os.path.splitext(self.track_name)[0]
        dst_path = os.path.join(self.calc_dir, self.calc_case, file_name + ".feat")
        h5 = hdf_df.DataFrameStorage(dst_path)
        h5.save_points_df(export_df, self.track_name, self.source_cols_for_points)

        h5.save_mixnorm_source_cols(self.source_cols_for_mixnorm, self.track_name)
        print(f"Exported feature file to: {dst_path}")

    def calc_mix_norm(self):
        self.source_cols_for_mixnorm = []
        for key, params in self.source_cols_dict.items():
            self.source_cols_for_mixnorm.append(
                [
                    key,
                    self.member,
                    params[-1],
                    " ",
                    " ",
                    "No normalize",
                ]
            )


def execute_calc_features(args):
    calc = CalcFeatures(args)
    calc.set_member()
    calc.load_keypoint_toml()
    calc.calc_features()
    calc.calc_mix_norm()
    calc.export_points()
