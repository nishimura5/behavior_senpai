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
            else:
                print("invalid proc_history.")
        self.newest_proc_history = proc_history_list[-1]

    def validate_model(self, model_name):
        if self.attrs["model"] != model_name:
            print(f"model_name({model_name}) unmatch.")
            return False
        return True

    def validate_newest_history_proc(self, proc_name, model_name):
        if self.validate_model(model_name) is False:
            return False
        if self.newest_proc_history["type"] != proc_name:
            print(f"proc_name({proc_name}) unmatch.")
            return False
        if len(self.newest_proc_history["source_cols"]) == 0:
            print("source_cols is empty.")
            return False
        return True

    def get_source_cols(self):
        return self.newest_proc_history["source_cols"]

    def get_params(self):
        return self.newest_proc_history["params"]


def make_history_dict(feat_type, source_cols, params):
    history_dict = {"type": feat_type, "source_cols": source_cols, "params": params}
    return history_dict
