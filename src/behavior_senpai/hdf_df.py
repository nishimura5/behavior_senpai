import inspect
import os

import pandas as pd


class DataFrameStorage:
    """
    group structure in HDF5
    traj
        df, source_cols
    points
        df, source_cols
    mixnorm
        df, source_cols
    dimredu
        df, params, source_cols, features
    profile (dictionary)
        "track_name",
    """

    def __init__(self, filepath: str):
        """
        Initialize storage with HDF filepath

        Args:
            filepath: Path to HDF file
        """
        self.filepath = filepath

    def save_dimredu_df(self, df: pd.DataFrame, source_cols: list, params_dict: dict, cluster_names: list):
        """
        Save dimredu DataFrame to HDF store
        """
        with pd.HDFStore(self.filepath, mode="a") as store:
            # Save DataFrame
            store.put("dimredu/df", df, format="table")

            # Save attributes DataFrame
            attrs_dict = {}
            attrs_df = pd.DataFrame({"key": list(attrs_dict.keys()), "value": list(attrs_dict.values())})
            store.put("attrs", attrs_df, format="table")

            source_cols_dict = {"code": []}
            for source_col in source_cols:
                source_cols_dict["code"].append(source_col)
            source_cols_df = pd.DataFrame(source_cols_dict)

            store.put("dimredu/source_cols", source_cols_df, format="table")
            feature_df = pd.DataFrame({"feat": cluster_names})
            store.put("dimredu/features", feature_df, format="table")
            # stringify values
            params = {"key": [], "value": []}
            for key, value in params_dict.items():
                params["key"].append(key)
                params["value"].append(str(value))
            params_df = pd.DataFrame(params)
            store.put("dimredu/params", params_df, format="table")
        called_in = os.path.basename(inspect.stack()[1].filename)
        print(f"{called_in} > {os.path.basename(os.path.basename(self.filepath))}")

    def save_traj_df(self, src_df: pd.DataFrame, track_name: str):
        """
        Save trajectory DataFrame to HDF store
        """
        # create directory if it does not exist
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        with pd.HDFStore(self.filepath, mode="a") as store:
            store.put("traj/df", src_df, format="table")

            track_name = {"key": ["track_name"], "value": [track_name]}
            profile_df = pd.DataFrame(track_name)
            store.put("profile", profile_df, format="table")
        called_in = os.path.basename(inspect.stack()[1].filename)
        print(f"{called_in} > {os.path.basename(os.path.basename(self.filepath))}")

    def save_points_df(self, src_df: pd.DataFrame, track_name: str, source_cols: list):
        # create directory if it does not exist
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        with pd.HDFStore(self.filepath, mode="a") as store:
            store.put("points/df", src_df, format="table")

            dst_source_cols = {
                "code": [],
                "member": [],
                "point_a": [],
                "point_b": [],
                "point_c": [],
            }
            for source_col in source_cols:
                dst_source_cols["code"].append(source_col[0])
                dst_source_cols["member"].append(source_col[1])
                dst_source_cols["point_a"].append(str(source_col[2]))
                dst_source_cols["point_b"].append(str(source_col[3]))
                dst_source_cols["point_c"].append(str(source_col[4]))
            source_cols_df = pd.DataFrame(dst_source_cols)
            store.put("points/source_cols", source_cols_df, format="table")

            track_name = {"key": ["track_name"], "value": [track_name]}
            profile_df = pd.DataFrame(track_name)
            store.put("profile", profile_df, format="table")
        called_in = os.path.basename(inspect.stack()[1].filename)
        print(f"{called_in} > {os.path.basename(os.path.basename(self.filepath))}")

    def save_mixnorm_df(self, src_df: pd.DataFrame, track_name: str, source_cols: list):
        with pd.HDFStore(self.filepath, mode="r") as store:
            # validate track_name
            correct_track_name = self.load_profile()["track_name"]

        with pd.HDFStore(self.filepath, mode="a") as store:
            if track_name != correct_track_name:
                print(f"track_name mismatch: {track_name} != {correct_track_name}")
                return

            store.put("mixnorm/df", src_df, format="table")

            dst_source_cols = {
                "name": [],
                "member": [],
                "col_a": [],
                "op": [],
                "col_b": [],
                "normalize": [],
            }
            for source_col in source_cols:
                dst_source_cols["name"].append(source_col[0])
                dst_source_cols["member"].append(source_col[1])
                dst_source_cols["col_a"].append(str(source_col[2]))
                dst_source_cols["op"].append(source_col[3])
                dst_source_cols["col_b"].append(str(source_col[4]))
                dst_source_cols["normalize"].append(source_col[5])
            source_cols_df = pd.DataFrame(dst_source_cols)
            store.put("mixnorm/source_cols", source_cols_df, format="table")

        called_in = os.path.basename(inspect.stack()[1].filename)
        print(f"{called_in} > {os.path.basename(os.path.basename(self.filepath))}")

    def has_group(self, group_name: str) -> bool:
        """
        Check if group exists in HDF store. startswith() is used to check for subgroups.

        Args:
            group_name: Name of group to check ('points', 'mixnorm', 'dimredu')

        Returns:
            bool: True if group exists, False otherwise
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            return any([key.startswith(f"/{group_name}") for key in store.keys()])

    def load_dimredu_df(self) -> pd.DataFrame:
        """
        Load DataFrame from specified group

        Returns:
            pd.DataFrame: Loaded DataFrame
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/dimredu/df" not in store.keys():
                print("No dimredu data in HDF")
                return None
            df = store.get("dimredu/df")
        self._print_df_info(df)
        return df

    def load_points_df(self) -> pd.DataFrame:
        """
        Load DataFrame from points and traj groups if they exist, otherwise load points DataFrame
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            points_df = None
            traj_df = None
            if "/points/df" in store.keys():
                points_df = store.get("points/df")
            if "/traj/df" in store.keys():
                traj_df = store.get("traj/df")
            if points_df is None and traj_df is None:
                print("No data in HDF")
                return None
            elif points_df is not None and traj_df is not None:
                traj_df = traj_df.drop(columns="timestamp")
                df = pd.concat([points_df, traj_df], axis=1)
            elif points_df is not None:
                df = points_df
            elif traj_df is not None:
                df = traj_df

            self._print_df_info(df)
            return df

    def load_mixnorm_df(self) -> pd.DataFrame:
        """
        Load DataFrame from specified group if it exists, otherwise load points DataFrame
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/mixnorm/df" not in store.keys():
                print("No mixnorm data in HDF")
                df = self.load_points_df()
                return df
            df = store.get("mixnorm/df")
            self._print_df_info(df)
            return df

    def _print_df_info(self, df: pd.DataFrame):
        frame_num = df.index.get_level_values(0).nunique()
        member_num = df.index.get_level_values(1).nunique()
        called_in = os.path.basename(inspect.stack()[1].filename)
        print(f"{called_in} < {os.path.basename(self.filepath)}: shape={df.shape[0]:,}x{df.shape[1]} frames={frame_num:,} members={member_num}")

    def load_points_source_cols(self) -> list:
        source_cols = []
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/points/source_cols" not in store.keys():
                return source_cols
            source_cols_df = store.get("points/source_cols")
            source_cols = source_cols_df[["code", "member", "point_a", "point_b", "point_c"]].values.tolist()
            return source_cols

    def load_mixnorm_source_cols(self) -> list:
        source_cols = []
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/mixnorm/source_cols" not in store.keys():
                return source_cols
            source_cols_df = store.get("mixnorm/source_cols")
            source_cols = source_cols_df[["name", "member", "col_a", "op", "col_b", "normalize"]].values.tolist()
            return source_cols

    def load_dimredu_source_cols_and_params_and_features(self) -> (list, dict, list):
        source_cols = []
        params = {}
        features = []
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/dimredu/source_cols" in store.keys():
                source_cols_df = store.get("dimredu/source_cols")
                source_cols = source_cols_df["code"].tolist()
            if "/dimredu/params" in store.keys():
                params_df = store.get("dimredu/params")
                params = dict(zip(params_df["key"], params_df["value"]))
            if "/dimredu/features" in store.keys():
                features_df = store.get("dimredu/features")
                features = features_df["feat"].tolist()
            return source_cols, params, features

    def load_profile(self) -> dict:
        with pd.HDFStore(self.filepath, mode="r") as store:
            profile_df = store.get("profile")
            profile_dict = dict(zip(profile_df["key"], profile_df["value"]))
            return profile_dict
