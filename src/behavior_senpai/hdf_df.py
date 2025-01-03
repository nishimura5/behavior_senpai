import pandas as pd


class DataFrameStorage:
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
            group_name: Name of group to save to ('feat', 'norm', 'bc')
            df: DataFrame to save
        """
        with pd.HDFStore(self.filepath, mode="a") as store:
            # Save DataFrame
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
            if group_name == "feat":
                setting_df, source_cols_df = self._feat_to_df(proc_history)
            elif group_name == "norm":
                setting_df, source_cols_df = self._norm_to_df(proc_history)
            elif group_name == "bc":
                setting_df, source_cols_df = self._bc_to_df(proc_history)
                feature_list = df.attrs["features"]
                feature_df = pd.DataFrame({"feat": feature_list})
                store.put(f"{group_name}/features", feature_df, format="table")
            print("soutce_cols_df")
            print(source_cols_df)
            print("setting_df")
            print(setting_df)
            store.put(f"{group_name}/settings", setting_df, format="table")
            store.put(f"{group_name}/source_cols", source_cols_df, format="table")

    def _feat_to_df(self, src_dict):
        settings = {"key": [], "value": []}
        for key, value in src_dict.items():
            if key == "source_cols":
                source_cols = {"code": [], "member": [], "point_a": [], "point_b": [], "point_c": []}
                for source_col in value:
                    source_cols["code"].append(source_col[0])
                    source_cols["member"].append(source_col[1])
                    source_cols["point_a"].append(source_col[2])
                    source_cols["point_b"].append(source_col[3])
                    source_cols["point_c"].append(source_col[4])
            elif key == "params":
                continue
            else:
                settings["key"].append(key)
                settings["value"].append(value)
        setting_df = pd.DataFrame(settings)
        source_cols_df = pd.DataFrame(source_cols)
        return setting_df, source_cols_df

    def _norm_to_df(self, src_dict):
        settings = {"key": [], "value": []}
        for key, value in src_dict.items():
            if key == "source_cols":
                source_cols = {"name": [], "member": [], "col_a": [], "op": [], "col_b": [], "normalize": []}
                for source_col in value:
                    source_cols["name"].append(source_col[0])
                    source_cols["member"].append(source_col[1])
                    source_cols["col_a"].append(source_col[2])
                    source_cols["op"].append(source_col[3])
                    source_cols["col_b"].append(source_col[4])
                    source_cols["normalize"].append(source_col[5])
            elif key == "params":
                continue
            else:
                settings["key"].append(key)
                settings["value"].append(value)
        setting_df = pd.DataFrame(settings)
        source_cols_df = pd.DataFrame(source_cols)
        return setting_df, source_cols_df

    def _bc_to_df(self, src_dict):
        params = {"key": [], "value": []}
        source_cols = {"feat": []}
        for key, value in src_dict.items():
            if key == "source_cols":
                for source_col in value:
                    source_cols["feat"].append(source_col)
            elif key == "params":
                for k, v in value.items():
                    params["key"].append(k)
                    params["value"].append(str(v))
                continue
        setting_df = pd.DataFrame(params)
        source_cols_df = pd.DataFrame(source_cols)
        return setting_df, source_cols_df

    def load_df(self, group_name: str) -> pd.DataFrame:
        """
        Load DataFrame from specified group

        Args:
            group_name: Name of group to load ('feat', 'norm', 'bc')

        Returns:
            pd.DataFrame: Loaded DataFrame
        """
        with pd.HDFStore(self.filepath, mode="r") as store:
            df = store.get(f"{group_name}/df")

            attrs_df = store.get("attrs")
            attrs_dict = dict(zip(attrs_df["key"], attrs_df["value"]))
            df.attrs = attrs_dict

            # Load proc_history
            setting_df = store.get(f"{group_name}/settings")
            settings = {}
            for key, value in zip(setting_df["key"], setting_df["value"]):
                settings[key] = value

            source_cols = []
            source_cols_df = store.get(f"{group_name}/source_cols")
            if group_name == "feat":
                source_cols = self._df_to_feat(source_cols_df)
            elif group_name == "norm":
                source_cols = self._df_to_norm(source_cols_df)

            params_df = store.get(f"{group_name}/settings")
            if group_name == "bc":
                settings["type"] = "dimredu"
                source_cols, settings["params"] = self._df_to_bc(source_cols_df, params_df)
                features_df = store.get(f"{group_name}/features")
                features = features_df["feat"].tolist()
                df.attrs["features"] = features

            settings["source_cols"] = source_cols
            df.attrs["proc_history"] = [settings]

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
            source_cols.append(row["feat"])
        params_dict = {}
        for _, row in params.iterrows():
            params_dict[row["key"]] = row["value"]
        return source_cols, params_dict
