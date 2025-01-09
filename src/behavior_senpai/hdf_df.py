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
    profile
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

    def load_df(self, group_name: str) -> pd.DataFrame:
        """
        Load DataFrame from specified group

        Args:
            group_name: Name of group to load ('points', 'mixnorm', 'dimredu')

        Returns:
            pd.DataFrame: Loaded DataFrame
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            # bc/df -> used in scene_table
            df = store.get(f"{group_name}/df")

            attrs_df = store.get("attrs")
            attrs_dict = dict(zip(attrs_df["key"], attrs_df["value"]))
            df.attrs = attrs_dict

            # Load proc_history
            profile_df = store.get("profile")
            profile_dict = dict(zip(profile_df["key"], profile_df["value"]))

            source_cols = []
            source_cols_df = store.get(f"{group_name}/source_cols")
            if group_name == "points":
                print(store.keys())
                if "/traj/df" in store.keys():
                    traj_df = store.get("traj/df")
                    traj_df = traj_df.drop(columns="timestamp")
                    df = pd.concat([df, traj_df], axis=1)
                print(df)
                source_cols = self._df_to_feat(source_cols_df)
                profile_dict["type"] = "points"
            elif group_name == "mixnorm":
                source_cols = self._df_to_norm(source_cols_df)
                profile_dict["type"] = "mix"

            if group_name == "dimredu":
                params_df = store.get(f"{group_name}/params")
                profile_dict["type"] = "dimredu"
                source_cols, profile_dict["params"] = self._df_to_bc(source_cols_df, params_df)
                features_df = store.get(f"{group_name}/features")
                features = features_df["feat"].tolist()
                df.attrs["features"] = features

            profile_dict["source_cols"] = source_cols
            df.attrs["proc_history"] = [profile_dict]

        return df

    def _df_to_feat(self, source_cols_df: pd.DataFrame):
        source_cols = []
        for _, row in source_cols_df.iterrows():
            source_cols.append([row["code"], row["member"], row["point_a"], row["point_b"], row["point_c"]])
        return source_cols

    def _df_to_norm(self, source_cols_df: pd.DataFrame):
        source_cols = []
        for _, row in source_cols_df.iterrows():
            source_cols.append([row["name"], row["member"], row["col_a"], row["op"], row["col_b"], row["normalize"]])
        return source_cols

    def _df_to_bc(self, sources, params: pd.DataFrame):
        source_cols = []
        for _, row in sources.iterrows():
            source_cols.append(row["code"])
        params_dict = {}
        for _, row in params.iterrows():
            params_dict[row["key"]] = row["value"]
        return source_cols, params_dict

    def load_profile(self):
        with pd.HDFStore(self.filepath, mode="r") as store:
            profile_df = store.get("profile")
            profile_dict = dict(zip(profile_df["key"], profile_df["value"]))
            return profile_dict
