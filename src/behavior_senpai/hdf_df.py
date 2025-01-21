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
    profile: dictionary
    """

    def __init__(self, filepath: str):
        """
        Initialize storage with HDF filepath

        Args:
            filepath: Path to HDF file
        """
        self.filepath = filepath

    def save_df(self, group_name: str, df: pd.DataFrame):
        """
        Save DataFrame to specified group in HDF store

        Args:
            group_name: Name of group to save to ('points', 'mixnorm', 'dimredu')
            df: DataFrame to save
        """
        with pd.HDFStore(self.filepath, mode="a") as store:
            # Save DataFrame
            print(f"{group_name}/df")
            store.put(f"{group_name}/df", df, format="table")

            # Save attributes DataFrame
            attrs_dict = {}
            attrs_dict["model"] = df.attrs["model"]
            attrs_dict["video_name"] = df.attrs["video_name"]
            attrs_df = pd.DataFrame({"key": list(attrs_dict.keys()), "value": list(attrs_dict.values())})
            store.put("attrs", attrs_df, format="table")

            # Save proc_history
            proc_history = df.attrs["proc_history"][-1]
            if isinstance(proc_history, dict) is False:
                print("not dict")

            track_name = {"key": ["track_name"], "value": [proc_history["track_name"]]}
            profile_df = pd.DataFrame(track_name)
            store.put("profile", profile_df, format="table")

            if group_name == "traj":
                pass
            if group_name == "points":
                source_cols_df = self._feat_to_df(proc_history["source_cols"])
                store.put(f"{group_name}/source_cols", source_cols_df, format="table")
            elif group_name == "mixnorm":
                source_cols_df = self._norm_to_df(proc_history["source_cols"])
                store.put(f"{group_name}/source_cols", source_cols_df, format="table")
            elif group_name == "dimredu":
                source_cols_df = self._bc_to_df(proc_history["source_cols"])
                store.put(f"{group_name}/source_cols", source_cols_df, format="table")
                feature_list = df.attrs["features"]
                feature_df = pd.DataFrame({"feat": feature_list})
                store.put(f"{group_name}/features", feature_df, format="table")
                params_dict = proc_history["params"]
                # stringify values
                params = {"key": [], "value": []}
                for key, value in params_dict.items():
                    params["key"].append(key)
                    params["value"].append(str(value))
                params_df = pd.DataFrame(params)
                store.put(f"{group_name}/params", params_df, format="table")

    def _feat_to_df(self, src_list):
        source_cols = {"code": [], "member": [], "point_a": [], "point_b": [], "point_c": []}
        for source_col in src_list:
            source_cols["code"].append(source_col[0])
            source_cols["member"].append(source_col[1])
            source_cols["point_a"].append(source_col[2])
            source_cols["point_b"].append(source_col[3])
            source_cols["point_c"].append(source_col[4])
        source_cols_df = pd.DataFrame(source_cols)
        return source_cols_df

    def _norm_to_df(self, src_list):
        source_cols = {"name": [], "member": [], "col_a": [], "op": [], "col_b": [], "normalize": []}
        for source_col in src_list:
            source_cols["name"].append(source_col[0])
            source_cols["member"].append(source_col[1])
            source_cols["col_a"].append(source_col[2])
            source_cols["op"].append(source_col[3])
            source_cols["col_b"].append(source_col[4])
            source_cols["normalize"].append(source_col[5])
        source_cols_df = pd.DataFrame(source_cols)
        return source_cols_df

    def _bc_to_df(self, src_list):
        source_cols = {"code": []}
        for source_col in src_list:
            source_cols["code"].append(source_col)
        source_cols_df = pd.DataFrame(source_cols)
        return source_cols_df

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
            df = store.get(f"dimredu/df")

            attrs_df = store.get("attrs")
            attrs_dict = dict(zip(attrs_df["key"], attrs_df["value"]))
            df.attrs = attrs_dict

            # Load proc_history
            profile_df = store.get("profile")
            profile_dict = dict(zip(profile_df["key"], profile_df["value"]))

            params_df = store.get("dimredu/params")
            profile_dict["params"] = dict(zip(params_df["key"], params_df["value"]))
            profile_dict["type"] = "dimredu"

            features_df = store.get("dimredu/features")
            features = features_df["feat"].tolist()
            df.attrs["features"] = features

            source_cols_df = store.get("dimredu/source_cols")
            source_cols = source_cols_df["code"].tolist()
            profile_dict["source_cols"] = source_cols
            df.attrs["proc_history"] = [profile_dict]

        self._print_df_info(df)
        return df

    def load_points_df(self) -> pd.DataFrame:
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
        with pd.HDFStore(self.filepath, mode="r") as store:
            if "/mixnorm/df" not in store.keys():
                print("No mixnorm data in HDF")
                return None
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

    def load_profile(self) -> dict:
        with pd.HDFStore(self.filepath, mode="r") as store:
            profile_df = store.get("profile")
            profile_dict = dict(zip(profile_df["key"], profile_df["value"]))
            return profile_dict
